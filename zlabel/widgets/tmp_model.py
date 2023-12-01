from enum import Enum
import os
import json
import functools

import numpy as np
import cv2
from label_studio_converter import brush
from typing import List, Dict, Literal, Optional
from uuid import uuid4
from sam_predictor import SAMPredictor
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.utils import get_image_local_path, InMemoryLRUDictCache

LABEL_STUDIO_ACCESS_TOKEN = os.environ.get("LABEL_STUDIO_ACCESS_TOKEN")
LABEL_STUDIO_HOST = os.environ.get("LABEL_STUDIO_HOST")
SAM_CHOICE = os.environ.get("SAM_CHOICE", "MobileSAM")  # other option is just SAM
PREDICTOR = SAMPredictor(SAM_CHOICE)


class OutType(Enum):
    BBOX = 0
    MASK = 1


class CtxType(Enum):
    KEYPOINT = "keypointlabels"
    RECTANGLE = "rectanglelabels"


class PointMode(Enum):
    ONE = "one"
    ALL = "all"


class SamMLBackend(LabelStudioMLBase):
    def __init__(
        self,
        project_id: str | None = None,
        out_type: OutType = OutType.BBOX,
    ):
        super().__init__(project_id)
        self.out_type = out_type
        self.ctx_type: CtxType = None
        self.threshold = 80
        self.use_cv: bool = False
        self.point_mode: PointMode = PointMode.ONE
        self._tasks: List[Dict] = None
        # x, y, w, h
        # self.shifts = [-1.0, -1.0, 1.0, 1.0]
        self.shifts = [0.0, 0.0, 0.5, 0.5]

    def refresh_back_args(self):
        if len(self._tasks) == 0:
            return
        from_names = [
            "number_threshold",
            "rect_cv_sam",
            "point_mode_choice",
        ]
        results = {}
        for draft in self._tasks[0].get(
            "drafts", self._tasks[0].get("annotations", [])
        ):
            for result in draft.get("result", []):
                for from_name in from_names:
                    if result.get("from_name", "") == from_name:
                        results[from_name] = result
                if all([name in results for name in from_names]):
                    break
            if all([name in results for name in from_names]):
                break

        # print(f"{results=}")
        try:
            self.threshold = results[from_names[0]]["value"]["number"]
        except KeyError:
            # self.threshold = 80
            ...
        try:
            self.use_cv = results[from_names[1]]["value"]["choices"][0] == "CV"
        except KeyError:
            # self.use_cv = False
            ...
        try:
            self.point_mode = PointMode(results[from_names[2]]["value"]["choices"][0])
        except KeyError:
            # self.point_mode = PointMode.ONE
            ...

    def rectangles_cv(self, img, threshold: int, merge_one: bool = False):
        # img = cv2.blur(img, (2, 2))
        canny_out = cv2.Canny(img, threshold, threshold * 2)
        contours, _ = cv2.findContours(
            canny_out,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        # contours = [cv2.approxPolyDP(c, 3, True) for c in contours]
        if merge_one:
            new_contours = []
            for c in contours:
                new_contours.extend(list(c))
            rects = [cv2.boundingRect(np.array(new_contours))]
        else:
            rects = [cv2.boundingRect(m) for m in contours]
        areas = [w * h for _, _, w, h in rects]
        counts, bins = np.histogram(areas, bins="auto")
        area_most = bins[np.argmax(counts) + 1]
        print(f"{areas=}, {area_most=}")
        idxs = np.where((areas > area_most * 0.3) & (areas < area_most * 8))[0]
        return [rects[i] for i in idxs]

    def rectangles_to_results(
        self,
        rects: List,
        from_name: str,
        to_name: str,
        label: str,
        x0: float,
        y0: float,
        width: float,
        height: float,
        scores: List[float] = None,
    ):
        scores = scores or [1.0 for _ in range(len(rects))]
        results = []
        for score, rect in zip(scores, rects):
            x, y, w, h = rect
            result = {
                "from_name": from_name,
                "to_name": to_name,
                "type": "rectanglelabels",
                "value": {
                    "rectanglelabels": [label],
                    "x": self.map_hw(x + x0 + self.shifts[0], width),
                    "y": self.map_hw(y + y0 + self.shifts[1], height),
                    "width": self.map_hw(w + self.shifts[2], width),
                    "height": self.map_hw(h + self.shifts[3], height),
                },
                "score": float(score),
                "area": w * h,
                "id": str(uuid4())[:4],
            }
            results.append(result)
        # print(f"{results=}")
        return results

    def is_rect_valid(self, areas: List[float], area: float):
        counts, bins = np.histogram(areas, bins="auto")
        area_most = bins[np.argmax(counts) + 1]
        # print(f"{area=}, {area_most=}")
        if any([area > area_most * 10, area < area_most * 0.25]):
            return False
        return True

    def map_hw(self, v: int | float, hw: float):
        return float(v) / hw * 100

    def predict(
        self,
        tasks: List[Dict],
        context: Optional[Dict] = None,
        **kwargs,
    ) -> List[Dict]:
        """Returns the predicted mask for a smart keypoint that has been placed."""
        self._tasks = tasks
        self.refresh_back_args()
        # with open("tasks.json", "w", encoding="utf-8") as f:
        #     json.dump(tasks, f, indent=4)
        match self.out_type:
            case OutType.BBOX:
                from_name, to_name, value = self.get_first_tag_occurence(
                    "RectangleLabels",
                    "Image",
                )
            case OutType.MASK:
                from_name, to_name, value = self.get_first_tag_occurence(
                    "BrushLabels",
                    "Image",
                )
            case _:
                raise NotImplementedError

        # print("<Context>: ", context)

        if not context or not context.get("result"):
            # if there is no context, no interaction has happened yet
            return []

        image_width = context["result"][0]["original_width"]
        image_height = context["result"][0]["original_height"]

        # collect context information
        point_coords = []
        point_labels = []
        input_box = None
        selected_label = None
        for ctx in context["result"]:
            x: float = ctx["value"]["x"] * image_width / 100
            y: float = ctx["value"]["y"] * image_height / 100
            try:
                self.ctx_type = CtxType(ctx["type"])
            except ValueError:
                raise NotImplementedError(f"context type {ctx['type']} not supported")
            selected_label: str = ctx["value"][self.ctx_type.value][0]
            if self.ctx_type == CtxType.KEYPOINT:
                if self.point_mode == PointMode.ONE:
                    point_labels.append(round(ctx["is_positive"]))
                    point_coords.append([round(x), round(y)])
            elif self.ctx_type == CtxType.RECTANGLE:
                box_width: float = ctx["value"]["width"] * image_width / 100
                box_height: float = ctx["value"]["height"] * image_height / 100
                input_box = [
                    x,
                    y,
                    box_width + x,
                    box_height + y,
                ]
            else:
                raise NotImplementedError

        print(f"{self.use_cv=}, {self.point_mode=}, {self.threshold=}, {input_box=}")
        img_path: str = tasks[0]["data"][value]
        image_path = get_image_local_path(
            img_path,
            label_studio_access_token=LABEL_STUDIO_ACCESS_TOKEN,
            label_studio_host=LABEL_STUDIO_HOST,
        )
        image = cv2.imread(image_path)
        xb, yb, xb1, yb1 = 0, 0, 0, 0
        if self.ctx_type == CtxType.RECTANGLE:
            input_box: List[int] = [round(i) for i in input_box]
            xb, yb, xb1, yb1 = input_box
            image = image[yb:yb1, xb:xb1]
        rects = self.rectangles_cv(image, self.threshold, False)
        print(f"Generated {len(rects)} objects")
        if self.use_cv and (
            self.ctx_type == CtxType.RECTANGLE
            or (self.ctx_type == CtxType.KEYPOINT and self.point_mode == PointMode.ALL)
        ):
            results = self.rectangles_to_results(
                rects,
                from_name,
                to_name,
                selected_label,
                xb,
                yb,
                image_width,
                image_height,
            )
            return [{"result": results, "model_version": PREDICTOR.model_name}]
        elif self.use_cv and self.ctx_type == CtxType.RECTANGLE:
            point_coords = [
                [x + xx + ww / 2, y + yy + hh / 2] for xx, yy, ww, hh in rects
            ]
            point_labels = [1.0 for _ in range(len(rects))]

        # print(f"{point_coords=}, {point_labels=}, {input_box=}")

        predictor_results = PREDICTOR.predict(
            img_path=img_path,
            point_coords=point_coords or None,
            point_labels=point_labels or None,
            input_box=input_box,
        )

        predictions = self.get_results(
            masks=predictor_results["masks"],
            probs=predictor_results["probs"],
            width=image_width,
            height=image_height,
            from_name=from_name,
            to_name=to_name,
            label=selected_label,
        )

        return predictions

    def get_results(self, masks, probs, width, height, from_name, to_name, label):
        # print(from_name, to_name, label)
        results = []
        print(f"{self.ctx_type=}")
        for mask, prob in zip(masks, probs):
            match self.out_type:
                case OutType.MASK:
                    # converting the mask from the model to RLE format which is usable in Label Studio
                    mask = mask * 255
                    rle = brush.mask2rle(mask)
                    results.append(
                        {
                            "id": str(uuid4())[:4],
                            "from_name": from_name,
                            "to_name": to_name,
                            "original_width": width,
                            "original_height": height,
                            "image_rotation": 0,
                            "value": {
                                "format": "rle",
                                "rle": rle,
                                "brushlabels": [label],
                            },
                            "score": float(prob),
                            "type": "brushlabels",
                            "readonly": False,
                        }
                    )
                case OutType.BBOX:
                    rects = self.rectangles_cv(mask * 255, self.threshold, False)
                    if (
                        self.ctx_type == CtxType.KEYPOINT
                        and self.point_mode == PointMode.ONE
                    ):
                        rects = self.rectangles_cv(mask * 255, self.threshold, True)
                    results = self.rectangles_to_results(
                        rects=rects,
                        from_name=from_name,
                        to_name=to_name,
                        label=label,
                        x0=0,
                        y0=0,
                        width=width,
                        height=height,
                        scores=[prob for _ in range(len(rects))],
                    )

        return [{"result": results, "model_version": PREDICTOR.model_name}]


if __name__ == "__main__":
    # test the model
    model = SamMLBackend()
    model.use_label_config(
        """
<View>
    <View style="display:flex;align-items:start;gap:8px;flex-direction:row">
        <Image name="image" value="$url"  zoom="true" zoomControl="true" rotateControl="true"/>
        <View>
            <Header value="Brush Labels"/>
            <BrushLabels name="tag" toName="image">
            <Label value="OBJ1" background="#FFA39E"/>
            </BrushLabels>
            <Header value="Rectangle Labels"/>
            <RectangleLabels name="tag3" toName="image" smart="true" showInline="true">
                <Label value="OBJ1" background="#FFA39E"/>
            </RectangleLabels>
                <Header value="Point Labels"/>
            <KeyPointLabels name="tag2" toName="image" smart="true">
                <Label value="OBJ1" background="#FFA39E"/>
            </KeyPointLabels>
            <Header value="选择标签"/>
            <Choices name="choice" showInline="false" toName="image" value="$labels"/>
        </View>
    </View>
    <Header value="文件名: $filename"/>
</View>
    """
    )
    results = model.predict(
        tasks=[
            {
                "data": {
                    "id": 876,
                    "filename": "垂穗披碱草684-2.png",
                    "url": "/data/local-files/?d=seeds_data/exported_pngs/%E5%9E%82%E7%A9%97%E6%8A%AB%E7%A2%B1%E8%8D%89684-2.png",
                    "labels": [{"value": "垂穗披碱草"}, {"value": "垂穗披碱草684"}],
                }
            },
        ],
        context={
            "result": [
                {
                    "original_width": 512,
                    "original_height": 512,
                    "image_rotation": 0,
                    "value": {
                        "x": 14.19284940411701,
                        "y": 18.95991332611051,
                        "width": 81.79848320693391,
                        "height": 74.21451787648971,
                        "rotation": 0,
                        "rectanglelabels": ["OBJ1"],
                    },
                    "id": "HfIXMbds-z",
                    "from_name": "tag3",
                    "to_name": "image",
                    "type": "rectanglelabels",
                    "origin": "manual",
                }
            ]
        },
    )
    import json

    results[0]["result"][0]["value"][
        "rle"
    ] = f'...{len(results[0]["result"][0]["value"]["rle"])} integers...'
    print(json.dumps(results, indent=2))

import unittest
import cv2
from rich import print

from zlabel.models.sam_onnx import SamOnnxModel
from zlabel.utils.enums import AutoMode
from zlabel.utils.project import Label, ResultType
from zlabel.widgets.zworker import ZSamWorker


class TestZWroker(unittest.TestCase):
    model = SamOnnxModel(
        "data/sam_vit_l_encoder_quantized.onnx",
        "data/sam_vit_l_decoder_quantized.onnx",
    )

    def test_point_sam(self):
        points = [(150, 85)]
        labels = [1]
        self.run_default(points, labels, ResultType.POINT, AutoMode.SAM)

    def test_point_cv(self):
        points = [(150, 85)]
        labels = [1]
        self.run_default(points, labels, ResultType.POINT, AutoMode.CV)


    def test_rectangle_sam(self):
        points = [(130, 75, 175, 95)]
        labels = [1]
        self.run_default(points, labels, ResultType.RECTANGLE, AutoMode.SAM)

    def test_rectangle_cv(self):
        points = [(130, 75, 175, 95)]
        labels = [1]
        self.run_default(points, labels, ResultType.RECTANGLE, AutoMode.CV)


    def test_rectangle_sam_cv(self):
        points = [(130, 75, 175, 95)]
        labels = [1]
        self.run_default(points, labels, ResultType.RECTANGLE, AutoMode.SAM & AutoMode.CV, threshold=50)

    def run_default(self, points, labels, result_type, auto_mode, threshold=100):
        img = cv2.imread("401.png")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        worker = ZSamWorker(
            self.model,
            "TEST_RESULT_ID",
            [Label.default()],
            result_type,
            auto_mode,
            threshold=threshold,
            parent=None,
        )
        res = worker.run(img, points, labels)
        # print(r)
        for r in res:
            rr = r.result
            x, y, w, h = [int(i) for i in [rr.x, rr.y, rr.w, rr.h]]
            img = cv2.rectangle(img, (x, y), (x+w, y +h), (255, 0, 0), 1)
        cv2.imwrite(f"test/{result_type.name}_{auto_mode.name}.png", img)

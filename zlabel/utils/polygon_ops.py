from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union


def merge_polygons(polygons: list[list[tuple[float, float]]]) -> list[tuple[float, float]]:
    if not polygons:
        return []
    if len(polygons) == 1:
        return polygons[0]

    shapely_polygons = []
    for poly in polygons:
        if len(poly) >= 3:
            shapely_polygons.append(Polygon(poly))
    if not shapely_polygons:
        return []

    merged = unary_union(shapely_polygons)
    if isinstance(merged, Polygon):
        return list(merged.exterior.coords[:-1])
    elif isinstance(merged, MultiPolygon):
        # TODO: Merge multiple seperate polygons
        ...
    else:
        return []

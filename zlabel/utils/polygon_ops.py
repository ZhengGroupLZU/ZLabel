from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union


def merge_polygons(polygons: list[list[tuple[float, float]]]) -> list[tuple[float, float]]:
    if not polygons:
        return []

    valid = [p for p in polygons if len(p) >= 3]
    if not valid:
        return []
    if len(valid) == 1:
        # Return the input unchanged: keeps interior rings (holes) and the
        # closing vertex that the exterior ring would drop.
        return valid[0]

    shapely_polygons = [Polygon(p) for p in valid]
    merged = unary_union(shapely_polygons)
    if isinstance(merged, Polygon):
        return list(merged.exterior.coords[:-1])
    elif isinstance(merged, MultiPolygon):
        # TODO: Merge multiple seperate polygons
        return []
    else:
        return []

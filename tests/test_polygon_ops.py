from zlabel.utils.polygon_ops import merge_polygons


def test_empty():
    assert merge_polygons([]) == []


def test_single():
    poly = [(0, 0), (1, 0), (1, 1)]
    assert merge_polygons([poly]) == poly


def test_merge_overlapping():
    a = [(0, 0), (2, 0), (2, 2), (0, 2)]
    b = [(1, 1), (3, 1), (3, 3), (1, 3)]
    merged = merge_polygons([a, b])
    assert len(merged) >= 4
    xs = [p[0] for p in merged]
    ys = [p[1] for p in merged]
    assert min(xs) == 0 and max(xs) == 3
    assert min(ys) == 0 and max(ys) == 3


def test_disjoint_returns_empty():
    # unary_union yields a MultiPolygon, which merge_polygons does not merge yet
    a = [(0, 0), (1, 0), (1, 1), (0, 1)]
    b = [(5, 5), (6, 5), (6, 6), (5, 6)]
    assert merge_polygons([a, b]) == []


def test_too_few_vertices():
    assert merge_polygons([[(0, 0), (1, 1)]]) == []


def test_all_invalid_returns_empty():
    assert merge_polygons([[]]) == []

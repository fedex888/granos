import datetime as dt

from pipeline.src.normalize import Point, build_history, detect_outliers


def test_build_history_forward_fill():
    fx_rows = [
        {"date": dt.date(2024, 1, 1), "compra": 100.0, "venta": 101.0},
        {"date": dt.date(2024, 1, 5), "compra": 200.0, "venta": 202.0},
    ]
    pts = [
        {"date": dt.date(2024, 1, 2), "price_ars": 1000.0, "quality": "operated"},
        {"date": dt.date(2024, 1, 6), "price_ars": 4000.0, "quality": "operated"},
        {"date": dt.date(2024, 1, 7), "price_ars": None, "quality": "operated"},  # S/C
    ]
    out = build_history(pts, fx_rows, "BCR")
    assert len(out) == 2
    assert out[0].price_usd == 10.0   # 1000 / 100
    assert out[1].price_usd == 20.0   # 4000 / 200 (forward-fill usa el 200 del 1/5)


def test_detect_outliers():
    pts = [
        Point(dt.date(2024, 1, 1), 100.0, 1.0, 100.0, "operated", "BCR"),
        Point(dt.date(2024, 1, 2), 200.0, 2.0, 100.0, "operated", "BCR"),   # +100% -> outlier
        Point(dt.date(2024, 1, 3), 210.0, 2.1, 100.0, "operated", "BCR"),
    ]
    outliers = detect_outliers(pts)
    assert outliers == {dt.date(2024, 1, 2)}
    assert pts[1].outlier is True

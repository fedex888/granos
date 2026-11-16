import datetime as dt
import math

from pipeline.src.normalize import Point
from pipeline.src.signals import cap_signal, evaluate_series


def make_series(prices, start=dt.date(2024, 1, 1)):
    pts = []
    d = start
    for p in prices:
        pts.append(Point(date=d, price_ars=p * 1000.0, price_usd=p,
                         fx_usd_ars=1000.0, quality="operated", source="BCR"))
        d += dt.timedelta(days=1)
    return pts


def test_insufficient_data():
    prices = [100.0 + i for i in range(100)]  # < 250 observaciones
    pts = make_series(prices)
    res = evaluate_series(pts, pts[-1].date + dt.timedelta(days=1), "strong")
    assert res[-1]["insufficient"] is True
    assert res[-1]["signal_buy"] == "insufficient_data"


def test_scores_and_rsi_bounded():
    prices = [100 + 10 * math.sin(i / 20) + i * 0.5 for i in range(300)]
    pts = make_series(prices)
    res = evaluate_series(pts, pts[-1].date + dt.timedelta(days=1), "strong")
    last = res[-1]
    assert 0 <= last["score_buy"] <= 100
    assert 0 <= last["score_sell"] <= 100
    assert last["rsi_14"] is None or 0 <= last["rsi_14"] <= 100
    assert last["ma_50_usd"] is not None
    assert last["ma_200_usd"] is not None


def test_new_low_emits_strong_buy():
    prices = [200 - i * 0.1 for i in range(300)]  # bajista: el último es mínimo de 2 años
    pts = make_series(prices)
    res = evaluate_series(pts, pts[-1].date + dt.timedelta(days=1), "strong")
    assert res[-1]["signal_buy"] == "strong"


def test_girasol_cap_watch():
    prices = [200 - i * 0.1 for i in range(300)]
    pts = make_series(prices)
    res = evaluate_series(pts, pts[-1].date + dt.timedelta(days=1), "watch")
    # La señal cruda de compra sería strong (nuevo mínimo), el tope la deja en watch.
    assert res[-1]["signal_buy"] == "watch"
    # La de venta es none en una serie bajista y el tope no la modifica.
    assert res[-1]["signal_sell"] == "none"


def test_no_lookahead():
    prices = [100 + 10 * math.sin(i / 25) + i * 0.3 for i in range(320)]
    pts = make_series(prices)
    today = pts[-1].date + dt.timedelta(days=1)
    full = evaluate_series(pts, today, "strong")
    trunc = evaluate_series(pts[:261], today, "strong")
    assert trunc[-1]["signal_buy"] == full[260]["signal_buy"]
    assert trunc[-1]["score_buy"] == full[260]["score_buy"]


def test_cap_signal():
    assert cap_signal("strong", "watch") == "watch"
    assert cap_signal("buy", "watch") == "watch"
    assert cap_signal("watch", "watch") == "watch"
    assert cap_signal("strong", "strong") == "strong"

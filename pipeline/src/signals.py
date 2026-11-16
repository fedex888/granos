"""Cálculo de métricas, scores y señales (reglas del plan §7)."""
from __future__ import annotations

import datetime as dt
import statistics

from .config import (
    MA_FAST,
    MA_SLOW,
    MIN_OBSERVATIONS,
    RSI_PERIOD,
    SIGNAL_RANK,
    STALE_BUSINESS_DAYS,
    WINDOW_DAYS,
)
from .normalize import Point
from .util import business_days_between


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _rsi_wilder(prices: list[float], period: int = RSI_PERIOD) -> float | None:
    if len(prices) < period + 1:
        return None
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0.0 for d in deltas]
    losses = [-d if d < 0 else 0.0 for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def _sma(prices: list[float], n: int) -> float | None:
    if len(prices) < n:
        return None
    return sum(prices[-n:]) / n


def last_operated_date(points: list[Point]) -> dt.date | None:
    for p in reversed(points):
        if p.quality == "operated":
            return p.date
    return None


def is_fresh(points: list[Point], today: dt.date) -> bool:
    """Fresco: hay un operado con <= STALE_BUSINESS_DAYS días hábiles hasta hoy."""
    last = last_operated_date(points)
    if last is None:
        return False
    return business_days_between(last, today) <= STALE_BUSINESS_DAYS


def _quality_score(quality: str, fresh: bool) -> int:
    if not fresh:
        return 0
    return 100 if quality == "operated" else 70


def _compute_one(points: list[Point], i: int, today: dt.date) -> dict:
    """Métricas + scores + señal raw para la observación `i` (sin confirmación)."""
    current = points[i]
    prices = [p.price_usd for p in points]
    dates = [p.date for p in points]

    prior = [p for p in points[:i] if (current.date - p.date).days <= WINDOW_DAYS]
    window_prices = [p.price_usd for p in prior]

    base = {
        "i": i,
        "date": current.date,
        "price_usd": current.price_usd,
        "quality": current.quality,
        "raw_buy": "none",
        "raw_sell": "none",
        "score_buy": 0.0,
        "score_sell": 0.0,
        "percentile": None,
        "insufficient": False,
    }

    if len(prior) < MIN_OBSERVATIONS:
        base["insufficient"] = True
        base["raw_buy"] = "insufficient_data"
        base["raw_sell"] = "insufficient_data"
        return base

    low_2y = min(window_prices)
    low_date = prior[window_prices.index(low_2y)].date
    high_2y = max(window_prices)
    high_date = prior[window_prices.index(high_2y)].date
    avg_2y = statistics.fmean(window_prices)
    std_2y = statistics.pstdev(window_prices) if len(window_prices) > 1 else 0.0
    percentile = 100.0 * sum(1 for v in window_prices if v <= current.price_usd) / len(window_prices)
    distance_low = (current.price_usd / low_2y - 1) * 100.0 if low_2y else 0.0
    distance_high = (high_2y / current.price_usd - 1) * 100.0 if current.price_usd else 0.0
    zscore = (current.price_usd - avg_2y) / std_2y if std_2y > 0 else 0.0

    rsi = _rsi_wilder(prices[: i + 1])
    ma50 = _sma(prices[: i + 1], MA_FAST)
    ma200 = _sma(prices[: i + 1], MA_SLOW)
    ma50_prev = _sma(prices[:i], MA_FAST)
    slope50 = (ma50 - ma50_prev) if (ma50 is not None and ma50_prev is not None) else 0.0

    change_1d = (current.price_usd / prices[i - 1] - 1) * 100.0 if i >= 1 and prices[i - 1] else 0.0
    target30 = current.date - dt.timedelta(days=30)
    ref30 = None
    for j in range(i - 1, -1, -1):
        if dates[j] <= target30:
            ref30 = prices[j]
            break
    change_30d = (current.price_usd / ref30 - 1) * 100.0 if ref30 else 0.0

    fresh = is_fresh(points[: i + 1], today)
    last_op = last_operated_date(points[: i + 1])
    q_score = _quality_score(current.quality, fresh)

    metrics = {
        "low_2y_usd": low_2y,
        "low_2y_date": low_date,
        "high_2y_usd": high_2y,
        "high_2y_date": high_date,
        "avg_2y_usd": avg_2y,
        "percentile": percentile,
        "distance_from_low_pct": distance_low,
        "distance_from_high_pct": distance_high,
        "zscore": zscore,
        "rsi_14": rsi,
        "ma_50_usd": ma50,
        "ma_200_usd": ma200,
        "change_1d_pct": change_1d,
        "change_30d_pct": change_30d,
    }

    def scores(direction: str) -> float:
        if direction == "buy":
            s_perc = 100 - percentile
            s_dist = clamp(100 - distance_low * 5, 0, 100)
            s_z = clamp(50 - zscore * 25, 0, 100)
            s_rsi = clamp(100 - rsi if rsi is not None else 50, 0, 100)
            above = current.price_usd > ma50 if ma50 is not None else False
            s_trend = 100 if (above and slope50 > 0) else (50 if above else 0)
        else:
            s_perc = percentile
            s_dist = clamp(100 - distance_high * 5, 0, 100)
            s_z = clamp(50 + zscore * 25, 0, 100)
            s_rsi = clamp(rsi if rsi is not None else 50, 0, 100)
            below = current.price_usd < ma50 if ma50 is not None else False
            s_trend = 100 if (below and slope50 < 0) else (50 if below else 0)
        return (
            0.35 * s_perc + 0.25 * s_dist + 0.15 * s_z
            + 0.10 * s_rsi + 0.10 * s_trend + 0.05 * q_score
        )

    score_buy = scores("buy")
    score_sell = scores("sell")

    def classify(direction: str, score: float) -> str:
        if direction == "buy":
            new_extreme = current.price_usd <= low_2y
            if new_extreme or (score >= 80 and percentile <= 10):
                return "strong"
            if score >= 70 and percentile <= 20 and fresh:
                return "buy"
            if score >= 60 and percentile <= 30:
                return "watch"
            return "none"
        new_extreme = current.price_usd >= high_2y
        if new_extreme or (score >= 80 and percentile >= 90):
            return "strong"
        if score >= 70 and percentile >= 80 and fresh:
            return "sell"
        if score >= 60 and percentile >= 70:
            return "watch"
        return "none"

    base.update(metrics)
    base["score_buy"] = score_buy
    base["score_sell"] = score_sell
    base["raw_buy"] = classify("buy", score_buy)
    base["raw_sell"] = classify("sell", score_sell)
    base["fresh"] = fresh
    base["last_operated_date"] = last_op
    base["slope50"] = slope50
    base["avg_2y_usd"] = avg_2y
    return base


def _confirm(raw: str, prev_raw: str | None) -> str:
    """buy/sell (no fuertes) requieren 2 observaciones consecutivas."""
    if raw in ("buy", "sell"):
        if prev_raw not in (raw, "strong"):
            return "watch"
    return raw


def cap_signal(signal: str, max_signal: str) -> str:
    if SIGNAL_RANK[signal] > SIGNAL_RANK[max_signal]:
        return max_signal
    return signal


def evaluate_series(points: list[Point], today: dt.date | None = None, max_signal: str = "strong") -> list[dict]:
    """Evalúa toda la serie (sin lookahead) y aplica confirmación y tope.

    `today` es la fecha de la corrida para el cálculo de frescura. Si es None, se
    usa la fecha de cada observación (útil para el backtest, que evalúa as-of).
    Devuelve una lista con un dict por observación; el último es el "latest".
    """
    raw = []
    for i in range(len(points)):
        as_of = today if today is not None else points[i].date
        raw.append(_compute_one(points, i, as_of))
    for i, r in enumerate(raw):
        prev = raw[i - 1] if i > 0 else None
        for d in ("buy", "sell"):
            raw_sig = r["raw_" + d]
            if raw_sig == "insufficient_data":
                r["signal_" + d] = "insufficient_data"
                continue
            prev_sig = prev["raw_" + d] if prev else None
            r["signal_" + d] = cap_signal(_confirm(raw_sig, prev_sig), max_signal)
    return raw


def select_current(points: list[Point], today: dt.date) -> tuple[int, str]:
    """Índice del punto a mostrar y su calidad (puede ser 'stale').

    Si el último dato es estimado y hay un operado dentro de 5 días hábiles, se usa
    el operado y se marca 'stale' (plan §7.1). Con los datos actuales no se dispara.
    """
    i = len(points) - 1
    if points[i].quality == "estimated":
        for j in range(i - 1, -1, -1):
            if points[j].quality == "operated" and business_days_between(points[j].date, points[i].date) <= STALE_BUSINESS_DAYS:
                return j, "stale"
    return i, points[i].quality


def _round_metric(v):
    return None if v is None else round(float(v), 2)


def build_explanation(name: str, r: dict, mode: str) -> str:
    if r.get("insufficient"):
        return f"{name}: todavía no hay 2 años de datos para calcular la señal."
    if not r.get("fresh"):
        last_op = r.get("last_operated_date")
        date_str = last_op.isoformat() if last_op else r["date"].isoformat()
        return f"Dato desactualizado (última operación {date_str}). No se genera alerta hasta actualizar."
    price = r["price_usd"]
    if mode == "buy":
        if r["signal_buy"] == "strong" and price <= r["low_2y_usd"]:
            return (f"{name}: nuevo mínimo de 2 años. USD {price:.2f}/t. "
                    f"Puede seguir bajando; comprá por etapas.")
        if r["signal_buy"] in ("buy", "strong"):
            return (f"{name}: está {r['distance_from_low_pct']:.1f}% arriba del mínimo de 2 años "
                    f"(USD {r['low_2y_usd']:.2f}/t). El promedio de 2 años es USD {r['avg_2y_usd']:.2f}/t. "
                    f"Score {round(r['score_buy'])}/100.")
    else:
        if r["signal_sell"] == "strong" and price >= r["high_2y_usd"]:
            return f"{name}: nuevo máximo de 2 años. USD {price:.2f}/t. Considerá vender."
        if r["signal_sell"] in ("sell", "strong"):
            return (f"{name}: está {r['distance_from_high_pct']:.1f}% debajo del máximo de 2 años "
                    f"(USD {r['high_2y_usd']:.2f}/t). Score {round(r['score_sell'])}/100.")
    low = r.get("low_2y_usd")
    high = r.get("high_2y_usd")
    return (f"{name}: percentil {r['percentile']:.0f}. Mínimo de 2 años USD {low:.2f}/t, "
            f"máximo USD {high:.2f}/t. Sin señal clara.")


def build_latest_product(
    product_id: str,
    cfg: dict,
    points: list[Point],
    today: dt.date,
    source_url: str,
    updated_at: str,
) -> dict | None:
    """Arma el objeto de producto para `data/latest.json` (plan §6.1)."""
    if not points:
        return None

    idx, quality = select_current(points, today)
    current = points[idx]
    results = evaluate_series(points, today, cfg["max_signal"])
    r = results[idx]

    # Si elegimos un operado anterior en lugar del último estimado, la fecha mostrada
    # es la de ese operado y la calidad queda 'stale'.
    price_ars = current.price_ars
    price_usd = current.price_usd
    price_date = current.date

    mode = cfg["mode"]
    explanation = build_explanation(cfg["name"], r, mode)

    return {
        "id": product_id,
        "name": cfg["name"],
        "market": cfg["market"],
        "mode": mode,
        "price_ars": _round_metric(price_ars),
        "price_usd": _round_metric(price_usd),
        "price_date": price_date.isoformat(),
        "quality": quality,
        "change_1d_pct": _round_metric(r.get("change_1d_pct")),
        "change_30d_pct": _round_metric(r.get("change_30d_pct")),
        "low_2y_usd": _round_metric(r.get("low_2y_usd")),
        "low_2y_date": r.get("low_2y_date").isoformat() if r.get("low_2y_date") else None,
        "high_2y_usd": _round_metric(r.get("high_2y_usd")),
        "high_2y_date": r.get("high_2y_date").isoformat() if r.get("high_2y_date") else None,
        "avg_2y_usd": _round_metric(r.get("avg_2y_usd")),
        "percentile": _round_metric(r.get("percentile")),
        "distance_from_low_pct": _round_metric(r.get("distance_from_low_pct")),
        "distance_from_high_pct": _round_metric(r.get("distance_from_high_pct")),
        "zscore": _round_metric(r.get("zscore")),
        "rsi_14": _round_metric(r.get("rsi_14")),
        "ma_50_usd": _round_metric(r.get("ma_50_usd")),
        "ma_200_usd": _round_metric(r.get("ma_200_usd")),
        "score_buy": round(r.get("score_buy", 0)),
        "score_sell": round(r.get("score_sell", 0)),
        "signal_buy": r.get("signal_buy", "insufficient_data"),
        "signal_sell": r.get("signal_sell", "insufficient_data"),
        "explanation": explanation,
        "source": "BCR",
        "source_url": source_url,
        "updated_at": updated_at,
        # Campos internos (se descartan al publicar latest.json):
        "_fresh": bool(r.get("fresh", False)),
    }

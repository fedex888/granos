"""Normalización: convierte precios ARS a puntos canónicos con USD."""
from __future__ import annotations

import bisect
import datetime as dt
from dataclasses import dataclass, field

from .config import OUTLIER_DAILY_CHANGE
from .sources.fx import build_fx_map


@dataclass
class Point:
    date: dt.date
    price_ars: float
    price_usd: float
    fx_usd_ars: float
    quality: str          # operated | estimated
    source: str           # BCR | MAGyP
    outlier: bool = field(default=False)

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "price_ars": round(self.price_ars, 2),
            "price_usd": round(self.price_usd, 2),
            "fx_usd_ars": round(self.fx_usd_ars, 2),
            "quality": self.quality,
            "source": self.source,
        }


def build_history(
    points_ars: list[dict],
    fx_rows: list[dict],
    source: str,
) -> list[Point]:
    """Convierte [{date, price_ars, quality}] en puntos canónicos con USD.

    Aplica forward-fill del FX (último compra <= fecha del punto). Descarta días sin
    precio (S/C).
    """
    fx_map = build_fx_map(fx_rows)
    fx_dates = sorted(fx_map)

    out: list[Point] = []
    for p in points_ars:
        price_ars = p.get("price_ars")
        if price_ars is None or price_ars <= 0:
            continue
        d = p["date"]
        idx = bisect.bisect_right(fx_dates, d) - 1
        if idx < 0:
            continue
        fx = fx_map[fx_dates[idx]]
        out.append(
            Point(
                date=d,
                price_ars=float(p["price_ars"]),
                price_usd=float(p["price_ars"]) / fx,
                fx_usd_ars=fx,
                quality=p.get("quality", "operated"),
                source=source,
            )
        )
    return sorted(out, key=lambda x: x.date)


def detect_outliers(points: list[Point]) -> set[dt.date]:
    """Devuelve fechas cuya variación diaria operada supera el umbral.

    Compara cada observación operada con la operada inmediatamente anterior.
    """
    outliers: set[dt.date] = set()
    prev = None
    for p in points:
        if p.quality != "operated":
            continue
        if prev is not None and prev.price_usd:
            change = abs(p.price_usd / prev.price_usd - 1)
            if change > OUTLIER_DAILY_CHANGE:
                outliers.add(p.date)
        prev = p
    for p in points:
        if p.date in outliers:
            p.outlier = True
    return outliers

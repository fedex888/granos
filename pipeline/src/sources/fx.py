"""Descarga de la serie histórica de dólar oficial (ArgentinaDatos/BNA)."""
from __future__ import annotations

import datetime as dt

import httpx

from ..config import FX_URL, USER_AGENT
from ..util import parse_date


def fetch_series(client: httpx.Client, cap_date: dt.date) -> list[dict]:
    """Devuelve [{date, compra, venta}] ordenado, filtrando fechas futuras."""
    resp = client.get(FX_URL, headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    rows: list[dict] = []
    for item in data:
        d = parse_date(item.get("fecha"))
        compra = item.get("compra")
        if d is None or d > cap_date or not compra or compra <= 0:
            continue
        rows.append({"date": d, "compra": float(compra), "venta": float(item.get("venta") or 0)})

    return sorted(rows, key=lambda r: r["date"])


def build_fx_map(rows: list[dict]) -> dict[dt.date, float]:
    """Mapa fecha -> compra, listo para forward-fill."""
    return {r["date"]: r["compra"] for r in rows}


def fx_for(fx_map: dict[dt.date, float], dates: list[dt.date], target: dt.date) -> float | None:
    """Último compra disponible <= target (forward-fill)."""
    prev = [d for d in dates if d <= target]
    return fx_map[prev[-1]] if prev else None

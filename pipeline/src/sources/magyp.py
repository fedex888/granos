"""Descarga y parseo de la pizarra diaria de MAGyP (control cruzado / fallback)."""
from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup

from ..config import MAGYP_URL, USER_AGENT
from ..util import norm, parse_ar_number, parse_spanish_date


def parse_daily(html: str) -> dict:
    """Parsea el HTML y devuelve {date, prices: {nombre_producto: value}}.

    Solo la columna Rosario. `0.00` significa sin cotización.
    """
    soup = BeautifulSoup(html, "lxml")
    out: dict = {"date": None, "prices": {}, "headers": []}

    target = None
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if any("PRODUCTO" in r.get_text(" ", strip=True).upper() for r in rows):
            target = table
            break
    if target is None:
        raise ValueError("MAGyP: no se encontró la tabla de pizarra sobre puerto.")

    header = None
    rosario_idx = None
    for tr in target.find_all("tr"):
        cells = [re.sub(r"\s+", " ", c.get_text(" ", strip=True)) for c in tr.find_all(["th", "td"])]
        if not cells:
            continue
        if out["date"] is None:
            out["date"] = parse_spanish_date(cells[0])
        if any(norm(c) == "producto" for c in cells):
            header = [norm(c) for c in cells]
            out["headers"] = cells
            rosario_idx = header.index("rosario") if "rosario" in header else None
            continue
        if header and rosario_idx is not None and len(cells) > rosario_idx:
            out["prices"][norm(cells[0])] = parse_ar_number(cells[rosario_idx])

    return out


def fetch_daily(client: httpx.Client) -> dict:
    resp = client.get(MAGYP_URL, headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=60)
    resp.raise_for_status()
    return parse_daily(resp.text)

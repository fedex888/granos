"""Descarga y parseo de la fuente BCR (export XLSX histórico y pizarra del día)."""
from __future__ import annotations

import datetime as dt
import io
import re

import httpx
import openpyxl
from bs4 import BeautifulSoup

from ..config import BCR_CURRENT_URL, BCR_EXPORT_NODE, BCR_EXPORT_URL, USER_AGENT
from ..util import norm, parse_ar_number, parse_date


def _headers() -> dict:
    return {"User-Agent": USER_AGENT}


def parse_history_xlsx(content: bytes) -> list[dict]:
    """Parsea el XLSX de BCR y devuelve [{date, price_ars, quality}].

    Localiza la columna `Precio` por encabezado: girasol con `type=any` agrega una
    columna `(E)` antes del precio.
    """
    wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True, read_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    header_idx = None
    for i, row in enumerate(rows[:20]):
        cells = [norm(str(c)) if c is not None else "" for c in row]
        if any(c.startswith("fecha") for c in cells) and any(c.startswith("precio") for c in cells):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("BCR: no se encontró la fila de encabezado 'Fecha de operación | Precio'.")

    header = rows[header_idx]
    date_col = next(i for i, c in enumerate(header) if norm(str(c)).startswith("fecha"))
    price_col = next(i for i, c in enumerate(header) if norm(str(c)).startswith("precio"))
    quality_col = price_col - 1 if price_col - 1 > date_col else None

    points: list[dict] = []
    for row in rows[header_idx + 1:]:
        if not row or len(row) <= date_col or row[date_col] is None:
            continue
        date = parse_date(row[date_col])
        if date is None:
            continue
        price_raw = row[price_col] if price_col < len(row) else None
        marker = ""
        if quality_col is not None and quality_col < len(row) and row[quality_col] is not None:
            marker = str(row[quality_col])
        price = parse_ar_number(price_raw)
        if price is not None and price <= 0:
            price = None  # 0.0 no es un precio válido (plan §8.4: precio > 0)
        quality = "estimated" if "(E)" in marker or "(E)" in str(price_raw or "") else "operated"
        points.append({"date": date, "price_ars": price, "quality": quality})

    return sorted(points, key=lambda p: p["date"])


def fetch_history(
    client: httpx.Client,
    product_id: int,
    bcr_type: str,
    start: dt.date,
    end: dt.date,
) -> list[dict]:
    url = BCR_EXPORT_URL.format(node=BCR_EXPORT_NODE)
    params = {
        "product": product_id,
        "type": bcr_type,
        "date_start": start.isoformat(),
        "date_end": end.isoformat(),
        "period": "day",
    }
    resp = client.get(url, params=params, headers=_headers(), follow_redirects=True, timeout=120)
    resp.raise_for_status()
    return parse_history_xlsx(resp.content)


def parse_current(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    out: dict = {"products": {}, "tc_bna": None, "page_date": None, "published_at": None}

    m = re.search(r"Precios Pizarra del día\s+(\d{1,2}/\d{1,2}/\d{4})", soup.get_text(" ", strip=True))
    if m:
        out["page_date"] = parse_date(m.group(1))

    for board in soup.select("div.board"):
        classes = board.get("class", [])
        key = next((c.replace("board-", "") for c in classes
                    if c.startswith("board-") and c != "board"), None)
        if not key:
            continue
        h3 = board.find("h3")
        price_div = board.select_one(".price")
        price_text = price_div.get_text(" ", strip=True) if price_div else ""
        est = "(E)" in price_text or bool(board.select_one(".price-sc-estimated"))
        out["products"][key] = {
            "name": h3.get_text(" ", strip=True) if h3 else key,
            "price_ars": parse_ar_number(price_text),
            "quality": "estimated" if est else "operated",
        }

    text = soup.get_text(" ", strip=True)
    m = re.search(r"TC BNA Divisas\s+Comprador\s+(\d{1,2}/\d{1,2}/\d{4})\s*:\s*\$\s*([\d.,]+)", text)
    if m:
        out["tc_bna"] = {"date": parse_date(m.group(1)), "value": parse_ar_number(m.group(2))}
    m = re.search(r"Rosario,\s+(\d{1,2}\s+de\s+\w+\s+del?\s+\d{4})\s*-\s*Hora:\s*([\d:]+)", text, re.I)
    if m:
        out["published_at"] = f"{m.group(1)} {m.group(2)}"

    return out


def fetch_current(client: httpx.Client) -> dict:
    resp = client.get(BCR_CURRENT_URL, headers=_headers(), follow_redirects=True, timeout=60)
    resp.raise_for_status()
    return parse_current(resp.text)

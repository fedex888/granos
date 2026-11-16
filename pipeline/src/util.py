"""Utilidades compartidas: parseo de números/fechas argentinas y días hábiles."""
from __future__ import annotations

import datetime as dt
import re
import unicodedata
from typing import Iterable

MONTHS_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}


def norm(text: str) -> str:
    """Minúsculas y sin acentos, para comparar encabezados."""
    text = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in text if not unicodedata.combining(c)).strip().lower()


def parse_ar_number(value) -> float | None:
    """Convierte '$150.000,00', '150,000.00', '288,900.00' o 150000.0 a float.

    Devuelve None si no hay un precio (S/C, S/D, '-').
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip()
    if not raw or norm(raw) in {"s/c", "s/d", "-", "s/e"}:
        return None
    raw = re.sub(r"[^\d,.\-]", "", raw)
    if not raw:
        return None
    if "," in raw and "." in raw:
        # El último separador es el decimal.
        if raw.rfind(",") > raw.rfind("."):
            raw = raw.replace(".", "").replace(",", ".")
        else:
            raw = raw.replace(",", "")
    elif "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif raw.count(".") > 1:
        raw = raw.replace(".", "")
    try:
        return float(raw)
    except ValueError:
        return None


def parse_date(value) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if value is None:
        return None
    raw = str(value).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return dt.datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def parse_spanish_date(text: str) -> dt.date | None:
    m = re.search(r"(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})", text, re.I)
    if not m:
        return None
    month = MONTHS_ES.get(norm(m.group(2)))
    if not month:
        return None
    return dt.date(int(m.group(3)), month, int(m.group(1)))


def is_business_day(day: dt.date) -> bool:
    return day.weekday() < 5  # lunes..viernes


def business_days_between(start: dt.date, end: dt.date) -> int:
    """Días hábiles en (start, end], sin contar feriados (MVP)."""
    if end <= start:
        return 0
    count = 0
    d = start + dt.timedelta(days=1)
    while d <= end:
        if is_business_day(d):
            count += 1
        d += dt.timedelta(days=1)
    return count


def last_on_or_before(points: Iterable[tuple[dt.date, float]], target: dt.date) -> float | None:
    """Valor de la última observación con fecha <= target (para cambios de N días)."""
    best = None
    for d, v in points:
        if d <= target:
            best = v
        else:
            break
    return best

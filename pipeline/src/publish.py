"""Escritura de los JSON públicos en `data/`."""
from __future__ import annotations

import json
from pathlib import Path

from .config import ALERTS_DIR, DATA_DIR, HISTORY_DIR, SCHEMA_VERSION
from .normalize import Point


def _dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def strip_internal(product: dict) -> dict:
    """Elimina los campos internos (prefijo `_`) antes de publicar."""
    return {k: v for k, v in product.items() if not k.startswith("_")}


def write_latest(fx: dict, products: list[dict], generated_at: str) -> None:
    _dump(
        DATA_DIR / "latest.json",
        {
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at,
            "fx": fx,
            "products": [strip_internal(p) for p in products],
        },
    )


def write_history(product_id: str, points: list[Point]) -> None:
    _dump(
        HISTORY_DIR / f"{product_id}.json",
        {
            "schema_version": SCHEMA_VERSION,
            "product": product_id,
            "unit": "USD/t",
            "points": [p.to_dict() for p in points],
        },
    )


def write_status(status: dict) -> None:
    _dump(DATA_DIR / "status.json", {"schema_version": SCHEMA_VERSION, **status})


def write_alerts_latest(alerts: list[dict], generated_at: str) -> None:
    _dump(
        ALERTS_DIR / "latest.json",
        {
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at,
            "alerts": alerts,
        },
    )

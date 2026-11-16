"""Generación de alertas con antispam (cooldown y deduplicación) — plan §7.5.

En Fase 1 solo se registran en `data/alerts/`; el envío por FCM es Fase 3.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .config import ALERTS_DIR, COOLDOWN_DAYS, MAX_PUSH_PER_DAY, SIGNAL_RANK, now

ALERTABLE = {"strong", "buy", "sell"}


def _message(product: dict, direction: str, tier: str) -> str:
    name = product["name"]
    price = product["price_usd"]
    if direction == "buy":
        new_low = (
            price is not None and product.get("low_2y_usd") is not None
            and price <= product["low_2y_usd"]
        )
        if tier == "strong" and new_low:
            return (f"{name}: nuevo mínimo de 2 años. USD {price:.2f}/t. "
                    f"Puede seguir bajando; comprá por etapas.")
        return (f"{name}: está {product['distance_from_low_pct']:.1f}% arriba del mínimo de 2 años "
                f"(USD {product['low_2y_usd']:.2f}/t). Score {product['score_buy']}/100.")
    new_high = (
        price is not None and product.get("high_2y_usd") is not None
        and price >= product["high_2y_usd"]
    )
    if tier == "strong" and new_high:
        return f"{name}: nuevo máximo de 2 años. USD {price:.2f}/t. Considerá vender."
    return (f"{name}: está {product['distance_from_high_pct']:.1f}% debajo del máximo de 2 años "
            f"(USD {product['high_2y_usd']:.2f}/t). Score {product['score_sell']}/100.")


def _load_history() -> list[dict]:
    path = ALERTS_DIR / "history.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _within_cooldown(history: list[dict], product: str, direction: str, tier: str, today: dt.date) -> bool:
    cutoff = today - dt.timedelta(days=COOLDOWN_DAYS)
    for a in history:
        if a.get("product") != product or a.get("direction") != direction or a.get("tier") != tier:
            continue
        try:
            created = dt.datetime.fromisoformat(a["created_at"]).date()
        except (KeyError, ValueError):
            continue
        if created >= cutoff:
            return True
    return False


def evaluate_alerts(products: list[dict], today: dt.date) -> tuple[list[dict], list[dict]]:
    """Devuelve (alertas_nuevas, historial_actualizado) y persiste en data/alerts/."""
    history = _load_history()
    existing_ids = {a.get("id") for a in history}
    created_at = now().isoformat(timespec="seconds")

    candidates: list[dict] = []
    for p in products:
        if not p.get("_fresh"):
            continue  # sin dato operado reciente, no alertar (plan §7.1)
        for direction, signal_key, score_key in (("buy", "signal_buy", "score_buy"), ("sell", "signal_sell", "score_sell")):
            tier = p.get(signal_key)
            if tier not in ALERTABLE:
                continue
            alert_id = f"{p['id']}-{direction}-{today.isoformat()}"
            if alert_id in existing_ids:
                continue
            if _within_cooldown(history, p["id"], direction, tier, today):
                continue
            candidates.append({
                "id": alert_id,
                "product": p["id"],
                "direction": direction,
                "tier": tier,
                "price_usd": p["price_usd"],
                "price_ars": p["price_ars"],
                "score": p[score_key],
                "message": _message(p, direction, tier),
                "created_at": created_at,
            })

    # Prioridad: strong primero, luego buy/sell por score.
    candidates.sort(key=lambda a: (-SIGNAL_RANK[a["tier"]], -a["score"]))
    new_alerts = candidates[:MAX_PUSH_PER_DAY]

    history.extend(new_alerts)
    return new_alerts, history


def persist(history: list[dict], latest: list[dict]) -> None:
    ALERTS_DIR.mkdir(parents=True, exist_ok=True)
    (ALERTS_DIR / "history.json").write_text(
        json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
    )

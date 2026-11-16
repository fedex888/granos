"""Envío de alertas por Firebase Cloud Messaging (HTTP v1) — plan §8.6.

Lee la cuenta de servicio de:
  1. `FIREBASE_SERVICE_ACCOUNT` (JSON en variable de entorno, GitHub Actions).
  2. `GOOGLE_APPLICATION_CREDENTIALS` (ruta a un archivo JSON).
  3. `secrets/firebase-service-account.json` (local, gitignored).

Si no hay credenciales, no falla: devuelve `skipped`.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .config import ROOT, PRODUCTS

SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
FCM_URL = "https://fcm.googleapis.com/v1/projects/{project}/messages:send"
TOPIC = "alertas-granos"

_LOCAL_SECRET = ROOT / "secrets" / "firebase-service-account.json"


def _load_service_account() -> dict | None:
    raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if raw and raw.strip():
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    path_env = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if path_env and Path(path_env).exists():
        try:
            return json.loads(Path(path_env).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    if _LOCAL_SECRET.exists():
        try:
            return json.loads(_LOCAL_SECRET.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
    return None


def send_alerts(alerts: list[dict], product_names: dict[str, str] | None = None) -> dict:
    """Envía una notificación por alerta al topic. Devuelve un resumen."""
    if not alerts:
        return {"sent": 0, "skipped": "sin alertas nuevas"}

    service_account = _load_service_account()
    if service_account is None:
        return {"sent": 0, "skipped": "sin credenciales (FIREBASE_SERVICE_ACCOUNT)"}

    project_id = service_account.get("project_id")
    if not project_id:
        return {"sent": 0, "error": "la cuenta de servicio no tiene project_id"}

    # Import diferido: permite correr el pipeline sin google-auth si no hay push.
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account as sa_module
    import httpx

    creds = sa_module.Credentials.from_service_account_info(service_account, scopes=[SCOPE])
    creds.refresh(Request())

    names = product_names or {pid: cfg["name"] for pid, cfg in PRODUCTS.items()}
    url = FCM_URL.format(project=project_id)
    headers = {"Authorization": f"Bearer {creds.token}"}
    sent = 0
    errors: list[str] = []

    with httpx.Client(timeout=30) as client:
        for alert in alerts:
            name = names.get(alert["product"], alert["product"])
            direction = "Comprar" if alert["direction"] == "buy" else "Vender"
            payload = {
                "message": {
                    "topic": TOPIC,
                    "notification": {
                        "title": f"{name} · {direction}",
                        "body": alert["message"],
                    },
                    "data": {
                        "product_id": alert["product"],
                        "direction": alert["direction"],
                        "tier": alert["tier"],
                    },
                }
            }
            try:
                resp = client.post(url, json=payload, headers=headers)
            except httpx.HTTPError as exc:  # noqa: PERF203
                errors.append(f"{alert['id']}: {exc}")
                continue
            if resp.status_code == 200:
                sent += 1
            else:
                errors.append(f"{alert['id']}: {resp.status_code} {resp.text[:160]}")

    return {"sent": sent, "errors": errors}

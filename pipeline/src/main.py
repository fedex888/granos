"""Orquestación del pipeline: descarga, normaliza, calcula y publica."""
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path

import httpx

from . import alerts, notify, publish
from .config import (
    BCR_CURRENT_URL,
    DATA_DIR,
    PRODUCTS,
    TZ,
    USER_AGENT,
    WINDOW_DAYS,
    now,
    round2,
)
from .normalize import build_history, detect_outliers
from .signals import build_latest_product
from .sources import bcr, fx, magyp


def _client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
        timeout=120,
        transport=httpx.HTTPTransport(retries=3),
    )


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=DATA_DIR.parent, capture_output=True, text=True).stdout.strip()


def commit_data(message: str, push: bool) -> None:
    _git("add", "data/")
    diff = subprocess.run(["git", "diff", "--cached", "--quiet", "data/"], cwd=DATA_DIR.parent)
    if diff.returncode == 0:
        return  # sin cambios
    _git("commit", "-m", message)
    if push:
        _git("push", "origin", "main")


def run(start: dt.date, end: dt.date, today: dt.date, dry_run: bool, commit: bool, push: bool) -> int:
    generated_at = now().isoformat(timespec="seconds")

    status = {
        "last_run_at": generated_at,
        "status": "ok",
        "sources": [],
        "products_updated": 0,
        "stale_products": [],
        "warnings": [],
    }

    with _client() as client:
        # ---- FX (crítico: sin FX no hay USD) ----
        try:
            fx_rows = fx.fetch_series(client, today)
        except Exception as exc:  # noqa: BLE001
            status["status"] = "error"
            status["sources"].append({"name": "FX", "ok": False, "rows": 0, "error": str(exc)})
            if not dry_run:
                publish.write_status(status)
            print(f"ERROR FX: {exc}")
            return 1
        status["sources"].append({"name": "FX", "ok": bool(fx_rows), "rows": len(fx_rows), "error": None})
        if not fx_rows:
            status["status"] = "error"
            if not dry_run:
                publish.write_status(status)
            print("ERROR FX: sin datos")
            return 1
        last_fx = fx_rows[-1]
        fx_info = {
            "usd_ars": round2(last_fx["compra"]),
            "date": last_fx["date"].isoformat(),
            "source": "ArgentinaDatos/BNA",
        }

        # ---- BCR histórico por producto ----
        histories: dict[str, list] = {}
        bcr_errors: dict[str, str] = {}
        for pid, cfg in PRODUCTS.items():
            try:
                pts = bcr.fetch_history(client, cfg["bcr_id"], cfg["bcr_type"], start, end)
                points = build_history(pts, fx_rows, "BCR")
                detect_outliers(points)
                histories[pid] = points
            except Exception as exc:  # noqa: BLE001
                bcr_errors[pid] = str(exc)
        bcr_total = sum(len(v) for v in histories.values())
        status["sources"].append({
            "name": "BCR",
            "ok": not bcr_errors,
            "rows": bcr_total,
            "error": "; ".join(f"{k}: {v}" for k, v in bcr_errors.items()) or None,
        })
        for pid, err in bcr_errors.items():
            status["warnings"].append(f"BCR {pid}: {err}")

        # ---- BCR pizarra del día (control de frescura / TC) ----
        try:
            current = bcr.fetch_current(client)
            if current.get("tc_bna"):
                status["warnings"].append(
                    f"BCR TC BNA divisa {current['tc_bna']['value']} "
                    f"({current['tc_bna']['date']}) vs FX {fx_info['usd_ars']}"
                )
        except Exception as exc:  # noqa: BLE001
            status["warnings"].append(f"BCR pizarra actual: {exc}")

        # ---- MAGyP (fallback / control cruzado) ----
        try:
            magyp_data = magyp.fetch_daily(client)
            status["sources"].append({
                "name": "MAGyP",
                "ok": True,
                "rows": len(magyp_data["prices"]),
                "error": None,
            })
        except Exception as exc:  # noqa: BLE001
            status["sources"].append({"name": "MAGyP", "ok": False, "rows": 0, "error": str(exc)})

    # ---- Señales y productos ----
    products_latest: list[dict] = []
    for pid, cfg in PRODUCTS.items():
        points = histories.get(pid)
        if not points:
            status["stale_products"].append(pid)
            continue
        product = build_latest_product(pid, cfg, points, today, BCR_CURRENT_URL, generated_at)
        if product is None:
            status["stale_products"].append(pid)
            continue
        products_latest.append(product)
        if not product.get("_fresh"):
            status["stale_products"].append(pid)
            status["warnings"].append(f"{pid}: sin operado reciente (quality={product['quality']})")

    # ---- Alertas ----
    new_alerts, alert_history = alerts.evaluate_alerts(products_latest, today)

    # ---- Push (FCM) ----
    if new_alerts and not dry_run:
        push_result = notify.send_alerts(new_alerts)
        if push_result.get("sent"):
            status["warnings"].append(f"FCM: {push_result['sent']} enviadas")
        elif push_result.get("skipped"):
            status["warnings"].append(f"FCM: {push_result['skipped']}")
        else:
            status["warnings"].append(f"FCM: {push_result.get('error', push_result)}")

    status["products_updated"] = len(products_latest)

    # ---- Publicación ----
    if dry_run:
        print(f"[dry-run] {len(products_latest)} productos, {len(new_alerts)} alertas nuevas")
    elif not products_latest:
        # No sobrescribir un último dato bueno con una corrida vacía.
        status["status"] = "error"
        publish.write_status(status)
        print("ERROR: ningún producto con datos; no se sobrescribió latest.json")
        return 1
    else:
        publish.write_latest(fx_info, products_latest, generated_at)
        for pid, pts in histories.items():
            if pts:
                publish.write_history(pid, pts)
        status["status"] = "ok" if not bcr_errors else "partial"
        publish.write_status(status)
        publish.write_alerts_latest(new_alerts, generated_at)
        alerts.persist(alert_history, new_alerts)
        if commit:
            commit_data(f"data: actualización {today.isoformat()}", push)

    print(f"FX {fx_info['usd_ars']} ({fx_info['date']})")
    for p in products_latest:
        print(f"  {p['id']:8s} {p['price_usd']:>8.2f} USD  "
              f"buy={p['signal_buy']} sell={p['signal_sell']}  score_b={p['score_buy']} score_s={p['score_sell']}")
    if new_alerts:
        print(f"Alertas nuevas: {[a['id'] for a in new_alerts]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pipeline de datos de granos")
    parser.add_argument("--start", type=dt.date.fromisoformat, help="Fecha de inicio (YYYY-MM-DD)")
    parser.add_argument("--end", type=dt.date.fromisoformat, help="Fecha de fin (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="No escribir data/")
    parser.add_argument("--commit", action="store_true", help="Commit de data/ al finalizar")
    parser.add_argument("--push", action="store_true", help="Push de data/ al finalizar")
    args = parser.parse_args(argv)

    today = now().date()
    end = args.end or today
    start = args.start or (end - dt.timedelta(days=WINDOW_DAYS))

    return run(start, end, today, args.dry_run, args.commit, args.push)


if __name__ == "__main__":
    sys.exit(main())

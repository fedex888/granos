#!/usr/bin/env python3
"""Envía una notificación de prueba al topic `alertas-granos`.

Requiere la cuenta de servicio de Firebase (ver docs/fcm.md).

Uso:
    python scripts/send-test-push.py --product maiz --message "Prueba"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.src import notify  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", default="maiz")
    parser.add_argument("--direction", default="buy", choices=["buy", "sell"])
    parser.add_argument("--tier", default="strong", choices=["strong", "buy", "sell", "watch"])
    parser.add_argument("--message", default="Prueba de notificación de Oportunidades de Granos.")
    args = parser.parse_args()

    alert = {
        "id": "test",
        "product": args.product,
        "direction": args.direction,
        "tier": args.tier,
        "message": args.message,
    }
    result = notify.send_alerts([alert])
    print(result)
    return 0 if result.get("sent") else 1


if __name__ == "__main__":
    raise SystemExit(main())

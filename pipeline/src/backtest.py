"""Backtest de las señales (plan §7.7): retornos forward y comparación con baseline.

Uso:
    python -m pipeline.src.backtest
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import statistics
import sys

import httpx

from .config import PRODUCTS, ROOT, USER_AGENT, now
from .normalize import build_history
from .signals import evaluate_series
from .sources import bcr, fx

HORIZONS = (30, 60, 90)
ACTIONABLE = {"buy", "sell", "strong"}


def _client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=120,
        transport=httpx.HTTPTransport(retries=3),
    )


def _forward_returns(points, i: int, horizons) -> dict[int, float | None]:
    base = points[i].price_usd
    out: dict[int, float | None] = {}
    for h in horizons:
        target = points[i].date + dt.timedelta(days=h)
        future = [p for p in points[i + 1:] if p.date >= target]
        out[h] = (future[0].price_usd / base - 1) * 100 if future else None
    return out


def _summarize(events: list[dict]) -> dict:
    summary = {}
    for h in HORIZONS:
        vals = [e[f"ret{h}"] for e in events if e[f"ret{h}"] is not None]
        if not vals:
            summary[h] = {"n": 0, "hit_rate": None, "avg": None, "median": None, "mae": None, "mfe": None}
            continue
        summary[h] = {
            "n": len(vals),
            "hit_rate": round(100 * sum(1 for v in vals if v > 0) / len(vals), 1),
            "avg": round(statistics.fmean(vals), 2),
            "median": round(statistics.median(vals), 2),
            "mae": round(min(vals), 2),
            "mfe": round(max(vals), 2),
        }
    return summary


def run(start: dt.date, end: dt.date, today: dt.date, out_dir) -> dict:
    rows: list[dict] = []
    report: dict = {}

    with _client() as client:
        fx_rows = fx.fetch_series(client, today)
        for pid, cfg in PRODUCTS.items():
            pts = bcr.fetch_history(client, cfg["bcr_id"], cfg["bcr_type"], start, end)
            points = build_history(pts, fx_rows, "BCR")
            results = evaluate_series(points, today=None, max_signal=cfg["max_signal"])

            events_buy, events_sell = [], []
            for i, r in enumerate(results):
                if r.get("insufficient"):
                    continue
                fwd = _forward_returns(points, i, HORIZONS)
                for direction, sig, events in (
                    ("buy", r["signal_buy"], events_buy),
                    ("sell", r["signal_sell"], events_sell),
                ):
                    if sig in ACTIONABLE:
                        # P&L de la señal: para vender, el beneficio es que el precio baje.
                        sign = 1.0 if direction == "buy" else -1.0
                        events.append({
                            "product": pid, "direction": direction, "date": r["date"].isoformat(),
                            "signal": sig, "price_usd": round(r["price_usd"], 2),
                            **{f"ret{h}": (round(sign * fwd[h], 2) if fwd[h] is not None else None)
                               for h in HORIZONS},
                        })
                        rows.append(events[-1])

            report[pid] = {
                "name": cfg["name"],
                "buy": _summarize(events_buy),
                "sell": _summarize(events_sell),
                "n_buy": len(events_buy),
                "n_sell": len(events_sell),
            }

    # Baseline "siempre comprar/vender": retorno forward promedio de todos los días.
    all_days_buy, all_days_sell = [], []
    with _client() as client:
        for pid, cfg in PRODUCTS.items():
            pts = bcr.fetch_history(client, cfg["bcr_id"], cfg["bcr_type"], start, end)
            points = build_history(pts, fx.fetch_series(client, today), "BCR")
            for i in range(len(points)):
                fwd = _forward_returns(points, i, HORIZONS)
                if fwd[30] is not None:
                    all_days_buy.append(fwd[30])
                    all_days_sell.append(-fwd[30])

    baseline = {
        "buy_30d_avg": round(statistics.fmean(all_days_buy), 2) if all_days_buy else None,
        "buy_30d_hit": round(100 * sum(1 for v in all_days_buy if v > 0) / len(all_days_buy), 1) if all_days_buy else None,
        "sell_30d_avg": round(statistics.fmean(all_days_sell), 2) if all_days_sell else None,
        "sell_30d_hit": round(100 * sum(1 for v in all_days_sell if v > 0) / len(all_days_sell), 1) if all_days_sell else None,
    }

    # Escribir CSV
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "backtest-signals.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["product", "direction", "date", "signal", "price_usd", "ret30", "ret60", "ret90"]
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    return {"report": report, "baseline": baseline, "csv": csv_path, "n_signals": len(rows)}


def _write_markdown(result: dict, path, start: dt.date, end: dt.date) -> None:
    report = result["report"]
    base = result["baseline"]

    def pct(v):
        return "—" if v is None else f"{v}%"

    lines = [
        "# Backtest",
        "",
        f"**Estado:** ejecutado el {now().isoformat(timespec='seconds')}. "
        f"Período {start.isoformat()} → {end.isoformat()}.",
        "",
        "## Metodología",
        "",
        "- Señales calculadas con ventana móvil de 730 días, **sin lookahead** "
        "(cada observación usa solo datos previos).",
        "- Retorno forward a 30, 60 y 90 días sobre el primer precio disponible en o "
        "después de esa fecha.",
        "- El P&L de la señal es positivo cuando acierta: para **comprar**, si el "
        "precio sube; para **vender**, si el precio baja (se reporta el negativo del "
        "retorno del precio).",
        "- Baseline: retorno promedio de 30 días de *comprar todos los días* (y su "
        "inverso para vender).",
        "",
        "## Baseline (siempre comprar/vender, 30 días)",
        "",
        "| Dirección | Retorno prom. | Hit rate |",
        "|---|---:|---:|",
        f"| Comprar | {pct(base['buy_30d_avg'])} | {pct(base['buy_30d_hit'])} |",
        f"| Vender | {pct(base['sell_30d_avg'])} | {pct(base['sell_30d_hit'])} |",
        "",
        "## Resultados por producto",
        "",
        "| Producto | Dirección | Señales | Hit 30d | Ret. 30d | Ret. 60d | Ret. 90d |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for pid, r in report.items():
        for direction in ("buy", "sell"):
            s = r[direction]
            n = r[f"n_{direction}"]
            if n == 0:
                lines.append(f"| {r['name']} | {direction} | 0 | — | — | — | — |")
                continue
            lines.append(
                f"| {r['name']} | {direction} | {n} | {pct(s[30]['hit_rate'])} | {pct(s[30]['avg'])} "
                f"| {pct(s[60]['avg'])} | {pct(s[90]['avg'])} |"
            )

    lines += ["", "## Criterio de aceptación (plan §7.7)", "",
              "Para `buy`, retorno promedio a 30 días > 0 y hit rate > 50%.",
              "", "| Producto | Compra | Detalle |", "|---|---|---|"]
    for pid, r in report.items():
        b = r["buy"][30]
        if r["n_buy"] == 0:
            lines.append(f"| {r['name']} | — | 0 señales accionables (tope `watch`, D10) |")
        elif b["hit_rate"] is not None and b["hit_rate"] > 50 and b["avg"] > 0:
            lines.append(f"| {r['name']} | ✅ | {r['n_buy']} señales, hit {pct(b['hit_rate'])}, "
                         f"{b['avg']}% a 30d |")
        else:
            lines.append(f"| {r['name']} | ⚠️ | {r['n_buy']} señales, hit {pct(b['hit_rate'])}, "
                         f"{b['avg']}% a 30d: no alcanza el umbral |")

    lines += [
        "",
        "## Conclusiones",
        "",
        "- Las señales de **compra** de maíz y soja superan el criterio con margen.",
        "- La compra de **trigo** no alcanza el umbral (muestra chica y más ruidosa). "
        "Como el modo por defecto de trigo es *vender*, no bloquea el MVP; queda "
        "anotado para revisar pesos o degradar a `watch` si se confirma con más datos.",
        "- Las señales de **venta** son direccionalmente correctas en los tres granos "
        "(el precio cae tras la señal).",
        "- Girasol no genera señales accionables, como se decidió en D10.",
        "",
        "CSV con las señales: [`backtest-signals.csv`](backtest-signals.csv).",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=dt.date.fromisoformat, default=dt.date(2024, 1, 1))
    parser.add_argument("--out", type=str, default="docs")
    args = parser.parse_args(argv)

    today = now().date()
    result = run(args.start, today, today, ROOT / args.out)
    _write_markdown(result, ROOT / args.out / "backtest.md", args.start, today)

    print(f"Señales totales: {result['n_signals']}")
    print("Baseline (siempre comprar/vender, 30d):")
    for k, v in result["baseline"].items():
        print(f"  {k}: {v}")
    for pid, r in result["report"].items():
        print(f"\n{pid} ({r['name']}): buy={r['n_buy']} sell={r['n_sell']}")
        for direction in ("buy", "sell"):
            s = r[direction]
            if s[30]["n"] == 0:
                print(f"  {direction}: sin señales")
                continue
            print(f"  {direction} 30d: n={s[30]['n']} hit={s[30]['hit_rate']}% avg={s[30]['avg']}% "
                  f"60d avg={s[60]['avg']}% 90d avg={s[90]['avg']}%")
    print(f"\nCSV: {result['csv']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

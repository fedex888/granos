#!/usr/bin/env python3
"""Validación de fuentes de datos — Fase 0.

Descarga y valida las tres fuentes del plan:
  * BCR  — export XLSX histórico por producto (2 años).
  * MAGyP — pizarra diaria sobre puerto (control cruzado, columna Rosario).
  * FX   — serie histórica dólar oficial (ArgentinaDatos/BNA).

Guarda los archivos crudos en artifacts/fase0/<fecha>/ y un resumen JSON en
artifacts/fase0/report.json. No escribe en data/ (eso es Fase 1).

Uso:
    python scripts/validate-sources.py
    python scripts/validate-sources.py --days 730 --out artifacts/fase0
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import re
import sys
import unicodedata
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import openpyxl
from bs4 import BeautifulSoup

TZ = ZoneInfo("America/Argentina/Buenos_Aires")
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"
    )
}

# IDs internos de BCR verificados el 2026-11-15 contra el <select name="product">.
PRODUCTS = {
    "trigo": {"bcr_id": 8, "bcr_type": "pizarra", "name": "Trigo pan"},
    "maiz": {"bcr_id": 3, "bcr_type": "pizarra", "name": "Maíz"},
    "girasol": {"bcr_id": 9, "bcr_type": "any", "name": "Girasol"},
    "soja": {"bcr_id": 13, "bcr_type": "pizarra", "name": "Soja"},
}

BCR_EXPORT = "https://www.cac.bcr.com.ar/es/api/prices/{node}/export"
BCR_EXPORT_NODE = 987
BCR_CURRENT = "https://www.cac.bcr.com.ar/es/precios-de-pizarra"
MAGYP_URL = (
    "https://www.magyp.gob.ar/sitio/areas/ss_mercados_agropecuarios/areas/granos/"
    "_archivos/000056_Precios%20Locales/000020_Precios%20C%C3%A1mara%20-%20Diario/"
    "000001_Cotizaciones%20de%20Pizarra%20sobre%20Puerto%20-%20Precios%20C%C3%A1maras.php"
    "?accion=imp"
)
FX_URL = "https://api.argentinadatos.com/v1/cotizaciones/dolares/oficial"

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
    """Convierte '$150.000,00', '150,000.00' o 150000.0 a float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip()
    if not raw or norm(raw) in {"s/c", "s/d", "-"}:
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


def fetch(client: httpx.Client, url: str, **kwargs) -> httpx.Response:
    response = client.get(url, headers=UA, follow_redirects=True, timeout=120, **kwargs)
    response.raise_for_status()
    return response


def parse_bcr_xlsx(content: bytes) -> list[dict]:
    """Parsea el XLSX de BCR detectando la columna de precio por encabezado.

    Formatos observados (2026-11-15):
      - Trigo/Maíz/Soja: A=Fecha de operación, B=Precio.
      - Girasol (type=any): A=Fecha, B=marca '(E)', C=Precio.
    """
    wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True, read_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    header_idx = None
    for i, row in enumerate(rows[:15]):
        cells = [norm(str(c)) if c is not None else "" for c in row]
        if any(c.startswith("fecha") for c in cells) and any(c.startswith("precio") for c in cells):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("No se encontró la fila de encabezado 'Fecha de operación | Precio'.")

    header = rows[header_idx]
    date_col = next(i for i, c in enumerate(header) if norm(str(c)).startswith("fecha"))
    price_col = next(i for i, c in enumerate(header) if norm(str(c)).startswith("precio"))
    quality_col = price_col - 1 if price_col - 1 > date_col else None

    points = []
    for row in rows[header_idx + 1:]:
        if not row or row[date_col] is None:
            continue
        date = parse_date(row[date_col])
        if date is None:
            continue
        price_raw = row[price_col] if price_col < len(row) else None
        marker = ""
        if quality_col is not None and quality_col < len(row) and row[quality_col] is not None:
            marker = str(row[quality_col])
        price = parse_ar_number(price_raw)
        quality = "estimated" if "(E)" in marker or "(E)" in str(price_raw or "") else "operated"
        points.append({"date": date, "price_ars": price, "quality": quality})

    return sorted(points, key=lambda p: p["date"])


def parse_bcr_current(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    out = {"products": {}, "tc_bna": None, "page_date": None, "published_at": None}

    m = re.search(r"Precios Pizarra del día\s+(\d{1,2}/\d{1,2}/\d{4})", soup.get_text(" ", strip=True))
    if m:
        out["page_date"] = parse_date(m.group(1))

    for board in soup.select("div.board"):
        classes = board.get("class", [])
        key = next((c.replace("board-", "") for c in classes if c.startswith("board-") and c != "board"), None)
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
            "raw": price_text,
        }

    text = soup.get_text(" ", strip=True)
    m = re.search(r"TC BNA Divisas\s+Comprador\s+(\d{1,2}/\d{1,2}/\d{4})\s*:\s*\$\s*([\d.,]+)", text)
    if m:
        out["tc_bna"] = {"date": parse_date(m.group(1)), "value": parse_ar_number(m.group(2))}
    m = re.search(r"Rosario,\s+(\d{1,2}\s+de\s+\w+\s+del?\s+\d{4})\s*-\s*Hora:\s*([\d:]+)", text, re.I)
    if m:
        out["published_at"] = f"{m.group(1)} {m.group(2)}"
    return out


def parse_magyp(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    out = {"date": None, "prices": {}, "headers": []}
    tables = soup.find_all("table")
    target = None
    for table in tables:
        rows = table.find_all("tr")
        if any("PRODUCTO" in r.get_text(" ", strip=True).upper() for r in rows):
            target = table
            break
    if not target:
        raise ValueError("No se encontró la tabla de pizarra de MAGyP.")

    rows = target.find_all("tr")
    header = None
    for tr in rows:
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
            product = norm(cells[0])
            out["prices"][product] = {
                "raw": cells[rosario_idx],
                "value": parse_ar_number(cells[rosario_idx]),
            }
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=730)
    parser.add_argument("--out", type=Path, default=Path("artifacts/fase0"))
    args = parser.parse_args()

    today = dt.datetime.now(TZ).date()
    start = today - dt.timedelta(days=args.days)
    out_dir = args.out / today.isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)

    report: dict = {
        "schema_version": 1,
        "generated_at": dt.datetime.now(TZ).isoformat(timespec="seconds"),
        "window": {"start": str(start), "end": str(today), "days": args.days},
        "sources": {},
        "products": {},
        "checks": [],
        "warnings": [],
        "ok": True,
    }

    def check(name: str, ok: bool, detail: str) -> None:
        report["checks"].append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            report["ok"] = False

    with httpx.Client() as client:
        # ---------------- FX ----------------
        try:
            fx_resp = fetch(client, FX_URL)
            (out_dir / "fx_oficial.json").write_bytes(fx_resp.content)
            fx_data = fx_resp.json()
            fx_rows = [
                {"date": parse_date(row["fecha"]), "compra": row.get("compra"), "venta": row.get("venta")}
                for row in fx_data
            ]
            fx_rows = sorted((r for r in fx_rows if r["date"]), key=lambda r: r["date"])
            fx_valid = [r for r in fx_rows if r["compra"] and r["compra"] > 0 and r["date"] <= today]
            fx_in_window = [r for r in fx_valid if r["date"] >= start]
            report["sources"]["FX"] = {
                "ok": True,
                "url": FX_URL,
                "rows_total": len(fx_rows),
                "rows_window": len(fx_in_window),
                "first_window": str(fx_in_window[0]["date"]) if fx_in_window else None,
                "last_date": str(fx_valid[-1]["date"]) if fx_valid else None,
                "last_compra": fx_valid[-1]["compra"] if fx_valid else None,
                "rows_future_excluded": len([r for r in fx_rows if r["date"] > today]),
            }
            check("FX: serie disponible", bool(fx_in_window), f"{len(fx_in_window)} filas en la ventana")
            nulls = [r for r in fx_in_window if not r["compra"] or r["compra"] <= 0]
            check("FX: sin valores nulos o cero en la ventana", not nulls, f"{len(nulls)} filas inválidas")
        except Exception as exc:  # noqa: BLE001
            fx_valid = []
            report["sources"]["FX"] = {"ok": False, "error": str(exc)}
            check("FX: serie disponible", False, str(exc))

        # ---------------- BCR histórico ----------------
        bcr_products: dict[str, list[dict]] = {}
        for pid, meta in PRODUCTS.items():
            params = {
                "product": meta["bcr_id"],
                "type": meta["bcr_type"],
                "date_start": str(start),
                "date_end": str(today),
                "period": "day",
            }
            try:
                resp = fetch(client, BCR_EXPORT.format(node=BCR_EXPORT_NODE), params=params)
                raw_path = out_dir / f"bcr_{pid}.xlsx"
                raw_path.write_bytes(resp.content)
                points = parse_bcr_xlsx(resp.content)
                points = [p for p in points if start <= p["date"] <= today]
                bcr_products[pid] = points

                with_price = [p for p in points if p["price_ars"]]
                estimated = [p for p in with_price if p["quality"] == "estimated"]
                operated = [p for p in with_price if p["quality"] == "operated"]
                dates = [p["date"] for p in points]
                duplicates = len(dates) - len(set(dates))
                op_dates = [p["date"] for p in operated]
                gaps = [(b - a).days for a, b in zip(op_dates, op_dates[1:])]
                outliers = 0
                for prev, cur in zip(operated, operated[1:]):
                    if prev["price_ars"] and abs(cur["price_ars"] / prev["price_ars"] - 1) > 0.5:
                        outliers += 1
                report["products"][pid] = {
                    "name": meta["name"],
                    "bcr_id": meta["bcr_id"],
                    "bcr_type": meta["bcr_type"],
                    "rows": len(points),
                    "rows_with_price": len(with_price),
                    "rows_no_quote": len(points) - len(with_price),
                    "rows_estimated": len(estimated),
                    "rows_operated": len(operated),
                    "duplicate_dates": duplicates,
                    "max_gap_days_operated": max(gaps) if gaps else None,
                    "median_gap_days_operated": sorted(gaps)[len(gaps) // 2] if gaps else None,
                    "outliers_gt_50pct": outliers,
                    "first_date": str(points[0]["date"]) if points else None,
                    "last_date": str(points[-1]["date"]) if points else None,
                    "last_operated_date": str(operated[-1]["date"]) if operated else None,
                    "last_price_ars": with_price[-1]["price_ars"] if with_price else None,
                    "last_quality": with_price[-1]["quality"] if with_price else None,
                    "min_price_ars": min((p["price_ars"] for p in with_price), default=None),
                    "max_price_ars": max((p["price_ars"] for p in with_price), default=None),
                }
                check(
                    f"BCR {pid}: >= 250 observaciones",
                    len(with_price) >= 250,
                    f"{len(with_price)} precios en {len(points)} filas",
                )
                if len(with_price) >= 250 and len(operated) < 250:
                    report["warnings"].append(
                        f"{pid}: solo {len(operated)} observaciones operadas; el umbral de 250 del plan "
                        f"solo se alcanza incluyendo {len(estimated)} estimadas."
                    )
                check(
                    f"BCR {pid}: sin fechas duplicadas",
                    duplicates == 0,
                    f"{duplicates} duplicados",
                )
                if outliers:
                    report["warnings"].append(
                        f"{pid}: {outliers} variaciones diarias > 50% (revisar en Fase 1)."
                    )
                check(
                    f"BCR {pid}: cubre 2 años",
                    bool(points) and points[0]["date"] <= start + dt.timedelta(days=10),
                    f"primer dato {points[0]['date'] if points else 'n/a'}",
                )
            except Exception as exc:  # noqa: BLE001
                report["products"][pid] = {"name": meta["name"], "ok": False, "error": str(exc)}
                check(f"BCR {pid}: descarga y parseo", False, str(exc))

        # ---------------- BCR pizarra actual ----------------
        try:
            resp = fetch(client, BCR_CURRENT)
            (out_dir / "bcr_current.html").write_text(resp.text, encoding="utf-8")
            current = parse_bcr_current(resp.text)
            tc = current["tc_bna"]
            report["sources"]["BCR"] = {
                "ok": True,
                "url": BCR_CURRENT,
                "export_node": BCR_EXPORT_NODE,
                "page_date": str(current["page_date"]) if current["page_date"] else None,
                "tc_bna": {"date": str(tc["date"]), "value": tc["value"]} if tc else None,
                "products": current["products"],
                "published_at": current["published_at"],
            }
            check("BCR actual: 4 productos presentes",
                  all(k in current["products"] for k in ("trigo", "maiz", "girasol", "soja")),
                  ", ".join(sorted(current["products"])))
            check("BCR actual: TC BNA parseado", tc is not None,
                  json.dumps(report["sources"]["BCR"]["tc_bna"], ensure_ascii=False))
            for pid, meta in PRODUCTS.items():
                cur = current["products"].get(pid)
                hist = report["products"].get(pid, {})
                if cur and cur["price_ars"] and hist.get("last_price_ars"):
                    same = abs(cur["price_ars"] - hist["last_price_ars"]) < 0.01
                    check(f"BCR {pid}: actual == último histórico", same,
                          f"actual={cur['price_ars']} hist={hist['last_price_ars']}")
        except Exception as exc:  # noqa: BLE001
            current = {"products": {}, "tc_bna": None}
            report["sources"]["BCR"] = {"ok": False, "error": str(exc)}
            check("BCR actual: descarga y parseo", False, str(exc))

        # ---------------- MAGyP ----------------
        try:
            resp = fetch(client, MAGYP_URL)
            (out_dir / "magyp_pizarra.html").write_text(resp.text, encoding="utf-8")
            magyp = parse_magyp(resp.text)
            report["sources"]["MAGyP"] = {
                "ok": True,
                "url": MAGYP_URL,
                "date": str(magyp["date"]) if magyp["date"] else None,
                "headers": magyp["headers"],
                "prices": magyp["prices"],
            }
            check("MAGyP: tabla y fecha parseadas", magyp["date"] is not None,
                  f"fecha={magyp['date']}, productos={len(magyp['prices'])}")

            map_ids = {"trigo": "trigo pan", "maiz": "maiz", "girasol": "girasol", "soja": "soja"}
            for pid, magyp_name in map_ids.items():
                m_price = (magyp["prices"].get(magyp_name) or {}).get("value")
                bcr_last = report["products"].get(pid, {}).get("last_price_ars")
                if m_price and bcr_last:
                    same = abs(m_price - bcr_last) < 0.01
                    check(f"MAGyP {pid}: coincide con BCR (Rosario)", same,
                          f"magyp={m_price} bcr={bcr_last}")
                elif m_price in (None, 0):
                    report["warnings"].append(
                        f"MAGyP sin cotización Rosario para {pid} ({magyp_name}); "
                        "no sirve como fallback ese día"
                    )
        except Exception as exc:  # noqa: BLE001
            magyp = {"prices": {}}
            report["sources"]["MAGyP"] = {"ok": False, "error": str(exc)}
            check("MAGyP: descarga y parseo", False, str(exc))

        # ---------------- FX aplicado a BCR ----------------
        if fx_valid and bcr_products:
            fx_map = {r["date"]: r["compra"] for r in fx_valid}
            fx_dates = sorted(fx_map)

            def fx_for(date: dt.date) -> float | None:
                prev = [d for d in fx_dates if d <= date]
                return fx_map[prev[-1]] if prev else None

            for pid, points in bcr_products.items():
                with_price = [p for p in points if p["price_ars"]]
                if not with_price:
                    continue
                last = with_price[-1]
                fx_value = fx_for(last["date"])
                entry = report["products"][pid]
                entry["last_fx_usd_ars"] = fx_value
                entry["last_fx_date"] = str(max(d for d in fx_dates if d <= last["date"])) if fx_value else None
                entry["last_price_usd"] = round(last["price_ars"] / fx_value, 2) if fx_value else None

                bcr_usd = (current["products"].get(pid) or {}).get("price_ars")
                # BCR publica su propio US$; se compara contra el TC BNA de la página.
                if current.get("tc_bna") and current["tc_bna"]["value"] and bcr_usd:
                    bcr_usd_calc = bcr_usd / current["tc_bna"]["value"]
                    entry["bcr_own_usd"] = round(bcr_usd_calc, 2)
                    if entry["last_price_usd"]:
                        diff_pct = (entry["last_price_usd"] / bcr_usd_calc - 1) * 100
                        entry["fx_offset_vs_bcr_pct"] = round(diff_pct, 3)
                        report["warnings"].append(
                            f"{pid}: USD calculado con ArgentinaDatos difiere {diff_pct:+.2f}% "
                            f"del US$ publicado por BCR (TC divisa {current['tc_bna']['value']})"
                        )

            if current.get("tc_bna") and fx_valid:
                api_fx = fx_valid[-1]["compra"]
                bcr_fx = current["tc_bna"]["value"]
                diff = (api_fx / bcr_fx - 1) * 100
                report["sources"]["FX"]["tc_bna_bcr"] = bcr_fx
                report["sources"]["FX"]["offset_vs_bcr_pct"] = round(diff, 3)
                check("FX: diferencia con TC BNA de BCR < 2%", abs(diff) < 2,
                      f"ArgentinaDatos={api_fx} BCR={bcr_fx} ({diff:+.2f}%)")
                if abs(diff) >= 0.5:
                    report["warnings"].append(
                        "La serie ArgentinaDatos 'oficial compra' no es idéntica al 'dólar divisa "
                        f"BNA comprador' que usa BCR ({diff:+.2f}%). Documentado en docs/data-sources.md."
                    )

    report_path = args.out / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # ------------------- salida legible -------------------
    print(f"Ventana: {start} .. {today} ({args.days} días)")
    for pid, entry in report["products"].items():
        print(
            f"  {pid:8s} filas={entry.get('rows', '-'):>4} precios={entry.get('rows_with_price', '-'):>4} "
            f"operados={entry.get('rows_operated', '-'):>3} est={entry.get('rows_estimated', '-'):>3} "
            f"{entry.get('first_date')}..{entry.get('last_date')} "
            f"ARS={entry.get('last_price_ars')} USD={entry.get('last_price_usd')} "
            f"({entry.get('last_quality')})"
        )
    print(f"BCR TC BNA: {report['sources'].get('BCR', {}).get('tc_bna')}")
    print(f"FX último: {report['sources'].get('FX', {}).get('last_date')} "
          f"compra={report['sources'].get('FX', {}).get('last_compra')}")
    print(f"MAGyP fecha: {report['sources'].get('MAGyP', {}).get('date')}")
    print()
    for item in report["checks"]:
        print(f"  [{'OK ' if item['ok'] else 'FAIL'}] {item['name']}: {item['detail']}")
    if report["warnings"]:
        print("\nAdvertencias:")
        for warning in report["warnings"]:
            print(f"  - {warning}")
    print(f"\nReporte: {report_path}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

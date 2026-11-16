import datetime as dt
from pathlib import Path

from pipeline.src.sources import bcr

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_maiz_xlsx():
    points = bcr.parse_history_xlsx((FIXTURES / "bcr_maiz.xlsx").read_bytes())
    with_price = [p for p in points if p["price_ars"] is not None]
    assert len(points) == 481
    assert len(with_price) == 469
    last = with_price[-1]
    assert last["price_ars"] == 275800.0
    assert last["quality"] == "operated"


def test_parse_girasol_xlsx_extra_column():
    points = bcr.parse_history_xlsx((FIXTURES / "bcr_girasol.xlsx").read_bytes())
    with_price = [p for p in points if p["price_ars"] is not None]
    estimated = [p for p in with_price if p["quality"] == "estimated"]
    assert len(with_price) == 480
    assert len(estimated) == 285
    assert with_price[-1]["price_ars"] == 752885.0
    assert with_price[-1]["quality"] == "estimated"


def test_parse_current_page():
    current = bcr.parse_current((FIXTURES / "bcr_page.html").read_text(encoding="utf-8"))
    assert current["tc_bna"]["value"] == 1536.5
    assert current["page_date"] == dt.date(2026, 11, 12)
    assert current["products"]["trigo"]["price_ars"] == 288900.0
    assert current["products"]["girasol"]["quality"] == "estimated"

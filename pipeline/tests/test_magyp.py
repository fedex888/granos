import datetime as dt
from pathlib import Path

from pipeline.src.sources import magyp

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_magyp_daily():
    data = magyp.parse_daily((FIXTURES / "magyp_pizarra.html").read_text(encoding="utf-8"))
    assert data["date"] == dt.date(2026, 11, 12)
    assert data["prices"]["trigo pan"] == 288900.0
    assert data["prices"]["maiz"] == 275800.0
    assert data["prices"]["soja"] == 540000.0
    # Sin cotización Rosario para girasol
    assert data["prices"]["girasol"] in (0.0, None)

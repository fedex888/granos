"""Pipeline de datos de granos — configuración y constantes."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]  # <repo>/ (proyecto/)
DATA_DIR = ROOT / "data"
HISTORY_DIR = DATA_DIR / "history"
ALERTS_DIR = DATA_DIR / "alerts"
ARTIFACTS_DIR = ROOT / "artifacts"
PIPELINE_DIR = ROOT / "pipeline"

# ---------------------------------------------------------------------------
# Zona horaria y esquema
# ---------------------------------------------------------------------------
TZ = ZoneInfo("America/Argentina/Buenos_Aires")
SCHEMA_VERSION = 1

# ---------------------------------------------------------------------------
# Fuentes
# ---------------------------------------------------------------------------
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36 granos-app/1.0"
)

BCR_EXPORT_URL = "https://www.cac.bcr.com.ar/es/api/prices/{node}/export"
BCR_EXPORT_NODE = 987
BCR_CURRENT_URL = "https://www.cac.bcr.com.ar/es/precios-de-pizarra"
MAGYP_URL = (
    "https://www.magyp.gob.ar/sitio/areas/ss_mercados_agropecuarios/areas/granos/"
    "_archivos/000056_Precios%20Locales/000020_Precios%20C%C3%A1mara%20-%20Diario/"
    "000001_Cotizaciones%20de%20Pizarra%20sobre%20Puerto%20-%20Precios%20C%C3%A1maras.php"
    "?accion=imp"
)
FX_URL = "https://api.argentinadatos.com/v1/cotizaciones/dolares/oficial"

# ---------------------------------------------------------------------------
# Productos MVP
# ---------------------------------------------------------------------------
# `max_signal` limita el nivel de señal por producto:
#   none < watch < buy/sell < strong
# Girasol queda topeado en `watch` (ver docs/decisiones.md D10).
PRODUCTS: dict[str, dict] = {
    "maiz": {
        "name": "Maíz",
        "bcr_id": 3,
        "bcr_type": "pizarra",
        "mode": "buy",
        "max_signal": "strong",
        "market": "Rosario",
    },
    "soja": {
        "name": "Soja",
        "bcr_id": 13,
        "bcr_type": "pizarra",
        "mode": "sell",
        "max_signal": "strong",
        "market": "Rosario",
    },
    "trigo": {
        "name": "Trigo pan",
        "bcr_id": 8,
        "bcr_type": "pizarra",
        "mode": "sell",
        "max_signal": "strong",
        "market": "Rosario",
    },
    "girasol": {
        "name": "Girasol",
        "bcr_id": 9,
        "bcr_type": "any",
        "mode": "sell",
        "max_signal": "watch",
        "market": "Rosario",
    },
}

# Nombre del producto en la pizarra de MAGyP (clave de su tabla).
MAGYP_NAMES = {
    "maiz": "maiz",
    "soja": "soja",
    "trigo": "trigo pan",
    "girasol": "girasol",
}

# ---------------------------------------------------------------------------
# Reglas de señal
# ---------------------------------------------------------------------------
WINDOW_DAYS = 730
MIN_OBSERVATIONS = 250          # observaciones con precio en la ventana
STALE_BUSINESS_DAYS = 5         # frescura: último operado <= N días hábiles
OUTLIER_DAILY_CHANGE = 0.50     # variación diaria > 50% => outlier
COOLDOWN_DAYS = 7               # antispam por producto+dirección+nivel
MAX_PUSH_PER_DAY = 3
RSI_PERIOD = 14
MA_FAST = 50
MA_SLOW = 200

# Niveles de señal (orden de prioridad para el tope y el antispam).
SIGNAL_RANK = {"none": 0, "watch": 1, "buy": 2, "sell": 2, "strong": 3}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def now() -> datetime:
    return datetime.now(TZ)


def round2(value: float | None) -> float | None:
    """Redondea a 2 decimales para la salida JSON."""
    if value is None:
        return None
    return round(float(value), 2)

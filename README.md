# Oportunidades de granos — Argentina

App Android para detectar oportunidades de compra y venta de granos en Argentina,
con precios de referencia de la Cámara Arbitral de Cereales de Rosario (BCR).

**Estado actual: Fase 1 (pipeline y señales) implementada.** La UI se construye en
Fase 2; las alertas push (FCM) en Fase 3.

- Productos MVP: **maíz, soja, trigo pan y girasol**.
- Señal en **USD/t**; visualización en **ARS/t** con cotización BNA.
- Mercado de referencia: **Rosario**. Precio local = Rosario + flete configurable
  (Chaco no tiene pizarra oficial propia).
- Backend sin servidor: GitHub Actions + JSON en el repo + FCM.

## Estructura

```text
proyecto/
├── app/                     # Flutter (Fase 2)
├── pipeline/                # Python (Fase 1)
├── data/                    # JSON generado por el pipeline
├── docs/                    # documentación y reporte de Fase 0
├── scripts/                 # setup del entorno y validación de fuentes
├── artifacts/               # crudos descargados (no se versiona)
└── .github/workflows/       # GitHub Actions (Fase 1)
```

## Documentación

| Documento | Contenido |
|---|---|
| [docs/fase-0-entorno.md](docs/fase-0-entorno.md) | Reporte de Fase 0: entorno, checklist y pendientes |
| [docs/data-sources.md](docs/data-sources.md) | Fuentes BCR/MAGyP/FX: endpoints, parseo y validación |
| [docs/fase-0-validation.json](docs/fase-0-validation.json) | Reporte máquina de la validación de fuentes |
| [docs/architecture.md](docs/architecture.md) | Arquitectura y decisiones técnicas |
| [docs/signal-spec.md](docs/signal-spec.md) | Especificación de señales (implementada) |
| [docs/backtest.md](docs/backtest.md) | Resultados del backtest |
| [docs/disclaimer.md](docs/disclaimer.md) | Texto legal y atribución de fuentes |
| [docs/decisiones.md](docs/decisiones.md) | Registro de decisiones |

## Entorno de desarrollo (Windows)

```powershell
# Ejecutar como Administrador
powershell -ExecutionPolicy Bypass -File scripts\setup-dev-windows.ps1
```

Instala JDK 17, Android Studio, Android SDK, Flutter stable y Python 3.12 de forma
idempotente. Ver [docs/fase-0-entorno.md](docs/fase-0-entorno.md).

## Ejecutar el pipeline

```powershell
.\.venv\Scripts\python.exe -m pipeline.main            # escribe data/
.\.venv\Scripts\python.exe -m pipeline.main --dry-run  # solo imprime
.\.venv\Scripts\python.exe -m pipeline.src.backtest    # regenera docs/backtest.md
.\.venv\Scripts\python.exe -m pytest -q                # tests
```

El workflow `.github/workflows/update-data.yml` lo corre 2 veces por día hábil y
commitea `data/`.

## Validar las fuentes de datos

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r pipeline\requirements.txt
.\.venv\Scripts\python.exe scripts\validate-sources.py
```

Descarga BCR (4 productos, 2 años), MAGyP y la serie FX; deja los crudos en
`artifacts/fase0/` y un resumen en `artifacts/fase0/report.json`.

## Reglas del proyecto

- No hardcodear secretos.
- Fechas en `America/Argentina/Buenos_Aires`; precios con `Decimal` y 2 decimales en JSON.
- Todos los JSON llevan `schema_version`.
- Tests antes de conectar FCM.
- La app no es asesoramiento financiero (ver disclaimer).

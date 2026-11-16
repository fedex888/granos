# Pipeline de datos (Fase 1)

Descarga BCR, MAGyP y FX, normaliza a USD/t, calcula señales y publica los JSON que
consume la app.

## Estructura

```text
pipeline/
├── main.py              # entrypoint: `python -m pipeline.main`
├── src/
│   ├── config.py        # productos, fuentes, reglas y rutas
│   ├── util.py          # parseo de números/fechas y días hábiles
│   ├── sources/{bcr,magyp,fx}.py
│   ├── normalize.py     # puntos canónicos con USD (forward-fill de FX)
│   ├── signals.py       # métricas, scores, señales y explicaciones
│   ├── alerts.py        # alertas con antispam (cooldown/dedup)
│   ├── publish.py       # escritura de data/*.json
│   ├── main.py          # orquestación (src/main.py)
│   └── backtest.py      # backtest y reporte docs/backtest.md
├── tests/
│   ├── fixtures/        # snapshots de BCR/MAGyP/FX del 2026-11-15
│   └── test_*.py
└── requirements.txt
```

## Uso

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r pipeline\requirements.txt

# Dry-run (no escribe data/)
.\.venv\Scripts\python.exe -m pipeline.main --dry-run

# Corrida real (escribe data/)
.\.venv\Scripts\python.exe -m pipeline.main

# Con commit y push de data/ (lo usa GitHub Actions)
.\.venv\Scripts\python.exe -m pipeline.main --commit --push

# Backtest
.\.venv\Scripts\python.exe -m pipeline.src.backtest
```

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Configurado vía `pytest.ini` (raíz). Los tests usan los fixtures de
`pipeline/tests/fixtures/` y no golpean las fuentes.

## Reglas implementadas

- **Girasol**: `type=any`, `quality` por punto, tope de señal `watch` (D10).
- **Frescura**: operado con ≤ 5 días hábiles; sin operado reciente no hay alertas.
- **FXC**: ArgentinaDatos `oficial/compra` con forward-fill; se filtra la fila futura.
- **Confirmación**: `buy`/`sell` no fuertes requieren 2 observaciones consecutivas.
- **Antispam**: cooldown de 7 días por producto+dirección+nivel; máx 3 alertas/día.
- **Precio > 0**: los `0.00` y `S/C` se descartan.

## Notas

- El envío por FCM es Fase 3; `alerts.py` solo registra en `data/alerts/`.
- `google-services.json` y la cuenta de servicio de FCM no están en el repo.

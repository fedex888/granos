# Pipeline (Fase 1)

Todavía no implementado. Esta carpeta contiene el esqueleto y las dependencias.

## Estructura prevista

```text
pipeline/
├── src/
│   ├── config.py
│   ├── sources/{bcr,magyp,fx}.py
│   ├── normalize.py
│   ├── signals.py
│   ├── alerts.py
│   ├── publish.py
│   └── main.py
├── tests/
│   ├── fixtures/
│   ├── test_bcr.py
│   ├── test_magyp.py
│   └── test_signals.py
└── requirements.txt
```

## Notas de Fase 0

- El parser de BCR debe localizar la columna `Precio` por encabezado: girasol con
  `type=any` agrega una columna `(E)` antes del precio.
- El nodo de export `987` no se descubre desde el HTML; dejarlo configurable.
- `S/C` y `(E)` no son precios operados.
- Girasol no alcanza 250 operados: ver `docs/decisiones.md` D10.
- Filtrar la fila futura de ArgentinaDatos y usar `compra`.
- Guardar crudos en `artifacts/` (30 días, no versionado).

## Instalación local

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r pipeline\requirements.txt
```

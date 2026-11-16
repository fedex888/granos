# Fixtures de prueba

Snapshots descargados el **2026-11-15** por `scripts/validate-sources.py`.
Sirven para tests de parseo de la Fase 1; no se actualizan automáticamente.

| Archivo | Origen | Qué cubre |
|---|---|---|
| `bcr_trigo.xlsx` | BCR export, `product=8`, `type=pizarra` | Formato estándar: Fecha \| Precio |
| `bcr_maiz.xlsx` | BCR export, `product=3`, `type=pizarra` | Días `S/C` |
| `bcr_soja.xlsx` | BCR export, `product=13`, `type=pizarra` | Formato estándar |
| `bcr_girasol.xlsx` | BCR export, `product=9`, `type=any` | **Columna `(E)` antes del precio** |
| `bcr_page.html` | `https://www.cac.bcr.com.ar/es/precios-de-pizarra` | Pizarra del día y TC BNA |
| `magyp_pizarra.html` | MAGyP pizarra sobre puerto (`?accion=imp`) | Tabla, fecha y columna Rosario |
| `fx_oficial_sample.json` | ArgentinaDatos, últimas 60 filas | Serie FX e inclusión de fecha futura |

## Casos de prueba sugeridos

- `bcr_girasol.xlsx`: el precio está en la columna C, no en B; detectar por encabezado.
- `bcr_maiz.xlsx`: ignorar `S/C` sin romper la serie.
- `bcr_page.html`: parsear `S/C (E) $752.885,00` como `estimated`.
- `magyp_pizarra.html`: `GIRASOL = 0.00` significa sin cotización.
- `fx_oficial_sample.json`: descartar `2026-11-16` si hoy es 2026-11-15.

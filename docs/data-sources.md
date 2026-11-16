# Fuentes de datos — validación Fase 0

**Fecha de validación:** 2026-11-15  
**Script:** [`scripts/validate-sources.py`](../scripts/validate-sources.py)  
**Reporte máquina:** [`docs/fase-0-validation.json`](fase-0-validation.json) (versionado)  
**Crudos:** `artifacts/fase0/` (no versionado)  
**Ventana validada:** 2024-11-15 → 2026-11-15 (730 días)

## Resumen

| Fuente | Estado | Uso |
|---|---|---|
| BCR — export XLSX histórico | ✅ OK | Serie principal de precios |
| BCR — pizarra del día (HTML) | ✅ OK | Último precio y TC BNA divisa |
| MAGyP — pizarra diaria sobre puerto | ✅ OK (parcial) | Control cruzado / fallback |
| FX — ArgentinaDatos (BNA oficial) | ✅ OK con salvedad | Conversión ARS→USD |

Los cuatro productos descargan 481 filas cada uno (una por día de la ventana).
Trigo, maíz y soja tienen más de 460 precios operados. **Girasol no cumple el
mínimo de 250 observaciones operadas** (ver limitaciones).

## 1. BCR — export histórico XLSX

### Endpoint

```text
https://www.cac.bcr.com.ar/es/api/prices/987/export
  ?product={id}
  &type={pizarra|estimativo|any|average}
  &date_start=YYYY-MM-DD
  &date_end=YYYY-MM-DD
  &period=day
```

- Responde `200`, `Content-Type: application/vnd.ms-excel`, pero el archivo es **XLSX real**.
- `Content-Disposition: attachment; filename=precios.xlsx`.
- No requiere cookies, login ni navegador.
- El **ID `987` no aparece en el HTML** de la página de consultas: se genera del lado
  del cliente. No se puede "extraer del HTML" como sugiere el plan; debe quedar
  configurable (`BCR_EXPORT_NODE`) y monitorearse. Verificado el 2026-11-15.

### IDs de producto

Confirmados contra el `<select name="product">` de
`https://www.cac.bcr.com.ar/es/precios-de-pizarra/consultas`:

| Producto | `product` | `type` usado | Nombre en BCR |
|---|---|---|---|
| Trigo pan | 8 | `pizarra` | Trigo |
| Maíz | 3 | `pizarra` | Maíz |
| Girasol | 9 | `any` | Girasol |
| Soja | 13 | `pizarra` | Soja |
| (Sorgo, fuera del MVP) | 6 | — | Sorgo |

Tipos disponibles: `pizarra`, `estimativo`, `any`, `average`.

### Formato del XLSX

Hoja única `Worksheet`. Filas iniciales de título, luego:

```text
Fila 4:  Trigo
Fila 5:  Fecha de operación | Precio
Fila 6+: <datetime>         | <número o "S/C">
```

Particularidad de **girasol con `type=any`**: se inserta una columna de calidad
antes del precio y el encabezado queda corrido:

```text
Fila 5:  Fecha de operación | (vacío) | Precio
Fila 6+: <datetime>         | "(E)"    | 752885
```

Por eso el parser **no debe asumir columnas fijas**: busca la fila de encabezado y
localiza la columna `Precio` por nombre. La marca `(E)` significa precio estimado
(sin operación). `S/C` significa sin cotización y se descarta.

### Pizarra del día (HTML server-side)

```text
https://www.cac.bcr.com.ar/es/precios-de-pizarra
```

- HTML renderizado en servidor, sin JavaScript para los precios.
- Cada producto es un `div.board.board-<producto>` con `h3`, `div.price` y el valor
  en USD. Girasol puede venir como `S/C (E) $752.885,00` (operado no disponible,
  estimado sí).
- El pie trae `TC BNA Divisas Comprador 12/11/2026: $ 1.536,50` y la fecha de
  publicación.
- El CAPTCHA de la página pertenece al formulario de contacto; **no bloquea** la
  lectura de precios.
- Verificado: los valores ARS de la pizarra coinciden exactamente con la última
  fila del XLSX para los 4 productos.

### Resultado por producto (ventana 730 días)

| Producto | Filas | Con precio | Operados | Estimados | Sin cotización | Último dato | Últ. operado | Precio ARS/t | USD/t\* | Brecha máx. operada |
|---|---:|---:|---:|---:|---:|---|---|---:|---:|---:|
| Trigo | 481 | 474 | 474 | 0 | 7 | 2026-11-12 | 2026-11-12 | 288.900,00 | 190,07 | 6 días |
| Maíz | 481 | 469 | 469 | 0 | 12 | 2026-11-12 | 2026-11-12 | 275.800,00 | 181,45 | 5 días |
| Soja | 481 | 472 | 472 | 0 | 9 | 2026-11-12 | 2026-11-12 | 540.000,00 | 355,26 | 5 días |
| Girasol | 481 | 480 | **195** | **285** | 1 | 2026-11-12 (E) | 2026-10-13 | 752.885,00 (E) | 495,32 | **73 días** |

\* USD calculado con FX ArgentinaDatos del último día hábil (ver salvedad FX).

- Sin fechas duplicadas.
- Sin variaciones diarias > 50% en la serie operada.
- Los días faltantes son feriados/fines de semana sin pizarra.

### Limitación importante: girasol

Con `type=pizarra`, girasol tiene **195 precios operados y 286 días `S/C`** en dos
años. Con `type=any` se completan 480 observaciones, pero **285 son estimadas
(59%)** y la última operación es del **2026-10-13** (brecha máxima de 73 días).

Consecuencias frente al plan:

- No alcanza el mínimo de 250 observaciones **operadas**.
- La regla "usar el operado anterior dentro de 5 días hábiles" casi nunca se cumple:
  el dato de girasol quedaría `stale` de forma permanente y **nunca generaría alerta**.
- Decisión pendiente para Fase 1 (ver [decisiones.md](decisiones.md)): aceptar
  estimados con `quality=estimated` y limitar girasol a `watch`, o dejarlo como
  producto informativo sin alertas.

## 2. MAGyP — pizarra diaria

### Endpoint

```text
https://www.magyp.gob.ar/sitio/areas/ss_mercados_agropecuarios/areas/granos/
_archivos/000056_Precios%20Locales/000020_Precios%20C%C3%A1mara%20-%20Diario/
000001_Cotizaciones%20de%20Pizarra%20sobre%20Puerto%20-%20Precios%20C%C3%A1maras.php?accion=imp
```

- Devuelve un fragmento HTML pequeño (≈14 KB, UTF-8), sin login.
- Tabla `Cotizaciones de Pizarra sobre Puerto en $/Tn` con fecha en la primera fila
  (`Jueves 12 de noviembre de 2026`).
- Columnas: `PRODUCTO | BUENOS AIRES | BAHIA BLANCA | QUEQUEN | ROSARIO | CORDOBA`.
- Precios en formato `288,900.00` (coma de miles, punto decimal) o `0.00`.
- **`0.00` significa sin cotización.**
- Es una foto diaria, no una serie histórica.

### Control cruzado del 2026-11-12

| Producto | MAGyP Rosario | BCR | ¿Coincide? |
|---|---:|---:|---|
| Trigo pan | 288.900,00 | 288.900,00 | ✅ |
| Maíz | 275.800,00 | 275.800,00 | ✅ |
| Soja | 540.000,00 | 540.000,00 | ✅ |
| Girasol | 0,00 (sin cotización) | 752.885,00 (E) | ⚠️ MAGyP no sirve de fallback |

MAGyP replica la pizarra de BCR para Rosario, pero **no cubre girasol** el día
validado y no tiene historial diario descargable. Sirve como control de frescura y
como fallback de trigo/maíz/soja.

### Histórico mensual (opcional)

La página
`.../000010_Precios%20Internos%20de%20los%20Principales%20Granos/000001_Informe%20Actual...php`
tiene un link a `Historicos de la Evolucion de los Precios Internos de los Principales Granos.xlsx`
con promedios mensuales en ARS. No se usa para la señal diaria; sirve para
auditorías de largo plazo.

## 3. FX — dólar oficial (ArgentinaDatos)

### Endpoint

```text
https://api.argentinadatos.com/v1/cotizaciones/dolares/oficial
```

Respuesta: array de `{ casa, compra, venta, fecha }`.

- 5.797 filas desde 2011-01-03.
- 731 filas en la ventana de 730 días, sin valores nulos ni ceros.
- Último dato: 2026-11-15, `compra = 1520`, `venta = 1570`.
- **Incluye una fila con fecha futura** (2026-11-16). El pipeline debe filtrar
  `fecha <= hoy` en `America/Argentina/Buenos_Aires`.
- Se usa `compra`, tal como indica el plan.

### Salvedad: no es el mismo dólar que usa BCR

BCR convierte con **dólar divisa BNA comprador**: 1.536,50 al 2026-11-12.
ArgentinaDatos "oficial compra" devuelve **1.520,00** para esa fecha.

| Concepto | Valor |
|---|---:|
| TC BNA divisa (BCR) | 1.536,50 |
| ArgentinaDatos oficial compra | 1.520,00 |
| Diferencia | **-1,07%** |

Impacto: el USD calculado con ArgentinaDatos queda **+1,09%** por encima del USD
que publica BCR para los 4 productos (verificado el 2026-11-12). Ejemplo: trigo
288.900 / 1.520 = 190,07 USD/t, mientras BCR publica 188,02 USD/t.

Implicancias:

- Un **desplazamiento constante** no altera percentiles, z-score ni el ranking de
  señales; sí altera el valor absoluto mostrado.
- Si la brecha entre "oficial" y "divisa" varía en el tiempo, agrega ruido a la
  serie. No se pudo verificar la estabilidad histórica con las fuentes actuales.
- Decisión: mantener ArgentinaDatos para la serie de 2 años (es la única serie
  histórica gratuita y consistente disponible), guardar `fx_usd_ars` en cada punto
  y registrar el TC BNA de BCR cuando esté disponible para control. **No mezclar
  fuentes dentro de una misma serie.**

## 4. Riesgos y observaciones para Fase 1

1. **Girasol**: 195 operados < 250. Definir política antes de implementar señales.
2. **Nodo de export BCR (`987`)**: no es descubrible desde el HTML; si cambia, el
   pipeline falla. Hacerlo configurable y validar que el XLSX tenga el encabezado
   esperado.
3. **FX**: brecha de -1,07% con el TC de BCR; no mezclar fuentes y filtrar fechas
   futuras.
4. **MAGyP no tiene girasol** y no tiene serie diaria histórica.
5. **`S/C` y `(E)`**: no son precios operados; no usarlos para mínimos/máximos ni
   para alertas sin marcar `quality`.
6. **Rate limit**: BCR no exige cookies, pero conviene un User-Agent identificable,
   una descarga por producto y reintentos con backoff.
7. **Feriados**: la serie tiene huecos; no interpolar para mínimos. Usar el último
   dato operado y la regla de 5 días hábiles.
8. **Datos crudos**: guardar XLSX/HTML en `artifacts/` (30 días) para reproducir
   fallas de parseo.

## 5. Cómo reproducir la validación

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r pipeline\requirements.txt
.\.venv\Scripts\python.exe scripts\validate-sources.py
```

Salida esperada: checks `OK` para descargas, cobertura y control cruzado; warnings
por girasol y por la brecha de FX.

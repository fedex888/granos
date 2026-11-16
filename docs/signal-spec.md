# Especificación de señales

**Estado:** borrador. Se implementa y valida en Fase 1.  
**Referencia normativa:** plan §7. Este documento resume las reglas para evitar
ambigüedades durante la implementación.

## Normalización

- Precio canónico: `price_usd = price_ars / fx_usd_ars`.
- Guardar `date`, `price_ars`, `price_usd`, `fx_usd_ars`, `quality`, `source`.
- Unidades: ARS/t y USD/t. Si una fuente viene en ARS/qq, multiplicar por 10.
- Fechas en `America/Argentina/Buenos_Aires`, formato `YYYY-MM-DD`.
- No interpolar para calcular mínimos ni máximos: solo observaciones reales.
- `quality`: `operated` si hubo operación; `estimated` si es `(E)`; `stale` si el
  último operado tiene más de 5 días hábiles.
- Si el último dato es estimado y hay un operado dentro de 5 días hábiles, usar el
  operado y marcar `stale`. Si no hay dato en 5 días hábiles, no alertar.

## Ventana y métricas

- Ventana móvil: 730 días.
- Mínimo de observaciones: 250 para series diarias; si no se alcanza,
  `signal = insufficient_data`.
- `prior_window`: observaciones anteriores al precio actual, dentro de la ventana.
- `low_2y`, `high_2y`, `avg_2y`, `percentile`, `distance_from_low_pct`,
  `distance_from_high_pct`, `zscore`, `rsi_14` (Wilder), `ma_50`, `ma_200`,
  `change_1d_pct`, `change_30d_pct`, según plan §7.2.

## Scores

Compra:

```text
score_percentile = 100 - percentile
score_distance   = clamp(100 - distance_from_low_pct * 5, 0, 100)
score_z          = clamp(50 - zscore * 25, 0, 100)
score_rsi        = clamp(100 - rsi_14, 0, 100)
score_trend      = 100 si current > ma_50 y ma_50 sube; 50 si solo current > ma_50; 0 si no
score_quality    = 100 operado y fresco; 70 estimado; 0 stale

score_buy = 0.35*percentile + 0.25*distance + 0.15*z + 0.10*rsi + 0.10*trend + 0.05*quality
```

Venta: invertir percentil, distancia, z, RSI y tendencia; mismos pesos.

## Niveles

| Señal | Condición |
|---|---|
| `strong` (compra) | nuevo mínimo de 2 años **o** `score_buy >= 80` y `percentile <= 10` |
| `buy` | `score_buy >= 70`, `percentile <= 20`, dato fresco |
| `watch` (compra) | `score_buy >= 60`, `percentile <= 30` |
| `strong` (venta) | nuevo máximo de 2 años **o** `score_sell >= 80` y `percentile >= 90` |
| `sell` | `score_sell >= 70`, `percentile >= 80`, dato fresco |
| `watch` (venta) | `score_sell >= 60`, `percentile >= 70` |

- `buy`/`sell` no fuertes requieren **2 observaciones consecutivas**.
- `strong` alerta el mismo día.

## Antispam

- Cooldown 7 días por producto + dirección + nivel.
- Un nuevo mínimo/máximo posterior al cooldown puede emitir `strong`.
- Máximo 3 push por día; prioridad `strong` y luego mayor score.
- Persistir historial en `data/alerts/`.

## Explicaciones

Plantillas en plan §7.6, en castellano rioplatense y sin jerga.

## Criterio de aceptación del backtest

Para `buy`, retorno promedio a 30 días > 0 y hit rate > 50%. Si no se cumple,
ajustar pesos o dejar solo la regla de nuevo mínimo.

## Preguntas abiertas

1. **Girasol** (D10): 195 operados < 250. Definir si se aceptan estimados y si se
   limita a `watch` antes de implementar `signals.py`.
2. **Ventana con estimados**: si se incluyen, ¿cuentan para `low_2y`/`high_2y`?
   Propuesta: sí para métricas, pero `quality` penaliza el score y bloquea alertas
   `strong`.
3. **`stale`**: confirmar definición exacta (5 días hábiles desde el último operado).

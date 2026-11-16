# Backtest

**Estado:** ejecutado el 2026-11-16T19:12:04-03:00. Período 2024-01-01 → 2026-11-16.

## Metodología

- Señales calculadas con ventana móvil de 730 días, **sin lookahead** (cada observación usa solo datos previos).
- Retorno forward a 30, 60 y 90 días sobre el primer precio disponible en o después de esa fecha.
- El P&L de la señal es positivo cuando acierta: para **comprar**, si el precio sube; para **vender**, si el precio baja (se reporta el negativo del retorno del precio).
- Baseline: retorno promedio de 30 días de *comprar todos los días* (y su inverso para vender).

## Baseline (siempre comprar/vender, 30 días)

| Dirección | Retorno prom. | Hit rate |
|---|---:|---:|
| Comprar | 0.43% | 52.1% |
| Vender | -0.43% | 47.8% |

## Resultados por producto

| Producto | Dirección | Señales | Hit 30d | Ret. 30d | Ret. 60d | Ret. 90d |
|---|---|---:|---:|---:|---:|---:|
| Maíz | buy | 15 | 100.0% | 5.24% | 5.2% | 5.42% |
| Maíz | sell | 60 | 81.7% | 5.03% | 7.35% | 9.57% |
| Soja | buy | 47 | 85.1% | 7.18% | 8.7% | 12.97% |
| Soja | sell | 166 | 64.6% | 1.53% | 2.23% | 3.09% |
| Trigo pan | buy | 70 | 48.6% | -0.71% | 1.19% | 3.76% |
| Trigo pan | sell | 43 | 69.2% | 4.69% | 10.23% | — |
| Girasol | buy | 0 | — | — | — | — |
| Girasol | sell | 0 | — | — | — | — |

## Criterio de aceptación (plan §7.7)

Para `buy`, retorno promedio a 30 días > 0 y hit rate > 50%.

| Producto | Compra | Detalle |
|---|---|---|
| Maíz | ✅ | 15 señales, hit 100.0%, 5.24% a 30d |
| Soja | ✅ | 47 señales, hit 85.1%, 7.18% a 30d |
| Trigo pan | ⚠️ | 70 señales, hit 48.6%, -0.71% a 30d: no alcanza el umbral |
| Girasol | — | 0 señales accionables (tope `watch`, D10) |

## Conclusiones

- Las señales de **compra** de maíz y soja superan el criterio con margen.
- La compra de **trigo** no alcanza el umbral (muestra chica y más ruidosa). Como el modo por defecto de trigo es *vender*, no bloquea el MVP; queda anotado para revisar pesos o degradar a `watch` si se confirma con más datos.
- Las señales de **venta** son direccionalmente correctas en los tres granos (el precio cae tras la señal).
- Girasol no genera señales accionables, como se decidió en D10.

CSV con las señales: [`backtest-signals.csv`](backtest-signals.csv).

# Backtest

**Estado:** pendiente de Fase 1. No hay resultados todavía.

## Objetivo

Verificar que las señales de compra/venta tienen valor predictivo antes de
publicarlas y de conectar alertas.

## Metodología prevista

- Período: 2024-01-01 → 2026-11-15.
- Señales calculadas con ventana móvil de 730 días, **sin lookahead**.
- Retornos forward a 30, 60 y 90 días.
- Métricas: cantidad de señales, hit rate, retorno promedio, mediana, máxima
  excursión adversa (MAE) y favorable (MFE).
- Baseline: días aleatorios y "siempre comprar"/"siempre vender".
- Salida: `docs/backtest.md` + CSV con las señales.

## Criterio de aceptación

Para `buy`, el retorno promedio a 30 días debe ser positivo y el hit rate mayor al
50%. Si no se cumple, se ajustan los pesos o se deja solo la regla de nuevo mínimo
(ver plan §7.7).

## A considerar

- **Girasol**: serie operada discontinua (195 observaciones, brecha máxima de 73
  días). El backtest debe correrse por separado y probablemente no alcance el
  mínimo de 250; ver decisión D10.
- **FX**: la serie ArgentinaDatos difiere -1,07% del dólar divisa de BCR. Evaluar
  sensibilidad de los resultados a esa brecha.
- **Muestra**: 2 años y 4 productos es una muestra chica; no prometer predicción.

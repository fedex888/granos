# Decisiones — Fase 0

Registro de decisiones tomadas durante la preparación. Las decisiones marcadas
**Pendiente** deben resolverse antes de implementar la parte afectada en Fase 1.

| # | Fecha | Decisión | Estado | Motivo |
|---|---|---|---|---|
| D1 | 2026-11-15 | Productos MVP: maíz, soja, trigo pan y girasol | Aceptada | Confirmado en el plan; hay datos BCR para los cuatro |
| D2 | 2026-11-15 | Android 8.0+ (`minSdk 26`) | Aceptada | Cobertura suficiente para el usuario objetivo; permite APIs modernas de notificaciones |
| D3 | 2026-11-15 | Distribución por APK directa, sin Google Play | Aceptada | Presupuesto cero y un solo usuario |
| D4 | 2026-11-15 | Paquete Android: `com.fedex888.granos` | Aceptada | Confirmado por el usuario; fijado al crear la app en Firebase |
| D5 | 2026-11-15 | Flete inicial compra/venta = 0 USD/t | Aceptada | El plan lo fija en 0; se calibra con el usuario final |
| D6 | 2026-11-15 | Fuente FX: ArgentinaDatos `oficial/compra` | Aceptada con salvedad | Única serie histórica gratuita y consistente; difiere -1,07% del dólar divisa BNA de BCR |
| D7 | 2026-11-15 | No mezclar fuentes FX dentro de una serie | Aceptada | Evita saltos artificiales; el TC BNA de BCR se guarda solo como control |
| D8 | 2026-11-15 | Nodo de export BCR `987` configurable | Aceptada | No se puede extraer del HTML; si cambia, el pipeline debe fallar con error claro |
| D9 | 2026-11-15 | `schema_version: 1` en todos los JSON | Aceptada | Requisito del plan |
| D10 | 2026-11-16 | Girasol: serie `type=any` (operado+estimado), métricas sobre la serie completa, tope de señal `watch` | Aceptada | 195 operados < 250; los estimados de BCR son referencia válida para el gráfico, pero no sostienen señales accionables |
| D11 | 2026-11-15 | Zona horaria `America/Argentina/Buenos_Aires` | Aceptada | Requisito del plan; `tzdata` incluido para Windows |
| D12 | 2026-11-16 | Repositorio GitHub `fedex888/granos` (público, rama `main`) | Aceptada | Requerido para que la app lea `data/*.json` sin autenticación |
| D13 | 2026-11-16 | Proyecto Firebase `granos-oportunidades` + app Android `com.fedex888.granos` | Aceptada | Proyecto y app creados; `google-services.json` descargado |
| D14 | 2026-11-15 | Precio local Chaco = Rosario ± flete, con override manual | Aceptada | No existe pizarra local oficial |
| D15 | 2026-11-15 | `google-services.json` no se versiona | Aceptada | Guardado en `app/android/app/` (ignorado por Git); en CI se inyecta desde un secreto |

## Detalle

### D4 — Package ID

Confirmado: `com.fedex888.granos`. Una vez creada la app Android en Firebase, el ID
no se puede cambiar sin crear otra app.

### D10 — Política de girasol

Decisión final (aceptada):

1. **Serie:** descargar girasol con `type=any` (incluye estimados) y guardar
   `quality` (`operated` / `estimated`) por punto.
2. **Métricas:** `low_2y`, `high_2y`, `avg_2y`, `percentile`, `zscore`, `rsi_14`,
   `ma_50`, `ma_200` se calculan sobre la **serie completa** (operados + estimados),
   porque los estimados de BCR son la referencia oficial para el gráfico.
3. **Mínimo de observaciones:** 250 sobre la serie completa (girasol tiene 480 → OK).
4. **Frescura:** un punto es "fresco" solo si es operado y tiene ≤ 5 días hábiles.
   Con la brecha actual (último operado 2026-10-13), girasol queda `stale` para
   alertas.
5. **Tope de señal:** `max_signal = watch`. Girasol puede mostrar `watch` (contexto)
   pero **nunca** `strong`, `buy` ni `sell`; por lo tanto nunca genera push.
6. **Configurable** por producto en `config.py` (`max_signal`): si BCR publica más
   operados en el futuro, se levanta el tope sin tocar código.

Resultado: girasol se ve en la app con precio y gráfico reales, muestra un `watch`
cuando corresponde, y no promete señales accionables que sus datos no sostienen.

### D12 / D13 — GitHub y Firebase (completados)

Ejecutados el 2026-11-16:

- **GitHub:** repo público `https://github.com/fedex888/granos`, rama `main`, con el
  contenido de Fase 0 subido. Token de `gh` con scopes `repo`, `workflow`,
  `read:org` y `gist`.
- **Firebase:** proyecto `granos-oportunidades` (nº 770713701053) y app Android
  `com.fedex888.granos` (app id `1:770713701053:android:dbae6d26565838b5f505d4`).
  `google-services.json` descargado y guardado en `app/android/app/` (no versionado).

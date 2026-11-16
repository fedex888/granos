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
| D10 | 2026-11-15 | Girasol: incluir con `quality=estimated`; alertas solo si hay operado reciente | **Pendiente** | Solo 195 operados en 2 años (<250) y brecha máxima de 73 días; con la regla actual nunca alertaría |
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

Opciones para Fase 1:

1. **Recomendada:** usar `type=any`, guardar `quality=estimated`, calcular métricas
   con toda la serie y limitar girasol a señal `watch` como máximo. Nunca `strong`.
2. Tratar girasol como informativo: mostrar precio y gráfico, sin score ni alertas.
3. Exigir 195 operados como mínimo específico para girasol y alertar solo con
   operado fresco (en la práctica, casi nunca).

La opción 1 mantiene el producto en la app sin prometer una señal que los datos no
sostienen. Requiere que el score penalice `quality=estimated` (ya previsto: 70/100).

### D12 / D13 — GitHub y Firebase (completados)

Ejecutados el 2026-11-16:

- **GitHub:** repo público `https://github.com/fedex888/granos`, rama `main`, con el
  contenido de Fase 0 subido. Token de `gh` con scopes `repo`, `workflow`,
  `read:org` y `gist`.
- **Firebase:** proyecto `granos-oportunidades` (nº 770713701053) y app Android
  `com.fedex888.granos` (app id `1:770713701053:android:dbae6d26565838b5f505d4`).
  `google-services.json` descargado y guardado en `app/android/app/` (no versionado).

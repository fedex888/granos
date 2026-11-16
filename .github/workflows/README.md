# GitHub Actions (Fase 1)

El workflow `update-data.yml` se implementa en Fase 1.

## Configuración prevista

- `on.schedule`: `0 14 * * 1-5` y `0 22 * * 1-5` UTC (11:00 y 19:00 ART).
- `workflow_dispatch` para ejecución manual.
- `permissions: contents: write`.
- `concurrency` para evitar solapamientos.
- Secretos: `FIREBASE_SERVICE_ACCOUNT` (solo Fase 3).
- Si falla, el workflow termina en error y GitHub notifica por email.

No se crea el workflow todavía para no dejar una acción roja en el repositorio.

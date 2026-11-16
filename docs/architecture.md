# Arquitectura

**Estado:** definida en el plan; implementación empieza en Fase 1.  
**Referencia:** `C:\Users\Administrator\.opencode\plan\plan-app-granos.md` §4–§10.

## Vista general

```text
BCR (XLSX histórico + pizarra HTML)
MAGyP (pizarra diaria, control cruzado)
ArgentinaDatos (FX BNA oficial)
        │ HTTPS
        ▼
GitHub Actions (Python 3.12)
  descarga → normaliza → valida → calcula señales → escribe JSON
        │                              │
        ▼                              ▼
GitHub (data/*.json)            Firebase Cloud Messaging
        │                              │ topic alertas-granos
        ▼                              ▼
App Flutter Android  ←──────── notificaciones push
  cache SQLite, gráficos, score
```

## Componentes

### Pipeline (Fase 1)

- Python 3.12 en GitHub Actions, sin servidor propio.
- Descarga BCR por producto (XLSX), pizarra BCR del día, MAGyP y FX.
- Normaliza a ARS/t y USD/t; conserva `quality` (`operated` / `estimated`).
- Valida precios, fechas, outliers y columnas antes de publicar.
- Calcula métricas y señales con ventana móvil de 730 días, sin lookahead.
- Escribe `data/latest.json`, `data/history/{id}.json`, `data/alerts/latest.json`
  y `data/status.json`.
- Commit de `data/` desde el workflow. Si una fuente falla, no pisa el último dato
  bueno y lo reporta en `status.json`.
- Envía FCM solo si hay alertas nuevas (Fase 3).

### Datos

- `data/` es la API pública de la app: JSON estático servido por GitHub.
- Todos los archivos llevan `schema_version`.
- La app cachea en SQLite y refresca en segundo plano.
- Contrato detallado: plan §6.

### App (Fase 2+)

- Flutter 3.x / Dart 3.x, Android únicamente, `minSdk 26` (Android 8.0).
- Riverpod, Dio, Drift/SQLite, fl_chart, go_router, intl, shared_preferences.
- FCM + notificaciones locales (Fase 3).
- Offline primero: muestra cache y avisa si `status.json` tiene más de 3 días.

### Distribución

- APK release firmada con keystore propio (fuera del repo).
- GitHub Releases + `version.json` para avisar actualizaciones.
- Sin Google Play en el MVP.

## Estructura del repositorio

```text
proyecto/
├── app/                     # Flutter (Fase 2)
│   ├── lib/{core,data,domain,features}/
│   ├── android/
│   └── pubspec.yaml
├── pipeline/
│   ├── src/{sources,normalize,signals,alerts,publish,main}.py   # Fase 1
│   ├── tests/{fixtures}/
│   └── requirements.txt
├── data/{latest.json,history/,alerts/,status.json}              # generado
├── .github/workflows/update-data.yml                            # Fase 1
├── docs/
├── scripts/
└── README.md
```

## Decisiones técnicas relevantes

| Tema | Decisión |
|---|---|
| Mercado de referencia | Rosario (BCR) |
| Moneda de análisis | USD/t; ARS/t solo visual |
| Ventana histórica | 730 días móviles |
| Frecuencia | Diaria, días hábiles |
| Persistencia remota | JSON en GitHub |
| Persistencia local | SQLite (Drift) |
| Push | FCM, topic `alertas-granos` |
| Zona horaria | `America/Argentina/Buenos_Aires` |
| Secretos | Variables de GitHub Actions; nunca en el repo |

## Riesgos de arquitectura

- **Scraping BCR**: cambios de HTML/XLSX o del nodo `987`. Mitigación: parser por
  encabezados, fixtures, `status.json`, fallback MAGyP.
- **Girasol**: datos operados insuficientes; ver `docs/decisiones.md` D10.
- **FX**: diferencia con el dólar divisa de BCR; ver `docs/data-sources.md` §3.
- **GitHub Actions**: demoras o fallos; dos corridas diarias y monitoreo de frescura.
- **Sin servidor**: no hay actualización en tiempo real; es aceptable para el MVP.

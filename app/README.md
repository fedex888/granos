# App Flutter (Fase 2)

Todavía no hay código de UI. Esta carpeta queda reservada para el proyecto Flutter
que se crea al cerrar la Fase 1.

## Estructura prevista

```text
app/
├── lib/
│   ├── core/       # tema, configuración, utilidades
│   ├── data/       # API, SQLite (Drift), repositorios
│   ├── domain/     # modelos y reglas de presentación
│   └── features/   # onboarding, home, detalle, alertas, ajustes
├── android/
└── pubspec.yaml
```

## Requisitos

- Flutter 3.50.0 / Dart 3.14.0 (ver `docs/fase-0-entorno.md`).
- Android SDK 36, JDK 17.
- `minSdk 26` (Android 8.0).

No crear `google-services.json` en el repo: se inyecta desde un secreto de CI
(ver `docs/decisiones.md` D15).

# App Flutter (Fase 2)

App Android para ver oportunidades de compra/venta de granos.

## Stack

- Flutter 3.50 / Dart 3.14, `minSdk 26` (Android 8.0+).
- `material_ui` (Material en Flutter 3.50), `flutter_riverpod`, `go_router`,
  `dio`, `fl_chart`, `intl`, `shared_preferences`, `path_provider`,
  `url_launcher`, `package_info_plus`.

## Estructura

```text
lib/
├── main.dart              # bootstrap (SharedPreferences + router)
├── app.dart               # GoRouter y MaterialApp.router
├── core/{format,theme}.dart
├── data/{models,api,cache,settings}.dart
├── domain/providers.dart  # Riverpod
└── features/
    ├── onboarding/
    ├── home/
    ├── detail/
    ├── alerts/
    └── settings/
```

## Datos

Consume los JSON públicos del repo (`raw.githubusercontent.com/fedex888/granos/main/data/`):

- `latest.json` → Home y Detalle.
- `history/{id}.json` → gráfico del detalle.
- `alerts/latest.json` → pantalla de alertas.

Offline-first: cada respuesta se cachea en disco (path_provider); si la red falla,
se muestra la última copia cacheada. Ajustes en `shared_preferences`.

## Compilar

```powershell
flutter build apk --debug   # entregable de Fase 2
flutter build apk --release # Fase 4 (firmada)
```

## Notas

- Las notificaciones push (FCM) ya están integradas (`lib/data/push.dart`): topic
  `alertas-granos`, permiso Android 13+, foreground con notificación local y tap
  que abre el detalle. Ver `docs/fcm.md`.
- `google-services.json` no se versiona (se inyecta en CI); está en
  `android/app/` localmente.
- El cache es por archivos JSON + `shared_preferences` en lugar de Drift/SQLite
  (ver `docs/decisiones.md` D16).

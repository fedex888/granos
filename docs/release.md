# Entrega — versión 1.0.0

## APK

- Archivo: `app-release.apk` (adjunto en el GitHub Release v1.0.0).
- Package: `com.fedex888.granos`.
- Firma: keystore propio (no versionado).
- `minSdk 26` (Android 8.0+).
- Release: <https://github.com/fedex888/granos/releases/tag/v1.0.0>

Descarga directa:
<https://github.com/fedex888/granos/releases/latest/download/app-release.apk>

## Instalación en el teléfono

1. Descargar el APK (desde el navegador del teléfono o pasarlo por USB).
2. Si Android lo pide, permitir **"Instalar apps desconocidas"** para el navegador /
   gestor de archivos.
3. Abrir el APK y tocar **Instalar**.
4. Abrir la app, completar el onboarding (comprar/vender, productos, flete) y
   aceptar el permiso de notificaciones.

## Firma (keystore)

- Keystore: `C:\Users\Administrator\keystores\granos-release.jks` (fuera del repo).
- Alias: `granos`.
- Credenciales: `secrets/keystore-backup.txt` (gitignored) y
  `app/android/key.properties` (gitignored).

> **Importante:** guardá el `.jks` y la contraseña en un lugar seguro y aparte.
> Sin ellos no se pueden publicar actualizaciones de la app.

## Recompilar

Requiere **JDK 21** (AGP 9.3.1 usa `List.removeLast()` en lint, que no existe en
JDK 17; con JDK 17 el build release falla en `lintVitalAnalyzeRelease`).

```powershell
cd app
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot"
flutter build apk --release
```

Salida: `app/build/app/outputs/flutter-apk/app-release.apk`.

Sin `app/android/key.properties` el build usa la firma debug (útil para desarrollo,
no para distribuir).

## Actualizaciones

`data/version.json` publica la última versión y la URL del APK:

```json
{
  "schema_version": 1,
  "latest": "1.0.0",
  "build": 1,
  "url": "https://github.com/fedex888/granos/releases/latest/download/app-release.apk"
}
```

Para publicar una nueva versión:

1. Subir `version` en `app/pubspec.yaml` (ej. `1.0.1+2`).
2. Compilar y firmar el APK.
3. Actualizar `data/version.json`.
4. Crear el release: `gh release create v1.0.1 app-release.apk --title "v1.0.1"`.

## Checklist de Fase 4

- [x] Arranque más rápido (FCM diferido al primer frame).
- [x] Aviso de datos desactualizados (> 3 días) en Home.
- [x] APK release firmada.
- [x] GitHub Release + instrucciones.
- [x] `version.json`.
- [x] Instalación y prueba en dispositivo.
- [ ] Revisión UX con el usuario final (abuelo/suegro): pendiente de su feedback.

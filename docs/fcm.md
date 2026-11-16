# Notificaciones push (FCM) — Fase 3

**Estado:** implementado en código y compilado. Falta la prueba en un dispositivo
real y cargar la cuenta de servicio (credencial del usuario).

## Componentes

| Pieza | Dónde |
|---|---|
| Proyecto Firebase | `granos-oportunidades` (nº 770713701053) |
| App Android | `com.fedex888.granos` |
| Topic | `alertas-granos` |
| Config Android | `app/android/app/google-services.json` (no versionado) |
| Plugin Gradle | `com.google.gms.google-services` 4.6.0 |
| App | `firebase_core`, `firebase_messaging`, `flutter_local_notifications` |
| Pipeline | `pipeline/src/notify.py` (FCM HTTP v1) |

## App (`app/lib/data/push.dart`)

- Inicializa Firebase y pide permiso de notificaciones (Android 13+).
- Se suscribe al topic `alertas-granos`.
- **Foreground:** muestra una notificación local con el mismo título/cuerpo.
- **Background / app cerrada:** el sistema muestra la notificación; al tocarla,
  la app abre el detalle del producto (`/product/{id}`) usando el `product_id` del
  payload.
- Canal de notificaciones: `alertas-granos` (`Alertas de granos`).

## Pipeline (`pipeline/src/notify.py`)

- Lee la cuenta de servicio de `FIREBASE_SERVICE_ACCOUNT` (JSON), de
  `GOOGLE_APPLICATION_CREDENTIALS` (ruta) o de
  `secrets/firebase-service-account.json` (local, gitignored).
- Obtiene un token OAuth con scope `firebase.messaging` y hace `POST` a
  `https://fcm.googleapis.com/v1/projects/{project}/messages:send`.
- Envía al topic `alertas-granos` con `notification` + `data`
  (`product_id`, `direction`, `tier`).
- Si no hay credenciales, **no falla**: registra `skipped` en `status.json`.
- Solo envía las alertas nuevas (después de cooldown/dedup y del tope de 3/día).

## Configuración pendiente (requiere tus credenciales)

### 1. Cuenta de servicio

En Firebase Console → ⚙️ **Configuración del proyecto** → **Cuentas de servicio**
→ **Generar nueva clave privada**. Descargá el JSON.

Opciones para usarla:

- **GitHub Actions:** crear el secreto `FIREBASE_SERVICE_ACCOUNT` con el contenido
  JSON:
  ```powershell
  gh secret set FIREBASE_SERVICE_ACCOUNT --repo fedex888/granos < ruta\service-account.json
  ```
- **Local:** guardarlo en `secrets/firebase-service-account.json` (gitignored) y
  correr el pipeline sin variables de entorno.

### 2. Probar el push

Con la cuenta de servicio configurada:

```powershell
.\.venv\Scripts\python.exe scripts\send-test-push.py --product maiz --message "Prueba"
```

Luego, en el teléfono con la app instalada y el permiso de notificaciones
aceptado, debería llegar la notificación. Al tocarla, debe abrir el detalle de
maíz.

### 3. Prueba desde la consola Firebase (alternativa)

Firebase Console → **Messaging** → **Enviar mensaje de prueba** → topic
`alertas-granos`, con datos `product_id=maiz`.

## Seguridad

- `google-services.json` y la cuenta de servicio **no se versionan**
  (`.gitignore`).
- El topic no guarda tokens de dispositivos: FCM gestiona la suscripción.
- Para compilar la APK en CI (Fase 4) habrá que inyectar `google-services.json`
  desde un secreto (`GOOGLE_SERVICES_JSON`).

## Pendiente de Fase 3

- [ ] Generar la cuenta de servicio y cargar el secreto.
- [ ] Probar en un dispositivo real: push recibido y tap → detalle.
- [ ] Confirmar el comportamiento con la app en foreground, background y cerrada.

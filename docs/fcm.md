# Notificaciones push (FCM) — Fase 3

**Estado:** completa y verificada en dispositivo (moto g31, Android 12): la push
llega, se muestra la notificación y al tocarla abre el detalle del producto.

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

## Configuración (completada)

### 1. Cuenta de servicio ✅

Generada en Firebase Console → ⚙️ **Configuración del proyecto** → **Cuentas de
servicio** → **Generar nueva clave privada** (cuenta
`firebase-adminsdk-fbsvc@granos-oportunidades.iam.gserviceaccount.com`).

- **GitHub Actions:** secreto `FIREBASE_SERVICE_ACCOUNT` cargado en
  `fedex888/granos`. ✅
- **Local:** `secrets/firebase-service-account.json` (gitignored). ✅

### 2. Envío de prueba ✅

```powershell
.\.venv\Scripts\python.exe scripts\send-test-push.py --product maiz --message "Prueba"
```

Resultado: `{'sent': 1, 'errors': []}` (FCM aceptó el mensaje para el topic).

### 3. Prueba desde la consola Firebase (alternativa)

Firebase Console → **Messaging** → **Enviar mensaje de prueba** → topic
`alertas-granos`, con datos `product_id=maiz`.

## Seguridad

- `google-services.json` y la cuenta de servicio **no se versionan**
  (`.gitignore`).
- El topic no guarda tokens de dispositivos: FCM gestiona la suscripción.
- Para compilar la APK en CI (Fase 4) habrá que inyectar `google-services.json`
  desde un secreto (`GOOGLE_SERVICES_JSON`).

## Verificación en dispositivo

- [x] Generar la cuenta de servicio y cargar el secreto.
- [x] Verificar el envío de prueba desde el pipeline (`sent: 1`).
- [x] Probar en un dispositivo real (moto g31, Android 12): push recibida y tap → detalle.
- [x] Foreground: notificación local con "Maíz · Comprar" (verificado en `dumpsys notification`).
- [x] Background: tap en la notificación abrió `/product/maiz`.
- [ ] App cerrada (terminated): usa el mismo camino vía `getInitialMessage`; no se
  probó explícitamente.

### Nota de rendimiento

El primer arranque en frío tardó ~9,7 s porque la inicialización de Firebase/FCM
se hace antes de `runApp`. En Fase 4 conviene diferirla al primer frame para que la
UI aparezca antes.

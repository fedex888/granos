# Fase 0 — Entorno y preparación

**Fecha:** 2026-11-15 (cierre de credenciales: 2026-11-16)  
**Estado:** completa. Repositorio GitHub y proyecto Firebase creados con las
credenciales del usuario.  
**Alcance:** estructura del repo, entorno de desarrollo y validación de fuentes.
**Fuera de alcance:** UI, pipeline y alertas (Fases 1–3).

## Checklist del plan

| Ítem | Estado | Evidencia |
|---|---|---|
| Confirmar los 4 productos | ✅ | Maíz, soja, trigo pan y girasol validados en BCR |
| Crear repo GitHub | ✅ | `https://github.com/fedex888/granos` (público, rama `main`) |
| Crear proyecto Firebase y app Android | ✅ | Proyecto `granos-oportunidades`; app `com.fedex888.granos` |
| Descargar `google-services.json` | ✅ | Guardado en `app/android/app/` (no versionado) |
| Instalar Flutter + Android Studio + JDK 17 | ✅ | Ver tabla de entorno |
| Correr `flutter doctor` | ✅ | Ver salida abajo |
| Verificar export BCR de los 4 productos y 2 años | ✅ | 481 filas por producto; ver `data-sources.md` |
| Verificar serie FX | ✅ | 731 filas en ventana; salvedad de -1,07% vs BCR |
| Definir flete inicial (0 por defecto) | ✅ | Decisión D5 |
| Confirmar Android 8+ e instalación de APK | ✅ | `minSdk 26`; APK directa (D2/D3). Prueba en dispositivo: Fase 4 |
| Aceptar disclaimer | ✅ | Texto en `disclaimer.md`; aceptación explícita en onboarding (Fase 2) |

## Entorno instalado

| Componente | Versión | Ruta |
|---|---|---|
| Windows | 10 IoT Enterprise LTSC 22H2 (19045) | — |
| Git | 2.56.0 | `C:\Program Files\Git` |
| Python | 3.12.10 | `%LOCALAPPDATA%\Programs\Python\Python312` |
| JDK | Eclipse Temurin 17.0.21.9 | `C:\Program Files\Eclipse Adoptium\jdk-17.0.21.9-hotspot` |
| Android Studio | 2026.2.2.8 | `C:\Program Files\Android\Android Studio` |
| Android SDK | platform-tools, android-36, build-tools 36.0.0 | `C:\Android\sdk` |
| Flutter | 3.50.0 stable | `C:\src\flutter` |
| Dart | 3.14.0 | incluido en Flutter |

`JAVA_HOME`, `ANDROID_SDK_ROOT`, `ANDROID_HOME` y los `PATH` correspondientes quedan
a nivel máquina. Cerrar y reabrir la terminal después de correr el script.

### Reproducir la instalación

```powershell
# Ejecutar como Administrador
powershell -ExecutionPolicy Bypass -File scripts\setup-dev-windows.ps1
```

El script es idempotente: omite lo ya instalado. Para una máquina sin IDE:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup-dev-windows.ps1 -SkipAndroidStudio
```

## flutter doctor

```text
[√] Flutter (Channel stable, 3.50.0, on Microsoft Windows [Version 10.0.19045.6036], locale es-AR)
[√] Windows Version (10 IoT Enterprise LTSC 64-bit, 22H2, 2009)
[√] Android toolchain - develop for Android devices (Android SDK version 36.0.0)
    • Android SDK at C:\Android\sdk
    • Platform android-36, build-tools 36.0.0
    • Java binary at: C:\Program Files\Eclipse Adoptium\jdk-17.0.21.9-hotspot\bin\java
      (JDK especificado por JAVA_HOME)
    • Java version OpenJDK Runtime Environment Temurin-17.0.21+9
    • All Android licenses accepted.
[√] Chrome - develop for the web
[X] Visual Studio - develop Windows apps
    X Visual Studio not installed (solo necesario para apps de escritorio Windows)
[√] Connected device (2 available: Windows desktop y Chrome)
[√] Network resources
```

**Interpretación:** el único warning (`Visual Studio`) no afecta a Android y se puede
ignorar. No hay teléfono Android conectado en esta máquina; la instalación real de
la APK se prueba en Fase 4. Flutter y Dart quedaron agregados al `PATH` de máquina.

Android Studio quedó instalado (2026.2.2.8), pero `flutter doctor` no lo lista como
IDE porque todavía no se abrió por primera vez (no existe su carpeta de
configuración). No hace falta para compilar por consola; si se va a editar desde el
IDE, abrirlo una vez e instalar los plugins **Flutter** y **Dart** en
`Settings → Plugins`.

## Compilación de prueba

Para verificar el toolchain completo se generó un proyecto descartable en `%TEMP%`
y se compiló con `flutter build apk --debug`: **OK** (≈11 min la primera vez,
incluye la descarga del NDK 28.2.13676358 y de las dependencias de Gradle). El APK
`app-debug.apk` se generó correctamente.

> El primer build descarga automáticamente el **NDK** que pide el proyecto
> (Flutter 3.50 usa `28.2.13676358`, ≈1 GB) y las dependencias de Gradle. Ya quedó
> cacheado para la Fase 2.

## Validación de fuentes (resumen)

Detalle completo, endpoints y formato en [data-sources.md](data-sources.md).

| Producto | Filas 2 años | Operados | Estimados | Último dato | Precio ARS/t | USD/t\* |
|---|---:|---:|---:|---|---:|---:|
| Trigo | 481 | 474 | 0 | 2026-11-12 | 288.900,00 | 190,07 |
| Maíz | 481 | 469 | 0 | 2026-11-12 | 275.800,00 | 181,45 |
| Soja | 481 | 472 | 0 | 2026-11-12 | 540.000,00 | 355,26 |
| Girasol | 481 | **195** | **285** | 2026-11-12 (E) | 752.885,00 | 495,32 |

\* Calculado con FX ArgentinaDatos (compra 1.520,00 del 2026-11-15). BCR publica
valores ≈1,09% menores porque usa dólar divisa BNA (1.536,50).

### Datos de prueba

Los crudos del 2026-11-15 quedaron como fixtures versionados en
`pipeline/tests/fixtures/` (ver su `README.md`): XLSX de los 4 productos, HTML de
BCR y MAGyP, y una muestra de 60 filas de FX. Sirven para los tests de parseo de la
Fase 1 sin volver a golpear las fuentes.

### Hallazgos que afectan la Fase 1

1. **Girasol no alcanza el mínimo de 250 observaciones operadas** (195 operados,
   285 estimados, brecha máxima de 73 días). Con la regla actual de "operado dentro
   de 5 días hábiles" nunca generaría alertas. Decisión D10 pendiente.
2. **El nodo de export `987` de BCR no aparece en el HTML estático** (la URL se arma
   del lado del cliente). Queda configurable y validado por encabezados.
3. **La serie FX no es el mismo dólar que usa BCR** (-1,07%). Se documenta y se
   mantiene una única fuente por serie; el TC de BCR se guarda como control.
4. **MAGyP no cubre girasol** el día validado (`0.00`) y no ofrece serie diaria
   histórica; sirve como control/fallback de trigo, maíz y soja.
5. **ArgentinaDatos publica una fila con fecha futura** (2026-11-16): el pipeline
   debe filtrar `fecha <= hoy`.

## Decisiones tomadas

Ver [decisiones.md](decisiones.md). Resumen:

- 4 productos y mercado Rosario.
- Android 8+ (`minSdk 26`), APK directa.
- Flete inicial 0 USD/t; precio local = Rosario ± flete con override manual.
- FX ArgentinaDatos `compra`; no mezclar fuentes.
- Package ID propuesto `com.fedex888.granos` (pendiente de confirmar).
- `schema_version: 1` y fechas en `America/Argentina/Buenos_Aires`.

## Credenciales y recursos externos (completados)

- **GitHub:** repo público <https://github.com/fedex888/granos>, rama `main`, con el
  contenido de Fase 0 subido. El CLI `gh` quedó autenticado como `fedex888` con los
  scopes `repo`, `workflow`, `read:org` y `gist`.
- **Firebase:** proyecto `granos-oportunidades` (nº 770713701053) y app Android
  `com.fedex888.granos` (app id `1:770713701053:android:dbae6d26565838b5f505d4`).
  Google Analytics y la asistencia de IA quedaron desactivados.
- **`google-services.json`:** descargado y guardado en `app/android/app/` (ignorado
  por Git). Para CI se guardará como secreto `GOOGLE_SERVICES_JSON` en GitHub Actions
  (Fase 3, junto con FCM).

## Cómo validar de nuevo

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r pipeline\requirements.txt
.\.venv\Scripts\python.exe scripts\validate-sources.py
```

El script sale con código 0 si las descargas y los controles pasan; imprime warnings
por girasol y por la brecha de FX. Los crudos quedan en `artifacts/fase0/`.

## Puerta para Fase 1

Antes de implementar `signals.py` queda resolver:

1. **D10**: política de girasol (recomendación: aceptar estimados y limitar a `watch`).

Lo demás ya está: package ID (`com.fedex888.granos`), repo remoto público y proyecto
Firebase. La cuenta de servicio de FCM y su secreto (`FIREBASE_SERVICE_ACCOUNT`) se
configuran en Fase 3, cuando se implementen las notificaciones.

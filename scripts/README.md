# Scripts

## `setup-dev-windows.ps1`

Prepara el entorno Windows de Fase 0. Requiere PowerShell **como Administrador**.

Instala de forma idempotente:

1. JDK 17 (Eclipse Temurin) y configura `JAVA_HOME`.
2. Android Studio (se puede omitir con `-SkipAndroidStudio`).
3. Android SDK en `C:\Android\sdk` (platform-tools, android-36, build-tools 36.0.0).
4. Python 3.12 si no está disponible.
5. Flutter stable desde el zip oficial en `C:\src\flutter` (se puede omitir con
   `-SkipFlutter`).
6. Agrega al `PATH` de máquina Flutter, JDK y platform-tools.
7. Corre `flutter doctor -v`.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup-dev-windows.ps1
```

Parámetros: `-FlutterRoot`, `-AndroidSdkRoot`, `-SkipAndroidStudio`, `-SkipFlutter`.

> El primer `flutter build apk` descarga automáticamente el NDK que pida el
> proyecto (Flutter 3.50 usa `28.2.13676358`). Es normal que tarde varios minutos.

## `validate-sources.py`

Valida las fuentes de datos del plan sin escribir en `data/`.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r pipeline\requirements.txt
.\.venv\Scripts\python.exe scripts\validate-sources.py
```

Descarga:

- BCR XLSX histórico de los 4 productos (ventana de 730 días).
- BCR pizarra del día (ARS y TC BNA).
- MAGyP pizarra sobre puerto (columna Rosario).
- FX ArgentinaDatos (serie completa).

Salidas:

- `artifacts/fase0/<fecha>/`: crudos (`bcr_*.xlsx`, `bcr_current.html`,
  `magyp_pizarra.html`, `fx_oficial.json`).
- `artifacts/fase0/report.json`: resumen máquina.
- Consola: checks y warnings.

Código de salida `0` si las descargas y los controles pasan. Los warnings (girasol,
brecha FX) no hacen fallar el script.

Opciones: `--days 730`, `--out artifacts/fase0`.

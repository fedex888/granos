<#
.SYNOPSIS
    Prepara el entorno de desarrollo Windows para el proyecto de granos (Fase 0).

.DESCRIPTION
    Instala de forma idempotente:
      - JDK 17 (Eclipse Temurin)
      - Android Studio (solo IDE; el SDK se instala aparte con cmdline-tools)
      - Android SDK (platform-tools, platforms;android-36, build-tools;36.0.0)
      - Flutter estable (zip oficial) + Dart incluido
      - Python 3.12

    Requiere PowerShell como Administrador (el script escribe variables de entorno
    a nivel máquina y acepta licencias del SDK).

.PARAMETER FlutterRoot
    Carpeta donde descomprimir Flutter. Por defecto C:\src\flutter.

.PARAMETER AndroidSdkRoot
    Carpeta del Android SDK. Por defecto C:\Android\sdk.

.PARAMETER SkipAndroidStudio
    No instala Android Studio (útil en servidores/CI).

.PARAMETER SkipFlutter
    No descarga Flutter.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\setup-dev-windows.ps1
#>
[CmdletBinding()]
param(
    [string]$FlutterRoot = "C:\src\flutter",
    [string]$AndroidSdkRoot = "C:\Android\sdk",
    [switch]$SkipAndroidStudio,
    [switch]$SkipFlutter
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Test-Admin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    (New-Object Security.Principal.WindowsPrincipal($identity)).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Add-MachinePath([string]$PathToAdd) {
    $current = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $parts = $current -split ";" | Where-Object { $_ -ne "" }
    if ($parts -notcontains $PathToAdd) {
        [Environment]::SetEnvironmentVariable("Path", (($parts + $PathToAdd) -join ";"), "Machine")
        Write-Host "PATH (máquina) += $PathToAdd"
    } else {
        Write-Host "PATH ya contiene $PathToAdd"
    }
    # Refrescar la sesión actual
    if (($env:Path -split ";") -notcontains $PathToAdd) {
        $env:Path = "$env:Path;$PathToAdd"
    }
}

function Install-WingetPackage([string]$Id) {
    Write-Host "Instalando $Id ..."
    winget install --id $Id --exact --silent --accept-package-agreements `
        --accept-source-agreements --disable-interactivity
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1978335189) {
        # -1978335189 = APPINSTALLER_CLI_ERROR_UPDATE_NOT_APPLICABLE (ya instalado)
        throw "winget falló para $Id (exit $LASTEXITCODE)"
    }
}

if (-not (Test-Admin)) {
    throw "Ejecutá este script como Administrador."
}

# ---------------------------------------------------------------------------
# 1. JDK 17
# ---------------------------------------------------------------------------
Write-Step "JDK 17 (Eclipse Temurin)"
$jdkRoot = "C:\Program Files\Eclipse Adoptium"
$jdk17 = Get-ChildItem $jdkRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "jdk-17*" } | Select-Object -First 1
if (-not $jdk17) {
    Install-WingetPackage "EclipseAdoptium.Temurin.17.JDK"
    $jdk17 = Get-ChildItem $jdkRoot -Directory | Where-Object { $_.Name -like "jdk-17*" } |
        Select-Object -First 1
}
if (-not $jdk17) { throw "No se encontró el JDK 17 luego de instalar." }
$env:JAVA_HOME = $jdk17.FullName
[Environment]::SetEnvironmentVariable("JAVA_HOME", $jdk17.FullName, "Machine")
Add-MachinePath "$($jdk17.FullName)\bin"
Write-Host "JAVA_HOME = $($jdk17.FullName)"

# ---------------------------------------------------------------------------
# 2. Android Studio
# ---------------------------------------------------------------------------
if (-not $SkipAndroidStudio) {
    Write-Step "Android Studio"
    $studio = "C:\Program Files\Android\Android Studio\bin\studio64.exe"
    if (-not (Test-Path $studio)) {
        Install-WingetPackage "Google.AndroidStudio"
    }
    if (Test-Path $studio) { Write-Host "Android Studio OK: $studio" }
    else { Write-Warning "Android Studio no quedó en la ruta esperada." }
}

# ---------------------------------------------------------------------------
# 3. Python 3.12
# ---------------------------------------------------------------------------
Write-Step "Python 3.12"
$python = Get-Command python -ErrorAction SilentlyContinue
$pythonCandidate = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
if (-not $python -or $python.Source -like "*WindowsApps*") {
    if (-not (Test-Path $pythonCandidate)) {
        Install-WingetPackage "Python.Python.3.12"
    }
    if (Test-Path $pythonCandidate) {
        Add-MachinePath (Split-Path $pythonCandidate)
        $env:Path = "$(Split-Path $pythonCandidate);$env:Path"
    }
}

# ---------------------------------------------------------------------------
# 4. Flutter
# ---------------------------------------------------------------------------
if (-not $SkipFlutter) {
    Write-Step "Flutter (canal stable, zip oficial)"
    if (-not (Test-Path "$FlutterRoot\bin\flutter.bat")) {
        $releases = Invoke-RestMethod `
            "https://storage.googleapis.com/flutter_infra_release/releases/releases_windows.json"
        $latest = $releases.releases | Where-Object { $_.channel -eq "stable" } |
            Sort-Object { [datetime]$_.release_date } -Descending | Select-Object -First 1
        $url = "$($releases.base_url)/$($latest.archive)"
        $zip = Join-Path $env:TEMP "flutter_windows_$($latest.version)-stable.zip"
        Write-Host "Descargando Flutter $($latest.version) desde $url"
        Invoke-WebRequest -Uri $url -OutFile $zip
        New-Item -ItemType Directory -Force -Path (Split-Path $FlutterRoot) | Out-Null
        # Expand-Archive es lento con ~1 GB; tar (bsdtar) es bastante más rápido.
        tar -xf $zip -C (Split-Path $FlutterRoot)
        Remove-Item $zip -Force
    }
    Add-MachinePath "$FlutterRoot\bin"
    & "$FlutterRoot\bin\flutter.bat" --version
}

# ---------------------------------------------------------------------------
# 5. Android SDK (cmdline-tools)
# ---------------------------------------------------------------------------
Write-Step "Android SDK en $AndroidSdkRoot"
$env:ANDROID_SDK_ROOT = $AndroidSdkRoot
$env:ANDROID_HOME = $AndroidSdkRoot
[Environment]::SetEnvironmentVariable("ANDROID_SDK_ROOT", $AndroidSdkRoot, "Machine")
[Environment]::SetEnvironmentVariable("ANDROID_HOME", $AndroidSdkRoot, "Machine")

$sdkManager = Join-Path $AndroidSdkRoot "cmdline-tools\latest\bin\sdkmanager.bat"
if (-not (Test-Path $sdkManager)) {
    $toolsZip = Join-Path $env:TEMP "commandlinetools-win.zip"
    Invoke-WebRequest `
        -Uri "https://dl.google.com/android/repository/commandlinetools-win-13114758_latest.zip" `
        -OutFile $toolsZip
    $tmp = Join-Path $env:TEMP "cmdline-tools-extract"
    if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    Expand-Archive -Path $toolsZip -DestinationPath $tmp -Force
    New-Item -ItemType Directory -Force -Path (Join-Path $AndroidSdkRoot "cmdline-tools") | Out-Null
    Move-Item (Join-Path $tmp "cmdline-tools") (Join-Path $AndroidSdkRoot "cmdline-tools\latest")
    Remove-Item $toolsZip, $tmp -Recurse -Force
}

Write-Host "Aceptando licencias del SDK ..."
$yes = ("y`n" * 40)
$yes | & $sdkManager --sdk_root=$AndroidSdkRoot --licenses | Out-Null

Write-Host "Instalando paquetes del SDK ..."
& $sdkManager --sdk_root=$AndroidSdkRoot `
    "platform-tools" "platforms;android-36" "build-tools;36.0.0" | Out-Null

Add-MachinePath (Join-Path $AndroidSdkRoot "platform-tools")

if (Test-Path "$FlutterRoot\bin\flutter.bat") {
    Write-Step "flutter doctor"
    & "$FlutterRoot\bin\flutter.bat" config --android-sdk $AndroidSdkRoot
    & "$FlutterRoot\bin\flutter.bat" doctor -v
}

Write-Step "Listo"
Write-Host "Cerrá y volvé a abrir la terminal para tomar el PATH actualizado."

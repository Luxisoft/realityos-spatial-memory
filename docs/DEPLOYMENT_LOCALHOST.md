# Localhost deployment

Evaluate RealityOS on your own machine with Windows + Docker Desktop: an
independent installation with its own configuration, account, database and
volumes. It never touches production, FRONTEND, or production credentials.
Back to the [main README](../README.md) · also see
[direct server](DEPLOYMENT_DIRECT.md) and
[server with gateway](DEPLOYMENT_GATEWAY.md).

The AI is real here: Muse Spark, SAM and transcription call the Meta API with
your key, ElevenLabs synthesizes voice with your key, and InsightFace runs
locally. No synthetic media is loaded and seed scripts never run — screens
start empty until you register your own data.

## Requirements

- Windows x64 with Docker Desktop, Linux containers and WSL2 (Windows
  containers mode does not work). See the official
  [Docker setup](https://docs.docker.com/desktop/setup/install/windows-install/)
  and [WSL2 backend](https://docs.docker.com/desktop/features/wsl/) docs.
- Git and PowerShell (5.1 or 7). Python and Node are not needed on the host;
  they build inside Docker.
- Internet access plus your own Meta key with `muse-spark-1.3`, `sam-3.1` and
  `muse-voice-transcribe-1.0` enabled, and your own ElevenLabs key.
- At least 4 CPUs, 8 GiB of RAM assigned to Docker and 25 GiB free. No GPU
  required.

## First boot

From PowerShell at the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\local\Start-RealityOS.ps1
```

(`Bypass` applies to that process only.) The script creates `.env.local`
from the example, asks for your keys and local email/password (12+ characters,
typed hidden), generates independent PostgreSQL/JWT/device secrets, builds
the images, applies migrations, creates your account with an empty workspace,
and waits for API and voice health — including a real EN/ES audio check that
publishes nothing. If Docker data lives on another drive, pass
`-DockerDataDrive 'D:\'`. If a credential, resource or model fails, the script
says so instead of claiming readiness.

| App | Default address |
| --- | --- |
| Panel | `http://localhost:8080` |
| Display web | `http://localhost:8080/display/` |
| API contract | `http://localhost:8080/v1/openapi.json` |
| Health | `http://localhost:8080/health/ready` |

Sign in with the email and password you chose — a real local account, with no
facial recognition at login. Facial features keep their permission/consent
requirements when explicitly requested. Key local settings (`.env.local`
only, direct Meta route, no gateway dependency):

```dotenv
ENVIRONMENT=local
META_MODE=live
FACE_ENGINE=insightface
META_CONNECTION_MODE=direct
META_GATEWAY_FALLBACK_ENABLED=false
```

## Local Android app

You additionally need Android SDK 36, Java 21, ADB and a phone with USB
debugging (or an emulator). The local APK installs as a separate app
(`com.luxisoft.realityos.local`) and never replaces the regular one:

```powershell
$env:ANDROID_HOME = 'C:\path\to\Android\Sdk'
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
Set-Location android
.\gradlew.bat -PlocalDevelopment=true -PrealityosApiBaseUrl=http://localhost:8080/v1 :app:assembleDebug
adb reverse tcp:8080 tcp:8080
adb install -r app\build\outputs\apk\debug\app-debug.apk
```

`adb reverse` links the phone's localhost to Windows (re-run on USB
reconnect; confirm the debugging prompt on the phone). This local Debug build
alone, confirmed by the local backend, skips entry face verification; Release
never accepts this mode or local HTTP. Physical glasses need real Meta/DAT
hardware — Docker does not substitute them. Testing Facebook import needs
your own real Facebook app, permissions, account and Android setup.

## Verify, stop, troubleshoot

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\local\Test-RealityOS.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\local\Test-RealityOS.ps1 -Speech
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\local\Stop-RealityOS.ps1
```

`Stop` keeps data and models; never use `down -v` if you want to keep them.
Re-running `Start` never replaces accounts, passwords or data. If port 8080
is taken, change `LOCAL_HTTP_PORT` in `.env.local` and use that port in URLs
and the Android connection. PostgreSQL and Redis are not published on
Windows. For voice errors:

```powershell
docker compose --project-name realityos-local --env-file .env.local --file infrastructure/docker-compose.local.yml logs --tail 50 api
```

Local execution requires real providers with no mock fallback. Automated
tests use doubles only inside their own runs.

Full local reference (Spanish): [Windows local setup](LOCAL_WINDOWS.md).

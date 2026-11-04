[Español](../../es/deployment/DEPLOYMENT_LOCALHOST.md) · [RealityOS](../README.md) · [Index](../INDEX.md)

# Local installation: Windows and Linux

This is the primary evaluation setup. Four Docker services run on your computer:
PostgreSQL (the single application database), Redis (task queue), the existing API
and the existing worker. Only the API is exposed, on `127.0.0.1:8080`.
No gateway, proxy, scheduler, bucket, Facebook login, SMTP or ElevenLabs is required.
Meta AI calls still need internet access and your own `MODEL_API_KEY`.

## Requirements

- Windows x64 with Docker Desktop using Linux containers/WSL2, or Linux x64 with Docker Engine and the Compose plugin. macOS is not supported by this installation.
- Allocate at least 4 CPU cores, 8 GiB RAM and 25 GiB free Docker storage. The first build downloads dependencies and InsightFace weights; allow additional time for this download.
- Android 12+ phone and Android Platform Tools (`adb`), USB debugging enabled. Glasses are optional for phone capture and stored-evidence evaluation.
- Your own Meta Model API key with access to the models already used by RealityOS: Muse Spark, SAM and Muse Voice Transcribe. No other provider account is required for the local walkthrough.

Clone or download the public repository. Run commands from its root. Do not copy a production `.env`.

## 1. Download and prepare

1. Download the [repository ZIP](https://github.com/Luxisoft/realityos-spatial-memory/archive/refs/heads/main.zip) and extract it, or run `git clone https://github.com/Luxisoft/realityos-spatial-memory.git`. No GitHub login is required.
2. Windows: install [Docker Desktop x64](https://docs.docker.com/desktop/setup/install/windows-install/), enable its WSL2/Linux backend and start Docker Desktop. Linux: follow [Docker Engine installation](https://docs.docker.com/engine/install/) for your distribution, including the Compose plugin. Verify `docker info` and `docker compose version` work in your terminal.
3. Download [Android Platform Tools for your system](https://developer.android.com/tools/releases/platform-tools), extract them and add their directory to PATH. Verify `adb version`.
4. Open PowerShell or Bash in the extracted `realityos-spatial-memory` folder. Everything else runs in Docker; Python, PostgreSQL and Redis need no host installation.

## 2. Start

Windows PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\local\Start-RealityOS.ps1
```

Linux:

```bash
bash scripts/local/start.sh
```

The launcher creates the private `.env.local` from `.env.local.example`, generates internal secrets and asks for your Meta key without echoing it. Alternatively, fill `MODEL_API_KEY` in that private file before starting. Do not publish that file. Internal passwords are generated for local infrastructure; judges do not obtain them from the README.

The API prepares the schema and existing fixtures on the first start. Existing local installations retain their database and are upgraded. An unversioned, nonempty database is rejected instead of being overwritten. The initial schema uses the current ORM schema, required PostgreSQL search indexes and a pinned Alembic baseline because the historical initial migration cannot reliably recreate an empty database. No production migrations or runtime files are changed by the launcher.

Initialization prepares **3 groups, 9 users, 47 records, 27 record attachments and 48 licensed gallery scenes** from repository files. Fictional records remain marked simulated; licensed scenes identify their source and license. No AI detections, biometric consent or enrollments are preclaimed. The worker indexes publications through the existing real Meta processing pipeline. Search becomes available as indexing completes; failures remain visible and can be retried from the normal index action.

Restarting never refreshes fixtures or restores deleted data. Do not run `down -v` unless you deliberately want to erase the local installation.

<a id="android"></a>

## 3. Android

Download **[app-debug.apk](https://github.com/Luxisoft/realityos-spatial-memory/releases/download/local-evaluation/app-debug.apk)** from the public GitHub release (no sign-in required). No Android Studio, Java or full SDK is needed to install this prebuilt APK; Platform Tools are enough. Building it yourself is optional:

```bash
cd android
./gradlew :app:assembleDebug
```

On Windows use `gradlew.bat`. Building requires Java 21 and Android SDK 36. The canonical output is `android/app/build/outputs/apk/debug/app-debug.apk`. Debug defaults to the local application ID `com.luxisoft.realityos.local` and `http://localhost:8080/v1`.

Connect the phone by USB, accept its debugging prompt, then run from the repository root:

```bash
adb reverse tcp:8080 tcp:8080
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

For a downloaded APK, pass its path to `adb install -r`. USB reverse must be restored after reconnecting the phone. Android's localhost is the phone itself until this tunnel is established. No host LAN port needs to be published.

Open RealityOS and choose one of the nine accounts grouped by scenario. There is no password or Facebook login. Changing users preserves workspace boundaries. Local login does not enroll a face or grant biometric search consent.

Responses use Android's installed offline ES/EN voices. Install the language voice in Android's text-to-speech settings if unavailable; the text response remains visible. Audio input continues through Meta transcription. Do not put the Meta key in the APK.

## Files and data

Public starting files live in `simulator/workspaces/assets/`, `simulator/workspaces/profile-photos/` and `simulator/real-scenes/assets/`, with manifests alongside them. Existing resources are packaged in the image; the setup never downloads private production media. Select a local photo/video in Android and publish it to an existing group with its category and tags. Editing, deleting, queries and profile updates use the same application operations and local PostgreSQL data.

Original uploaded media is persisted as PostgreSQL `BYTEA` (or its existing ordered chunks), so database content and original files stay together in the `realityos-local_postgres_data` volume. Redis has its own queue volume. There is no folder watcher, storage adapter, bucket connection or background file synchronization. Merely copying a new file into a fixture folder does not publish it.

## Postman and diagnostics

Import [RealityOS.postman_collection.json](../../postman/RealityOS.postman_collection.json). Select **No environment**, then **Localhost requests → 00 Quick start** or **00 Local scenarios**. Sessions and refresh tokens are obtained automatically through the local selector. **Server requests** is a disabled historical catalog without an endpoint or passwords. Writes require the destination's explicit `enable_write_requests=true` setting.

Windows diagnostics and stop:

```powershell
.\scripts\local\Test-RealityOS.ps1
.\scripts\local\Stop-RealityOS.ps1
```

Linux diagnostics and stop:

```bash
bash scripts/local/test.sh
bash scripts/local/stop.sh
```

Check `http://localhost:8080/health/ready` and `http://localhost:8080/docs`. Provider diagnostics make real Meta requests with your key. Stopping preserves data. If startup reports invalid credentials, fix your private key and rerun; there is no simulated-model fallback. Review API/worker logs through the isolated Compose file, and do not paste keys or personal media into reports.

A complete Windows, physical-phone, offline-voice and live-Meta walkthrough must be recorded separately; automated tests do not establish those outcomes. See [verified status](../project/IMPLEMENTATION_STATUS.md).

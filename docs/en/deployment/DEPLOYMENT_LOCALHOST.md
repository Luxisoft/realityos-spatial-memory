[Español](../../es/deployment/DEPLOYMENT_LOCALHOST.md) · [RealityOS](../README.md) · [Index](../INDEX.md)

# Local installation: Windows and Linux

Four Docker services run on your computer: PostgreSQL (database), Redis (task queue),
API and worker. The API is available at `127.0.0.1:8080`.

## Requirements

- Windows x64 with Docker Desktop using Linux containers/WSL2, or Linux x64 with Docker Engine and the Compose plugin. macOS is not supported by this installation.
- Allocate at least 4 CPU cores, 8 GiB RAM and 25 GiB free Docker storage. The first build downloads dependencies and InsightFace weights; allow additional time for this download.
- Android 12+ phone and Android Platform Tools (`adb`), USB debugging enabled. Glasses are optional for phone capture and stored-evidence evaluation.
- Internet access and your own Meta `MODEL_API_KEY` with access to Muse Spark, SAM and Muse Voice Transcribe.

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

Download **[app-debug.apk](https://github.com/Luxisoft/realityos-spatial-memory/releases/download/local-evaluation/app-debug.apk)** from the public GitHub release (no sign-in required). Platform Tools are enough to install it. To build it yourself, use **JDK 21 LTS** (the CI version) and Android SDK 36. [Java setup on Windows](#java-windows).

Linux:

```bash
cd android
./gradlew :app:assembleDebug
```

Windows PowerShell:

```powershell
cd android
.\gradlew.bat :app:assembleDebug
```

The canonical output is `android/app/build/outputs/apk/debug/app-debug.apk`. Debug defaults to the local application ID `com.luxisoft.realityos.local` and `http://localhost:8080/v1`.

Connect the phone by USB, accept its debugging prompt, then run from the repository root:

```bash
adb reverse tcp:8080 tcp:8080
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

For a downloaded APK, pass its path to `adb install -r`. USB reverse must be restored after reconnecting the phone. Android's localhost is the phone itself until this tunnel is established. No host LAN port needs to be published.

Open RealityOS and choose one of the nine accounts grouped by scenario. Changing users preserves workspace boundaries. Local login does not enroll a face or grant biometric search consent.

Responses use Android's installed offline ES/EN voices. Install the language voice in Android's text-to-speech settings if unavailable; the text response remains visible. Audio input continues through Meta transcription. Do not put the Meta key in the APK.

## Files and data

Public starting files live in `simulator/workspaces/assets/`, `simulator/workspaces/profile-photos/` and `simulator/real-scenes/assets/`, with manifests alongside them. Existing resources are packaged in the image; the setup never downloads private production media. Select a local photo/video in Android and publish it to an existing group with its category and tags. Editing, deleting, queries and profile updates use the same application operations and local PostgreSQL data.

Original uploaded media is persisted as PostgreSQL `BYTEA` (or its existing ordered chunks), so database content and original files stay together in the `realityos-local_postgres_data` volume. Redis has its own queue volume. Add publications from Android.

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

<a id="java-windows"></a>

## Java on Windows: fix `JAVA_HOME`

Use **JDK 21 LTS**, matching the [CI build](../../../.github/workflows/ci.yml). The [Android project](../../../android/app/build.gradle.kts) targets Java/Kotlin 17 bytecode; that does not change the recommended build JDK. [AGP 8.11 requires at least JDK 17](https://developer.android.com/build/releases/agp-8-11-0-release-notes#compatibility).

The warning `JAVA_HOME is set to 'C:\Program Files\Java\jdk-23', but it does not contain a usable Java executable` means the editor cannot run Java from that path.

1. Install [Eclipse Temurin JDK 21 LTS for Windows x64](https://adoptium.net/temurin/releases/?version=21&os=windows&arch=x64&package=jdk), choosing the **JDK** package and MSI installer. Check the exact installation directory: it must contain `bin\java.exe` and `bin\javac.exe`.
2. In Windows, search for **Edit the system environment variables** and open **Environment Variables**. Set `JAVA_HOME` to that JDK root directory, without quotes or a trailing `\bin`. Check both user and system variables for the obsolete path. If `JDK_HOME` also contains the old path, correct or remove it.
3. In `Path`, place `%JAVA_HOME%\bin` before other Java entries and remove entries pointing to deleted installations.
4. Fully close the editor and terminals. Open a new PowerShell and check:

```powershell
$env:JAVA_HOME
Test-Path "$env:JAVA_HOME\bin\java.exe"
Test-Path "$env:JAVA_HOME\bin\javac.exe"
& "$env:JAVA_HOME\bin\java.exe" -version
java -version
javac -version
.\android\gradlew.bat --version
```

Both `Test-Path` commands should return `True`; Java, javac and the Gradle JVM should report version 21. If `java -version` reports another version, use `where.exe java` to find the entry taking precedence in `Path`.

If the editor still displays the warning, open its user and workspace JSON settings. Remove references to the old installation in `java.home` or `java.jdt.ls.java.home`. The [current Java extension for Windows x64](https://github.com/redhat-developer/vscode-java#java-tooling-jdk) bundles its own language-server runtime; set `java.import.gradle.java.home` to the actual JDK 21 directory for project builds. In Android Studio, select the same JDK 21 under **Settings → Build, Execution, Deployment → Build Tools → Gradle → Gradle JDK**.

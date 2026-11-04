[Español](../../es/deployment/DEPLOYMENT_LINUX.md) · [Windows](../README.md)

<a id="linux-server"></a>

# Private evaluation on a Linux server

Run the same **four services and prepared scenarios** on a Linux x64 server. The API stays on the server's `127.0.0.1:8080`; your computer connects through SSH. No domain or public HTTPS endpoint is needed. Keep port 8080 private: the evaluation account selector has no passwords.

**1. Prepare the server.** Use at least 4 CPU cores, 8 GiB RAM and 25 GiB free Docker storage. Install Git, [Git LFS](https://git-lfs.com/), curl, [Docker Engine and the Compose plugin](https://docs.docker.com/engine/install/ubuntu/), and start Docker. Connect using your own SSH account; replace `deploy@YOUR_SERVER` throughout this section:

```bash
ssh deploy@YOUR_SERVER
uname -m
docker info
docker compose version
```

Expect `x86_64`, a responding Linux engine and Compose. Docker commands must work from this account. Run the following server commands **inside that SSH session**.

**2. Download and start RealityOS.** Use a separate checkout for this evaluation:

```bash
git lfs install &&
git clone https://github.com/Luxisoft/realityos-spatial-memory.git &&
cd realityos-spatial-memory &&
bash scripts/local/start.sh
```

Enter your own Meta key when prompted. The launcher creates a private `.env.local` on the server, generates internal secrets and prepares the three groups and nine accounts once. Existing local configuration and data are preserved on restart. PostgreSQL and Redis stay internal; Android uses its installed offline voices.

**3. Verify on the server.** Wait for setup to finish, then run:

```bash
curl --fail --silent --show-error http://127.0.0.1:8080/health/ready
curl --fail --silent --show-error http://127.0.0.1:8080/v1/openapi.json -o /dev/null
bash scripts/local/test.sh
```

Diagnostics check service status, model availability and local accounts. Background indexing can continue after startup; wait for it before searching the prepared evidence.

**4. Connect from your computer.** Open another terminal **on your computer**, ensure local port 8080 is free, and keep this [SSH tunnel](https://man.openbsd.org/ssh#L) running:

```bash
ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:8080:127.0.0.1:8080 deploy@YOUR_SERVER
```

Open [http://localhost:8080/docs](http://localhost:8080/docs) on your computer. Postman uses **Localhost requests** through the tunnel; leave **Server requests** disabled. If your computer already runs a local RealityOS instance, stop that instance first to free port 8080.

**5. Connect Android.** With the tunnel open and the phone connected to your computer by USB, install the [local Debug APK](../README.md#android), then run in Git Bash on your Windows computer:

```bash
/c/platform-tools/adb.exe reverse tcp:8080 tcp:8080
```

The app keeps `http://localhost:8080/v1` and reaches the server through your computer. Select one of the nine accounts. Repeat `adb reverse` after reconnecting the phone. Closing the tunnel disconnects clients but leaves the server running.

**6. Stop or resume.** Inside the server's checkout, use `bash scripts/local/stop.sh` to stop and `bash scripts/local/start.sh` to resume. Stopping preserves data. Do not remove volumes or use `down -v` unless you intend to delete the evaluation data.

These steps reuse the existing Linux launcher. The SSH/USB path must be verified on your own server and phone; this documentation change does not deploy a server.

## Updates and console output

From the server checkout:

```bash
git pull --ff-only &&
git lfs pull &&
bash scripts/local/start.sh
```

Start, diagnostics and stop commands show English progress by stage, summaries, warnings, errors and success messages. The first run downloads dependencies; a long stage may keep the same percentage while working. Reaching 100% means the command finished; indexing may continue in the background. Restarting preserves edits and deletions. Keep `.env.local` private.

To update the phone, repeat the update and installation from the [Windows README](../README.md#android) while keeping the tunnel open.

**Postman:** import the [collection](../../postman/RealityOS.postman_collection.json) and use **No environment → Localhost requests → 00 Quick start**. Enable `enable_write_requests=true` to write; leave **Server requests** disabled.

## Running on a Linux computer

If you run the backend on your own Linux computer, perform steps 1–3 in its local terminal and skip SSH. Start Docker Engine before `bash scripts/local/start.sh`; use `bash scripts/local/test.sh` for diagnostics and `bash scripts/local/stop.sh` to stop while preserving data.

## Building Android on Linux

For development, install JDK 21 and Android SDK 36 with Build-Tools 36.0.0. Configure `JAVA_HOME` and `ANDROID_HOME`. From the repository root:

```bash
REALITYOS_API_BASE_URL=http://localhost:8080/v1 ./android/gradlew -p android -PlocalDevelopment=true :app:assembleDebug
```

Wait for `BUILD SUCCESSFUL`. The APK replaces `android/app/build/outputs/apk/debug/app-debug.apk`. Use the same server signing key when publishing updates through Git LFS.

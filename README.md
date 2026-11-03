# RealityOS — An Intelligent Spatial Memory

RealityOS records intentional visual observations in a workspace and later
retrieves the **last verified evidence** for an object. It is built for
workshops, warehouses, homes and Meta wearable experiences where a useful answer
needs a real photograph, not a guess.

The MVP keeps original captures inside PostgreSQL as BYTEA. Registering and
consulting are deliberately separate: capture requires an open, consented
session; query endpoints are evidence-only and never start a recording.

## Included

- FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL contracts, Redis and
  Celery worker entry point.
- JWT access and rotating refresh tokens, scrypt password hashes, workspace
  RBAC and authorized binary media retrieval.
- Original-media hashing/deduplication, logical objects, observations, history,
  verified last-seen retrieval and PNG highlights.
- Device-originated capture with a workspace-bound device ID, a rotatable
  server-issued upload key and optional administrator-managed operator label.
- Evidence-backed inventory intelligence for visible brand, model, count,
  condition and observed use, with confidence, provenance and review status.
- MP4/MOV/WebM ingestion: the original clip remains PostgreSQL BYTEA; FFmpeg
  partitions long clips logically and extracts representative JPEG frames per
  configured segment, linked to their parent video and approximate timestamps.
- Explicit detailed video mode follows administrator-selected priority objects
  with SAM 3.1 Video and stores per-frame geometry, visibility and RLE masks
  without duplicating every video frame as an image asset.
- Deterministic Mock Meta provider and a Live client for Muse Spark 1.3, SAM
  3.1 and Muse Voice Transcribe. Muse identifies the catalog at registration;
  SAM is requested explicitly only to refine a selected, verified observation.
- Optional restricted Meta egress gateway for deployments where only an
  approved server can reach Model API. See [Gateway](docs/GATEWAY.md).
- Native DAT 1.0.1 host for Meta Ray-Ban Display: glasses-side Register/Query
  screens, camera photo/video capture, on-device speech query, highlighted
  evidence and Android-routed TTS; a Live virtual-device bootstrap fills the
  phone's editable Debug connection inputs without embedding a permanent key;
  plus a separate 600×600 Display Web App demo.
- Admin object explorer with workspace-scoped name/alias, category and location
  filters, evidence history and a non-metric location hierarchy.
- Compose, Nginx reverse proxy, migration, synthetic seed and automated tests.

## Windows localhost: real providers

An independent Windows + Docker Desktop installation is available alongside the
server deployment. It has its own configuration, account, database and volumes.
Meta and ElevenLabs use your own API keys; InsightFace runs locally. No sample media
or simulated model responses are loaded.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\local\Start-RealityOS.ps1
```

Open `http://localhost:8080` (Display: `/display/`) and use the local account you
create during setup. The isolated local Android Debug build uses that account
without Facebook or facial recognition at login. Production retains its existing
entry flow. See [Windows local setup](docs/LOCAL_WINDOWS.md) for requirements,
Android/USB instructions, diagnostics and stopping without deleting data.

## Meta integration

The server and Windows local installation use `META_MODE=live`. Select
`META_CONNECTION_MODE=direct|gateway` and optionally enable automatic gateway
fallback. Windows defaults to direct and does not depend on FRONTEND. Server-only
keys never enter Android or browser assets. Test doubles remain available for
automated unit tests; a Live provider failure never silently becomes mock data.

Detailed SAM Video uploads only temporary MP4 clips to Meta Files API with
`purpose=user_data`, expiry and deletion. The original PostgreSQL BYTEA video
remains RealityOS's source of truth. An uncertain provider submission is not
retried automatically.

## Quality checks

    make lint
    make test
    npm --prefix frontend run build
    npm --prefix display-webapp run build
    (cd android && ANDROID_HOME=/opt/android-sdk ./gradlew :app:assembleDebug)

See docs/IMPLEMENTATION_STATUS.md for validations actually run in this workspace
and remaining verification work.

For a deliberate, consent-gated test with your own photos, use the private
staging workflow in [Manual photo test](docs/MANUAL_PHOTO_TEST.md). Staging a
file alone does not register it or call Meta.

Video intake has no fixed application or proxy size/duration cap by default
(`MAX_VIDEO_BYTES=0`, `MAX_VIDEO_SECONDS=0`). Videos over the configurable
inline threshold are retained as ordered PostgreSQL BYTEA chunks, never as file
paths or buckets, avoiding a single-value allocation limit. Capacity remains
constrained by server disk/RAM. Long clips are partitioned for bounded
extraction (`VIDEO_SEGMENT_SECONDS=120`, eight sampled frames per segment), not
streamed, audio-transcribed or treated as surveillance.

English is the default evidence and answer language. Queries may be spoken or
written in other languages: Muse Spark maps them only to existing
workspace-local names and aliases, then PostgreSQL retrieves verified evidence.

## On-demand SAM geometry

Registration stores Muse Spark detections, relationships and approximate boxes,
but does not spend SAM credits for every visible object. Query is still read
only: it returns an exact cached SAM mask when one exists, otherwise an
explicitly labelled approximate Muse box. An admin or register member may call
`POST /v1/observations/{id}/segment` for a verified observation. The worker
uses the known box as the official SAM box prompt, stores the decoded one-bit
mask as a related PostgreSQL BYTEA PNG and reuses that cache on later queries.
One SAM image refinement is billed by Meta at US$0.0025; repeated requests for
the same observation reuse its idempotent job.

## Architecture and privacy

    Admin / Android / Display -> FastAPI -> PostgreSQL metadata + BYTEA
                                      |-> Redis + Celery -> Mock or Meta API

Evidence is scoped to a workspace. A query says “last seen”; it does not assert
that an item remains in place. Customer media and credentials stay outside Git.
Fictional generated evaluation assets are isolated in `simulator/workspaces/`.

User access follows workspace membership and roles. A device identifies itself with
`X-RealityOS-Device-ID` and authorizes uploads with its separate
`X-RealityOS-Device-Key`; its public ID is provenance, not a human identity.
Only workspace administrators can inspect device/operator labels or analytics.
The native Display renderer receives only an observation-scoped, expiring image
URL; it never receives the device key or Model API key.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Database](docs/DATABASE.md)
- [REST API](docs/API.md)
- [Meta integration](docs/META_INTEGRATION.md)
- [Wearables](docs/WEARABLES.md)
- [Deployment in Spanish](docs/DEPLOYMENT.md)
- [Demo](docs/DEMO.md)
- [Security](docs/SECURITY.md)

Licensed under [Apache License 2.0](LICENSE).

## Evaluación con espacios de trabajo

La aplicación usa registro por usuario/correo y contraseña, conserva Facebook y
ofrece una API REST para importar registros y medios por espacio. Consulte
[cuentas, API y escenarios](docs/WORKSPACE_DATA.md).

| Espacio ficticio | Cuenta del jurado | Otros trabajadores |
| --- | --- | --- |
| Pacific Ridge Police Department | `alex-rivera` | `maya-johnson`, `daniel-kim` |
| California Valley Medical Center | `elena-marquez` | `mateo-rios`, `sarah-chen` |
| Sonoran Neurological Institute | `noah-brooks` | `lucia-vega`, `owen-patel` |

Las contraseñas se entregan de forma privada. En el host, el operador autorizado
puede recuperar las tres cuentas del jurado de `.runtime/jury-access.json`.
El inventario de nueve cuentas e integraciones queda en
`.runtime/jury-workspace-credentials.json`; no se publica en este repositorio.
Las direcciones `@jury.example.test` no reciben correo y no
se presentan como verificadas. El flujo normal de registro confirma correos reales.

Pruebas sugeridas: buscar la linterna amarilla o el destornillador rojo; consultar
`Ana Solis` y su expediente; comparar `DEMO MEDICINE` de `20 mg` con la prescripción
ficticia de `10 mg`; consultar dónde se vieron los documentos de `Luis Moreno`.
Las respuestas deben mostrar evidencia, fuentes y fechas, respetando el espacio
seleccionado. Los pacientes son registros importados, no cuentas de acceso.

Datos, retratos y escenas son ficticios y están identificados como pruebas.
El almacenamiento, API y procesamiento utilizan el circuito real. Los MP4 del
conjunto son escenas estáticas simuladas. El reconocimiento biométrico existente
no se modifica ni se conecta automáticamente a estas personas importadas.

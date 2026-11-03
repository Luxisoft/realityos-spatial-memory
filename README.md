# RealityOS — An Intelligent Spatial Memory

RealityOS records intentional visual observations inside a workspace and later
retrieves the **last verified evidence** for an object: a real photograph with
provenance, not a guess. It is built for workshops, warehouses, clinics and
Meta wearable experiences where a useful answer needs a picture, a source and
a date.

Two rules shape the whole product:

- **Register is explicit and writable.** Capture requires an open, consented
  session. Nothing is recorded silently.
- **Query is read-only and evidence-only.** Query endpoints never start a
  recording and never fabricate media. Answers say "last seen" — they do not
  claim the item is still there.

Original captures are stored in PostgreSQL as BYTEA, scoped to workspaces with
role-based access (admin, register, query).

## For Meta evaluators (jury)

The fastest evaluation path is the hosted production server plus the Android
Debug APK. No installation is required to start.

**1. Install the app.** Sideload
`android/app/build/outputs/apk/debug/app-debug.apk` (Debug build
`0.1.6`, `versionCode 7`; filenames may carry a build timestamp). Point it at
`https://realityos.luxisoft.com` (the connection URL is editable in the app).

**2. Sign in with a jury account.** The app uses username/email plus
password; Facebook login is also available but is not required for the
evaluation scenarios.

| Fictional workspace | Jury account | Other workers |
| --- | --- | --- |
| Pacific Ridge Police Department | `alex-rivera` | `maya-johnson`, `daniel-kim` |
| California Valley Medical Center | `elena-marquez` | `mateo-rios`, `sarah-chen` |
| Sonoran Neurological Institute | `noah-brooks` | `lucia-vega`, `owen-patel` |

Passwords are delivered privately. On the host, the authorized operator can
recover them from `.runtime/jury-access.json` (never committed). Addresses
`@jury.example.test` cannot receive email; the normal registration flow
confirms real emails.

**3. Run the suggested scenarios.** Each workspace is isolated: answers must
respect the selected space.

- Search the yellow flashlight or the red screwdriver (object search with
  photographic evidence, sources and dates).
- Open the `Ana Solis` record and read her file: related case, notes and
  portrait.
- Search `Ana Solis` **by photo** to retrieve her file (authorized portrait;
  every match is a candidate the professional must confirm).
- Compare `DEMO MEDICINE` `20 mg` against the fictional `10 mg` prescription
  (manual professional comparison; the system never auto-prescribes).
- Ask where the `Luis Moreno` documents were last seen.

**How to interpret results.** Fictional people, portraits and scenes are
labelled as test data (`simulated`); storage, API and processing run the real
pipeline. MP4 fixtures are static simulated scenes. Patients are imported
records, not login accounts. Face matching requires explicit biometric
authorization with a traceable basis plus portrait enrollment — it is never
automatic.

## How RealityOS uses Meta AI models

All Meta inference goes through the Model API at `https://api.meta.ai/v1`
(either directly or via the restricted gateway below). Keys stay server-side;
Android and browser bundles never contain them. `META_MODE=mock` runs a
deterministic provider with zero HTTP calls for tests; every mock result is
labelled simulated, and a Live failure never silently becomes mock data.

| Model | Model ID | What RealityOS uses it for |
| --- | --- | --- |
| Muse Spark | `muse-spark-1.3` | Image understanding via the Responses API: detects visible objects (brand, model, visible text, count) with approximate boxes at registration; identifies multi-object publication content; maps spoken or written queries to existing workspace names and aliases; produces the persisted bilingual (`en`/`es`) text maps; translates authorized viewer texts only. Output is validated structured JSON — a fact is omitted when visible evidence cannot support it. |
| SAM | `sam-3.1` | Explicit segmentation refinement only. An admin or register member requests it per verified observation; Query never triggers it. Takes Muse's box as an official box prompt (at most 16 objects per request; larger sets are partitioned), or a one-noun-phrase concept prompt on a source crop (accepted only at IoU ≥ 0.5 with the confirmed instance). Video mode uploads temporary clips to the Files API (`purpose=user_data`, deleted afterwards) and tracks priority objects across frames. One-bit masks are decoded with Meta's `meta-sam-parser` and stored as BYTEA PNG/RLE geometry for reuse. Billed by Meta at US$0.0025 per image refinement; cached masks are reused instead of re-billed. |
| Muse Voice Transcribe | `muse-voice-transcribe-1.0` | Speech-to-text only. Receives multipart WAV audio (`PUSH_TO_TALK`) and returns the transcription. It is never used for speech synthesis. |

Related endpoints: `GET /v1/models` (catalog preflight), `POST /v1/files`
and `DELETE /v1/files/{id}` (temporary video hosting for SAM video).

**What is not a Meta model in this stack:** speech synthesis uses ElevenLabs
(`eleven_flash_v2_5`, WAV PCM mono 24 kHz via authenticated `POST /v1/tts`);
face recognition uses local InsightFace (`buffalo_l` on CPU) behind explicit
biometric consent; Facebook Login is a Meta *platform* integration (auth plus
consented photo import), not an AI model.

Details and endpoint contracts: [Meta integration](docs/META_INTEGRATION.md).

## Deployment guides

| Guide | Use when |
| --- | --- |
| [Direct server deployment](docs/DEPLOYMENT_DIRECT.md) | One Ubuntu + Docker host reaching Meta directly; production TLS via CI. |
| [Server with gateway fallback](docs/DEPLOYMENT_GATEWAY.md) | Egress must flow through the approved FRONTEND host, or as standby. |
| [Localhost deployment](docs/DEPLOYMENT_LOCALHOST.md) | Windows + Docker Desktop evaluation with your own keys and data. |

## How it works

```text
Admin / Android / Display -> FastAPI -> PostgreSQL metadata + BYTEA
                                    |-> Redis + Celery -> Mock or Meta API
```

- **Capture (Register):** device-bound sessions with server-issued upload
  keys; originals hashed and deduplicated; Muse Spark detects the catalog;
  SAM geometry is computed only on explicit request per observation.
- **Consult (Query):** SQL pre-filter plus contextual retrieval over the
  workspace; images, video frames and record timelines with "last seen"
  dates; visual confidence kept separate from still-there confidence.
- **Workspace records:** versioned REST imports (`person`, `case`,
  `encounter`, `event`, `object`, `prescription`, `allergy`,
  `administration`) with idempotent batches, per-record notes, media and
  revisions. See [workspace data](docs/WORKSPACE_DATA.md).
- **Face search:** isolated, consent-gated arm (`/v1/faces/*`). User
  enrollments and authorized person-record portraits are searched per
  workspace with boxed evidence; group photos are never auto-enrolled.
- **Wearables:** native DAT host for Meta Ray-Ban Display (Register/Query
  screens, capture, voice query, routed TTS) plus a 600×600 Display web demo.

## Repository map

- `backend/` — FastAPI API + Celery worker, Alembic migrations, providers.
- `frontend/` — browser panel. `display-webapp/` — Display UI demo.
- `android/` — phone app and wearables code; Debug APK under
  `app/build/outputs/apk/debug/`.
- `meta-gateway/` — restricted Meta egress service (allowlisted routes only).
- `simulator/` — synthetic fixtures for evaluation (never real credentials).
- `infrastructure/` — Compose files, Nginx, gateway runtime examples.
- `docs/` — architecture, API, database, security and operations guides.

## Quality checks

```bash
make lint
make test
npm --prefix frontend run build
npm --prefix display-webapp run build
(cd android && ANDROID_HOME=/opt/android-sdk ./gradlew :app:assembleDebug)
```

`docs/IMPLEMENTATION_STATUS.md` records validations actually run and the
remaining verification work.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) · [Database](docs/DATABASE.md) ·
  [REST API](docs/API.md) · [Meta integration](docs/META_INTEGRATION.md) ·
  [Wearables](docs/WEARABLES.md) · [Security](docs/SECURITY.md) ·
  [Demo](docs/DEMO.md) · [Workspace data](docs/WORKSPACE_DATA.md)

Licensed under [Apache License 2.0](LICENSE).

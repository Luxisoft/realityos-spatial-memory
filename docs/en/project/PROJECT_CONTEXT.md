[Español](../../es/project/PROJECT_CONTEXT.md) · [RealityOS](../README.md) · [Index](../INDEX.md)

# Project context

Current working map. Read the [conventions](../../../AGENTS.md), check [verified status](IMPLEMENTATION_STATUS.md), then open the guide for the area being changed. Git retains the change history.

## Structure

| Path | Responsibility |
| --- | --- |
| `backend/app/` | API and contracts shared with the worker: HTTP, providers, processing, accounts, social features, records and storage. |
| `backend/app/faces.py` | Isolated biometrics protected by AGENTS.md. |
| `backend/alembic/versions/` | Alembic schema; documented current revision `20261103_0035`. |
| `android/` | Only app: Kotlin/Compose, CameraX, DAT and native Display; Mock Device Kit only in Debug. |
| `meta-gateway/` | Restricted egress to allowlisted Meta routes. |
| `infrastructure/` | Compose for postgres, redis, api, worker, scheduler and proxy; TLS and gateway. |
| `simulator/` | Synthetic scenario and QA resources. |
| `tests/`, `gateway-tests/` | Regressions and frozen OpenAPI contract. |
| `scripts/` | Data preparation, import, maintenance and documentation generators/checks. |
| `docs/en/`, `docs/es/` | Guides by language and topic with matching filenames. |
| `docs/assets/`, `docs/postman/` | Shared resources and downloadable collections. |
| `.runtime/` | Ignored private access details, evidence, releases and rollback files. |

## Flows and invariants

- Explicit capture/publication/import → BYTEA original → processing → persisted evidence and translations. Queries do not register new evidence.
- R2/S3 is an account-private source; imports retain a RealityOS copy. Disconnecting keeps existing posts.
- Authorize every resource again when querying or downloading it. Groups do not receive the creator's bucket keys.
- Biometrics retains explicit consent and enrollment, separate from object processing. Do not modify protected modules as a side effect.
- Direct Meta access with configurable gateway fallback; Muse Voice Transcribe for input and ElevenLabs for output. Credentials remain server-side.
- Local Windows uses `.env.local`, the `realityos-local` Docker project and its own Debug APK. No automatic reuse of production data or keys.

## Working guides

- [API and Postman](../api/API.md), [generated contract](../api/API_REFERENCE.md) and [data](../architecture/DATABASE.md).
- [Architecture](../architecture/ARCHITECTURE.md), [security](../architecture/SECURITY.md) and [design](../architecture/UI_DESIGN.md).
- [Android](../integrations/ANDROID.md), [glasses](../integrations/WEARABLES.md), [Meta](../integrations/META_INTEGRATION.md) and [speech](../integrations/TTS.md).
- [Installation/operations](../deployment/DEPLOYMENT.md), [gateway](../deployment/DEPLOYMENT_GATEWAY.md) and [Windows](../deployment/DEPLOYMENT_LOCALHOST.md).
- [Buckets](../guides/STORAGE_CONNECTIONS.md), [records](../guides/WORKSPACE_DATA.md), [demo](../guides/DEMO.md) and [checklist](../testing/IMPLEMENTATION_CHECKLIST.md).
- [Status and pending work](IMPLEMENTATION_STATUS.md) and [hackathon submission](HACKATHON.md).

## Validation and delivery

From the root: `make docs-check`, `make architecture-check`, `make lint`, `make test` and `make android-check`, as relevant. Single APK artifact: `android/app/build/outputs/apk/debug/app-debug.apk`.

Publish changes to `main` under AGENTS.md. Documentation changes do not require a new APK. For server releases, preserve runtime/rollback and check health, OpenAPI and Alembic; AGENTS.md defines Docker authorization. Do not mark device, R2, provider or Windows runs passed unless they actually ran.

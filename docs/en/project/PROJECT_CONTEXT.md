[Español](../../es/project/PROJECT_CONTEXT.md) · [RealityOS](../README.md) · [Index](../INDEX.md)

# Project context

RealityOS has a modular monolith with two compositions: **local** on the judge's Windows/Linux PC and **server** on the RealityOS server. The current development host is the RealityOS server; localhost does not mean its production services. **FRONTEND** is a separate server for the restricted Meta gateway. This reorganization does not authorize deployments, restarts or data changes on either server.

Read the [conventions](../../../AGENTS.md), [verified status](IMPLEMENTATION_STATUS.md) and the guide for the area being changed. Delivery history remains in Git.

## Structure

| Path | Responsibility |
| --- | --- |
| `backend/app/runtime/` | Explicit local/server router and worker composition; schema installer. |
| `backend/app/` | HTTP, services, providers, models and persistence shared by API and worker. |
| `backend/app/local/` | Database-backed local access and SQL initialization separated from operational runtime. |
| `backend/app/faces.py`, `face_setup.py` | Protected biometric arm; consent and private enrollment. |
| `backend/schema/20261104_0040/` | Immutable DDL snapshot for empty PostgreSQL databases. |
| `backend/alembic/versions/` | Preserved history; current code revision `20261104_0041`. |
| `android/` | Only app: Kotlin/Compose, CameraX, DAT and native Display; shared repositories and components. |
| `meta-gateway/` | Remote egress restricted to approved Meta routes. |
| `infrastructure/` | Four-service local Compose and separate server composition. |
| `simulator/database/` | Single SQL dataset for local scenario initialization. |
| `simulator/media/` | Organized local images/videos and technical license/hash manifest. |
| `tests/`, `gateway-tests/` | Regressions, disposable PostgreSQL and OpenAPI contracts. |
| `scripts/` | Local installation, maintenance and generators/checkers. |
| `docs/es/`, `docs/en/` | Equivalent language guides; shared assets in `docs/assets/` and `docs/postman/`. |
| `.runtime/` | Private files, isolated tests and builds; ignored by Git. |

## Invariants

- PostgreSQL/BYTEA is the source of truth. Queries do not read JSON catalogs or installation SQL.
- Explicit capture/publication → original → processing → persisted evidence. Query does not register new evidence.
- Publications require a workspace. Every read, download and modification revalidates permissions and membership.
- Local initialization is transactional and versioned; restarts do not restore deleted content or overwrite edits.
- Biometrics retain permissions, consent and private references, outside object processing.
- Localhost uses PostgreSQL, Redis, API and worker; direct Meta with the judge's key and installed Android voices. No gateway, buckets, Facebook, SMTP, scheduler or ElevenLabs.
- The server retains its private integrations and FRONTEND fallback gateway. Keys stay out of the client and Git.
- Environment files are explicitly selected with `REALITYOS_ENV_FILE`; Compose injects the selected configuration.

## Guides and validation

[Architecture](../architecture/ARCHITECTURE.md) · [Data](../architecture/DATABASE.md) · [Security](../architecture/SECURITY.md) · [Design](../architecture/UI_DESIGN.md) · [API and Postman](../api/API.md)

[Android](../integrations/ANDROID.md) · [Glasses](../integrations/WEARABLES.md) · [Meta](../integrations/META_INTEGRATION.md) · [Localhost](../deployment/DEPLOYMENT_LOCALHOST.md) · [Server](../deployment/DEPLOYMENT.md) · [Gateway](../deployment/DEPLOYMENT_GATEWAY.md)

From the root: `make docs-check`, `make architecture-check`, `make lint`, `make test` and `make android-check`, as appropriate. PostgreSQL tests create temporary clusters in `.runtime/`, separate from existing services. Do not claim device, external provider, Docker or Windows tests that were not run.

Changes are delivered to `main` under AGENTS.md; remote deployment requires separate authorization. The canonical Debug APK is `android/app/build/outputs/apk/debug/app-debug.apk`, stored with Git LFS and the existing signing certificate. Android or contract changes require rebuilding it; validation is recorded for each delivery.

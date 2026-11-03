<p align="center"><a href="DATABASE.md"><img src="../../assets/readme/language-en-active.svg" alt="English" height="32"></a> <a href="../../es/architecture/DATABASE.md"><img src="../../assets/readme/language-es.svg" alt="Español" height="32"></a></p>

# Data and persistence

[← Documentation](../INDEX.md) · [API / Postman](../api/API.md)

## Reading guide

| Topic | What to know |
| --- | --- |
| **Originals** | `media_assets.original_bytes`; large videos in ordered `media_asset_chunks.content` with a full hash. |
| **Objects** | `tracked_objects` represents logical identity; `object_observations` retains evidence and time. Location derives from verified observations. |
| **Geometry** | Muse boxes and SAM masks link derivatives to originals; tracks retain PTS and RLE masks. |
| **Faces** | `face_enrollments`, `biometric_consents` and `face_record_enrollments` preserve authorization, model version and evidence. |
| **Publications** | `gallery_evidence` retains immutable versions; indexing runs activate a completed generation. EN/ES translations are persisted. |
| **Profiles** | The CV is private and replaceable; replacement clears derivatives. Public projections never expose its file or extracted text. |
| **Migrations** | Alembic defines the schema. Check deployed revision per release; historical dates are not current server state. |

```mermaid
flowchart LR
    N0["Capture"] --> N1["BYTEA"]
    N1["BYTEA"] --> N2["Evidence"]
    N2["Evidence"] --> N3["Query"]
```

## Commands

Run from the root with dependencies installed. Migrations and processing require the chosen environment and authorized data.
```bash
make migrate
```

[ARCHITECTURE ](ARCHITECTURE.md) · [WORKSPACE DATA ](../guides/WORKSPACE_DATA.md) · [SECURITY ](SECURITY.md)

Revision `20261103_0035` adds `storage_connections`, `storage_imports` and `storage_syncs`: private connections with encrypted keys, import provenance/status and synchronization rules. Buckets do not replace BYTEA originals. [Operations and retention](../guides/STORAGE_CONNECTIONS.md).

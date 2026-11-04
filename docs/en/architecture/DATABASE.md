# Data and persistence

[Español](../../es/architecture/DATABASE.md) · [Documentation](../INDEX.md) · [API / Postman](../api/API.md)

PostgreSQL is the source of truth in both environments. Accounts, workspaces, permissions, records, publications and their ES/EN text are queried from the database. The local installer imports SQL data once; the API does not combine those queries with catalog files.

| Data | Persistence |
| --- | --- |
| Originals | `media_assets.original_bytes`; large videos in ordered `media_asset_chunks.content`, with a complete-content hash. |
| Objects | `tracked_objects` and `object_observations` preserve logical identity, evidence and last-seen time. |
| Publications | Required workspace; copies share originals while keeping separate comments/reactions. `gallery_evidence` stores versioned evidence. |
| Records | Stored records, media links and translations; access requires current membership. |
| Profiles | Avatar separate from private references and CV. Public responses do not expose private originals. |
| Biometrics | Protected consents and enrollments, separate from object/publication workflows. |
| Local access | `local_access_accounts` links only the six selectable accounts to their workspaces. |
| Local installation | Versioned database receipts prevent initialization from repeating or deleted data from returning on restart. |

## Empty schema and upgrades

The shared entry point is `python -m app.runtime.schema`. For an empty PostgreSQL database it installs immutable SQL from `backend/schema/20261104_0040/`, stamps that revision and runs Alembic to `head`. The snapshot includes indexes and the historical quarantine journal; it is not derived from current models at startup.

An existing versioned database receives only pending migrations. A database containing tables without `alembic_version` is rejected without changing its data. A PostgreSQL transaction advisory lock coordinates concurrent initializers. Historical migrations remain unchanged; revision `20261104_0041` adds the local access table. The code revision does not establish the server's current database revision.

Tests use disposable PostgreSQL, isolated schemas and the same installer: they verify an empty database, model column/key/index equivalence after Alembic, idempotence, rejection of unversioned databases and preservation of an edited row. SQLite is reserved for tests that do not require PostgreSQL semantics.

## Evaluation data and assets

`simulator/database/` contains the installation SQL dataset; `simulator/media/` contains local assets organized by purpose, together with provenance/license/hash `manifest.csv`. Modules in `app.local` validate the environment before installation. Receipts and data changes belong to the same transaction: an error must not leave the installation marked complete.

The current dataset has two workspaces and six access accounts. Pacific Ridge Police Department has sixteen portraits and records linked to publications, plus three videos. Meta Social Media has introductions for its three accounts, three videos and thirteen additional synthetic profiles with private references. Additional profiles do not expand the six-account selector. The local versioned retirement removes Sonoran/Memory and its exclusive resources. Restarts preserve edits, deletions, membership and consent in the retained groups.

Initial loading copies verified files into BYTEA. Subsequent queries use the database even when installation assets are unavailable. Biometric reference originals are never published; only the separate avatar is displayed.

## Retention and privacy

S3/R2 connections are private server sources and do not replace BYTEA. Changing or disconnecting a source retires its imported copies without deleting external objects. Shared bytes are removed only when no valid workspace, profile, record or biometric references remain.

Historical deletion of personal/unassigned publications cannot be reversed by a schema downgrade. Development commands do not authorize changing live server data. `make migrate ENV_FILE=.env.local` and `make seed ENV_FILE=.env.local` must target the selected local environment.

[Architecture](ARCHITECTURE.md) · [Records](../guides/WORKSPACE_DATA.md) · [Security](SECURITY.md)

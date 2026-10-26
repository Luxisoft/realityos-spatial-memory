# Implementation status — 2026-10-26

## Verified in this workspace

- Backend lint passed: ruff check backend tests.
- Five SQLite integration tests passed: health/auth, BYTEA capture/retrieval/hash,
  mock processing, highlighted evidence, missing object, role restriction and
  workspace isolation.
- Admin-panel and Display production builds passed.
- Docker Engine and Compose were installed on the target server. PostgreSQL,
  Redis, API, Celery, panel, Display and Nginx are currently running.
- Alembic completed against PostgreSQL 16. An authenticated proxy query returned
  a highlighted BYTEA-backed observation, and a new capture completed through
  Redis/Celery in Mock mode.
- Meta Model API documentation was reviewed. The locally configured key
  authenticated to Models but has no enabled models; Muse Spark 1.3 returned
  model_not_found, so production runtime remains Mock.

## Implemented but not fully environment-verified

- Live Muse Spark, SAM and ASR clients match reviewed contracts but need a
  Meta account with the requested model entitlement. SAM box parsing works;
  pixel-mask persistence remains incomplete.

## Not implemented

- FFmpeg video ingestion, frame extraction and video traceability.
- PostgreSQL FTS/trigram retrieval beyond extension/schema; current MVP uses
  bounded SQL name/alias matching.
- Android Kotlin/Compose, DAT SDK and Mock Device Kit tests.
- Official Ray-Ban Display toolkit and simulator validation.
- Production TLS automation, restore test and a published PR.

No claim of physical-glasses, Android, Live Meta or simulator success is made.

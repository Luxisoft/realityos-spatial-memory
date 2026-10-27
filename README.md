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
- React administrative panel and separate 600×600 Display query web app.
- Admin object explorer with workspace-scoped name/alias, category and location
  filters, evidence history and a non-metric location hierarchy.
- Compose, Nginx reverse proxy, migration, synthetic seed and automated tests.

## Quick start: Mock mode

Requirements: Python 3.12+, Node 22+, Docker Compose for the complete stack.

    cp .env.example .env
    # Set POSTGRES_PASSWORD, JWT_SECRET and DEVICE_CREDENTIAL_PEPPER to unique values.
    make install
    make lint
    make test
    make compose-up

The proxy is available at localhost port 8090 by default. Run the synthetic seed
inside the API container:

    docker compose --env-file .env -f infrastructure/docker-compose.yml exec api python /scripts/seed_demo.py

The demo credentials are SEED_ADMIN_EMAIL and SEED_ADMIN_PASSWORD in .env.
Replace them outside a local demonstration.

## Meta integration

META_MODE=mock is the default and is used by seed/tests. It makes no external
request and labels results simulated. For META_MODE=live, use either direct
`MODEL_API_KEY` in a development-only environment or configure
`META_GATEWAY_BASE_URL` plus `META_GATEWAY_TOKEN`; the latter keeps the Meta key
on the gateway host. The application does not silently fall back to mock when
Live fails.

Detailed SAM Video uploads only temporary MP4 clips to Meta Files API with
`purpose=user_data`, expiry and deletion. The original PostgreSQL BYTEA video
remains RealityOS's source of truth. An uncertain provider submission is not
retried automatically.

## Quality checks

    make lint
    make test
    npm --prefix frontend run build
    npm --prefix display-webapp run build

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
that an item remains in place. No customer media, credentials or generated
images are included in the repository.

Human logins are administrative only. A device identifies itself with
`X-RealityOS-Device-ID` and authorizes uploads with its separate
`X-RealityOS-Device-Key`; its public ID is provenance, not a human identity.
Only workspace administrators can inspect device/operator labels or analytics.

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

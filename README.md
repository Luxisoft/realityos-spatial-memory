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
- Deterministic Mock Meta provider and a Live client for Muse Spark 1.3, SAM
  3.1 and Muse Voice Transcribe.
- Optional restricted Meta egress gateway for deployments where only an
  approved server can reach Model API. See [Gateway](docs/GATEWAY.md).
- React administrative panel and separate 600×600 Display query web app.
- Compose, Nginx reverse proxy, migration, synthetic seed and automated tests.

## Quick start: Mock mode

Requirements: Python 3.12+, Node 22+, Docker Compose for the complete stack.

    cp .env.example .env
    # Set POSTGRES_PASSWORD and JWT_SECRET to unique values.
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

## Quality checks

    make lint
    make test
    npm --prefix frontend run build
    npm --prefix display-webapp run build

See docs/IMPLEMENTATION_STATUS.md for validations actually run in this workspace
and remaining verification work.

## Architecture and privacy

    Admin / Android / Display -> FastAPI -> PostgreSQL metadata + BYTEA
                                      |-> Redis + Celery -> Mock or Meta API

Evidence is scoped to a workspace. A query says “last seen”; it does not assert
that an item remains in place. No customer media, credentials or generated
images are included in the repository.

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

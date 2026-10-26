# Architecture

RealityOS is a modular monorepo: FastAPI owns authorization and business rules;
Celery runs long-running processing against the same SQLAlchemy domain model;
React clients consume only the REST contract.

    Register client -> API -> PostgreSQL BYTEA -> Redis/Celery -> Meta provider
    Query client    -> API -> verified observation + authorized media URL

The query path does not create capture-domain resources. Audit and eventual
query analytics are isolated from observations so they cannot become evidence.

The current API uses synchronous SQLAlchemy inside async endpoints to avoid a
runtime thread-pool limitation in the supported Python 3.13 environment.
Production scaling should move to an async driver or process replicas before
high concurrency.

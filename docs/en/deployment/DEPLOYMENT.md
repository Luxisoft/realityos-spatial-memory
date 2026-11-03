[Español](../../es/deployment/DEPLOYMENT.md) · [RealityOS](../README.md) · [Index](../INDEX.md)

# Installation and operations

| Environment | Guide |
| --- | --- |
| Ubuntu server with direct access | [Install the server](DEPLOYMENT_DIRECT.md) |
| Meta gateway or fallback | [Install the gateway](DEPLOYMENT_GATEWAY.md) |
| Windows + Docker Desktop | [Isolated local installation](DEPLOYMENT_LOCALHOST.md) |

## Private configuration

The server uses `.env` to choose direct Meta access or gateway routing and fallback. Optional `.env.facebook`, `.env.elevenlabs` and `.env.storage` files hold integration settings. Keep them outside Git with mode 0600. ElevenLabs synthesis and R2/S3 connections are independent of the Meta gateway.

Before connecting buckets, configure a persistent random `STORAGE_ENCRYPTION_KEY` in `.env.storage`. API and worker must share it; losing or replacing it prevents decryption of existing connections. The scheduler schedules synchronization and the worker processes it. Follow the [bucket guide](../guides/STORAGE_CONNECTIONS.md) before preparing demo data.

## Deployment and checks

The [production workflow](../../../.github/workflows/deploy-production.yml) publishes immutable images and deploys API/worker/scheduler and the gateway in independent jobs. It preserves runtime settings and saves image rollback in `.runtime/ci-runtime-rollback.json`. The proxy exposes the API and email action pages over HTTPS.

After each deployment, verify `/health/ready`, the complete `/v1/openapi.json` document and `alembic current`. Fresh-install commands are in the [direct guide](DEPLOYMENT_DIRECT.md). A health response alone does not establish API readiness.

If the host runs demand ingress installed by `scripts/deploy/enable_demand_api.py`, restart the deployment user's `backend-demand-realityos.service` after recreating the API: it caches the container address. The workflow already does this and verifies a public `/v1/` request.

## Rollback and data

To return to a published image, run **Deploy production** with its immutable `release_tag`. Code rollback does not remove new tables or recover deleted data. If the previous version had no scheduler, stop it before applying its rollback. Schema/data reversal requires a tested procedure specific to that migration.

Ordinary releases do not require a PostgreSQL dump. Only a migration requiring reversal may create a technical `pre-*.dump` snapshot under `.runtime/`, expiring after 24 hours —one hour under disk pressure. Official code/database backups belong in the owner's approved private GitHub destination; R2 is reserved for media. Preserve data volumes when stopping services.

Docker commands on this host follow the authorization in [AGENTS.md](../../../AGENTS.md). After a release, retire unused build images and working containers while preserving the rollback image.

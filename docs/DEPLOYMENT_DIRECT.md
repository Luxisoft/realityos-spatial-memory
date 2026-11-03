# Direct server deployment

Run RealityOS on a single Ubuntu + Docker host that reaches the Meta Model
API directly. This is the primary production topology.
Back to the [main README](../README.md) · also see
[server with gateway](DEPLOYMENT_GATEWAY.md) and
[localhost](DEPLOYMENT_LOCALHOST.md).

## Requirements

- Ubuntu host with Docker Engine and Compose v2, plus Git.
- A domain with an `A` record pointing at the server (production TLS).
- A Meta API key with `muse-spark-1.3`, `sam-3.1` and
  `muse-voice-transcribe-1.0` enabled, and an ElevenLabs key for speech.
- For CI production deploys: the protected GitHub Environment `production`
  with the secrets listed in [Gateway](GATEWAY.md) (Meta key, gateway token,
  SSH access, ACME email, allowlists, deploy path).

## Start on the host

```bash
git clone <repo> && cd realityos-spatial-memory
cp .env.example .env
# Edit .env: POSTGRES_PASSWORD, JWT_SECRET, MODEL_API_KEY,
# META_MODE=live, META_CONNECTION_MODE=direct
docker compose --env-file .env -f infrastructure/docker-compose.yml up --build -d
```

The Compose proxy listens on `${HTTP_BIND_ADDRESS:-127.0.0.1}:${HTTP_PORT:-8080}`.
Verify locally before exposing anything:

```bash
curl -sf http://127.0.0.1:8080/health/ready
curl -sf http://127.0.0.1:8080/v1/openapi.json -o /dev/null
docker compose --env-file .env -f infrastructure/docker-compose.yml exec -T api alembic current
```

Key settings live in `.env` (private, never committed):

| Variable | Meaning |
| --- | --- |
| `META_MODE` | `live` for Meta inference, `mock` for deterministic tests. |
| `META_CONNECTION_MODE` | `direct` here; see the gateway guide for `gateway`. |
| `META_GATEWAY_FALLBACK_ENABLED` | `true` keeps FRONTEND as standby on connection/auth/rate-limit failures. |
| `MODEL_API_KEY` | Server-only Meta key (also installed on FRONTEND for one account). |
| `META_API_BASE_URL` | `https://api.meta.ai/v1`. |
| `ELEVENLABS_API_KEY` | Voice synthesis key (in private `.env.elevenlabs`). |
| `CORS_ORIGINS` | Restrict to real domains before production. |

Restart API/worker after editing `.env`. Only API, worker and proxy join the
egress network; PostgreSQL and Redis stay unreachable from the host. Volumes
`postgres_data` and `redis_data` persist state; back up with
`scripts/backup-postgres.sh` and test restores.

## Production TLS via CI

Merges to `main` run `.github/workflows/deploy-production.yml`: tests, then
immutable GHCR images, then deployment. The workflow installs the host Nginx
virtual host, obtains the Let's Encrypt certificate and serves panel, Display
and `/v1/` over `https://realityos.luxisoft.com:443`. Do not expose the
backend port to the Internet.

First-time TLS notes:

- Point the domain `A` record at the server IP.
- If the zone sits behind Cloudflare Workers/Pages routing, exclude this host
  (dedicated `Worker: None` route) or start **DNS only** (grey cloud), run the
  workflow, then re-enable proxying with SSL/TLS **Full (strict)**.
- A LUXIPANEL 404 on `/.well-known/acme-challenge/` means Cloudflare is
  routing the challenge to the wrong origin.

To roll back, run **Deploy production** manually with a previously published
immutable `release_tag` (commit SHA); builds are skipped and that exact image
pair is deployed.

For the full operator reference (Spanish), see
[Deployment](DEPLOYMENT.md).

> Historical source / Fuente histórica — preserved 2026-11-03. [Current guide](../GATEWAY.md) · [Guía actual](../GATEWAY.es.md). Earlier deployment instructions may be retired.

# Meta egress gateway

RealityOS can run Live requests through a restricted gateway at
`https://meta.luxisoft.com`. The gateway is a separate FastAPI service deployed
on FRONTEND; it is not a general-purpose HTTP proxy.

## Boundary

RealityOS sends `X-RealityOS-Gateway-Token` to the gateway. The gateway accepts
only `GET /v1/models`, `POST /v1/responses`, `POST /v1/asr/transcribe`,
`POST /v1/files`, and `DELETE /v1/files/{id}`,
then replaces that header with the server-side Meta bearer token. It forwards
request bytes to Meta without storing bodies, rejects every other route, and forwards
the upstream response status and safe headers.

The gateway streams request bodies and permits up to 1 GiB so a bounded MP4
segment can use Meta Files API. For large uploads, configure the worker's
gateway hostname as a direct/private route or DNS-only record: a CDN proxy may
impose a lower request-body ceiling than RealityOS or Meta. The gateway remains
protected by its IP allowlist and independent token.

## Connection selection (2026-11-01)

RealityOS `.env` is authoritative for API and worker routing:

```dotenv
META_CONNECTION_MODE=direct
META_GATEWAY_FALLBACK_ENABLED=true
MODEL_API_KEY=<active server-only Meta key>
META_API_BASE_URL=https://api.meta.ai/v1
META_GATEWAY_BASE_URL=https://meta.luxisoft.com/v1
META_GATEWAY_TOKEN=<independent gateway token>
```

`direct` uses RealityOS egress even when gateway settings are present. `gateway`
uses FRONTEND only. Restart API/worker after editing `.env`. Fallback is explicit:
connection failures, 401/403/404, 408/429 and 5xx switch from direct to gateway;
400/422 are returned unchanged. Each new request starts on the selected primary
route. Only the final route uses the configured transient retry policy.

Video/file operations switch only on definite rejection (401/403/404/429) or
connection failure before submission. Ambiguous submissions and accepted streams
are never replayed; they remain `uncertain`. Seekable upload handles rewind to
their original offset before a permitted replay. The same active Meta key is
installed privately on both servers, so uploaded file IDs stay in one account.
Bearer authentication goes only to Meta; the gateway receives only its own token.
Keys, tokens and captured content are never logged or committed.

The gateway remains running as standby. API/worker deployment does not depend on
FRONTEND availability. CI retains unrelated runtime settings but does not overlay
old connection settings on `.env`. Private rollback overlays retain the previous
image and environment; they must never enter Git.

## FRONTEND deployment

GitHub Actions deploys immutable GHCR image tags after a merge to `main`. Before
the first deployment, create `A meta.luxisoft.com -> 198.252.105.131`. The
workflow installs a loopback-only Docker gateway, renders the versioned Nginx
configuration, obtains an ACME certificate, and only then updates the
RealityOS API and worker.

The Nginx allowlist is derived from `GATEWAY_ALLOWED_CIDRS`. The initial value
must include the RealityOS server's actual public egress address. This domain
can remain proxied by Cloudflare: each deployment fetches Cloudflare's current
published IPv4/IPv6 ranges, configures Nginx to trust `CF-Connecting-IP` only
from those ranges, then applies the allowlist to the recovered client address.
Keep the gateway token as a second, independent control; never rely on an IP
allowlist alone. Set Cloudflare SSL/TLS mode to **Full (strict)** after the
workflow obtains the origin certificate.

To roll back, run **Deploy production** manually and supply a previously
published immutable `release_tag` (the commit SHA). The workflow skips builds
and deploys that exact gateway/backend image pair.

## Required GitHub Environment secrets

Configure these in the protected `production` environment, never in repository
files: `MODEL_API_KEY`, `META_GATEWAY_TOKEN`, `FRONTEND_SSH_HOST`,
`FRONTEND_SSH_USER`, `FRONTEND_SSH_PRIVATE_KEY`, `REALITYOS_SSH_HOST`,
`REALITYOS_SSH_USER`, `REALITYOS_SSH_PRIVATE_KEY`, `ACME_EMAIL`,
`GATEWAY_ALLOWED_CIDRS`, `FRONTEND_SSH_KNOWN_HOSTS`,
`REALITYOS_SSH_KNOWN_HOSTS`, and `REALITYOS_DEPLOY_PATH`. Set
`DEVICE_CREDENTIAL_PEPPER` in RealityOS's protected server `.env` before
enrolling devices when a credential-specific pepper is required; it is not a
GitHub secret because the deployment keeps the existing server `.env` intact.
If omitted, the existing server-only `JWT_SECRET` is used as a secure fallback
instead of a public development value.

## Local check

Use `make gateway-api` with a local `meta-gateway/.env` copied from
`infrastructure/gateway/runtime.env.example`. Do not expose its port publicly.

## Síntesis fuera del gateway

El gateway conserva exclusivamente las rutas permitidas de Meta, incluida
Muse Voice Transcribe. La generación de voz usa ElevenLabs desde el API de
RealityOS y su credencial privada; no existe una ruta de síntesis en este
gateway. Ver [TTS](../TTS.md).

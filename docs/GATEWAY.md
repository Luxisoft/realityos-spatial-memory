# Meta egress gateway

RealityOS can run Live requests through a restricted gateway at
`https://meta.luxisoft.com`. The gateway is a separate FastAPI service deployed
on FRONTEND; it is not a general-purpose HTTP proxy.

## Boundary

RealityOS sends `X-RealityOS-Gateway-Token` to the gateway. The gateway accepts
only `GET /v1/models`, `POST /v1/responses`, and `POST /v1/asr/transcribe`,
then replaces that header with the server-side Meta bearer token. It forwards
request bytes to Meta without storing bodies, rejects every other route, and forwards
the upstream response status and safe headers.

`MODEL_API_KEY` is configured only in FRONTEND's ignored gateway runtime file.
The RealityOS API and worker use `META_GATEWAY_BASE_URL` and
`META_GATEWAY_TOKEN`; their production environment explicitly blanks
`MODEL_API_KEY`.

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
`REALITYOS_SSH_KNOWN_HOSTS`, and `REALITYOS_DEPLOY_PATH`.

## Local check

Use `make gateway-api` with a local `meta-gateway/.env` copied from
`infrastructure/gateway/runtime.env.example`. Do not expose its port publicly.

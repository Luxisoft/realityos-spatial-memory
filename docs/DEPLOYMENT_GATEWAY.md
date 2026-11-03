# Server with gateway deployment

Run RealityOS with Meta traffic flowing through (or falling back to) the
approved FRONTEND egress host at `https://meta.luxisoft.com`. Use this when
the main server's network cannot or must not reach the Model API directly.
Back to the [main README](../README.md) · also see
[direct server](DEPLOYMENT_DIRECT.md) and [localhost](DEPLOYMENT_LOCALHOST.md).

## Architecture

```text
RealityOS API/worker -> FRONTEND gateway -> https://api.meta.ai/v1
```

The gateway is a separate FastAPI service on FRONTEND. It is **not** a
general-purpose proxy: it accepts only five Meta routes, swaps the
`X-RealityOS-Gateway-Token` header for the server-side Meta Bearer [REDACTED] forwards
bytes without storing bodies, and rejects everything else.

Allowlisted routes:

- `GET /v1/models` (catalog preflight)
- `POST /v1/responses` (Muse Spark, SAM)
- `POST /v1/asr/transcribe` (Muse Voice Transcribe)
- `POST /v1/files` and `DELETE /v1/files/{id}` (temporary SAM video clips)

Request bodies stream up to 1 GiB so bounded MP4 segments can use the Files
API. Defense is layered: Nginx IP allowlist from `GATEWAY_ALLOWED_CIDRS`
(which must include the RealityOS egress address) **plus** the independent
gateway token — never the allowlist alone. Speech synthesis is not routed
here: TTS always calls ElevenLabs directly from the RealityOS API.

## Selecting the route

Routing is configured in the private server `.env` (CI never overwrites it):

```dotenv
META_CONNECTION_MODE=gateway
META_GATEWAY_FALLBACK_ENABLED=false
MODEL_API_KEY=<active server-only Meta key>
META_API_BASE_URL=https://api.meta.ai/v1
META_GATEWAY_BASE_URL=https://meta.luxisoft.com/v1
META_GATEWAY_TOKEN=<independent gateway token>
```

- `gateway` uses FRONTEND only. `direct` with
  `META_GATEWAY_FALLBACK_ENABLED=true` uses RealityOS egress first and FRONTEND
  as standby.
- Fallback triggers on connection failures, 401/403/404, 408/429 and 5xx;
  400/422 pass through unchanged. Each new request starts on the configured
  primary route.
- Video/file operations replay only before submission (definite rejection or
  connection failure). Accepted streams and ambiguous submissions stay
  `uncertain` — they are never replayed.
- Install the same active Meta key privately on both servers so uploaded file
  IDs stay in one account. Restart API/worker after editing `.env`.

## FRONTEND setup

Before the first deployment, create `A meta.luxisoft.com -> 198.252.105.131`.
Merging to `main` runs the production workflow, which installs a loopback-only
Docker gateway, renders the versioned Nginx config, obtains the ACME
certificate, and then updates RealityOS. RealityOS and gateway deploys are
independent: a FRONTEND failure never blocks an API/worker update on direct
mode.

Cloudflare notes: the domain may stay proxied; each deploy refreshes
Cloudflare's published ranges, trusts `CF-Connecting-IP` only from them, then
applies the allowlist to the recovered client address. Set SSL/TLS to **Full
(strict)** after the origin certificate exists.

Required GitHub Environment `production` secrets: `MODEL_API_KEY`,
`META_GATEWAY_TOKEN`, `FRONTEND_SSH_HOST`, `FRONTEND_SSH_USER`,
`FRONTEND_SSH_PRIVATE_KEY`, `REALITYOS_SSH_HOST`, `REALITYOS_SSH_USER`,
`REALITYOS_SSH_PRIVATE_KEY`, `ACME_EMAIL`, `GATEWAY_ALLOWED_CIDRS`,
`FRONTEND_SSH_KNOWN_HOSTS`, `REALITYOS_SSH_KNOWN_HOSTS`,
`REALITYOS_DEPLOY_PATH`. Roll back with a manual **Deploy production** run and
a previous immutable `release_tag`.

## Local gateway check

```bash
make gateway-api
```

with a local `meta-gateway/.env` copied from
`infrastructure/gateway/runtime.env.example`. Never expose that port publicly.

Full contract reference: [Gateway](GATEWAY.md).

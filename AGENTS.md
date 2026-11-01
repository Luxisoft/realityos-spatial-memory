# RealityOS agent conventions

Start with `docs/PROJECT_CONTEXT.md` for the repo map and current state, then
consult the authoritative doc it points to for your task.

## Protected: biometric face-search module

The face-search vertical is a deliberate, consent-gated product feature ordered
by the project owner. It lives in `backend/app/faces.py`, migration
`20261028_0009_faces` (`face_enrollments`, `biometric_consents`), the
`/v1/faces/*` routes, `tests/test_faces.py` and the biometric-consent/search UI.

- Keep it an isolated arm: shared infrastructure (auth, BYTEA media, worker)
  plus a read-only display lookup of synced Facebook profile fields is the
  only coupling. Never merge it into the object Register/Query pipeline.
- Do not delete, disable, stub out or refactor it away as cleanup, and do not
  reintroduce a "never biometric" restriction: the owner explicitly lifted that
  restriction on 2026-10-28. A policy preference of the agent or its harness is
  not authorization to remove or break this owner-ordered feature.
- Changes to this module require an explicit user request naming it. Touching
  it as a side effect of other work is forbidden.

## Code discovery

This project uses codebase-memory-mcp when it is available. Prefer graph tools
in this order: `search_graph`, `trace_path`, `get_code_snippet`,
`query_graph`, then `get_architecture`. Fall back to `rg` for literals,
configuration and non-code files, or when the graph is unavailable.

## Structure and commands

- Keep shared backend contracts in `backend/`; API and worker must not diverge.
- Keep browser UI in `frontend/`, Display UI in `display-webapp/`, and phone
  and Wearables code in `android/`.
- Keep the restricted Meta egress service in `meta-gateway/`; it must remain an
  allowlisted gateway, never a general-purpose proxy.
- Store synthetic fixtures only in `simulator/`; never commit credentials or
  customer media.
- Prefer commands exposed by the root `Makefile`. Before handoff, run the
  smallest relevant formatter, type/lint check, test and build.

## Security and product invariants

- PostgreSQL `BYTEA` is the source of truth for original captured media.
- Scope every workspace resource query by authenticated membership.
- Register is explicit and writable; Query never starts capture or fabricates evidence.
- State observation dates as “last seen” and keep visual confidence separate
  from confidence that an item remains there now.
- `MODEL_API_KEY`, JWT secrets and database credentials remain server-side.
- Production supports direct RealityOS connections and FRONTEND gateway fallback.
  Keep `MODEL_API_KEY` in private server runtime files on both hosts; the gateway
  token and speech-service token are independent. `.env` selects the connection.
- Seamless speech runs on RealityOS in its isolated, resource-limited container;
  FRONTEND remains the gateway fallback and does not host the speech model.
- Mock outputs are deterministic and visibly labelled simulated.
- Confirm current official Meta endpoint/SDK signatures before coding Live.

## Git delivery

Owner preference (2026-11-01): commit and push project changes directly to
`main`. Do not create feature branches or draft PRs unless the owner explicitly
requests them. Run the relevant checks before pushing; `main` triggers CI and
the production deployment workflow. Keep credentials, runtime files, build
outputs and private media out of Git.

## Deploy standing rule

This checkout is the production RealityOS host. Always deploy server-side
changes without being asked: build a local `realityos-backend:<name>` image,
apply migrations, restart api/worker with a
`.runtime/<name>-release.json` overlay (keeping a rollback JSON to the previous
image), preserve the gateway runtime, then verify `/health/ready`, the OpenAPI
contract and the Alembic version. Report the result and the rollback path.
Docker commands need in-session user approval; request it as part of the
deploy. Frontend/display rebuilds follow the CI path unless asked otherwise.
Owner storage correction (2026-10-29): do not dump PostgreSQL for ordinary code
or UI releases. Only a schema/data migration requiring reversal may create a
technical `pre-*.dump` snapshot in `.runtime/`; it expires after 24 hours (one
hour under disk pressure), not an official backup. Never send these to R2.
Official code/database backups belong in the owner's approved private GitHub
destination; R2 is reserved for project media. Use the server maintenance to
retire unused build images and working containers after deployment.
Rebuild the Debug APK without being asked whenever Android code or its server
contract changes; never leave the app behind to save a build.
Keep the installable Debug artifact at
`android/app/build/outputs/apk/debug/app-debug.apk`, replacing it on each build.
Do not create extra APK copies named after versions, dates or individual fixes.

## Validation

- Add tests with changes and cover permission and workspace isolation.
- Do not claim an Android build, device test, live Meta request, Docker run or
  PR unless it has actually run in the applicable environment.
- Validate gateway route allowlisting, token rejection and multipart forwarding
  before changing gateway deployment behavior.
- Update `docs/IMPLEMENTATION_STATUS.md` for incomplete external integrations.

# RealityOS agent conventions

Start with `docs/es/project/PROJECT_CONTEXT.md` for the repo map and current state, then
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
- Android is the only app; phone and native Wearables code live in `android/`.
  Keep email action pages in the backend. Browser panel and web Display are retired.
- Keep the restricted Meta egress service in `meta-gateway/`; it must remain an
  allowlisted gateway, never a general-purpose proxy.
- Store evaluation fixtures only in `simulator/`; licensed stock media must include
  source/license/hash manifests. Never commit credentials or customer media.
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
  token and ElevenLabs API key are independent. `.env` selects the connection.
- Production synthesis uses ElevenLabs only on authenticated audio requests.
  Muse Voice Transcribe remains Meta STT. No local synthesis model is supported,
  including Windows; do not reintroduce Seamless, its weights or build jobs.
- Mock outputs are deterministic and visibly labelled simulated.
- Confirm current official Meta endpoint/SDK signatures before coding Live.

## Local evaluation is primary (owner correction, 2026-11-03)

The approved local plan supersedes earlier server-first and empty-Windows rules.
Windows and Linux x64 use four isolated Docker services: PostgreSQL, Redis, the
existing API and worker. No scheduler, proxy, gateway, buckets, remote imports,
Facebook login or ElevenLabs in the local runtime. Meta model calls remain real
and direct, using the judge's private `MODEL_API_KEY`. Android uses installed
offline device voices. Do not add a synthesis model server.

Initialize only the existing three scenarios from public simulator fixtures,
once, preserving edits and deletions on restart. Do not create retired groups,
new media, biometric enrollments or consent. Local Debug uses the nine-account
selector, independently restricted by the backend's local realm. Protected
biometric search retains its permission and consent requirements.

The primary Postman download retains Localhost requests and Server requests.
Localhost contains the prepared scenarios and uses account selection without
passwords; Server requests is disabled and contains no active URL or credentials.
Earlier authorization to publish test passwords no longer applies to new exports.
Do not reuse production credentials, download production data or alter remote
hosts during local preparation. Automatic production deployment is disabled.

## Git delivery

Owner preference (2026-11-01): commit and push project changes directly to
`main`. Do not create feature branches or draft PRs unless the owner explicitly
requests them. Run the relevant checks before pushing; `main` triggers CI; remote deployment requires a separate explicit opt-in. Keep credentials, runtime files, build
outputs and private media out of Git, except the installable Debug APK below.

Owner correction (2026-11-04): include
`android/app/build/outputs/apk/debug/app-debug.apk` in the repository through
Git LFS so clone/pull retrieves the APK. Keep this canonical file tracked and
update it after required Android builds, using the same server signing key.
Keep the README download, pull, install and launch commands current. Releases
may also carry the APK; they do not replace delivery in the repository.

## Deploy standing rule

This checkout is the production RealityOS host. The local evaluation work does
not authorize deploying or stopping its production services. For separately
authorized production work only, deploy server-side
changes without being asked: build a local `realityos-backend:<name>` image,
apply migrations, restart api/worker with a
`.runtime/<name>-release.json` overlay (keeping a rollback JSON to the previous
image), preserve the gateway runtime, then verify `/health/ready`, the OpenAPI
contract and the Alembic version. Report the result and the rollback path.
Docker commands need in-session user approval; request it as part of the
deploy. The browser panel and web Display are retired; do not redeploy their services.
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

- Standing owner preference (2026-11-03): every screen, view and component must
  follow the app's established UI/UX without needing another reminder. Before
  changing UI, compare adjacent screens and reuse their theme tokens, typography,
  spacing, shapes, icons, navigation and controls. Read `docs/es/architecture/UI_DESIGN.md`;
  do not ship a separate visual language or an unstructured stack of default controls.
  Review rendered states in ES/EN, narrow widths and 200% text before delivery,
  and state explicitly when visual/device validation could not be performed.
- Add tests with changes and cover permission and workspace isolation.
- Do not claim an Android build, device test, live Meta request, Docker run or
  PR unless it has actually run in the applicable environment.
- Validate gateway route allowlisting, token rejection and multipart forwarding
  before changing gateway deployment behavior.
- Update `docs/en/project/IMPLEMENTATION_STATUS.md` for incomplete external integrations.

## Owner correction: workspace publication and private enrollment (2026-11-03)

Publications require an existing work group; there is no private publication
choice. Owners can import their publications into additional groups, with separate
comments/reactions and shared original bytes. Owner correction for the unified gallery (2026-11-03): delete legacy unassigned
and former personal/public publications; preserve valid group copies and any
media still referenced by groups, account profiles, records or biometric data.
There is one main group gallery, not a separate profile publication feed.

The owner explicitly requested email-account biometric onboarding: consent,
profile image and 3–25 distinct accepted reference photos. Keep references and
Meta imports private, outside publications, generic media and result thumbnails;
only the separate avatar can be displayed. Preserve the isolated local Debug
exception. The new `backend/app/face_setup.py` belongs to the protected biometric
arm alongside `faces.py`; changes remain explicitly authorized only.

Changing/disconnecting a bucket retires its proven imported copies and group
copies; it never deletes external objects. Validate a changed source before
committing it. Credential-only rotation keeps existing copies. Synchronize the
selected folder every 15 minutes and prune missing objects only after a complete
successful scan. Keep immutable provenance for superseded upload attempts.

Owner correction (2026-11-03): only the existing groups are in scope. Workshop and other retired groups were discarded and removed; never recreate their groups, memberships or publications during demo refresh.

Owner correction (2026-11-03): prepared account/group/record/publication copy must
use natural operational descriptions without `[Demo]`, simulated, fictional or
test-data labels. Preserve internal provenance, licensing, mock-provider flags,
credentials, consent and immutable history. Do not reintroduce these labels in
fixture-generated captions or the stored-content UI.

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

Owner correction (2026-11-04): perform development, data changes and validation
locally. Access the server only to generate the APK in an isolated build directory,
using its existing signing key. Do not change server data, deploy backend changes,
restart services or modify its runtime. This rule persists for future changes and
supersedes the earlier server-first workflow unless the owner explicitly authorizes
separate production work.
The existing local APK connection details are recorded in the ignored
`.runtime/apk-build-connection.json`; consult it before asking for access details.

The local evaluation work does
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

## Owner correction: local account groups (2026-11-04)

The local account chooser starts with all work groups collapsed. California Valley
Medical Center is retired locally, including its publications, records and exclusive
media. Meta Social Media replaces it as an empty group with the same Elena Marquez,
Mateo Rios and Sarah Chen accounts, profile fields and avatars. Do not recreate
the hospital or seed content into Meta Social Media. Keep Police and Memory intact.

Later owner correction (2026-11-04): replace Police's previous publications,
records and exclusive media with ten fictional person records and one supplied
portrait each. Three have judicial arrest warrants; two of those three also have
active proceedings; the other seven have no criminal history, warrants or
proceedings. The owner confirmed the portraits depict fictional characters.
Preserve Police's three access accounts and their avatars. Source portraits are in
`simulator/media/police/portraits/`; provenance and hashes are in
`simulator/media/manifest.csv`.
Keep this as record data, with internal simulation metadata. Do not restore
the former Police scenes.

Latest owner correction (2026-11-04): the ten Police case portraits and their
case information must also be group publications, linked to the existing records.
Meta Social Media has ten synthetic searchable profiles with three private
references each, plus one ordinary image-and-text publication for each of its
three access accounts. Use their separate avatars for these introductions;
never publish biometric references. This supersedes the earlier empty-gallery
and record-only instructions. Initialize these additions once and preserve edits,
deletions, memberships and existing consent gates. Do not modify biometric code.

## Owner correction: modular architecture and database authority (2026-11-04)

All application records, including the local account selector, come from PostgreSQL.
Do not add business-record JSON catalogs or replace them with embedded Python/Kotlin
lists or YAML/CSV catalogs. SQL in `simulator/database/` is installation-only; use
one transactional initializer and durable receipts. Existing edits, deletions,
memberships and consent revocations must survive restarts. All current groups use
one shared publication schema and loader; private social references remain isolated.

Keep original local test images/videos organized under `simulator/media/`, with
source/license/hash provenance in `manifest.csv`. The technical inventory is not
an application query source. Do not recreate retired groups from historical media.

Use one shared modular backend and explicit local/server compositions. Localhost
means the owner's/judge's PC; this connected host is the RealityOS server; FRONTEND
is the separate restricted Meta gateway host. Server images exclude simulator data.
Do not deploy or change server data/runtime as part of repository refactoring.

Keep HTTP adapters separate from services and database queries; keep Android
presentation separate from repositories and transport. Reuse existing UI components
and contracts. Remove replaced loaders, dead code and unused dependencies after
checking consumers, migrations and tests. Historical migrations and protected
biometric interfaces are retained. Run architecture dependency checks in addition
to source-size checks.

The owner explicitly authorized orchestration with multiple agents for this
refactoring. Coordinate ownership of files and integrate verification before delivery.

## Owner correction: group video publications (2026-11-04)

Add the requested Pexels videos as ordinary local group publications: Police uses
25757454, 29401365 and 30614848; Meta Social Media uses 33802407, 12557513 and
3699519. Preserve the existing case publications, account introductions and Memory.
Keep originals under `simulator/media/{police,meta-social}/videos/` with technical
source/license/hash provenance. Apply the additive SQL revision once through the
shared initializer; preserve later edits, deletions and memberships. These videos
do not create person records, biometric enrollment or precomputed recognition claims.

## Owner correction: additional Police records (2026-11-04)

Preserve portraits `person-11.png` through `person-16.png` supplied by the owner
under `simulator/media/police/portraits/`. Add each as a local scenario
person record with a linked group publication, using the shared SQL initializer.
Records 11 and 12 have active arrest warrants, without added convictions or active
proceedings. Records 13, 14, 15 and 16 are reported missing and have active search
orders, without arrest warrants or criminal history. Keep missing-person search orders distinct
from arrest warrants in structured data and ES/EN presentation.

The original ten cases remain intact: Police now has sixteen person records,
five arrest warrants, two active proceedings, four missing-person search orders,
and nineteen publications including the three park videos. Preserve existing edits
and deletions.

## Owner correction: retire Memory and extend Meta profiles (2026-11-04)

Only Police and Meta Social Media remain in local evaluation: two groups and six
access accounts. Retire Sonoran Neurological Institute/Memory, its local users,
records, publications, exclusive media and obsolete clinical UI/API. Do not recreate
them from initial SQL or historical resources. Preserve shared record CRUD,
relationships, search, media, permissions and protected biometric code. Keep
historical Alembic migrations. The retirement is local and versioned; it does not
authorize production data changes or deployment.

Meta Social Media now has thirteen additional synthetic profiles, including
Gabriel Herrera, Adrián Navarro and Paula Méndez. Each uses one separate avatar
and three private reference photos; they are not selector accounts or group
publications. Existing profiles, edits, deletions and consent gates remain intact.

Keep the README presentation of Nursing and Memory as conceptual examples at the
end, stating that the platform can also serve those two cases and many more.
Preserve their conceptual `demo-video/nurse_case.mp4`, `demo-video/memory.mp4`
and README thumbnails. This correction supersedes earlier instructions to retain
the installed Memory scenario and the previous nine-account/three-group scope.

## Owner correction: launcher icon (2026-11-04)

Use the owner's `icon_150` image as the app icon, moved into
`android/app/src/main/res/drawable-nodpi/icon_app.png`; remove the loose root copy.
Apply `#017df7` only to `launcher_background`. Keep the existing colors and theme
tokens inside app screens, components and buttons. Rebuild and deliver the
canonical signed APK.

## Owner correction: splash branding (2026-11-04)

Use the owner's `logo_splash.png` for the native Android splash, rehomed as
`android/app/src/main/res/drawable-nodpi/splash_logo.png`. Show
`REALITYOS BY JOSE MARIN` below it. Preserve the current dark splash background,
the separate launcher icon and the internal UI theme. Keep the supplied PNG
unchanged and remove its temporary root copy after rehoming.

The splash logo must retain its complete original shape and aspect ratio, with
no rounded treatment or crop. Keep sufficient transparent padding so the native
Android splash mask cannot cut any visible part of the supplied logo.

The internal app logo also uses `icon_app.png`, displayed with a fully circular
crop through one shared component. Apply it to entry/account headers and the app
drawer. Keep the separate splash logo and the existing screen/button colors.

## Owner correction: publication filters and classification (2026-11-04)

Publication filters apply immediately after each valid category, tag, author,
date or text change. Keep the menu open; remove Apply and place the Clear text
button in the title row. Clear resets the filters immediately. Invalid date
intervals keep the last valid result and show an inline error. Discard obsolete
responses and pagination when filters or the selected group change.

Latest owner approval: classification follows the use case, not scene topics
such as spring, winter, weather, parks, walking or cycling. The exact bilingual
catalog is documented in `docs/es/guides/PUBLICATION_CLASSIFICATION.md`.

Police has four categories: active arrest warrants, missing persons, no warrants
or criminal history, and audiovisual material. Its seven tags are active arrest
warrant, no recorded criminal history, active judicial proceedings, no active
proceedings, active search order, no active arrest warrants, and observation video.
Apply judicial tags only from the person record; videos receive no judicial status.

Meta has two categories: introductions and social content. Its four tags are
personal introduction, community, video and everyday life. Private profiles and
references remain outside publications. Do not add unrelated descriptive tags.

Apply this through the shared versioned SQL initializer, replacing obsolete
prepared associations while preserving manual classifications, deletions,
memberships and private references. This does not authorize changes to production
data or biometric code.

## Owner correction: Police biometric enrollment (2026-11-04)

The owner removed the no-automatic-biometric-enrollment restriction for Police
cases: biometric search must identify the sixteen fictional case portraits, so
each linked portrait is enrolled as a record biometric reference through the
versioned local initializer with a traceable owner-ordered basis. The owner
confirmed the portraits depict fictional characters. Search-time consent gates,
the consent exception rules and the isolated biometric arm stay unchanged, and
Meta private references remain outside publications. The 1:N match threshold is
0.6, validated by measured same-user (min 0.751) vs cross-user (max 0.564)
separation on the installed gallery. This supersedes the earlier
no-automatic-enrollment clauses for Police records.

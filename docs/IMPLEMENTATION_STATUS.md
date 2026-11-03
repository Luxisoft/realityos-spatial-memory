# Implementation status — 2026-10-28

## Verified in this workspace

- Device credential, device-session capture, key rotation/revocation, device
  workspace isolation, marketing facts, analytics and detailed Mock video-track
  coverage were added. The current local suite has 37 passing tests.
- The frontend production build passed after adding the administrator-only
  Device Registry and Inventory Intelligence views.

- Backend and gateway lint passed: ruff check backend tests meta-gateway
  gateway-tests.
- Thirty-seven automated tests passed locally: application tests cover
  health/auth, BYTEA capture/retrieval/hash, mock processing and SAM geometry,
  highlighted evidence, missing-object and ambiguous-query handling, role
  restriction, workspace/device isolation, aliases, evidence facts and detailed
  Mock video tracks; gateway and mocked Live transport tests cover multipart
  Files upload/delete, route restrictions and uncertain-provider handling.
- Admin-panel and Display production builds passed.
- Docker Engine and Compose were installed on the target server. PostgreSQL,
  Redis, API, Celery, panel, Display and Nginx are currently running.
- Alembic completed against PostgreSQL 16. An authenticated proxy query returned
  a highlighted BYTEA-backed observation, and a new capture completed through
  Redis/Celery in Mock mode.
- A dedicated Meta egress gateway is implemented, including route allowlisting,
  independent gateway authentication, Meta-key injection, multipart forwarding,
  Docker image and GitHub deployment workflow. Gateway and backend tests pass
  locally, and the gateway Docker image builds successfully.
- GitHub Actions CI completed successfully for the published gateway branch:
  backend, web/Display and gateway jobs passed.
- Commit `88503d5` adds a live-only virtual-device bootstrap route for the
  Android virtual-glasses workflow. It creates a real, short-lived,
  workspace-scoped device credential at runtime; no Model API key or device
  credential is embedded in the APK. The redesigned Android app was compiled
  locally in Debug and Release forms, linted, and its instrumented test source
  compiled. The complete CI run
  [40577511588](https://github.com/Luxisoft/realityos-spatial-memory/actions/runs/40577511588)
  passed backend, gateway, web and Android jobs.
- The Android host experience now has an English-first, persistent welcome
  prelude; a Spanish language option; the active LUXISOFT favicon as launcher
  and system-splash icon; a transparent in-app LUXISOFT mark; and an
  icon-only, safe-area-aware bottom action rail. The main stage is an immersive
  Meta Display canvas: both drawers use their respective horizontal edge
  swipes, while the right diagnostic panel retains normal vertical scrolling
  and the bottom action rail remains available. On 2026-10-28,
  `:app:compileDebugKotlin :app:compileReleaseKotlin :app:testDebugUnitTest`
  completed locally; handset visual review and instrumented execution remain
  pending because this server has no attached emulator or device.
- Successful CI runs now retain the installable Debug APK for 14 days as the
  `realityos-android-debug-apk` artifact. This is not a signed production APK.
- Commit `24702e5` fixes PostgreSQL enum persistence for device status and
  inventory fact provenance, and adds revision `20261027_0007` for the
  existing `JobStatus.UNCERTAIN` contract. `make lint` and `make test` passed
  with 37 tests locally. CI
  [40579548167](https://github.com/Luxisoft/realityos-spatial-memory/actions/runs/40579548167)
  passed backend, gateway, web and Android jobs and published the Debug APK.
- The second Alembic migration was applied to production PostgreSQL. It enables
  PostgreSQL `pg_trgm` and creates workspace-scoped trigram and FTS indexes for
  object names and aliases. Search uses those indexes on PostgreSQL and a
  bounded SQLite fallback in tests.
- Alembic revisions `20261027_0005` and `20261027_0006` are applied in
  production. The `devices`, `device_assignments`, `object_facts`,
  `object_tracks` and `object_track_frames` relations were checked directly;
  API `/health/ready` and the Celery worker were healthy after deployment of
  commit `c8ad030`.
- The synthetic production seed was rerun and now contains six legally-created
  workshop objects and the `Bodega A → Estantería 3 → Nivel 2` hierarchy.
- The administrative panel now has an authorized object catalog (name/alias,
  category and location filters), object observation history, and a location
  hierarchy. The map explicitly is not metric or 3D.

## Production verification

- Pull request #1 was merged into `main`. The successful production workflow
  [40434117386](https://github.com/Luxisoft/realityos-spatial-memory/actions/runs/40434117386)
  verified code, built immutable GHCR backend/gateway images, deployed the
  gateway, then deployed API and Celery worker.
- FRONTEND runs the restricted gateway behind `https://meta.luxisoft.com` with
  a Let's Encrypt certificate, Cloudflare original-client-IP handling, an IP
  allowlist and independent gateway-token authentication.
- The gateway's real `GET /v1/models` request returned the enabled Meta catalog,
  including `muse-spark-1.3`, `sam-3.1` and `muse-voice-transcribe-1.0`.
- RealityOS API and worker are healthy and run in `META_MODE=live` with the
  gateway URL configured. At that initial deployment, the Meta key was kept only
  in FRONTEND. Superseded by the direct connection deployment below (2026-11-01).
- Subsequent production deployments for indexed retrieval and the expanded demo
  seed completed successfully in workflow runs
  [40435541580](https://github.com/Luxisoft/realityos-spatial-memory/actions/runs/40435541580)
  and
  [40436600135](https://github.com/Luxisoft/realityos-spatial-memory/actions/runs/40436600135).
- Commit `e920362` added and deployed the object explorer, hierarchy map and
  frontend/display rebuild step. Workflow
  [40438080792](https://github.com/Luxisoft/realityos-spatial-memory/actions/runs/40438080792)
  completed successfully; direct checks confirmed all seven Compose services
  running, `/health/live`, `/health/ready`, and the published panel bundle
  containing the explorer.
- Private, consent-gated manual-photo staging is stored under the deployed
  project's Git-ignored `.runtime/manual-captures/incoming/` directory; it is
  not committed or made public.

## Public deployment verification

- `realityos.luxisoft.com` now resolves directly to the RealityOS server and
  has a valid Let's Encrypt certificate through 2027-01-25. Public HTTPS
  checks for `/health/ready` pass.
- The production API and worker run migration `20261027_0007`. A public
  `POST /v1/virtual-devices/bootstrap` issued a live, time-limited device
  profile for `Taller de electrónica`; its device credential successfully
  accessed the workspace-scoped zones endpoint. Credential values were not
  logged or committed.
- The initial certificate workflow run issued the certificate successfully but
  reported failure because it checked TLS during Nginx's graceful-reload
  handover. The deployment workflow now retries that local SNI readiness check.
- The corrected production workflow
  [40582206272](https://github.com/Luxisoft/realityos-spatial-memory/actions/runs/40582206272)
  completed successfully: gateway, API, worker, frontend, Display proxy and
  the HTTPS readiness check all passed.
- The production workflow now also verifies the API OpenAPI contract includes
  the device-scoped processing-status route before publishing a release. This
  prevents an Android client that uploads successfully from polling a backend
  image that lacks its matching job endpoint.

## Implemented and production-deployed; device QA remains

- Profile/media unification is implemented and production-deployed: Android now defaults to a
  three-action **Perfil / Trabajo / Buscar** rail, removes Global and the
  duplicate drawer Gallery, and automatically pages the account gallery.
  Facebook inventory is bounded to the newest 25 uploaded photos and 5 videos
  (avatar separate), with availability diagnostics rather than silent empty
  results. Migration `20261028_0015` adds idempotent publication provenance,
  profile avatars and cursor indexes; profile AI search can return only media
  authorized to the caller. A reproducible 20-profile directory uses 10
  Muse-anchored scenes per profile (identity similarity 0.51–0.88, one face
  each, unique bytes) but runs through the real BYTEA import and configured
  InsightFace enrolment path; no synthetic videos ship. Production uses image
  `realityos-backend:workshop20-20261028` at Alembic `20261028_0015`.
  The seeded directory has exactly 20 profiles, 200 photo inventory rows,
  200 public publications and 20 work publications; the "Mechanic Workshop"
  group holds 5 members across day/night shifts with 15 same-shop takes plus
  the original 546 MB shop video. `/gallery/{post_id}/media` serves HTTP
  Range (206/416) for inline and chunked BYTEA. Authenticated production
  checks verified cross-chunk ranges, outsider 403, instant video thumbnails,
  a 16-post work feed and 10-item cursor pagination without duplicates.
  Five slots per directory profile are group takes with 10 profile-less
  companions (16 appearances each, owner sim ≥ 0.52, companion sim ≥ 0.60);
  live 1:N probes of companion faces match 12–16 third-party profiles, and a
  committed mock-engine test guards the cross-profile rule. 380 directory
  enrollments, all `insightface-buffalo_l`.
  All 82 backend/gateway tests and Android compile/unit/lint/assembly pass;
  the APK SHA-256 is
  `664dd7c42743790f82c7e1b60047b07c7e71c77959de765cde9ff54087a4f595`.
  Backup: `.runtime/pre-workshop20-20261029T042307Z.dump`; rollback:
  `.runtime/workshop20-rollback.json`. Handset visual QA remains pending.

- Unified Android navigation and public profiles are implemented and the
  matching backend contract is deployed:
  one contextual bottom bar replaces the duplicate gallery/host bars; the
  left drawer owns the only horizontal edge gesture; Meta Ray-Ban Display has
  Preview/Glasses/Controls actions; About replays onboarding; and the empty
  gallery state is centered. Migration `20261028_0014` adds public profiles,
  Graph-returned friend avatars and one private, replaceable PDF/DOCX CV per
  user. Natural-language profile questions may use the private extracted
  context without returning or persisting it, and image object queries remain
  ephemeral. Backend/gateway lint and all 79 automated tests pass locally;
  Android compile passes. `:app:lintDebug`, `:app:testDebugUnitTest` and
  `:app:assembleDebug` pass locally; the generated APK SHA-256 is
  `3ebe61a0c2b60f98f8a8caa1f3f111a20034dc52d17b52aba24ff3c336202de3`.
  Production API/worker use `realityos-backend:profile-nav-20261028`; Alembic
  reports `20261028_0014`, public readiness is healthy, the six new OpenAPI
  paths are present, unauthenticated profile access returns 401, the Celery
  worker responds to ping and `FACE_ENGINE=insightface` remains active. The
  pre-deploy dump is `.runtime/pre-profile-nav-20261028T221004Z.dump` and the
  image rollback overlay is `.runtime/profile-nav-rollback.json`. Handset
  visual QA remains pending.

- Live face enforcement is deployed: the backend image now ships InsightFace
  buffalo_l (baked weights, CPU) behind `FACE_ENGINE=insightface` via
  `.runtime/faces-live.json`, with passive anti-spoof heuristics v1 enforced
  on capture uploads. The 46 mock enrollments were reset so the next login
  re-imports with live 512-d embeddings; image
  `realityos-backend:live-20261028` is active (rollback
  `.runtime/live-rollback.json` without the live overlay) and the engine was
  verified in-container (loads, blank image yields zero faces). Real-face
  accuracy and threshold tuning await the next handset login + capture; a
  trained presentation-attack model and video liveness remain future work.
- Identity verification and scoped imports are implemented (migrations
  `20261028_0012`/`0013`): login syncs the last 30 photos plus the current
  profile picture, the last 10 videos and the last 50 posts (raw material for
  future profiling). The selfie is retaken on every fresh login
  (`capture-profile` clears it, so verification can only run on a new photo);
  resumed sessions silently re-verify the stored capture against the account
  Facebook faces. On mismatch the user stays in place: the capture view shows
  an informative error with the remaining attempts and offers a direct retake
  (the stale selfie is wiped on scored mismatches; unscored denials keep it).
  After 5 failures the account locks for 30 minutes (`face_max_attempts` /
  `face_lockout_minutes`); a success resets the chain. Attempts are audited in
  `face_verifications`. With the mock engine the check passes as simulated:
  real enforcement needs the live face engine. The identity threshold was
  tuned 0.6 -> 0.5 from live genuine scores (0.52/0.59 with hair/age variation
  vs 0.29 for a rotated capture), matching the search operating point. Image
  `realityos-backend:lockoutfix-20261028` is deployed with Alembic at `0013`
  (rollback `.runtime/lockoutfix-rollback.json`) and the Debug APK gates entry
  on capture + verification.
- Staged face search is implemented (migration `20261028_0011` backfills
  `facebook` enrollments into `facebook-photo`/`facebook-video`): stage 1 face
  captures, stage 2 Facebook photos, stage 3 videos, first non-empty stage
  wins, matches typed `direct`/`possible_acquaintance`. First login now
  requires a private face capture (Android gate + `face_capture_done` flag).
  Image `realityos-backend:stages-20261028` is deployed with Alembic at `0011`
  (rollback `.runtime/stages-rollback.json`); the 46 production enrollments
  backfilled to `facebook-photo` and the Debug APK includes capture/badges UI.
- Facebook profile sync and media import are implemented (`facebook_profiles`,
  `facebook_media`, migration `20261028_0010`, worker task
  `realityos.import_facebook_media`, `GET /v1/me/facebook-profile`). Login
  syncs profile fields, counts, granted scopes and photo/video inventory;
  bytes import into BYTEA (origin `facebook-import`) with face enrollments,
  and face matches now include the candidate picture and profile link. Image
  `realityos-backend:fbprofile-20261028` is deployed with Alembic at `0010`
  (rollback `.runtime/fbprofile-rollback.json`). A fresh login is required to
  trigger the first sync; likes/posts content beyond counts stays out of scope.
- Consent-gated 1:N face search is implemented as an isolated, protected arm
  (`backend/app/faces.py`, migration `20261028_0009`, `/v1/faces/*`,
  `tests/test_faces.py`; see AGENTS.md). Enrollment accepts caller-owned media
  or a profile photo; search is read-only with an ephemeral probe or stored
  media, scoped to consenting workspace members and ranked by similarity. The
  mock engine is deterministic and labelled simulated; the provisional local
  engine (`faces` extra) is unverified live. Locally `make lint` and `make
  test` pass (51 tests) and `:app:testDebugUnitTest :app:assembleDebug`
  succeeded with the new consent/search UI. On 2026-10-28 the local image
  `realityos-backend:faces-20261028` was built and activated for api/worker via
  `.runtime/faces-release.json` (rollback: `.runtime/faces-rollback.json`,
  backup `.runtime/pre-faces-deploy-20261028.dump`); Alembic is at
  `20261028_0009`, `/health/ready` and public HTTPS return 200, OpenAPI
  exposes the faces routes, and one Celery node is online. Handset testing of
  face enroll/search and the live engine remain pending; the image is local,
  not a GitHub-published release.
- Facebook-only Android entry and the social gallery are under integration.
  The user subsequently supplied a replacement standard-login Meta app,
  `1465393708894529`. Android 0.1.2 (version code 3) and the deployed API now
  use that App ID. Private credentials remain in ignored, mode-0600 files.
  Graph accepted the app credential, returned the expected App ID and the
  exact registered Debug certificate hash. No inference about completed Login
  setup is made from the permissions-list edge. The APK manifest was checked
  for the new App ID, and prior Android sessions are cleared when App ID changes.
  Backend identities now include App ID in their subject key so changing Meta
  apps cannot accidentally merge app-scoped Facebook identities. This is covered
  by a provider-mocked regression test; the full suite passes (42 tests).
  API/worker run `realityos-backend:facebook-consumer-20261028`, using the private
  `.runtime/consumer-release.json` overlay on the existing runtime configuration.
  Deployed credentials were verified against Graph; public readiness is healthy.
  Android compilation, unit tests, lint and Debug assembly passed. Real account
  consent and handset login remain unverified; no replacement user login token
  was provided or fabricated. The paragraphs below retain the earlier incident
  history for the previous Meta app and do not describe current credentials.
  A subsequent Graph API read confirmed that the certificate hash is now
  correct, and `public_profile` / `email` both report `live`. The reported
  "at least one supported permission" dialog is a separate provider failure.
  Android 0.1.1 (version code 2) now requests both enabled read scopes rather
  than public_profile alone. This is a targeted login-request adjustment, not
  a confirmed handset fix; email remains optional to RealityOS identity and
  no email field is required or used to link accounts. On 2026-10-28 the
  dashboard enabled 13 read scopes (profile, email, age range, birthday,
  friends, gender, hometown, likes, link, location, photos, posts, videos);
  the Debug APK requests all of them, the prior "Jose Marin" test account was
  deleted from production (backup `.runtime/pre-face-account-delete-20261028.dump`)
  for a fresh re-registration, and `/v1/auth/facebook` now echoes
  `granted_scopes` from `debug_token` for verification. A provider app/product
  configuration mismatch remains possible until the real login is tested.
  The 2026-10-28 handset report identified an exact native login failure:
  Meta's configured certificate hash used `MwLS`, whereas the signed Debug APK
  requires `MWLS`. The verified APK hash is `4tPwlnClMWLS08TeIYlcOA3r+Y4=`.
  This provider-side correction must be saved in the Meta app dashboard; changing
  the selected Android store does not correct a certificate hash mismatch.
  The bare login/gallery gate was replaced with an access screen reusing the
  existing welcome typography, spacing and MemoryTrace illustration. Welcome
  remains available, navigation has a visible menu button in the gallery, and
  sign-out is in the account menu. No new full-app redesign is intended.
  The new backend migration `20261028_0008` adds Facebook identity mapping,
  private/public/work publications, likes, threaded comments, reports and
  single-use group invitations. New user-owned captures are listed privately;
  historical device captures are not assigned to a new Facebook identity.
  Android has a three-column gallery, blue accents, explicit sharing, group
  creation/joining and voice navigation/query. Camera navigation and a timed
  retry/return surface were restored after the reported empty-lens regression.
  Backend `FACEBOOK_APP_ID` / `FACEBOOK_APP_SECRET` and Android local properties
  `facebook_app_id` / `facebook_client_token`, signing hashes and provider
  configuration are required for a real login. No handset Facebook login or
  camera verification has been performed. Facebook app
  settings now use ignored local files. Android stores sessions encrypted and
  renews them with rotated refresh tokens; logout revokes server refresh tokens.
  Group member management, report review/hiding, image/video thumbnails and
  voice action preparation with explicit confirmation are implemented. Personal
  evidence queries use the private capture workspace; Public/Work voice searches
  match accessible publication captions. Global moderation requires an explicit
  `SOCIAL_MODERATOR_FACEBOOK_IDS` allowlist; workspace administrators manage
  reports and members only in their own groups.
  On 2026-10-28 the backend image `realityos-backend:social-20261028` was built
  locally and activated for API/worker, preserving the existing gateway runtime.
  A PostgreSQL backup and private release/rollback files exist under `.runtime/`.
  Migration `20261028_0008` passed against temporary PostgreSQL 16 and is applied
  on the deployed API. Public readiness returns 200; unauthenticated gallery
  access returns 401; all Android API routes are present. Facebook app credentials
  were checked against Graph API with HTTP 200 and matching App ID, without a
  user login. Backend checks pass (41 tests), as do Android Debug/Release compile,
  unit tests, lint and Debug assembly. Device visual QA and Facebook account
  login remain the final external checks. The deployed image is local, not a
  GitHub-published release; a later CI deployment must include these source changes.

- Live SAM Video Files API upload, streaming parser, RLE persistence and cleanup
  are implemented against the reviewed official contract but have not sent a
  paid production video request in this workspace. An ambiguous live provider
  result is stored as `uncertain`, never claimed as success.

- Live Muse Spark, SAM and ASR clients match reviewed contracts. The production
  gateway is verified against the real Meta model catalog from FRONTEND. Paid
  image analysis and SAM segmentation ran on consented server-local test images:
  two jobs completed and one received a transient Meta 503. SAM box parsing
  boxes ran on consented server-local test images. The code now implements
  binary one-bit SAM-mask decoding/persistence through the official Python
  parser; this new mask path remains pending an end-to-end paid SAM stream
  verification.

- A native Android DAT 1.0.1 host now compiles into Debug and Release. It
  initializes DAT after Bluetooth consent, provides encrypted device
  provisioning, opens a Display session and renders Register/Query screens.
  The Debug/mock route uses the phone's CameraX camera, microphone and Android
  speech recognizer; a physical Display route uses DAT camera, microphone and
  speech. Both routes keep capture explicit. Phone MP4 captures contain camera
  video plus microphone audio; the DAT recorder now accepts HEVC plus PCM and
  muxes AAC audio. Backend devices can poll only their own processing jobs, so
  the display shows processing instead of searching unready evidence. Physical
  hardware has not been installed or tested.

- The Debug Android variant now contains a Developer Preview based on Meta's
  Mock Device Kit. It pairs a virtual Display model, drives the same production
  RealityViewModel/session path, mounts Meta's in-app Display renderer, supports
  a Chrome preview server and excludes the Mock Device Kit from release. Before
  starting the mock it gives a detected physical Display priority; otherwise
  the mock's Display transport is paired with phone camera/microphone input.
  Its
  Debug-only phone shell uses a supplied panoramic Ray-Ban frame with the
  camera on the right, an alpha-traced lens aperture and a contained square
  Meta renderer. During explicit Register capture, the renderer and host
  chrome yield to a centered, inset 9:16 CameraX viewfinder; it stays
  transparent until CameraX reports a stream, then fades in. Native icon-only
  photo/video controls sit inside that card, and a successful capture closes
  the phone session automatically. The shared CameraX viewport aligns the
  preview crop with photo or video output. This is a phone Debug simulation,
  not a physical-optics claim or a stream sent to physical glasses.
  Debug and release compilation plus release-APK inspection have run locally.
  The controller's In-App renderer and Chrome preview-server tests passed in a
  GitHub-hosted Android 15 emulator on 2026-10-27 (three Mock Device Kit tests
  total); the eligibility regression test has compiled but has not run on a
  locally attached emulator or handset. The updated frame, aperture and
  panoramic composition still require attached-handset visual review.
  Interactive phone and desktop-Chrome extension validation remain pending; no
  physical glasses test is claimed.

- The revised first-run carousel, per-app language switch, adaptive launcher
  icon, system splash and phone layout have not yet been reviewed on a physical
  handset in this workspace. No emulator or Android device is currently
  attached to this server, so the new `RealityExperienceStoreTest` has compiled
  but has not run instrumented. Compilation verifies the native resources and
  code paths; it does not substitute for visual or accessibility QA on a device.

- The virtual-device bootstrap flow has unit coverage for live profile creation,
  key rotation and expiry, but it cannot be exercised from an Android phone
  until the public HTTPS hostname described above is corrected.

## 2026-10-30 — Gallery AI index

- Every gallery publication now gets one bounded worker pass at publish/import
  time (migration `20261030_0022`): Meta Muse labels every visible object and a
  local InsightFace pass counts faces (presence only, no identity lookup).
  Results land in `publications.ai_labels/ai_caption/face_count/search_text`.
- Query (`/v1/queries`), `/assistant` and `/profiles/search` match synonyms
  through the model over that index plus trigram similarity on PostgreSQL; the
  Query response carries a new `gallery_matches` list that is never presented
  as verified evidence. Only viewer-visible publications match (owner/public/
  member-work, guest rules preserved).
- Production runs `realityos-backend:gallery-index-20261030` at Alembic
  `20261030_0022`; all 243 existing publications were backfilled (242 photos +
  1 sampled video) and a live end-to-end check matched workshop labels.
  Rollback overlay: `.runtime/gallery-index-20261030-rollback.json`.
- Cost note: one Meta analysis call per photo, up to three per video (sampled
  frames), once per publication. Faces are counted locally at no model cost.
- Chat history now persists gallery matches and the simulated flag per turn
  (migration `20261030_0023`, image `realityos-backend:chat-gallery-20261030`):
  reloaded conversations render thumbnails and the SIMULADO badge exactly as
  on send. Rollback overlay: `.runtime/chat-gallery-20261030-rollback.json`.
- Chat turns also persist quick replies and the face action (migration
  `20261030_0024`, image `realityos-backend:chat-actions-20261030`); expired
  actions answer gracefully instead of staying dead. Audio playback moved to
  async prepare with error reset so the play button never sticks, and the
  typing indicator now reads "Buscando…". Gallery fallback failures are logged
  server-side. Rollback overlay:
  `.runtime/chat-actions-20261030-rollback.json`.
- Chat history merge is now idempotent by server id: the Buscar tab and the
  search sheet share one list and concurrent loads no longer duplicate bubbles.
  Gallery search gained near-match synonyms (`interpret_gallery_terms`,
  gallery-only), per-word terms, relevance ranking and request-filler
  stopwords; image `realityos-backend:gallery-filter-20261030` (no migration).
  Verified live: "buscar un alicate" returns the crimping-tool workshop photo
  first. Rollback overlay: `.runtime/gallery-filter-20261030-rollback.json`.
- Gallery matches now render unfilled boxes around the identified object
  (migration `20261030_0025`, image `realityos-backend:gallery-boxes-20261030`):
  the index stores per-detection boxes, `GET /v1/gallery/{id}/boxed` draws the
  matched ones over an ephemeral thumbnail (originals untouched, videos fall
  back to plain), and chat shows/persists the boxed URL. Textual matches now
  exclude trigram-only photos, so unrelated portraits no longer dilute tool
  searches. All 243 publications were re-indexed (238 with boxes, 5 with no
  detectable object). Rollback overlay:
  `.runtime/gallery-boxes-20261030-rollback.json`.
- Fixed chat phantom gaps (image `realityos-backend:chat-nullfix-20261030`, no
  migration): org.json `optString` leaked JSON null as the text `"null"`, so
  every reloaded bubble reserved a blank 160dp evidence slot. Android now
  parses nullables safely, the server sanitizes `"null"` chat URLs, and the 3
  contaminated history rows were cleaned. Rollback overlay:
  `.runtime/chat-nullfix-20261030-rollback.json`.
- TTS speaks naturally (image `realityos-backend:tts-natural-20261030`, no
  migration): gallery templates use real one/other plurals ("6 fotos
  coincidentes", never "foto(s)"), and the app normalizes parenthetical
  plurals before speaking so old turns sound right too. The TTS button is now
  the same circular play/stop control as voice notes, with real stop,
  completion tracking and single-audio focus. Rollback overlay:
  `.runtime/tts-natural-20261030-rollback.json`.

## Not implemented

- A full end-to-end Live SAM Video run against a user-provided long clip has
  not been performed. Server-side audio extraction/transcription from source
  video remains out of scope.
- Vector retrieval abstraction and optional vector database integration.
- Physical Meta Ray-Ban Display QA (camera, microphone, TTS route, Display
  rendering and recovery).
- Official browser Display simulator validation for the supplementary Web App.
- Restore test.

No claim of physical-glasses, real camera/microphone/audio behavior, or an
end-to-end paid visual inference is made. The official Android MockDeviceKit
instrumentation test did pass in an emulator; it is not equivalent to hardware
validation.


## Reorganización estructural — 2026-10-30

Backend separado en adaptadores HTTP, proveedores, procesamiento y módulos
sociales con interfaces compatibles; pruebas sociales agrupadas por función.
Android separa navegación, operaciones del host, presentación e historial de
chat y reproducción de audio. Web separa las pantallas principales y usa
Prettier. CI comprueba el límite de 999 líneas, formato y pruebas; las dos
excepciones biométricas permanecen protegidas.

Verificado: 119 pruebas Python, 62 pruebas unitarias Android, Ruff, ktlint,
lint Android, builds Debug/Release y ambas aplicaciones web. Pruebas
instrumentadas compiladas; no se ejecutaron pruebas físicas ni Meta Live.
API/worker desplegados como `realityos-backend:architecture-20261030`, salud,
OpenAPI y Alembic `20261030_0025` verificados. Rollback en
`.runtime/architecture-20261030-rollback.json`. La publicación web sigue CI.
Las integraciones externas pendientes descritas arriba permanecen pendientes.


## Búsqueda señalizada, revisión de subidas y carrusel — 2026-10-30

Implementado y desplegado `realityos-backend:search-evidence-20261030`, Alembic
`20261030_0026`: evidencia inmutable, filtrado por geometría y objeto solicitado,
deduplicación de resultados, comparación Meta de subidas con confirmación de
reemplazo, y retiro reversible de publicaciones repetidas dentro del mismo
dueño/destino. Se conservan BYTEA, comentarios, reacciones y permisos.

Android incorpora carrusel, miniaturas encima de notas, PTS de video en
HH:MM:SS y reproducción a pantalla completa desde tres segundos antes.
Comprobados Live: comparación de una foto idéntica, localización de 13 objetos
en una foto y de 13 objetos en un fotograma del video de taller; acceso HTTP
a evidencia señalizada de 1600 × 1600. Pasaron 141 pruebas Python/gateway y
71 pruebas Android, lint, formato y APK Debug. Falta QA táctil en teléfono.

En curso: reindexación serial reanudable de 238 publicaciones, task id en
`.runtime/search-evidence-20261030-task.json`. Consultar versiones/errores por
publicación; reanudar con `scripts/rebuild_search_evidence.py --apply` si el
worker se interrumpe. No lanzar tareas paralelas del mismo mantenimiento.
Rollback: `.runtime/search-evidence-20261030-rollback.json`; mantiene el esquema
aditivo y omite Alembic en el comando de arranque de la API anterior. Salud,
OpenAPI y runtime del gateway verificados. No se creó dump de PostgreSQL.


La revisión de cierre añadió cobertura de reemplazos simultáneos, cancelación
al borrar un grupo, revocación de membresía durante el análisis y recepción de
subidas sin esperar bloqueos del worker. La comparación vacía Live está corregida:
Meta puede devolver JSON null solo cuando no hay candidatos. Se reanudó la tarea
tras esa corrección; el identificador vigente está en el mismo archivo de runtime.
Validación final: 141 pruebas Python/gateway y 71 Android aprobadas. Los endpoints
legacy y los nuevos comparten la protección; el asistente social también exige
evidencia localizada para sus resultados visuales.


## Recuperación de imágenes y seguimiento del chat — 2026-10-30

Desplegado `realityos-backend:search-recovery-20261030` en API y worker; Alembic
permanece en `20261030_0026`, salud pública y OpenAPI comprobados. Las huellas
completas del entorno de cada servicio coinciden con las previas, incluido el
runtime del gateway. Rollback: `.runtime/search-recovery-20261030-rollback.json`,
aplicado como último overlay sobre la cadena anterior guardada en
`.runtime/search-recovery-20261030-before.json`. No hubo migración nueva ni dump.

Se restauró la relación exacta/familia/similar en la interpretación de galería,
se eliminó el corte prematuro de 1000 etiquetas y el vocabulario de búsqueda
se deriva de todas las detecciones localizadas y accesibles. «Me busques un
alicate» y «me ayudes a buscar un alicate» producen el mismo objetivo. Las
respuestas conservan la etiqueta real y añaden `match_kind` y
`localization_quality`, también en el historial y el carrusel Android. Los
estados de indexación, ausencia de coincidencias y error de búsqueda son
explícitos; un fallo del proveedor conserva los candidatos locales seguros y
advierte que la búsqueda quedó incompleta.

La reparación administrativa `scripts/rebuild_search_evidence.py --apply
--repair-legacy-images` creó 189 evidencias v1 inmutables con cajas previas
válidas, confianza suficiente y orientación conocida; omitió tres publicaciones,
sin modificar originales BYTEA ni marcar SAM como terminado. Query no ejecuta
reparaciones ni encola análisis. La tarea serial de SAM se reanudó con prioridad
para fotos del taller; identificador vigente en
`.runtime/search-recovery-20261030-task.json` y en el puntero histórico
`.runtime/search-evidence-20261030-task.json`. El reindexado completo sigue en
curso y aún hay publicaciones con errores que deben revisarse al finalizar.

Prueba real autenticada contra ambas frases españolas: HTTP 200, 3 resultados
sin medios repetidos, una crimpadora y un pelacables clasificados como familia,
y una prensa como similar. Las fotos abren señalizadas a 1920 × 1280 y sus
miniaturas a 360 × 240. Se inspeccionó visualmente el recuadro de la crimpadora.
Registro agregado privado en `.runtime/search-recovery-20261030-verification.json`.

Android desplaza al final ante envío y recepción explícitos; cargar historial o
actualizar IDs del servidor no fuerza el desplazamiento. El seguimiento de
teclado y tamaño de imagen se pausa con el arrastre manual y se reanuda al
regresar al final o con un turno nuevo. Pasaron 156 pruebas Python/gateway,
74 pruebas Android, ruff, control de estructura, ktlint, lint Debug y APK Debug.
No se ejecutaron pruebas táctiles en dispositivo; quedan pendientes.


## Información visible y localizada del recurso del chat — 2026-10-30

Desplegado `realityos-backend:evidence-info-20261030` en API y worker; Alembic
sigue en `20261030_0026`. Salud pública y OpenAPI coincidente con la instantánea
comprobados. Las huellas completas del entorno de API/worker coinciden con las
anteriores, conservando gateway y secretos. Rollback en
`.runtime/evidence-info-20261030-rollback.json`, aplicado como último overlay
sobre la cadena guardada en `.runtime/evidence-info-20261030-before.json`.
Sin migraciones nuevas ni dump de PostgreSQL.

El visor de Buscar abre la información desplegada. La cabecera presenta fecha
localizada y confianza visual; título y notas van debajo. Solo la cabecera
pliega el panel. Miniaturas y reproducción de video permanecen disponibles.
El panel tiene desplazamiento y una altura máxima del 45 %, reservando espacio
para mostrar el recurso completo sin recortarlo ni ampliar automáticamente.
Los otros visores conservan su comportamiento compacto.

La API de información traduce únicamente textos almacenados y autorizados por
lotes de hasta seis recursos, usando el idioma seleccionado de la app. Valida
las etiquetas originales y revisa acceso antes y después de la inferencia.
No cambia notas originales, etiquetas de búsqueda, URLs, recuadros ni historial.
El cliente reutiliza la traducción durante esa apertura; presenta skeleton y,
ante error, permite reintentar o consultar el original explícitamente.

El orden por confianza descendente se aplica antes de deduplicar/limitar en el
servidor y en Android para miniaturas/carrusel/historial. La identidad del
recurso pulsado se conserva al ordenar y los valores desconocidos van al final.
Prueba real autenticada: tres imágenes a 97 %, 92 %, 88 %; información y
etiquetas traducidas correctamente a español e inglés; imagen señalizada a
1920 × 1280 y etiquetas canónicas conservadas. Registro agregado privado en
`.runtime/evidence-info-20261030-verification.json`.

Pasaron 167 pruebas Python/gateway y 79 pruebas Android, ruff, formato, control
de estructura, ktlint, lint Debug y ensamblado de APK Debug. Las pruebas cubren
traducción de títulos/notas, cambio de idioma, permisos, revocación, consultas
sin escrituras y errores del proveedor, además de orden, empates y selección.
No hay dispositivo conectado: falta QA táctil, fuentes grandes y revisión de
layout en handset. La reindexación serial se reanudó; task id vigente en
`.runtime/evidence-info-20261030-task.json` y los punteros históricos de runtime.


## Traducciones persistidas al publicar — 2026-10-30

Corrección del flujo anterior: traducir al abrir dependía de la latencia del
proveedor y dejaba el visor esperando. API/worker desplegados como
`realityos-backend:publication-languages-20261030`; Alembic `20261030_0027` añade
únicamente `publication_translations`. Salud pública y OpenAPI comprobados;
entornos completos de API/worker conservados. No se creó dump ni se tocaron
medios originales. Rollback `.runtime/publication-languages-20261030-rollback.json`
con arranque directo de la API anterior para mantener la migración aditiva.

La revisión privada de subidas prepara ambos idiomas antes de publicar o
confirmar un reemplazo; si falla la preparación, no aparece una publicación
incompleta. La indexación guarda etiquetas nuevas con sus traducciones en la
misma transacción. Una traducción fallida conserva la evidencia anterior.
Los textos se versionan por hash dentro de cada publicación y se mantienen
las versiones previas que necesita el historial.

El visor recibe los mapas `en`/`es` en el resultado y los conserva en historial,
sin solicitud de traducción al abrir. Para mensajes anteriores consulta datos
persistidos con una petición corta, independiente del bloqueo de otras
solicitudes del cliente y con tiempos de espera acotados. No hay traducción,
escritura ni reindexación iniciada desde esa consulta. La falta de preparación
se muestra explícitamente, sin sustituir el idioma por inglés.

Pasaron 173 pruebas Python/gateway y 80 Android, ruff, estructura, ktlint, lint
Debug y APK Debug. Cobertura de consulta sin proveedor ni escrituras,
preparación de ambos idiomas antes de publicar, error de un idioma, reemplazo,
historial, orden y conservación de evidencia si falla una traducción. No hay
dispositivo conectado; la validación táctil continúa pendiente.

La preparación reanudable de datos anteriores completó los 1852 textos únicos
pendientes mediante `prepare_publication_languages.py --apply`, sin errores y
con cero textos pendientes. Al verificar había 2232 versiones guardadas por
idioma, en 241 publicaciones con texto; dos publicaciones no contenían texto.
El reindexado serial de evidencia se reanudó con el nuevo flujo de traducciones
atómicas; task id en `.runtime/publication-languages-20261030-task.json`.

La prueba real del chat devolvió ambos mapas preparados y leyó la información
en 17 ms (español) y 10 ms (inglés) por HTTP interno. La misma lectura funcionó
con los métodos del proveedor de traducción bloqueados en el proceso de prueba.
Los resultados agregados están en
`.runtime/publication-languages-20261030-coverage.json`,
`.runtime/publication-languages-20261030-verification.json` y
`.runtime/publication-languages-20261030-final.json`. Salud, imagen efectiva,
OpenAPI, Alembic y entornos se comprobaron al cerrar. Se retiró la imagen de
trabajo sustituida y no quedaron contenedores de trabajo detenidos.


## Historial actualizado y recuperación automática de idiomas — 2026-10-30

Desplegado `realityos-backend:history-languages-20261030`; API/worker, entorno
completo, salud pública y OpenAPI comprobados. Alembic sigue en
`20261030_0027`, sin migración ni dump nuevos. Rollback en
`.runtime/history-languages-20261030-rollback.json` sobre la cadena guardada en
`.runtime/history-languages-20261030-before.json`.

La causa del historial en inglés eran copias guardadas sin `localized_information`
y referencias anteriores a la evidencia versionada. GET de historial ahora
refresca sus recursos autorizados y utiliza la señalización inmutable existente.
Cuando no había etiquetas, recupera el contexto de la solicitud anterior y
solo vincula cajas válidas de objetos relacionados; mantiene la relación
exacta/familiar/similar. No genera capturas ni cajas para recursos antiguos.

La nueva acción `/gallery/evidence/information/prepare` recupera los textos
faltantes, comprueba permisos antes y después del proveedor, persiste la pareja
de idiomas y refresca las copias del historial del usuario. La consulta normal
y Query permanecen solo lectura. El cliente solicita esta acción solo si recibe
`pending`, muestra progreso acotado y presenta el resultado en esa apertura.
Al volver al chat o cambiar idioma, refresca filas ya cargadas conservando IDs,
adjuntos pendientes y mensajes anteriores. Las etiquetas de miniaturas también
usan el idioma seleccionado.

Reparación real: 14 adjuntos conservados y con ambos idiomas; 13 referencias
recuperadas con señalización y una conservada sin señalización recuperable.
Los originales no se eliminaron. Historial leído por HTTP real y consultas de
información de español/inglés a 14/12 ms. Datos agregados en
`.runtime/history-languages-20261030-repair.json` y
`.runtime/history-languages-20261030-verification.json`.

Validación final: 182 pruebas Python/gateway y 81 Android aprobadas, ruff,
estructura, ktlint, lint Debug y APK Debug. Cobertura de formato antiguo,
recuperación y persistencia de idiomas en una acción, reutilización sin llamada
al proveedor, referencias conservadas, permisos revocados durante inferencia y
refresco de mensajes cargados sin duplicación. No hubo prueba física en teléfono.
La indexación serial se reanudó; task id en
`.runtime/history-languages-20261030-task.json` y punteros históricos.

## Idioma de cuenta y respuestas del chat — 2026-10-31

Desplegado `realityos-backend:chat-languages-20261031`, migración aditiva
`20261031_0028`. Salud pública, contrato OpenAPI y hashes del entorno completo
verificados; configuración del gateway preservada. Rollback de imagen:
`.runtime/chat-languages-20261031-rollback.json`, aplicado al final de la cadena
Compose guardada en `.runtime/chat-languages-20261031-deploy.json`. El rollback
de imagen conserva las columnas/tablas nuevas y los textos originales.

La corrección anterior cubría recursos, pero no el cuerpo principal del chat.
Las respuestas 28 y 30 estaban guardadas con plantillas inglesas. No existía un
registro del idioma recibido en aquellas peticiones, por lo que no puede
atribuirse retrospectivamente el origen exacto a la selección local o al cuerpo
HTTP. Ahora se registra idioma solicitado, preferencia de cuenta, idioma efectivo,
versión del cliente e identificador de petición, sin preguntas ni audio.

La cuenta guarda `en`/`es` y prevalece en consultas humanas sobre parámetros
antiguos. Se cubren texto, imagen, WAV, asistente, búsqueda textual de perfiles
y metadatos del visor. Las consultas de dispositivos conservan un idioma
explícito porque su identidad representa un workspace, no una persona. Android
sincroniza la cuenta antes del historial/consultas; el cambio se confirma solo
al guardar. Una reinstalación recupera la preferencia. Voz y texto comparten la
versión mostrada; cambiar idioma descarta su presentación anterior sin repetir
la búsqueda.

Las respuestas IA disponen de versiones persistidas por mensaje, idioma y hash
del texto/opciones. Plantillas conocidas se renderizan sin modelo; texto libre
se prepara con un trabajo idempotente. GET del historial y consulta de estados
son lecturas. Recuperación autorizada explícita, bloqueo por mensaje y estados
de error/reintento evitan traducciones duplicadas y skeleton indefinido. Los
mensajes/grabaciones del usuario, acciones y referencias de evidencia se
conservan. Prueba real: cuenta del propietario inicializada en español conforme
a su selección declarada; nueve respuestas históricas localizadas, originales
preservados. Las dos respuestas libres se prepararon en 3,2 y 3,9 segundos.

Validación: 194 pruebas Python/gateway, 21 regresiones finales de idiomas/info,
85 pruebas Android, ruff/formato, estructura, ktlint y lint Debug aprobados. APK
`0.1.3-debug-20261031-0709` (versionCode 4) generado. No hay dispositivo conectado:
prueba visual física pendiente. Evidencia agregada en
`.runtime/chat-languages-20261031-{verification,live-check,android,contract}.json`.
La búsqueda real con parámetro inglés devolvió idioma efectivo español y TTS
coherente, pero `gallery_search_status=unavailable` y cero imágenes; la causa de
esa indisponibilidad de recuperación queda pendiente y no se declara corregida
por este cambio de idiomas. Indexación serial reanudada con 44 publicaciones
pendientes al inicio; task id en `.runtime/chat-languages-20261031-task.json`.

## Recuperación segura de búsqueda — 2026-10-31

Desplegado `realityos-backend:search-repair-20261031`; migración aditiva
`20261031_0029`, entorno completo/gateway preservados, salud pública y contrato
OpenAPI verificados. Rollback de imagen:
`.runtime/search-repair-20261031-rollback.json`, al final de la cadena en
`.runtime/search-repair-20261031-deploy.json`. La reversión de imagen conserva
las nuevas tablas y los originales; no se creó un dump de PostgreSQL.

Causa HTTP 400 reproducida en Live: el código enviaba 28 objetos a SAM con
límite oficial de 16. Se particionan todos los candidatos, sin truncarlos, y se
conservan correspondencias de cajas/máscaras. Las peticiones inválidas conservan
el motivo del proveedor y no se repiten. Prueba real corregida: grupos 16+4,
20 detecciones localizadas. Las respuestas de búsqueda distinguen resultados
parciales, ausencia de coincidencias y fallo del servicio. Los errores de otros
archivos dejan de ocultar coincidencias válidas.

Los intentos de análisis guardan candidatos y progreso antes de cambiar el índice
activo. Un fallo de grupo, fotograma, revisión o traducción conserva la generación
anterior. Las detecciones omitidas se verifican en los píxeles originales; los
objetos pequeños utilizan detalle y sus coordenadas regresan al espacio original.
Los umbrales de confianza permanecen iguales. Una incertidumbre sobre un objeto
activo impide reemplazar ese conjunto; una marca histórica ya descartada se
recupera únicamente si vuelve a confirmarse y localizarse. Los objetos históricos
inciertos no bloquean recuperaciones independientes confirmadas, y se reportan
como revisiones pendientes. Los registros de revisión conservan confianza visual
y de localización por separado. Evidencia en proceso no es visible por imagen,
información ni refresco de historial.

Caso real del martillo recuperado: confianza visual 0,93 y localización 0,832;
la publicación pasó a estado activo sin errores/revisiones pendientes. Consulta
HTTP autenticada: 1 resultado de martillo y 4 de alicate, idioma español incluso
con parámetro inglés, miniaturas 360×240 e imágenes señalizadas 1920×1280.
Se inspeccionó visualmente la imagen grande marcada. No hubo prueba en teléfono.

Validación final: 220 pruebas Python/gateway y 85 Android aprobadas; ruff,
formato, estructura, ktlint, lint Debug y APK Debug. Cobertura de 0/1/16/17/28/32/40
objetos, fallos permanentes sin reintento, recuperación/negación de objetivos,
revisión incierta, grupos incompletos, fotogramas reanudados, aislamiento y
coordenadas de detalle. APK `0.1.4-debug-20261031-1438`, versionCode 5.

El inventario selectivo inicial encontró 31 análisis fallidos y 155 publicaciones
con alguna detección anterior omitida. Se priorizó y recuperó el martillo; el
resto se procesa en segundo plano con un único mantenimiento, sin volver a
analizar escenas completas que solo requieren revisión de objetos omitidos.
Tras las primeras reparaciones se inició el lote restante de 183 candidatos
(31 análisis fallidos y 152 revisiones). **Este lote sigue en ejecución; no se
declara terminado ni se garantiza que toda detección histórica sea correcta.**
Cada fallo/inconclusión conserva el resultado activo y queda registrado para
reintento o revisión. Task id/punteros en
`.runtime/search-repair-20261031-task.json`; estado agregado en
`.runtime/search-repair-20261031-progress.json`. Evidencia técnica adicional:
`-sam-live.json`, `-hammer.json`, `-live-check.json`, `-contract.json`,
`-android.json` y `-final.json` con el mismo prefijo. Los leases de trabajos
interrumpidos por el despliegue se liberaron conservando fotogramas completos.

## Búsqueda biométrica por foto o video — 2026-10-31

`POST /v1/faces/search` acepta probe de video además de foto, con la misma
filosofía acotada que la detección de objetos: hasta
`FACE_VIDEO_PROBE_FRAMES` (8) fotogramas muestreados uniformemente con
ffmpeg/ffprobe, bytes efímeros nunca persistidos en BYTEA, y ranking sobre los
mejores `FACE_PROBE_MAX_FACES` (8) rostros. Probe y enrolamientos pasan un
filtro común de geometría válida y calidad mínima (`FACE_MIN_QUALITY` 0,3,
`FACE_MIN_BOX_AREA` 0,005); los descartes se reportan como
`probe_faces_skipped` / `enrollments_skipped` y los fotogramas analizados como
`probe_frames`. Orden determinista por similitud descendente y miniaturas con
`full_size=false` (360×480, como la evidencia de objetos). El brazo sigue
aislado: sin imports del pipeline Register/Query, sin migración de esquema y
con consentimiento, membership y etapas intactos. Android permite elegir video
como probe y muestra los fotogramas analizados.

Desplegado `realityos-backend:face-video-20261031` en API/worker; Alembic sigue
en `20261031_0029`, salud local/pública `ready`, contrato OpenAPI con los
nuevos campos verificado en ambos, `FACE_ENGINE=insightface` preservado
(hashes de entorno idénticos) y worker activo. La tarea de reindexado
`2f8c370b` se suspendió para el despliegue y se reanudó como `dedaf9de`
(179 reparaciones selectivas, 31 publicaciones pendientes); puntero en
`.runtime/face-video-20261031-task.json`. Rollback:
`.runtime/face-video-20261031-rollback.json` (imagen
`realityos-backend:search-repair-20261031`); imagen `chat-languages-20261031`
retirada. Validación: 225 pruebas Python/gateway, 85 Android, ruff y APK Debug
0.1.4 code 5 (SHA-256
`f6c19244aa8fbaf72bd0894d0b85ae25ae08f2f67e817715d13c1c311b555117`).
Sin QA en teléfono; búsqueda real con video en producción pendiente de prueba
con cuenta de propietario.


## Meta Display conectado con Perfil y Trabajo — 2026-10-31

Implementado en el Display DAT nativo y su sección Android: inicio Buscar /
Capturar, elección explícita entre galería de la app y registro por ubicación,
destino privado Perfil o grupo Trabajo elegido por cuenta en el teléfono,
fotos y video MP4 con confirmación antes de publicar, revisión de duplicados,
procesamiento y reintentos. Los originales pendientes se conservan en el
almacenamiento privado del teléfono con claves idempotentes; desconexión o
cambio de cuenta cancela sensores e invalida respuestas antiguas. Se conservan
el registro por zonas y la previsualización óptica Debug.

La galería sirve evidencia mediante permisos temporales por usuario/recurso,
con permisos reevaluados en cada lectura. El derivado Display contiene la imagen
completa y señalizada en 600×280; fecha de última observación y confianza visual
quedan separadas del título/notas, disponibles en Acciones. El original BYTEA
no se modifica. Video: máximo 120 s o límite servidor menor, detección de
repeticiones exactas por hash y evidencia de fotogramas con sus timestamps.
No se añadió ninguna tabla ni se modificó el módulo biométrico protegido.

Producción: API y worker en `realityos-backend:meta-display-20261031`, Alembic
`20261031_0029 (head)`. Salud pública y OpenAPI exacto verificados; prueba HTTP
real de emisión/lectura de imagen autorizada aprobada con dimensiones 600×280.
Runtime del gateway preservado y hash del módulo protegido comparado con el
release anterior. Sin dump de PostgreSQL. Retirada la imagen intermedia sin uso.
El primer intento de recreación se interrumpió; se recuperaron ambos servicios
y se completó el despliegue con espera de parada de 30 segundos.
Rollback: `.runtime/meta-display-20261031-rollback.json`; comandos en
`.runtime/meta-display-20261031-deploy.json`; verificación final en
`.runtime/meta-display-20261031-final.json`.

Validación: suite completa final de 233 pruebas backend/gateway aprobada;
las 8 pruebas específicas de Meta Display incluyen MP4, recuperación, aislamiento,
rechazo de credenciales de dispositivo para galería y geometría Display.
89 pruebas unitarias Android aprobadas; formato Kotlin, APK Debug y Release
compilados. APK 0.1.5, versionCode 6. Ruff y comprobación de arquitectura pasan.
`make android-check` sí se ejecutó y falla únicamente en tres traducciones
españolas preexistentes del módulo protegido: `face_pick_video`,
`face_probe_unreadable`, `face_frames`. No se cambiaron ni se silenciaron.

Pendiente: QA táctil del APK en teléfono, cámara/micrófono y audio Bluetooth,
y prueba en gafas físicas. Este servidor no tiene emulador Android instalado.
La revisión de contenido de prueba en el renderer web oficial de Meta permitió
compactar la navegación y reservar espacio a la evidencia; no demuestra el
comportamiento del APK ni del hardware.


## Zoom estable en el visor del buscador-chat — 2026-10-31

Corregida la desaparición de la imagen al terminar un gesto de zoom. El evento
que levanta el último dedo no tiene centroide (`Offset.Unspecified`); el visor
lo seguía procesando mientras la escala era mayor que uno. El cálculo anterior
propagaba NaN a la traslación de la capa gráfica y dejaba la imagen invisible
hasta volver a abrirla.

El visor ahora procesa únicamente punteros que siguen presionados y aplica
escala/desplazamiento como un estado conjunto validado. Descarta centroides,
desplazamientos y factores no finitos, conserva los límites de arrastre y
restaura el centro al volver a 1×. Las solicitudes autenticadas de imagen y
fondo se recuerdan por URL/token para mantener su identidad entre recomposiciones.
Se mantiene el bloqueo del carrusel mientras la imagen está ampliada.

Las dos pruebas de regresión reprodujeron el fallo con la fórmula anterior.
Pasan las nueve pruebas de zoom, incluido un evento real de liberación de
puntero de Compose, veinte gestos consecutivos, arrastre posterior, límites,
reducción a 1× y entradas no finitas. Suite Android: 94 pruebas aprobadas.
APK Debug y Release 0.1.6, versionCode 7. Formato y comprobación de arquitectura
aprobados. Lint completo conserva únicamente los tres errores de traducción
preexistentes del módulo protegido, sin modificarlos ni silenciarlos.

Cambio solo de Android, sin modificación de backend, contratos ni base de
datos. Pendiente validar el gesto táctil en un teléfono físico; el servidor
no tiene emulador Android instalado.


## Recuperación del procesamiento de búsqueda — 2026-10-31

Diagnóstico inicial de producción: 238 publicaciones visibles, 31 con error
de indexación y otras seis generaciones activas con revisión pendiente. No
había tareas Celery activas; un video conservaba un lease vencido y 28
fotogramas ya completados. Los errores antiguos incluían solicitudes SAM con
demasiados objetos, análisis estructurados inválidos y localizaciones poco
confiables de objetos visualmente confirmados.

Corregida la creación del parser SAM dentro de un bucle asyncio activo. La
columna `GalleryIndexRun.updated_at`, existente desde la migración 0029 pero
ausente del ORM, ahora persiste el heartbeat. Una revisión visual confirmada
puede obtener una máscara mediante un prompt independiente de concepto sobre
los píxeles originales recortados: confianza mínima sin cambios y coincidencia
de la misma instancia con IoU mínimo 0,5. Las incertidumbres conservan su
estado; una confirmación visual sin localización válida no fabrica evidencia.
Los rechazos explícitos confiables no se sustituyen por recortes ambiguos.
Al reanudar, también se persisten los objetos ya retenidos en evidencia
preparada: se limpia el contador antiguo incluso si no hay nuevas llamadas de
revisión. La regresión reproduce el aviso falso de una generación ya lista.

El mantenimiento `--pending-only --apply` encola tareas por publicación y medio
con confirmación al terminar, reentrega ante pérdida del worker y exclusión por
lease. Reanuda fotogramas guardados y omite medios cambiados o tareas ya
completadas. Los errores transitorios de análisis estructurado tienen un máximo de dos
reintentos, con presupuesto independiente de la espera por un lease activo.
Esa espera no agota una cadena mientras otro worker procesa un video largo. No elimina duplicados ni modifica originales. `PYTHONPATH=/app` evita
que los scripts de la imagen importen un paquete instalado anterior.

Desplegado `realityos-backend:processing-recovery-20261031` en API y worker.
Salud pública lista, OpenAPI exacto sin cambios, Alembic `20261031_0029 (head)`,
runtime del gateway y hash del módulo protegido preservados. Sin dump de
PostgreSQL. Release y rollback:
`.runtime/processing-recovery-20261031-release.json` y
`.runtime/processing-recovery-20261031-rollback.json`; comandos en
`.runtime/processing-recovery-20261031-deploy.json`. Verificación del release en
`.runtime/processing-recovery-20261031-release-verification.json`.

Validación: suite completa de 244 pruebas Python/gateway aprobada, incluidas
once regresiones de recuperación; ruff, formato de los archivos cambiados y
comprobación de arquitectura pasan. Sin cambios Android ni del contrato REST;
se conserva el único `app-debug.apk` 0.1.6 code 7.

El lote inicial de 37 archivos se está recuperando con dos cadenas seriales
complementarias y la reanudación independiente del video. Los leases impiden
duplicar análisis concurrentes. Estado real en
`.runtime/processing-recovery-20261031-progress.json` y tareas en
`.runtime/processing-recovery-20261031-task.json`. Verificación HTTP real posterior al despliegue: un martillo y cuatro alicates
en español, con imágenes grandes señalizadas de 1920×1280; respuestas parciales
coherentes con el lote pendiente. Conservadas las 243 referencias de medios,
hashes, tamaños y visibilidad del inventario previo. Los originales no se
reemplazan; retiradas las tres copias temporales de diagnóstico. El video
retomó sus 39 fotogramas guardados después del reemplazo controlado del worker.
Cierre operativo y pruebas en `.runtime/processing-recovery-20261031-final.json`.
La finalización de una tarea
no equivale a cero revisiones pendientes: el aviso del buscador se conserva si
el proveedor no puede verificar algún objeto anterior. Pendiente: terminar el
lote, revisar las ambigüedades que persistan y QA físico del visor
Android descrito anteriormente.

Corte operativo final: recuperados 18 de los 37 pendientes iniciales; cero
errores HTTP 400 antiguos restantes. Quedan 18 publicaciones con objetos aún
no verificados y el video largo en procesamiento (50 fotogramas guardados en
el corte). El video reintenta de forma acotada un análisis estructurado
transitorio sin perder los fotogramas completos. El buscador conserva estado
`partial`, comprobado por HTTP con 19 archivos de cobertura incompleta; no se
afirma que el lote terminó ni se ocultan las revisiones. Ambas búsquedas reales
y sus imágenes grandes siguen funcionando.

## Navegación Ray-Ban Meta simplificada — 2026-11-01

El inicio conserva Buscar y Capturar foto o video. Buscar abre Foto / Comando
de voz. Foto utiliza la cámara como entrada efímera del servicio existente
`/queries/image`, sin sesión Register ni publicación; voz conserva su lógica y
la fuente configurada en el teléfono. Si la consulta por foto devuelve un
resultado del registro sin enlace Display, se presenta la respuesta textual;
la evidencia de galería conserva su carrusel y enlaces autorizados.

Capturar abre directamente la cámara con foto y video. Al tomar la foto o
detener el video se envía al Perfil privado de la cuenta (`audience=home`,
sin `workspace_id`), sin formulario ni elección de grupo. La app queda como
lugar para clasificar y completar información. Se reutilizan procesamiento,
confirmación de duplicados, idempotencia y reintentos existentes. Una elección
antigua de Trabajo no redirige capturas nuevas; las subidas ya pendientes
conservan su destino guardado. La previsualización Debug comparte este flujo
y muestra solo foto al buscar, con cancelación accesible.

No hay cambios de backend, contratos, migraciones ni del módulo biométrico.
Las diez pruebas de integración específicas pasan, incluidas consulta por
imagen efímera, publicaciones, permisos y aislamiento. Formato Kotlin y 111
pruebas unitarias Android aprobados; APK Debug recompilado en la ruta única
`android/app/build/outputs/apk/debug/app-debug.apk`, versión
`0.1.6-debug-20261101-0913`, code 7, SHA-256
`a012650701e4ccab7c2b8d00326de6f585b0dc1e1c9ac0644f0a554f1f54aa05`.
Lint vuelve a fallar únicamente por las tres traducciones españolas
preexistentes protegidas: `face_pick_video`, `face_probe_unreadable`,
`face_frames`; no se silenciaron ni modificaron. Pendiente QA táctil en
teléfono y prueba de cámara, micrófono y Display en gafas físicas.

## Sensores y cámara del simulador Ray-Ban — 2026-11-01

La selección de sensores utiliza el dispositivo elegible realmente seleccionado,
con prioridad para gafas físicas. El controlador conserva los identificadores
virtuales de las generaciones anteriores, por lo que una reconexión automática
al Mock Device Kit sigue usando cámara CameraX y reconocimiento de voz Android.
La ruta se fija al iniciar la sesión y vuelve a teléfono al desconectar; no se
inician sensores ni capturas automáticamente. Firmas comprobadas contra los
artefactos oficiales instalados de DAT/Mock Device Kit 1.0.1.

Los controles frontal/trasero del simulador seleccionan la fuente CameraX de
la siguiente captura y ya no abren un segundo feed de cámara con el SDK. La
vista previa compara geometría por valor y cancela enlaces pendientes de
superficies anteriores. Estados de apertura/stream/error y generaciones evitan
activar el disparador sin imagen o aceptar callbacks de una pantalla cerrada.
El renderer oficial permanece montado, oculto y sin recibir toques mientras se
usa la cámara del teléfono.

Las barras superior e inferior y los menús siguen visibles. Buscar por foto
tiene X arriba a la derecha y foto abajo al centro; Capturar conserva además
video/detener sobre la foto. Eliminados Reintentar/Volver dentro de la cámara;
los errores conservan la X y permiten cerrar y volver a entrar. Navegar fuera
de Preview o recrear la Activity libera sensores locales sin borrar capturas
ya preparadas ni cancelar su subida. Backend, contratos, permisos de acceso a
medios, procesamiento y módulo biométrico no cambian.

Validación: formato Kotlin, 119 pruebas unitarias Android y 10 pruebas de
integración aprobados. Compilan Kotlin Release y las pruebas instrumentadas
Debug; estas últimas no se ejecutaron. APK Debug generado en la ruta única
`android/app/build/outputs/apk/debug/app-debug.apk`, versión
`0.1.6-debug-20261101-0936`, code 7, SHA-256
`d203a7e977930d96330e419712ccb10a2b7d32209fdef11ddd0d71d88b6b9b03`.
Lint mantiene únicamente las tres traducciones españolas protegidas ya
documentadas (`face_pick_video`, `face_probe_unreadable`, `face_frames`), sin
suprimirlas ni modificarlas. `adb devices -l` no detecta dispositivos y no hay
emulador/system image instalado: quedan pendientes imagen/audio reales en
teléfono, interacción táctil y validación en gafas físicas.

## Toques de foto y cerrar en el simulador — 2026-11-01

El visor nativo tiene prioridad explícita de dibujo y hit testing frente a
las capas Android del renderer SDK. La composición anterior podía dejar una
capa transparente receptora de eventos por encima de foto/video/X. La X ya no
se deshabilita durante una captura ocupada y mantiene su cancelación existente.
Si CameraX termina de guardar después de cancelar, elimina el archivo temporal
en vez de dejar la foto cancelada en caché. Se conservan posiciones, navegación,
video, consultas y publicación al Perfil; backend y módulo protegido sin cambios.

El componente usado por la app se prueba con Compose/Robolectric 4.16.1 y
eventos de puntero: cuatro escenarios fallaron antes del arreglo al colocar
una vista Android transparente que consume eventos encima; seis pasan después.
Cubren foto y X, foto/video, cerrar ocupado, cerrar durante apertura,
video/detener y recuperación de toques por el renderer al cerrar. La fixture
usa un visor compacto de 108×192 dp y vistas Android sustitutas: no demuestra
el comportamiento de la cámara física ni del WebView real del SDK.

Formato Kotlin y 125 pruebas Android aprobados. APK Debug generado en
`android/app/build/outputs/apk/debug/app-debug.apk`,
`0.1.6-debug-20261101-0952`, code 7, SHA-256
`ea26e544ed00dd4c7a100ba00781be60582f5f6896c4e079b9e372ec8271f637`.
Kotlin Release y las pruebas instrumentadas Debug compilan; no se ejecutaron
pruebas en dispositivo. `adb devices -l` sigue vacío. Pendiente validación de
foto/audio y SDK en teléfono y gafas físicas.
Lint conserva únicamente los tres errores españoles protegidos ya conocidos:
`face_pick_video`, `face_probe_unreadable` y `face_frames`, sin silenciarlos.

## Idioma completo de interfaz, chat y voz — 2026-11-01

Corregidos 191 textos de producto que estaban fuera de los recursos Android:
Perfil, Trabajo, navegación, administración, publicaciones, notas, chat,
permisos, estados vacíos y accesibilidad. Los callbacks y servicios resuelven
el idioma desde la preferencia guardada, también después de recrear la
actividad. Se completaron `face_pick_video`, `face_probe_unreadable` y
`face_frames`, con autorización explícita para traducir la UI protegida;
no se modificó el motor ni la lógica biométrica.

El chat traduce sus mensajes locales antes de presentarlos y evita marcar
texto fijo español como respuesta inglesa. El servidor reconoce esas frases
y los saludos en historial, incluso con una traducción antigua incorrecta:
GET sigue siendo lectura y la reparación administrativa es idempotente, sin
modelo ni cambios del original. Se repararon 19 mensajes reconocidos; la
verificación HTTP autenticada encontró 21 respuestas recientes `ready` en
inglés y los 19 mensajes reconocidos con su versión correcta. La cuenta ya
seleccionaba `en` y se conservó. Una consulta HTTP con parámetro español
respetó esa preferencia y devolvió texto/TTS coincidentes. Las descripciones
espaciales generadas se traducen para la respuesta sin modificar evidencia.

Cambiar de idioma detiene la locución y rechaza audio de una respuesta del
idioma anterior. El reconocimiento del teléfono consulta la selección al
iniciar cada escucha; la ausencia de una voz compatible muestra un aviso
traducido. Las respuestas de usuario y sus grabaciones conservan el original.
El Display vuelve a presentar sus controles al cambiar de idioma y conserva
capturas y subidas pendientes.

Ambas webs incluyen selector, preferencia de cuenta, catálogos tipados,
etiquetas de estado, fechas y locución con idioma explícito. Las consultas
sincronizan la cuenta y descartan resultados recibidos tras cambiar idioma.
Los paquetes productivos usan la API del mismo origen. El propietario autorizó
expresamente su publicación local como excepción al camino CI; no se envió
a Git el trabajo previo sin publicar. La suite de seis regresiones web quedó
añadida al workflow CI para futuras entregas.

Validación: 259 pruebas backend/gateway, seis pruebas web, compilación y
Prettier de ambas webs, Ruff, contrato OpenAPI y comprobación de estructura.
Android pasó 143 pruebas y lint Debug; el APK instalable se reemplaza en
`android/app/build/outputs/apk/debug/app-debug.apk`. La validación física de
reconocimiento, audio y hardware Ray-Ban sigue pendiente; no se afirma una
prueba en dispositivo.

API/worker: `realityos-backend:all-languages-20261101`, salud pública `ready`,
worker verificado y Alembic `20261101_0030 (head)`. Entorno completo comparado
y preservado, incluido gateway; no hubo migración de esquema ni dump.
Webs: `realityos-frontend:all-languages-web-20261101` y
`realityos-display:all-languages-web-20261101`, HTML y bundles nuevos verificados
por HTTPS en `/` y `/display/`. La revisión de mantenimiento no encontró
contenedores temporales detenidos ni imágenes colgantes del proyecto que retirar.
Rollback backend: `.runtime/all-languages-20261101-rollback.json`.
Rollback web: `.runtime/all-languages-web-20261101-rollback.json`.
Las cadenas Compose correspondientes están en los archivos `*-deploy.json`;
sustituir el overlay de release por rollback, recrear únicamente sus servicios
y recargar el proxy. Evidencia técnica: archivos `*-verification.json` y
`.runtime/all-languages-20261101-live-check.json`.

## Segunda revisión de idiomas — 2026-11-01

La prueba en Chromium encontró dos problemas adicionales en la web: los
mensajes de error de consulta quedaban dentro del bloque de resultado y no
aparecían si todavía no había respuesta; además, las respuestas sin coincidencia
no podían escucharse. Ahora el estado de error es independiente del resultado
y toda respuesta con TTS puede reproducirse, tanto en el panel como en Display.

Las consultas descartan respuestas y errores anteriores al cambiar idioma,
cuenta o workspace. Una respuesta más lenta tampoco reemplaza una consulta
más reciente del mismo idioma. El refinamiento SAM solo actualiza la evidencia
para la que fue solicitado; los callbacks tardíos de imágenes no restauran un
recurso anterior. No se repiten búsquedas al cambiar de idioma. El ejemplo del buscador cambia
con el idioma como placeholder; el borrador escrito por el usuario se conserva.

Android usa recursos plurales reales para personas encontradas y rostros
enrolados. El servidor reconoce los textos históricos `person(s)`/`persona(s)`
y presenta singular o plural natural, conservando nombres, originales e IDs.
Las lecturas de historial siguen sin llamar al modelo ni escribir traducciones.

Nueva regresión reproducible: `node tests/web/browser-language.cjs`, después
de compilar ambas webs con `VITE_API_URL=`. Usa Chromium, perfiles aislados,
API de prueba local y voz simulada; no accede a cuentas de producción. Pasaron
20 comprobaciones de DOM, cambio de idioma, errores, TTS y consultas con
respuestas fuera de orden. Las seis pruebas de preferencia/voz siguen pasando.
Esto no sustituye una prueba acústica ni QA física en teléfono o Ray-Ban.

Validación final de esta revisión: 265 pruebas backend/gateway y 144 Android,
ktlint, lint Debug y APK Debug aprobados; seis pruebas unitarias web y las
20 comprobaciones de Chromium aprobadas. Ambas webs compilan con API del mismo
origen y pasan Prettier; Ruff, formato Python y estructura también pasan.

Desplegada esta segunda revisión en API/worker como
`realityos-backend:language-review-20261101`; salud pública `ready`, OpenAPI
idéntico, Alembic `20261101_0030 (head)`, worker activo y runtime completo del
gateway preservado. Sin migraciones nuevas ni dump. Las webs publicadas son
`realityos-frontend:language-review-web-20261101` y
`realityos-display:language-review-web-20261101`, con sus HTML y bundles
verificados por HTTPS. Se conserva la autorización del propietario para
publicación local. La comprobación HTTP autenticada mantuvo la cuenta en
`en`, verificó 21 respuestas listas, 19 plantillas localizadas y coincidencia
entre respuesta y TTS. Mantenimiento: cero contenedores temporales detenidos
y cero imágenes colgantes del proyecto pendientes de retirar.

Rollback servidor: `.runtime/language-review-20261101-rollback.json`.
Rollback web: `.runtime/language-review-web-20261101-rollback.json`.
Las respectivas cadenas están en `*-deploy.json`; los resultados en
`*-verification.json`, `.runtime/language-review-20261101-live-check.json`
y `.runtime/language-review-final.json`. QA física de voz/gafas pendiente.

## SeamlessM4T v2 para respuestas de audio — 2026-11-01

Integración implementada para Android/gafas, panel y Display web: solicitud
separada `POST /v1/tts`, voz EN/ES desde un servicio privado detrás del gateway,
un único reintento transitorio en el backend dentro de 30 segundos y respaldo
con la voz anterior si no llega audio. Cancelación al detener, cambiar idioma,
salir o reemplazar respuesta; las webs incluyen Detener audio. No persiste
texto/audio generado, no consulta evidencia y no añade migraciones. Mock no
contacta al proveedor. El módulo biométrico protegido conserva su checksum.

Desplegados API/worker como `realityos-backend:seamless-tts-20261101-r2`.
Salud y contrato WAV verificados; Alembic sigue en `20261101_0030 (head)`;
runtime del gateway preservado y sin `MODEL_API_KEY` en RealityOS. La prueba
HTTP real rechaza anónimos con 401 y devuelve 503 autenticado mientras falta
activar el servicio: **todavía no hay audio real generado por Seamless**.

Imágenes locales preparadas: `realityos-meta-gateway:seamless-tts-20261101-r2`
y `realityos-tts:seamless-v2-20261101`. La imagen TTS pasó imports y descarga/
ejecución del procesador oficial en `spa`/`eng` sin cargar pesos. Esta prueba
detectó y permitió incorporar `protobuf` a las dependencias. No se ejecutó el
modelo completo ni el benchmark de memoria/latencia; no se instaló el motor en
API/worker ni se realizó una llamada de inferencia Live de Seamless.

Validación final: 291 pruebas Python/gateway, 147 Android, 12 unitarias web,
20 comprobaciones Chromium con API/voz simuladas, ruff/estructura, ktlint y
lint Debug. Ambas webs compilan para API del mismo origen y pasan formato.
APK Debug único reemplazado: `0.1.6-debug-20261101-1529`, code 7, en
`android/app/build/outputs/apk/debug/app-debug.apk`. QA acústica y gafas físicas
pendientes. Las webs están preparadas para CI; **no se publicaron** en esta tarea.

Bloqueo externo: la herramienta `servers.exec` rechazó la lectura de recursos
de FRONTEND con `This operation requires approval in an active chat`. Por ello
no se transfirieron ni activaron allí gateway/modelo ni se verificó capacidad.
Se mantienen los servidores actuales, sin contratar infraestructura. Antes de
activar, aplicar los controles y el benchmark de [TTS](TTS.md). La voz actual
sigue siendo el respaldo hasta completar esa activación.

Rollback servidor: `.runtime/seamless-tts-20261101-rollback.json`
(`realityos-backend:language-review-20261101`); cadena de Compose en
`.runtime/seamless-tts-20261101-deploy.json`, verificación y prueba HTTP en
`seamless-tts-20261101-{verification,live-check}.json`. Sin dump PostgreSQL.

## Tercera revisión: idioma de reproducción y metadatos del Display — 2026-11-01

Corregido un caso de reproducción manual: un mensaje anterior podía enviarse
al sintetizador con el idioma seleccionado al pulsar el botón, perdiendo el
idioma del texto. El chat conserva ahora la pareja texto/idioma y solo permite
locución de respuestas IA traducidas, listas y coincidentes con la selección.
Una traducción pendiente, fallida o sin idioma no se convierte en voz. Las
respuestas del usuario y sus grabaciones mantienen su reproducción original.

Las respuestas y botones de repetición del Display también conservan el idioma
de origen. El cliente comprueba el `response_language` real del servidor antes
de presentar una respuesta; las vistas de resultados y sus callbacks no
vuelven a etiquetar el texto con el idioma de una selección posterior.

El panel de acciones del Display mostraba el título/nota original cuando
faltaba la información localizada del objeto. Ahora muestra el estado de
traducción pendiente con textos de interfaz traducidos. Solo los nombres de
matches identificados por su enrolamiento conservan su escritura original;
la selección anterior de búsqueda no habilita fallback para objetos.

Se añadieron seis regresiones Android para respuestas antiguas, traducciones
listas/pendientes/fallidas, idioma desconocido, selección de información EN/ES,
ausencia de traducción y nombres propios. Pasan 153 pruebas Android; también
63 pruebas relevantes de idiomas/historial/TTS backend-gateway y 12 web. Las
pruebas de síntesis utilizan transportes o motores simulados. La comprobación
pública devuelve `ready` y OpenAPI coincide con el contrato, incluida `/v1/tts`.
No se modificaron contratos HTTP, lógica biométrica ni esquema de datos.
La prueba acústica y QA de hardware siguen pendientes.

ktlint, lint Debug y compilación final aprobados; el único APK se actualizó en
`android/app/build/outputs/apk/debug/app-debug.apk`. Evidencia y SHA-256 en
`.runtime/language-third-pass-final.json`. Esta pasada no requiere despliegue
de servidor: API/worker siguen en el release observado
`realityos-backend:seamless-tts-20261101`; su rollback previo permanece en
`.runtime/seamless-tts-20261101-rollback.json`.


## Conexión directa y Seamless local — 2026-11-01

Desplegado `realityos-backend:direct-meta-20261101` en API/worker y
`realityos-tts:direct-20261101` en este servidor. `.env` selecciona
`META_CONNECTION_MODE=direct|gateway`; producción está en `direct` con
`META_GATEWAY_FALLBACK_ENABLED=true`. La clave activa se instaló privadamente
y sustituyó las tres entradas locales rechazadas. Los tokens de Meta, gateway
y síntesis permanecen separados y no se publican.

Transporte común para JSON, ASR multipart, SAM imagen y Files/video. Directo
usa `api.meta.ai`; errores de conexión, 401/403/404, 408/429 y 5xx activan el
respaldo. 400/422 no lo activan. Cada petición nueva vuelve a directo. Archivos,
videos y streams aceptados o ambiguos no se repiten automáticamente: conservan
el estado `uncertain` y los handles se rebobinan solo para reenvíos permitidos.

Seamless corre localmente en BF16, con 4 GiB sin swap y dos CPU. El endpoint
HTTPS público `/tts/synthesize` exige su propio Bearer token; no altera
`POST /v1/tts` ni los contratos Android/web. El gateway de FRONTEND se conserva
con la imagen `realityos-meta-gateway:direct-backup-20261101`; su ruta de voz
apunta al motor de RealityOS. No hay otro modelo en FRONTEND ni un bucle de
forwarding. La voz del dispositivo continúa si no se consigue audio.

Validación: 326 pruebas backend/gateway, ruff, formato, arquitectura, YAML y
shell del workflow. Benchmark real: seis WAV EN/ES, 2,22–3,01 segundos, sin OOM.
Tras desplegar, consultas Muse reales pasaron en directo y en modo gateway;
un 404 inyectado únicamente en el cliente directo activó el gateway real y
terminó con HTTP 200/`OK`. La síntesis EN/ES por HTTPS directo y la síntesis por
respaldo real pasaron a ~2,7–2,8 segundos. La ruta pública de voz rechazó una
petición sin token con 401. Worker verificó nueve modelos usando únicamente
`api.meta.ai`. Salud pública lista, OpenAPI conservado, Alembic
`20261101_0030 (head)` y módulo biométrico sin cambios verificados. No se
realizó una nueva prueba física de gafas/teléfono ni una nueva inferencia SAM
Live; sus rutas se cubrieron con pruebas de transporte.

CI respeta `.env`, no conserva selecciones antiguas sobre ella y no depende
del éxito del despliegue FRONTEND para actualizar RealityOS. No hay migración
nueva, dump PostgreSQL ni cambio de contrato que requiera otro APK.
Informes privados: `.runtime/direct-meta-20261101-deployed.json`,
`.runtime/direct-meta-20261101-live-verification.json` y
`.runtime/direct-tts-20261101-benchmark.json`. Rollback API/worker:
`.runtime/direct-meta-20261101-rollback.json`, con el entorno anterior en
`.runtime/direct-meta-20261101-previous.env`. Rollback FRONTEND:
`/opt/realityos-meta-gateway/direct-backup-20261101-rollback.json`.


Ajuste de CI de esta entrega: el runner anterior usaba Ubuntu/FFmpeg 6.1.1,
mientras producción usa Debian 13/FFmpeg 7.1.5. Una prueba existente depende de
los bytes de fotogramas sintéticos y fallaba con esa diferencia. Backend,
verificación de despliegue y base Docker quedan alineados explícitamente en
Debian 13 (trixie). No se modificó el módulo protegido ni su comportamiento.


## Alternativa Windows / Docker con proveedores reales — 2026-11-01

Perfil independiente `realityos-local`, configuración `.env.local`, imágenes y
volúmenes propios. PowerShell prepara secretos, comprueba contexto Docker local,
CPU/memoria/disco, catálogo real Meta y salud/audio real de Seamless. API/worker
exigen Live e InsightFace; la voz selecciona BF16 nativo o FP32 localmente.
No se ejecutan seeds ni se cargan publicaciones de demostración. La configuración
real del servidor y sus volúmenes no se reutilizan ni sobrescriben.

El propietario pidió expresamente entrar con cuenta de prueba sin reconocimiento
facial en localhost. Las rutas de acceso local solo se registran con
`ENVIRONMENT=local` y `LOCAL_LOGIN_ENABLED=true`. Emiten tokens y credenciales de
captura propios sin consentir, reconocer, crear o retirar datos faciales. La app
Debug local tiene ID `.local`, HTTP exclusivamente loopback y confirmación de
entorno local al entrar/restaurar sesión. Normal/Release conservan su acceso
habitual; la omisión de verificación de entrada no afecta permisos ni
consentimientos de las funciones faciales. El módulo backend de caras y sus
migraciones permanecen intactos.

Validación en este host Linux: 340 pruebas backend/gateway; pruebas PowerShell de
secretos, persistencia, configuración independiente y rechazo de contextos
remotos; render de Compose y prueba real de escaping dotenv en contenedores
mínimos aislados. Los builds completos local y habitual y las pruebas Android
se ejecutan en CI para conservar recursos del servidor. Se añade verificación
PowerShell nativa en Windows con PowerShell 7 y 5.1. Una prueba integral de Docker
Desktop en Windows y QA de cámara/gafas físicas no se dan por ejecutadas desde
este host Linux. El diagnóstico local verifica proveedores reales al instalar.

Guía: [Windows local](LOCAL_WINDOWS.md). El APK final habitual debe quedar en
`android/app/build/outputs/apk/debug/app-debug.apk`; el build local es una
alternativa y no sustituye el APK del servidor. No se requiere migración nueva
ni dump PostgreSQL.

## Apertura de cámara desde Buscar en la vista previa — 2026-11-01

Los botones Buscar objeto/persona y Capturar pasan al hilo principal y muestran
el permiso pendiente, la operación activa o la revisión de una publicación
retenida en lugar de finalizar silenciosamente. Abrir CameraX tiene un plazo
máximo; su propia operación libera el estado ocupado incluso si cambia la
generación de respuestas. Cambiar idioma durante una búsqueda por foto conserva
la generación de captura; cancelar rechaza callbacks anteriores. El host conserva
la solicitud de permiso al recrear la actividad.
Una superficie descartada se rechaza antes de cancelar tareas, para que no pueda
interrumpir el enlace de una cámara recién abierta.

CI añade pruebas con toques en el WebView oficial de Meta, permiso concedido y
denegado, cancelación, reapertura, publicación retenida, fallo de inicio y cambio
de generación. Una prueba independiente utiliza CameraX y los frames de la
cámara emulada; las restantes controlan el origen para verificar el estado sin
subir fotografías. La ejecución manual `verify_display_baseline` permite
comprobar los dos fallos sobre la implementación anterior antes de ejecutar
la corregida. No implica validación de cámara, tacto ni gafas físicas. Sin cambios
de backend, contratos API o consentimientos biométricos.

## Señalización facial legible y perfil nativo — 2026-11-01

La tarjeta del probe usa contornos finos y etiquetas fuera de cualquier rostro.
Si no existe espacio junto a una cara, su número ocupa una banda inferior de
reserva; la tarjeta conserva 600 × 280 y el probe continúa siendo efímero.
La miniatura enrolada también dibuja el borde fuera del rostro y calcula el
grosor según la caja facial, para no llenar caras pequeñas en fotos grandes.
El cambio de `faces.py` se limita a ese dibujo solicitado por el propietario;
no cambia permisos, consentimiento, detección ni comparación biométrica.

Buscar persona conserva el `user_id` interno del match durante la sesión y
muestra Abrir perfil en la app. Un resultado abre su perfil nativo; varios
ofrecen un selector. Atrás conserva la búsqueda. No se usa `profile_link` para
abrir Facebook ni un navegador, y no se persiste este estado en el historial.
Solo se aceptan perfiles de los resultados vigentes de la cuenta; cambiar de
cuenta elimina la solicitud. Los permisos del perfil se comprueban en las rutas
existentes del servidor.

Pruebas de imagen cubren caras pequeñas, grupos densos y regiones que ocupan
toda la imagen. Las pruebas Android cubren IDs válidos, navegación desde el
WebView oficial, selección entre matches, regreso, cuenta y callbacks anteriores.
El contenido remoto del perfil sigue las pruebas del backend; las pruebas de
navegación sustituyen únicamente ese contenido. QA visual en teléfono y gafas
físicas sigue pendiente; no se infiere de la cámara emulada.


## Voz sin modelo residente — 2026-11-02

Producción pasa a `TTS_PROVIDER=elevenlabs`, modelo `eleven_flash_v2_5`, voz
George y WAV PCM 24 kHz; `/v1/tts` conserva autenticación y contrato. Muse Voice
Transcribe, Muse Spark y SAM permanecen. La credencial se copia desde la
configuración privada de Luxisoft a `.env.elevenlabs` (solo API). Seamless
queda detenido y sin reinicio automático en producción; Windows local conserva
su opción explícita. CI reconcilia el estado aun si existe el contenedor viejo.
El antiguo endpoint de servicio `/tts/synthesize` responde 410. Ver `TTS.md`.

Validación previa: 369 pruebas backend/gateway y lint aprobados; muestras
reales ElevenLabs EN/ES válidas, cuenta Starter
activa; pruebas cubren autenticación, ausencia de egress en mock, independencia
del gateway Meta, concurrencia/cancelación, límites, errores sin replay y
reconciliación del despliegue. El recibo privado de release y las mediciones de
RAM quedan en `.runtime/ram-elevenlabs-20261102-*` y
`/home/jmarin/server-memory-audit-20261102/`. Consultar esos recibos para el
resultado efectivo del despliegue y sus límites; no confundir preflight con QA
física de Android/gafas.


## Eliminación de síntesis local — 2026-11-02

Por instrucción explícita del propietario se elimina Seamless, incluyendo código,
contenedor, imagen, volumen de pesos, dependencias, trabajos de CI y opciones
Windows. ElevenLabs es el único motor de síntesis; Muse Voice Transcribe/Spark/SAM
se conservan. Windows utiliza su propia clave ElevenLabs y no copia claves de
producción. Las referencias previas a modelos/volúmenes y rollbacks de Seamless
son históricas y quedan retiradas; la recuperación inmediata usa la última
versión ElevenLabs, sin modelo local. Se mantienen datos de usuario y biometría.


## Carga verificada de fotos al navegar en Display — 2026-11-02

Se conserva el diseño de Buscar persona, la tarjeta grupal señalizada, las
fotos coincidentes y Abrir perfil en la app. Android descarga los derivados
firmados y comprueba HTTP, formato, tamaño, decodificación y vencimiento antes
de entregarlos a DAT como Bitmap. Un match sin enrolamiento o una foto fallida
muestra un error con reintento; no genera una tarjeta silenciosamente vacía.
Cada visita a un candidato solicita un enlace nuevo mediante la autorización
existente. La tarjeta grupal se conserva solo en memoria durante la búsqueda,
hasta el vencimiento del enlace; salir, desconectar o cambiar de cuenta la
elimina. Un enlace grupal vencido ofrece otra búsqueda. Cancelar la carga libera
el estado ocupado y las respuestas tardías no reemplazan pantallas nuevas.
La navegación del perfil mantiene montado el mismo resultado.

Las regresiones usan un servidor HTTPS de imágenes de prueba generado en
memoria, sin cuentas ni medios de producción. La decodificación usa el motor
gráfico nativo de Robolectric, incluyendo fotos corruptas. Las pruebas
instrumentadas activan los botones mediante el puente real del WebView y leen
sus píxeles tras repetir tres veces fotos
coincidentes, siguiente/anterior, acciones/volver y perfil/regresar. También
cubren 404, datos corruptos, enrolamiento ausente, vencimiento, búsqueda nueva,
cancelación y cambio de cuenta. El certificado de prueba se confía únicamente
en las conexiones de la fixture, sin modificar la confianza TLS de la app.

Validación local: 170 pruebas Android, ktlint, lint sin errores, compilación de
pruebas instrumentadas y APK Debug aprobados. APK `0.1.6-debug-20261102-0751`,
SHA-256 `8baa5555d95341b7c57b94d522b6e4eeb54508cd831c9eef2ed84effad78b92c`.
El Debug local declara explícitamente
`includeSubdomains=false` para los tres hosts de loopback, resolviendo errores
preexistentes de lint sin ampliar su acceso. Sin cambios de servidor,
contratos API, permisos, reconocimiento, consentimientos ni migraciones.
La ejecución instrumentada corresponde al emulador de CI; este host no tiene
emulador ni dispositivo ADB. La validación física en teléfono/gafas sigue
pendiente. El único APK Debug permanece en
`android/app/build/outputs/apk/debug/app-debug.apk`.


## Cabecera global compacta y referencias internas — 2026-11-02

Android comparte una cabecera fija de 96 dp entre Perfil, Trabajo, Buscar y
Ray-Ban: avatar/nombre/correo, Facebook y gafas; ubicación, ciudad y demás
datos empiezan plegados. El editor conserva los campos existentes e incorpora
la carga PDF/DOCX; EN/ES se guarda desde el menú, sin pantalla Idioma. Los
perfiles visitados reutilizan el componente con Volver y sin controles de dueño.
Publicaciones admite imágenes y MP4, señala videos y se refresca al volver de
Ray-Ban o cambiar el estado de una captura. Las escenas de Trabajo de prueba
conservadas llevan una etiqueta visible Simulado/Simulated.

El servidor excluye `facebook` y `simulator` antes de paginar y buscar, y de
los candidatos de duplicados. Sus URLs ordinarias, aliases y derivados no
permiten mostrarlos como publicaciones. Se conservan BYTEA, avatares,
importación y flujo facial autorizado, sin modificar el módulo biométrico ni
añadir migraciones. Los medios compartidos explícitamente mantienen sus permisos.

Validación: 225 pruebas sociales/biométricas/contrato, ocho regresiones de
visibilidad y 177 pruebas Android (siete nuevas) aprobadas; Ruff, arquitectura,
ktlint y lint sin errores. APK Debug en la ruta única habitual; compilaciones
Debug/Release y fuentes instrumentadas verificadas. No se ejecutó QA en
teléfono/gafas. También se verificaron 19 pruebas seleccionadas en una copia
con solo el contenido preparado para el commit.

Desplegados API/worker, con autorización Docker del propietario, como
`realityos-backend:compact-profile-20261102`. Salud real de API y pública,
contrato OpenAPI idéntico, Alembic `20261101_0030 (head)` y ping del worker
verificados. Las 27 comprobaciones HTTP autorizadas en producción validan tres
perfiles, paginación, enlaces internos denegados y permisos de Trabajo; no
invocan proveedores. Permanecen almacenadas las 225 referencias internas,
136 enrolamientos y 22 consentimientos; el código biométrico coincide por SHA-256.
Entorno, comandos, redes y límites de memoria/CPU conservados, junto con el
proxy/gateway y el arranque bajo demanda. Sin migración nueva ni dump.

Release y rollback: `.runtime/compact-profile-20261102-release.json` y
`.runtime/compact-profile-20261102-rollback.json`; comando Compose exacto en
`.runtime/compact-profile-20261102-compose-command.json`, comprobaciones en
`-verification.json` y `-live-smoke.json` bajo el mismo prefijo. Para revertir,
sustituir el último overlay por el rollback y recrear únicamente API/worker.
Se retiraron los contenedores anteriores y el temporal de Alembic; se conservan
la imagen actual y la anterior necesaria para rollback. La entrega omite CI
automático para preservar los ajustes locales de memoria/arranque aún no
publicados. La validación física del APK en teléfono/gafas sigue pendiente.


## Cuentas e integración por espacios — 2026-11-02

Registro por usuario/correo, confirmación y recuperación; acceso Android normal
independiente del Debug local. API REST de registros versionados, relaciones,
notas, adjuntos BYTEA, publicación e indexación por espacio; conexión HTTPS de
contrato explícito y credenciales cifradas. Formularios web/Android y comparación
de campos de medicación sin registrar administraciones. Ver WORKSPACE_DATA.md.

Migración productiva `20261102_0031`; nueve cuentas de trabajadores, tres espacios
con tres miembros, 47 registros y 27 adjuntos importados por HTTPS. Eliminados los
cinco espacios anteriores mediante inventario y respaldo técnico de 24 horas.
Biometría intacta: 136 enrolamientos y 22 consentimientos conservados. Las personas
importadas no se convierten en usuarios ni se enlazan automáticamente al buscador
facial existente. Credenciales del jurado solo en `.runtime/` privado.

Verificados 21 escenarios HTTP, dos respuestas contextuales y búsquedas de objetos
con Meta real. Las 21 publicaciones terminaron de indexarse, sin errores; la
consulta final de linterna devolvió cinco coincidencias señalizadas. Pasan 375
pruebas Python/gateway en una ejecución completa y nueve regresiones posteriores
de adjuntos/contrato. Android: 179 pruebas, lint y APK Debug final.

API/worker: `realityos-backend:workspace-data-20261102-r3`, con salud 200,
OpenAPI coincidente y runtime/proveedores/límites conservados. Panel publicado
por el workflow `Publish workspace web`, ejecución `41552026075` exitosa;
Chromium verificó formulario de registro, acceso real, grupo, expediente y retrato
con autenticación, sin errores JavaScript. Lectura parcial MP4 verificada (206).
Credenciales de las tres cuentas del jurado: `.runtime/jury-access.json` privado.

Pendientes: recepción real de confirmación/recuperación (falta destinatario
autorizado) y QA física de teléfono/gafas. SMTP TLS/autenticación comprobados;
no se han enviado correos de prueba. Las personas importadas no se enlazan al
buscador facial y la comparación clínica sigue siendo explícita de campos.
Los MP4 de evaluación son escenas estáticas sintéticas, rotuladas como tales.

Rollback de imagen backend: `.runtime/workspace-data-20261102-rollback.json`.
Rollback web anterior a esta entrega: `.runtime/workspace-data-web-rollback.json`.
Estos overlays revierten código; no revierten la limpieza de datos. El snapshot
técnico de migración caduca a las 24 horas y no se envió a R2. Comprobantes y
hash del APK: `.runtime/workspace-data-final-verification.json`.

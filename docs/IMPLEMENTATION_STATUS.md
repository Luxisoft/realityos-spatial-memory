# Implementation status — 2026-10-27

## Verified in this workspace

- Device credential, device-session capture, key rotation/revocation, device
  workspace isolation, marketing facts, analytics and detailed Mock video-track
  coverage were added. The current local suite has 36 passing tests.
- The frontend production build passed after adding the administrator-only
  Device Registry and Inventory Intelligence views.

- Backend and gateway lint passed: ruff check backend tests meta-gateway
  gateway-tests.
- Thirty-four automated tests passed locally: application tests cover
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
- Successful CI runs now retain the installable Debug APK for 14 days as the
  `realityos-android-debug-apk` artifact. This is not a signed production APK.
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
  gateway URL configured. They do not contain `MODEL_API_KEY`; the Model API
  credential remains only in FRONTEND's protected runtime environment.
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

## Current deployment blocker

- The API, worker, web bundles and loopback proxy from `88503d5` were deployed
  and the local proxy returned `200` for `/health/live` and `/health/ready`.
  Public `https://realityos.luxisoft.com` is **not** deployed yet: Cloudflare
  currently routes that hostname to the LUXIPANEL origin/rule rather than this
  RealityOS server. During a paused Certbot HTTP-01 test on 2026-10-27, the
  exact temporary ACME file returned `200` directly from this server but `404`
  through Cloudflare. Therefore Let’s Encrypt cannot issue the certificate and
  the Android app correctly cannot obtain its HTTPS live profile yet.
- The external correction is to exclude `realityos.luxisoft.com/*` from the
  LUXIPANEL Cloudflare Worker/origin route and point its DNS/origin to this
  RealityOS server (or temporarily make the A record DNS-only for certificate
  issuance). After that correction, rerun the production workflow; it will
  issue the certificate, install the HTTPS virtual host and make the live
  virtual-glasses bootstrap route available.

## Implemented but not fully environment-verified

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

- A native Android DAT 1.0.1 host now compiles into a debug APK. It initializes
  DAT, provides encrypted device provisioning, opens a Display session, renders
  glasses-side Register/Query screens, requests DAT camera/microphone access
  only from explicit actions, uploads glasses photos and bounded HEVC clips,
  queries existing evidence through a device credential, and requests Android
  TTS output. Backend device queries now provide a short-lived signed Display
  evidence URL and devices can list only their own workspace zones. Its official
  MockDeviceKit instrumentation smoke test passed in a GitHub-hosted Android 15
  emulator on 2026-10-27: simulated Display pairing/lifecycle, preview
  renderer/server, and speech controls ran successfully. It has not been
  installed on physical hardware.

- The Debug Android variant now contains a Developer Preview based on Meta's
  Mock Device Kit. It pairs a virtual Display model, drives the same production
  RealityViewModel/session path, mounts Meta's in-app Display renderer, supports
  a Chrome preview server, mock media feeds/permissions/speech and excludes the
  Mock Device Kit from release. Debug and release compilation plus release-APK
  inspection have run locally. The controller's In-App renderer and Chrome
  preview-server tests passed in a GitHub-hosted Android 15 emulator on
  2026-10-27 (three Mock Device Kit tests total). Interactive phone and
  desktop-Chrome extension validation remain pending; no physical glasses test
  is claimed.

- The virtual-device bootstrap flow has unit coverage for live profile creation,
  key rotation and expiry, but it cannot be exercised from an Android phone
  until the public HTTPS hostname described above is corrected.

## Not implemented

- A full end-to-end Live SAM Video run against a user-provided long clip has
  not been performed. Streaming ingestion and audio extraction/transcription
  from source video remain out of scope.
- Vector retrieval abstraction and optional vector database integration.
- Physical Meta Ray-Ban Display QA (camera, microphone, TTS route, Display
  rendering and recovery).
- Official browser Display simulator validation for the supplementary Web App.
- Restore test.

No claim of physical-glasses, real camera/microphone/audio behavior, or an
end-to-end paid visual inference is made. The official Android MockDeviceKit
instrumentation test did pass in an emulator; it is not equivalent to hardware
validation.

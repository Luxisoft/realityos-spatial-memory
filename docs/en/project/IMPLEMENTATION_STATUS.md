[Español](../../es/project/IMPLEMENTATION_STATUS.md) · [RealityOS](../README.md) · [Index](../INDEX.md)

# Current implementation status

Updated **November 4, 2026**. A build or HTTP check does not approve physical-device testing. Earlier releases remain in Git.

## Local evaluation — current delivery

Owner follow-up: the bottom bar restores Edit as a badge on the avatar’s lower-right corner, matching the previous top bar. **APK generation is deferred until the owner explicitly requests it.** The canonical APK below contains the account-selector photos; this later badge adjustment is source-only. CI is skipped for this follow-up commit because its Android job also generates a Debug APK. Eleven profile/chrome tests and targeted Kotlin formatting passed. Rendered ES/EN states were reviewed at 320–480 dp, including 200% text; the badge remains attached to the avatar and opens Edit independently. This source-only adjustment has not been installed or tested on a physical device.

The account selector now displays each account’s profile photo in a circular avatar. Missing or failed photos use an illustrated default portrait. The pre-login thumbnail route is restricted to the enabled local evaluation catalog, active users and current group membership; it reads only the explicit profile avatar and never falls back to captured or biometric images. Local access/avatar tests (25) and API documentation/contract checks (11) passed. The updated Windows local API serves all nine JPEG thumbnails successfully; API/PostgreSQL/Redis are healthy and the worker is running. Existing local data and private configuration were preserved.

Android validation: **299 unit tests passed**, including photo loading without login credentials, missing-photo fallback and failed-download fallback. Targeted Kotlin formatting, `lintDebug` and `assembleDebug` passed. EN/ES selector renders were reviewed, including 320 dp and 200% text. The APK retains the original signing certificate and was installed successfully as an update over wireless ADB. A new physical-screen review was unavailable because the phone was locked. Canonical APK SHA-256: `34a832950cb3bb4084dc4f78a4f0ba1a8a77690b20423606809582328a731409`.

Android startup now applies English before the first activity on Android 13+, using `LocaleManager`; Android 12 retains the AppCompat path. A saved language choice is preserved. **296 unit tests passed**, including six startup/persistence cases across API 32 and 35; targeted Kotlin formatting, `lintDebug` and the local Debug build passed. EN/ES welcome renders were reviewed, including 320 dp and 200% text. The APK was built in an isolated server checkout with the original signing certificate, installed over wireless ADB and opened on a Moto G54 5G (Android 15): the system remained `es-ES`, the app locale was `en`, and the account selector displayed “Choose an account”. No accounts or app data were cleared. Previous startup APK SHA-256: `a5f49bff5edb3e97ae9459f0e34c0c733fe04da8bcaf5b061fc1bfe046ed0a9b`. This verifies startup only; audio, glasses and live AI checks remain separate.

The primary installation is now Windows/Linux x64 localhost: PostgreSQL, Redis, the existing API and worker. There is no local gateway/proxy/scheduler, external storage connection, Facebook login or ElevenLabs requirement. Nine-account selection is local Debug only. Meta processing and search retain their real provider paths; Android speech uses installed offline voices.

Verified in an isolated Linux Docker project: empty PostgreSQL 16 bootstrap at `20261104_0039`, 9 accounts, 3 groups, 47 records, 27 attachments, 48 licensed publication hashes and 9 avatar downloads, membership isolation, profile editing, group creation/deletion, exact local OpenAPI, worker/Redis ping and persistence after restart. No production credentials or data were used. The 48 existing licensed scene files are now included in Git; their source/license/hash manifest remains authoritative.

Backend/gateway: **591 tests passed**, followed by the additional local queue-resume regression. Android: **290 unit tests passed**; rendered selector states reviewed in EN and ES, including 320 dp and 200% text. Postman script checks and Newman authentication/refresh/failure checks passed. `ktlintCheck`, `lintDebug`, Debug/Release builds and Android test compilation passed. [Sanitized verification receipt](../../assets/local/verification.json).

Windows startup now opens an installed Docker Desktop when the local engine is unavailable and waits up to two minutes for readiness. Nine PowerShell 5.1 regression cases passed with simulated Docker/process commands, covering startup, timeout and remote-context rejection; this does not verify a real Desktop startup.

Local start, diagnostics and stop commands now show English progress by completed steps and live phase summaries, warnings, errors and success messages. Package download logs are suppressed and private values are redacted. Six console regression cases passed in PowerShell 5.1 and six in Bash, plus the Windows isolation suite. A read-only status check confirmed the existing local API, PostgreSQL and Redis healthy and the worker running; no services were restarted to test this console change.

Follow-up: the Windows console uses only the text bar to avoid VS Code overlay collisions. `Start-RealityOS.ps1 -NoCache` rebuilds backend layers while preserving shared caches. Seven PowerShell console cases and the startup/isolation suite passed. The container pip option for intentional root installs was verified offline in a disposable container; the entire modified image has not been rebuilt. At the owner's request, the local containers, two data volumes, networks and backend image were removed for a first-run retest; `.env.local` was preserved unchanged. The next startup must recreate the local runtime.

Pending external validation: complete Windows installation, physical phone/USB/audio voices, glasses and live requests using the judge's own Meta key. These are not claimed by the Linux/container tests. Historical server release details below are retained for traceability and are not prerequisites for this installation. Automatic remote deployments are disabled; the local installer does not stop or modify historical servers.

## Publication classification

Group catalogs, required manual classification, thumbnail labels, video icons and authorized gallery filters are included in revision `20261103_0038`. Unclassified bucket files stay private for their owner to review. The [classification guide](../guides/PUBLICATION_CLASSIFICATION.md) documents this workflow.

The reviewed manifest covers the 48 licensed evaluation publications. Classification was applied to those and one additional visible publication reviewed separately: **49 visible publications across four existing groups** now have a category and tags. Original hashes were checked before and after; an idempotent repeat made zero changes. The private rollback journal is `.runtime/publication-classification-journal.json`, and its dry-run passed. The three jury accounts verified classifications and combined filters through the live API; cross-group filter requests returned `403`. Hidden publications and private media were not classified.

## Implemented

| Area | Current behavior |
| --- | --- |
| Android | One main gallery, one bottom bar for account details, editing, glasses and Muse search/chat; group actions remain above content. Avatar returns to the selected group. Meta controls sit beside its local title. |
| Groups | Publishing requires membership. Owned posts can be copied into several groups with independent reactions/comments; legacy unassigned posts were deleted by owner instruction. Cursor pagination and a single group publication model replace the former personal/public routes. |
| Biometrics | Consent and isolated face search remain. Email onboarding requests a profile photo/avatar and 3–25 accepted private reference photos, with resume and reselection. Meta reference originals and URLs never appear in galleries or account-result thumbnails. |
| Storage | Editable R2/S3 sources, right-side thumbnails, group destinations, immediate/15-minute synchronization, complete-scan reconciliation and revision-safe retirement of imported/shared copies. Remote objects remain untouched. |
| Evidence | BYTEA originals, real provider analysis, versioned evidence and translations. Queries never start capture or fabricate observations. |
| Records and speech | Existing versioned records and clinical comparison; Muse transcription and authenticated ElevenLabs synthesis remain. |

## Current verified server release

- Deployed `realityos-backend:unified-groups-20261103-verified`, Alembic **`20261103_0038`**. Readiness and exact public OpenAPI comparison passed. All three jury accounts browsed their 16 group publications and opened Connections while retaining their session.
- Deleted **234** legacy unassigned publications; retained **70** group publications and their original bytes unchanged. Table fingerprints confirmed unchanged profiles, biometric enrollments/consents, 47 records and 27 record attachments. The migration also preserves 25 existing import request hashes. PostgreSQL upgrade/downgrade/upgrade passed on an isolated restored database.
- Backend/gateway: **588 passed**, plus **14 focused checks** after the final cleanup. Formatting, lint, architecture, documentation and Newman runtime checks passed.
- Android: **287 tests passed**, `ktlintCheck`, `lintDebug`, Debug and Release builds passed. ES/EN rendered checks include 320 dp and 200% text. No physical device was connected. Current Debug APK: `android/app/build/outputs/apk/debug/app-debug.apk`; SHA-256 `5bc5984115419477bd516652c370d463872ae1fdfc806766aa26010d0765e3f1`.
- Private rollback instructions: `.runtime/unified-groups-20261103-rollback.md`, with image/runtime overlay `.runtime/unified-groups-20261103-rollback.json`. Data reversal requires the technical `pre-unified-publications.dump`, which expires after 24 hours (one hour under disk pressure). Old images require schema/data reversal first.

## Earlier verification

- Video renewal deployed as `realityos-backend:evaluation-videos-20261103-final`: healthy API, worker and scheduler, identical public OpenAPI contract and Alembic `20261103_0036`. All 16 renewal tests passed, along with formatting, lint, structure and documentation/Postman checks. The [video receipt](../../assets/storage/video-evaluation-verification.json) records real results and the requested deletion of unused media. Code rollback: `.runtime/evaluation-videos-20261103-rollback.json`; deleted videos cannot be restored.
- [Production deployment succeeded](https://github.com/Luxisoft/realityos-spatial-memory/actions/runs/41709265025): immutable backend image `99fe11f`, following the local `realityos-backend:workspace-privacy-20261103` release. API, worker and scheduler retain their runtime and connection settings. That release used PostgreSQL revision **`20261103_0036`**. Upgrade → downgrade → upgrade passed on a temporary PostgreSQL schema; the production update, readiness and exact public OpenAPI comparison passed.
- The 499-test backend/gateway suite finished CI with **496 passed and three skipped**, including the corrected contract, membership loss and reference-photo privacy. Android passed **228 tests**, formatting/lint and Debug/Release builds. Documentation, structure and Postman validation passed.
- Installable APK: `android/app/build/outputs/apk/debug/app-debug.apk`; SHA-256 `2666a4ee7a15decca18311a28f8d3072e05afe22823b2cae04167a46d78953bc`.
- Image rollback: `.runtime/workspace-privacy-20261103-rollback.json`. Demo visibility journal: `.runtime/real-scenes-20261103-visibility.json`. The technical `pre-workspace-privacy-20261103.dump` expires through server maintenance after 24 hours, or one hour under disk pressure; it is not an official backup and was not uploaded to R2.
- Production retains direct Meta with gateway fallback, private keys and the isolated Windows/Debug login exception. Server maintenance protects active images and the release rollback.
- [Live API receipt](../../assets/storage/workspace-privacy-verification.json): all three jury accounts could sign in, download avatars and new media, read their records and browse their author-specific bucket. Cross-group requests returned `403`; private publication attempts returned `422`.

## Current evaluation data

Only the **existing** groups are in scope. The three evaluation groups have **48 licensed scenes: 12 photos and four videos each**. The 12 replacement videos preserve complete recordings lasting 7.04–28.36 seconds, with native HD resolution and original 25–50 fps cadence. They show picking up keys, preparing instruments, transporting specimens and organizing belongings. The [source, license and hash manifest](../../../simulator/real-scenes/manifest.json) preserves provenance; media files remain outside Git. Real analysis is complete for all 12 videos.

The **47 records, 27 attachments and six enrolled record portraits** are preserved, along with all 36 photos and their identifiers. Renewal added no groups, accounts or memberships. Nine existing connections synchronize only their `evaluation-v3/` subfolder every 15 minutes. All 48 current scenes were verified by remote read-back and SHA-256. At the owner’s explicit request, the 12 previous videos, one rejected candidate and 96 obsolete remote copies were deleted, along with their local bytes and evidence. Two subsequent complete scans of all nine sources preserved current publications, with no duplicates or deleted media reappearing. Rollback of those videos is no longer available.

The [evaluation receipt](../../assets/storage/video-evaluation-verification.json) records **48 positive ES/EN queries, six negatives, six cross-group checks and 12 verified original downloads**. Returned frames and object boxes were visually reviewed. The [reproducible matrix](../testing/VIDEO_EVALUATION.md) retains the questions; annotation revisions and one clip rejected for incorrect boxes remain documented. This is a curated demonstration, not a general accuracy estimate.

Postman keeps exactly **Server requests** and **Localhost requests**, with **449 requests**, including the **87 existing-data walkthrough requests** (48 ES/EN video queries). Jury publication IDs now reference the renewed media. Only the three owner-authorized jury passwords are public. Email-account users, including existing test accounts without completed setup, receive the new private biometric onboarding; no consent or completed enrollment was fabricated.

<a id="next-steps"></a>

## Remaining acceptance work

| Pending | Required evidence |
| --- | --- |
| Phone UI | Physical keyboard, Android navigation insets, camera-overlay gestures and the full acceptance checklist against the identified APK. No device was connected in this session. |
| External integrations | Live Facebook login/import, physical DAT/glasses, real email and the complete Windows installation still need their own recorded walkthroughs. Unit tests do not approve them. |
| Empty database bootstrap | An existing historical baseline issue remains: migration `0001` loads current model metadata and a fresh SQLite bootstrap fails on an unresolved publication foreign key. Existing-schema PostgreSQL upgrade and rollback passed. This release does not claim a fresh Windows installation passed. |
| Third parties and submission | Authenticated DAT terms, `buffalo_l` rights evidence and the final accessible demo/submission receipt remain tracked in [Third parties](THIRD_PARTY.md) and [Hackathon](HACKATHON.md). |

Private credentials, tokens and personal media are excluded from this report. A complete manual acceptance claim requires evidence for every checklist case.

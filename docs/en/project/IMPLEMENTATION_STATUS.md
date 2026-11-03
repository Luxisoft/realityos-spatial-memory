[Español](../../es/project/IMPLEMENTATION_STATUS.md) · [RealityOS](../README.md) · [Index](../INDEX.md)

# Current implementation status

Updated **November 3, 2026**. A build or HTTP check does not approve physical-device testing. Earlier releases remain in Git.

## Implemented

| Area | Current behavior |
| --- | --- |
| Android | Media loading/buffering indicators, expanded details, initial-data skeletons, corrected root panels/insets, full-window group administration, invite sharing and bottom dismissible alerts. |
| Groups | Publishing requires membership. Owned posts can be copied into several groups with independent reactions/comments; legacy unassigned posts remain owner-only. |
| Biometrics | Consent and isolated face search remain. Email onboarding requests a profile photo/avatar and 3–25 accepted private reference photos, with resume and reselection. Meta reference originals and URLs never appear in galleries or account-result thumbnails. |
| Storage | Editable R2/S3 sources, right-side thumbnails, group destinations, immediate/15-minute synchronization, complete-scan reconciliation and revision-safe retirement of imported/shared copies. Remote objects remain untouched. |
| Evidence | BYTEA originals, real provider analysis, versioned evidence and translations. Queries never start capture or fabricate observations. |
| Records and speech | Existing versioned records and clinical comparison; Muse transcription and authenticated ElevenLabs synthesis remain. |

## Verified release

- Local image: `realityos-backend:workspace-privacy-20261103`; API, worker and scheduler use the preserved runtime. PostgreSQL is at **`20261103_0036`**. Upgrade → downgrade → upgrade passed on a temporary PostgreSQL schema; the production update, readiness and exact public OpenAPI comparison passed.
- CI passed the **499 backend/gateway tests**, including the corrected contract, membership loss and reference-photo privacy. Android passed **228 tests**, formatting/lint and Debug/Release builds. Documentation, structure and Postman validation passed.
- Installable APK: `android/app/build/outputs/apk/debug/app-debug.apk`; SHA-256 `2666a4ee7a15decca18311a28f8d3072e05afe22823b2cae04167a46d78953bc`.
- Image rollback: `.runtime/workspace-privacy-20261103-rollback.json`. Demo visibility journal: `.runtime/real-scenes-20261103-visibility.json`. The technical `pre-workspace-privacy-20261103.dump` expires through server maintenance after 24 hours, or one hour under disk pressure; it is not an official backup and was not uploaded to R2.
- Production retains direct Meta with gateway fallback, private keys and the isolated Windows/Debug login exception. Server maintenance protects active images and the release rollback.
- [Live API receipt](../../assets/storage/workspace-privacy-verification.json): all three jury accounts could sign in, download avatars and new media, read their records and browse their author-specific bucket. Cross-group requests returned `403`; private publication attempts returned `422`.

## Current evaluation data

Only the **existing** groups are in scope. Workshop and other discarded scenarios are not recreated. The three evaluation groups now have **48 licensed scenes: 12 photos and four moving videos each**. Videos are 10–15 seconds, 24 fps and at least 720p, with decoded frame-change validation. The [catalog and source/license/hash manifest](../../../simulator/real-scenes/manifest.json) describe the resources; downloaded media stays outside Git. Their real analysis runs through the existing worker queue.

The **47 records, 27 attachments and six enrolled record portraits** are preserved. No group or membership was added by renewal. The current bucket inventory is 48 scene resources plus six QA probes, verified by remote read-back/SHA-256, across **13 active connections**. Author subsets differ. The obsolete social-directory browser connection is disabled; its remote objects were retained.

Postman keeps exactly **Server requests** and **Localhost requests**, with **403 requests**, including the **39 existing-data walkthrough requests**. Jury publication IDs now reference the renewed media. Only the three owner-authorized jury passwords are public. Email-account users, including existing test accounts without completed setup, receive the new private biometric onboarding; no consent or completed enrollment was fabricated.

<a id="next-steps"></a>

## Remaining acceptance work

| Pending | Required evidence |
| --- | --- |
| Phone UI | Physical keyboard, Android navigation insets, camera-overlay gestures and the full acceptance checklist against the identified APK. No device was connected in this session. |
| External integrations | Live Facebook login/import, physical DAT/glasses, real email and the complete Windows installation still need their own recorded walkthroughs. Unit tests do not approve them. |
| Empty database bootstrap | An existing historical baseline issue remains: migration `0001` loads current model metadata and a fresh SQLite bootstrap fails on an unresolved publication foreign key. Existing-schema PostgreSQL upgrade and rollback passed. This release does not claim a fresh Windows installation passed. |
| Third parties and submission | Authenticated DAT terms, `buffalo_l` rights evidence and the final accessible demo/submission receipt remain tracked in [Third parties](THIRD_PARTY.md) and [Hackathon](HACKATHON.md). |

Private credentials, tokens and personal media are excluded from this report. A complete manual acceptance claim requires evidence for every checklist case.

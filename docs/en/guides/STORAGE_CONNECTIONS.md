# Connect a bucket and use its resources

[Español](../../es/guides/STORAGE_CONNECTIONS.md) · [Project](../README.md) · [API](../api/API.md)

A bucket is a private source for your account. Importing copies media into PostgreSQL BYTEA and publishes it in a group you belong to. There is no private publication destination. Searches do not publish probes or enroll faces automatically.

## Android

Open the right menu → **Connections**, above About. Add R2 or S3, enter the HTTPS endpoint, bucket, region, folder and credentials, and select an authorized work group. R2 uses region `auto`. Read/list credentials are recommended; encrypted secrets never return to the app.

The connections panel follows the search/chat layout. Each resource row has a thumbnail on the right; tap it to open the image/video viewer. Select resources and import them into the selected group. Recent imports show progress, duplicate review and retry actions.

Edit can change provider, endpoint, bucket, region, folder and target group. The server validates the new source before saving. A failed change preserves the previous connection. Credential rotation alone preserves imported copies.

**Changing the source or disconnecting retires its proven imported copies and their shared descendants.** Source revisions prevent old workers from publishing again. Independent records, avatars and biometric references are preserved. Remote bucket objects are never deleted by this operation.

## Synchronization and limits

Saving a group connection enables synchronization immediately and every **15 minutes**. Update now, pause and other intervals remain available. Folder scans are paginated. Missing keys retire local copies only after an entire successful scan; failed or incomplete scans never infer deletion. An unchanged source/content/destination is idempotent.

JPEG, PNG, WebP and MP4 publications use the existing analysis and duplicate review. Videos are limited to 120 seconds; downloads to 64 MiB and configured server limits. PDF/DOCX can replace the private CV, up to 10 MiB. Object image queries wait up to three minutes. Face search still requires biometric consent and workspace authorization.

## Server and API

`/v1/me/storage-connections` includes CRUD, test, objects, content, imports/retry, syncs/run and CV. See the [generated contract](../api/API_REFERENCE.md). Postman retains **Server requests** and **Localhost requests** with independent variables.

Keep `STORAGE_ENCRYPTION_KEY` stable in private runtime configuration, shared by API and worker. The scheduler emits jobs; the worker processes them. Group membership and connection revision are checked again before download and publication. HTTPS/public-address validation, pinned addresses, TLS verification and rejected redirects remain enforced.

## Licensed evaluation scenes

`simulator/real-scenes/catalog.json` and `manifest.json` describe 36 preserved photos and 12 complete videos: four per existing security, nursing and memory group. Recordings retain their original duration (7–29 seconds) and at least native 720p resolution. Sources, authors, licenses and hashes document provenance; downloaded files are ignored by Git.

The [video matrix](../testing/VIDEO_EVALUATION.md) contains ES/EN queries and expected intervals. `scripts/prepare_evaluation_videos.py` prepares only videos and reuses verified bytes. `scripts/renew_evaluation_videos.py` manages inventory, staging, real analysis, acceptance, activation and rollback with a private journal. It does not recreate accounts, groups or records.

Synchronization selects `demo/v2/{scenario}/{username}/evaluation-v3/` within the nine existing connections, every 15 minutes. All 36 photos keep their identifiers. At the owner's explicit request, replaced videos, the rejected candidate and 96 obsolete remote copies were deleted, including `evaluation-v2-rollback/`. The active generation retains its 48 scenes. QA stays under `demo/v1/qa/`.

Keep only the active folder selected; legacy preparation tools reject the versioned renewal. `scripts/prepare_bucket_demo.py` now honors the manifest's explicit folder and owner. Read/write credentials stay in private files and are not included in Postman.

Check the dated [implementation status](../project/IMPLEMENTATION_STATUS.md) for executed R2/API checks. Phone and glasses acceptance require separate device evidence.

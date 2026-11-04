> **Current direction: localhost is primary.** Windows/Linux x64 run PostgreSQL, Redis, API and worker. Meta uses the judge’s own key; speech output uses installed Android voices. Gateway, buckets, Facebook, SMTP, scheduler and ElevenLabs are outside the local walkthrough. Remote configuration in this guide is historical. [Current installation](../deployment/DEPLOYMENT_LOCALHOST.md).

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

## Local evaluation media

Local evaluation initializes application tables from versioned SQL in `simulator/database/` and imports the originals from the organized `simulator/media/` tree into PostgreSQL BYTEA. Source URLs, licenses, hashes and fixture paths are recorded in `simulator/media/manifest.csv` for provenance. They are not an alternative publication database.

The local runtime does not use buckets or remote imports. Its two groups contain 25 publications. Postman examples query a disposable database initialized with the same SQL; playback, byte ranges and permission checks are described in [video evaluation](../testing/VIDEO_EVALUATION.md).

Server storage integration remains a separate server capability. Its historical execution evidence is dated in [implementation status](../project/IMPLEMENTATION_STATUS.md); local preparation does not change remote sources or server data.

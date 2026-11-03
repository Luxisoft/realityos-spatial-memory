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

`simulator/real-scenes/catalog.json` and `manifest.json` describe **48 licensed resources**: 12 photos and four moving recordings for each of security, nursing and memory. Videos contain 10–15 seconds at 24 fps and at least 720p; frame-change checks reject still-image recordings. Accounts and roles remain fictional. Source links, licenses, hashes and validation metrics are in the manifest. Downloaded assets are ignored by Git.

Run `scripts/prepare_real_scenes.py` to prepare and validate media. `scripts/prepare_bucket_demo.py --upload --credentials-file /private/r2.json` uploads and reads back each object to verify SHA-256. It includes 48 scenes and six separate QA probes. Credentials require endpoint, bucket, region, access_key and secret_key; never publish the file.

Scenario folders are `demo/v2/{scenario}/{username}/`, partitioned by author. QA probes stay under `demo/v1/qa/`. `scripts/connect_demo_buckets.py --apply --read-credentials-file /private/r2.json` configures the nine existing scenario accounts and four QA accounts, preserving accounts and memberships. It validates sources before retiring old copies. The retired social-directory browser connection is disabled; its remote files remain untouched.

`scripts/refresh_demo_gallery.py --apply --journal /private/demo-visibility.json` replaces only identified old demo publications, preserving records and biometric portraits. The journal supports `--rollback`. Indexing uses the configured real provider; the media manifest is not fabricated detection evidence.

Check the dated [implementation status](../project/IMPLEMENTATION_STATUS.md) for executed R2/API checks. Phone and glasses acceptance require separate device evidence.

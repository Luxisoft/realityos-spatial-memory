# Connect a bucket and use its resources

[Español](../../es/guides/STORAGE_CONNECTIONS.md) · [Project](../README.md) · [API](../api/API.md)

Your bucket is a private source connected to your RealityOS account. **Importing stores a copy in RealityOS** and uses the existing publication, analysis and duplicate-review workflows. Disconnecting keeps imported publications and history. Using a resource as a search probe does not publish it or register new evidence.

## Android

Open **Profile → My connections → Add bucket**. Choose R2 or S3 and enter a name, HTTPS endpoint, bucket, region, optional folder, Access Key ID and Secret Access Key. R2 uses its S3 API endpoint and region `auto`. Use read/list credentials; the bucket remains private. Save and test access. Credentials are encrypted on the server and are not returned to the app.

Browse folders and previews, select resources, choose your private profile or an authorized group, and confirm import. Recent imports show individual results; review duplicates or retry failed items. Sharing a publication never shares the connection or bucket credentials.

Supported publication formats: JPEG, PNG, WebP, MP4 (up to 120 seconds). Remote downloads are capped at 64 MiB and also respect existing server image/video limits (images default to 10 MiB). PDF/DOCX can replace the private CV after confirmation, up to 10 MiB. Other formats are marked unsupported.

Use an image for object search, or an image/video for face search in the selected workspace. Facial consent, enrollment and quality rules still apply; imports do not automatically enroll faces. Authorized results open evidence, profiles or records.

## Synchronization

Configure manual synchronization or enable 15-minute, hourly or daily runs. The selected folder and subfolders are scanned in pages; Update now processes the next page. Automatic scans continue every minute while pages remain. Changed files enter the existing duplicate review. Unchanged source/content/destination combinations do not create another publication while the original remains published. If it was deleted or replaced, you can import the bucket original again. Remote deletions or listing failures never delete imported copies.

Pause disables the schedule. Disconnect disables future downloads while retaining imported copies. Group membership is rechecked before downloading and publishing. Rotate credentials with Edit credentials; create another connection to change endpoint, bucket, region or root folder.

## API and deployment

`/v1/me/storage-connections` exposes private CRUD, `/test`, `/objects`, `/content`, `/imports`, `/imports/{id}/retry`, `/syncs`, `/syncs/{id}/run` and `/cv`. See [API_REFERENCE](../api/API_REFERENCE.md). Postman keeps both Server requests and Localhost requests; storage operations require your own connection and explicit write enablement.

Set a stable random `STORAGE_ENCRYPTION_KEY` in ignored `.env.storage` (0600). On local Windows, the launcher generates this key in `.env.local`; `.env.storage` is for the server. API and worker must use the same key; changing it requires re-encrypting existing credentials. The scheduler emits tasks and the worker processes imports. Durable pending jobs and expired leases recover without storing file payloads or credentials in Redis.

S3 SigV4 requests validate HTTPS/public addresses and pin the connection IP while preserving hostname verification and SNI. Redirects and private-network endpoints are rejected. Imports serialize per connection; production worker concurrency remains one.

## Demo preparation and acceptance

**Prepared in production on November 3, 2026:** 426 synthetic resources uploaded to the private `realityos-demo` bucket, all read-back verified with SHA-256. The nine scenario accounts and four QA accounts already have their sources under **Profile → My connections**. Open `Demo police`, `Demo nursing`, `Demo memory` or `Demo qa` for your account; no key configuration or phone downloads are needed.

The `qa-hackathon-admin` account also has **Directorio social y taller (QA)** with 327 browsable resources. Total: 14 private connections for 13 accounts. Originals, previews, HTTP video ranges, PDF and cross-account access rejection were verified. [Public receipt without secrets](../../assets/storage/demo-verification.json). This preparation does not mark manual Android cases as executed.

Existing Luxisoft credentials were reused at the owner’s instruction. They are encrypted per connection and never returned to clients. They retain their original permissions, including writes; they are not described as a read-only R2 token. The app connector performs read/list operations only and enforces each connection’s folder. New connections should use read/list credentials limited to the bucket.

### Repeat preparation

`scripts/prepare_bucket_demo.py` defaults to an offline inventory in `.runtime/bucket-demo-manifest.json`. Use `--upload --credentials-file /private/r2.json` to upload and verify synthetic resources by reading them back and comparing SHA-256. `--create-bucket` creates the configured bucket when needed. Private configuration fields: `endpoint`, `bucket`, `region`, `access_key`, `secret_key`. Preparation needs write credentials; new evaluator connections should use read/list credentials limited to the bucket.

Prefixes: `demo/v1/police/`, `nursing/`, `memory/`, `qa/`. Existing scenarios remain intact; personal/Facebook media is excluded. Scenario JSON files describe fixtures and are not automatically imported as records by the media browser.

QA acceptance: connect, test, preview, import image/video, wait for analysis, search, repeat import, change an object, synchronize and disconnect. Repeat from another account to verify connection isolation. Real R2 and physical-device checks require recorded execution; see [implementation status](../project/IMPLEMENTATION_STATUS.md).

After upload verification, the operator runs `scripts/connect_demo_buckets.py --apply --read-credentials-file /private/r2-readonly.json` in the backend environment with `DATABASE_URL` and `STORAGE_ENCRYPTION_KEY`. This prepares private connections for the nine existing scenario accounts and four QA accounts. Without `--apply` it only checks accounts. It is idempotent and does not create accounts, posts, memberships or enrollments. Use list/read credentials with the same JSON format as the upload configuration. Evaluators receive ready connections in **My connections**. To reproduce the additional connection, sign in as QA admin and add another connection to the same bucket with folder `demo/v1/social-directory/` and name **Directorio social y taller (QA)**.

The local inventory contains **426 synthetic resources**, including social directory and workshop media under `demo/v1/social-directory/`; the count depends on generated media available on the host. The manifest records every SHA-256. Existing database originals and scenarios remain available.

Provider references: [Cloudflare R2 S3 API](https://developers.cloudflare.com/r2/api/s3/api/) and [boto3 configuration](https://developers.cloudflare.com/r2/examples/aws/boto3/).

A new import lets you review a file again after cancelling its duplicate candidate; replaying the original request preserves that cancellation. Once all pending files are confirmed, the import is reported as completed. Folder names containing spaces, Unicode and reserved characters retain correct S3 signing.

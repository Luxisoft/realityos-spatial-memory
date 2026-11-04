[Español](../../es/api/API.md) · [RealityOS](../README.md)

# API / Postman

The existing API runs inside local Docker. The collection reflects enabled localhost routes and retains a disabled historical server catalog.

<a id="quick-start"></a>

## Import → Send

1. Start the [local installation](../deployment/DEPLOYMENT_LOCALHOST.md).
2. Import the [collection](../../postman/RealityOS.postman_collection.json) and select **No environment**.
3. Open **Localhost requests → 00 Quick start** or **00 Local scenarios → Police / Meta Social Media**.
4. Click **Send**. The account selector obtains real tokens; renewal is automatic. No passwords are needed.

`localhost_user_id` selects the quick-start account. Scenarios retain independent `security_` and `meta_social_` prefixes, IDs and sessions. List the six available users with `GET /v1/auth/local-accounts`; `POST /v1/auth/local-select` accepts `{"user_id":"..."}`. These routes do not exist in production. They do not grant cross-workspace access or biometric consent.

Initial preparation loads local files and the worker indexes them using your Meta key. The 48 bilingual video checks require completed indexing; no AI results are precomputed.

**Server requests is disabled** by a script that prevents HTTP requests. It contains no endpoint or passwords. Localhost excludes buckets, Facebook, remote integrations, SMTP and remote TTS. The [local contract](../../../tests/contracts/openapi.local.json) is checked against actual routes; the [historical contract](../../../tests/contracts/openapi.json) remains separate.

Writes require the appropriate prefixed `enable_write_requests=true` variable. Use authorized resource IDs and select files for multipart operations. Publications require a group, category and tags. The catalog includes profile editing, publishing, deletion and queries. Authentication failures stop the request rather than being reported as success.

The [optional local environment](../../postman/RealityOS.local.postman_environment.json) contains no secrets. Keep the Meta key only in `.env.local`, never in Postman or the APK. Session tokens are obtained at runtime and are not exported.

Swagger: `http://localhost:8080/docs`. OpenAPI: `http://localhost:8080/v1/openapi.json`. [Generated reference](API_REFERENCE.md) · [Data and records](../guides/WORKSPACE_DATA.md) · [Scenarios](../guides/DEMO.md#access).

<p align="center"><a href="API.md"><img src="assets/readme/language-en-active.svg" alt="English" height="32"></a> <a href="API.es.md"><img src="assets/readme/language-es.svg" alt="Español" height="32"></a></p>

# RealityOS API

**Query people, records and visual evidence from your own tools.** This guide explains what to send, what to expect and how to begin. Permissions are the same as in Android.

[📥 Postman collection](https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/docs/postman/RealityOS.postman_collection.json) · [Optional environments](postman/README.md) · [Full reference](API_REFERENCE.md) · [Documentation index](README.md)

<a id="quick-start"></a>

## Test existing server data: Import → Send

**The public collection contains 39 ready requests against the current server and its three workspaces.** Usernames, passwords, workspace IDs, record IDs, publication IDs and questions are already configured. No data entry, token copying, file selection or initial login request is needed.

1. In Postman, click **Import** and paste this link:

   ```text
   https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/docs/postman/RealityOS.postman_collection.json
   ```

2. Leave **No environment** selected. Open **01 Police**, **02 Nursing** or **03 Memory**.
3. Open any request and click **Send**. Sign-in and renewal run automatically. Use **Run** to execute an entire scenario folder.

| Folder | Included username | Included password | Existing workspace |
| --- | --- | --- | --- |
| 01 Police | `alex-rivera` | `liMPaFG6f8KPbzSRcNFFpdu74dHmVxU5` | Pacific Ridge Police Department |
| 02 Nursing | `elena-marquez` | `GS112vlwNHjj4tVuaxDZrOpTs0s7lomj` | California Valley Medical Center |
| 03 Memory | `noah-brooks` | `FqgO_9etDGlTkZDJj_MxYGekwFatXNMB` | Sonoran Neurological Institute |

These three evaluation accounts and passwords are public with the owner's authorization of November 3, 2026. They retain their existing administrator role in their workspace. The evaluation collection reads existing data. The server and providers are live; the prepared fictional people and scenes retain their recorded provenance.

Each folder covers the current session, login, refresh, workspaces, record lists and details, revisions, gallery posts, image download, profiles and AI queries. Police opens case 1; Nursing opens Ana Solis; Memory opens Luis Moreno. The server contains 47 records and 21 group publications. Responses are fetched from the server when the request is sent.

The [public environment](postman/RealityOS.public.postman_environment.json) is optional and contains the same values. Replacing them with your own account is entirely optional. [Use these accounts in Android](DEMO.md#access).

## Choose an operation

| I want to… | Request | Result / requirement |
| --- | --- | --- |
| Check availability | `GET /health/live` · `GET /health/ready` | Process health and database readiness. |
| Sign in or renew | `POST /v1/auth/login` · `/v1/auth/refresh` | Session tokens; refresh rotates the previous refresh token. |
| Choose an organization | `GET /v1/workspaces` | My workspace IDs and roles. |
| Search a face | `POST /v1/faces/search` | `matches` and `matches_records` candidates; requires authorization and prior enrollments. |
| Open a record | `GET /v1/workspaces/{workspace_id}/records/{record_id}` | Authorized data, source and relationships. |
| Query records | `POST /v1/workspaces/{workspace_id}/records/search` | Contextual answer with permitted references. |
| Find an object | `POST /v1/queries` · `/v1/queries/image` · `/v1/queries/audio` | Last-observed evidence, not a guaranteed current location. |
| Register evidence | `POST /v1/sessions` → `/v1/captures` → `/v1/captures/{capture_id}/process` | Stored original and analysis job; requires a role and consented session. |
| Check progress | `GET /v1/jobs/{job_id}` | Requested job status; 202 does not mean processing is complete. |
| Read a profile | `GET /v1/profiles/{user_id}` | Visible projection; never the private CV file. |
| Import my data | `POST /v1/integrations/imports` | Versioned, idempotent batch using an integration key. |
| Hear an answer | `POST /v1/tts` | ElevenLabs WAV; requires authentication and uses a provider. |

[All methods, fields and declared responses →](API_REFERENCE.md)

## Variables and authentication

The `security_`, `hospital_` and `memory_` prefixes keep accounts, sessions and resource IDs separate. All required values are included. Only tokens and `session_identity` start empty: scripts obtain them automatically before sending a protected request. Authentication failure stops the request. Changing the account or API origin starts a new session.

`query` is the visual question and `record_question` searches records; `language=en` requests English AI answers. Observations report when something was last seen. A response without matches does not fabricate evidence.

## Complete reference for integrators

The [reference collection](postman/RealityOS.reference.postman_collection.json) preserves all 324 server and localhost requests, including writes, devices and integrations. Those templates need each operation's own permissions, files and credentials. Its optional environments are [server](postman/RealityOS.reference.postman_environment.json) and [localhost](postman/RealityOS.local.postman_environment.json). They are not needed to run the public jury collection.

Reference writes retain `enable_write_requests=false`. The [Windows installation](DEPLOYMENT_LOCALHOST.md) remains optional and is not needed to evaluate the existing server data.

## Troubleshooting

| Result | Check |
| --- | --- |
| 401 | Missing, expired or revoked session; refresh or sign in. |
| 403 | Insufficient role, membership or consent; another credential does not grant additional permission. |
| 404 | Unknown ID/route, inaccessible resource or a local route used in production. |
| 409 | Version conflict, duplicate or idempotency key reused with different content. |
| 422 | Fields, format, limits or file quality; read `detail`. |
| 429 | Request or attempt limit; respect the indicated delay. |
| 5xx / failed job | Service/provider availability; inspect job state before repeating a billable operation. |

## Contract and maintenance

[Interactive Swagger](https://realityos.luxisoft.com/docs) · [OpenAPI](https://realityos.luxisoft.com/v1/openapi.json) · [Versioned contract](../tests/contracts/openapi.json) · [Data imports](WORKSPACE_DATA.md)

Regenerate the reference and Postman with `python scripts/build_api_docs.py`; detect drift with `python scripts/build_api_docs.py --check`. The collection uses the [official v2.1 format](https://schema.postman.com/); see Postman's [import guide](https://learning.postman.com/docs/getting-started/importing-and-exporting/importing-data/). Original notes remain in the [historical reference](reference/API.legacy.md).

Offline script checks: `node scripts/check_postman_scripts.cjs`.

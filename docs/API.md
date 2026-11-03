<p align="center"><a href="API.md"><img src="assets/readme/language-en-active.svg" alt="English" height="32"></a> <a href="API.es.md"><img src="assets/readme/language-es.svg" alt="Español" height="32"></a></p>

# RealityOS API

**Query people, records and visual evidence from your own tools.** This guide explains what to send, what to expect and how to begin. Permissions are the same as in Android.

[📥 Postman collection](https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/docs/postman/RealityOS.postman_collection.json) · [Optional environments](postman/README.md) · [Full reference](API_REFERENCE.md) · [Documentation index](README.md)

<a id="quick-start"></a>

## First test: import and run

**Use Postman desktop and the existing server.** The public account checks access and queries in an empty workspace. For prepared photos, posts and records in Android, use the [scenario account guide](DEMO.md#access).

1. In Postman, open **Import** (in recent versions, **Use resources or import → Import**) and paste this link:

   ```text
   https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/docs/postman/RealityOS.postman_collection.json
   ```

2. Confirm the import and leave the environment selector on **No environment**. The collection already contains the username, password and workspace.
3. Open **Server requests → 00 Quick start** and click **Run**. Run that subfolder's five requests once, in the included order. If **Start run** appears, use it to start.
4. Check the responses:

If an older collection shows **Consultas servidor / Consultas localhost**, these are the same folders; **00 Quick start / Inicio rápido** is the same quick start.

| Request | Expected result |
| --- | --- |
| `GET /health/live` | `200`: server available. |
| `POST /v1/auth/login` | `200`: signed in; tokens saved automatically. |
| `GET /v1/auth/me` | `200`: authenticated test account. |
| `GET /v1/workspaces` | `200`: **Postman Demo - public test workspace** appears. |
| `POST /v1/queries` | `200`: no matches because this workspace is empty. |

**Included access:** `postman-demo@realityos.example.test` / `RealityOS-Postman-Demo-2026!`. This shared account has query permission in its workspace, without administration or capture. It is already confirmed; its `example.test` address does not receive email. The official [import instructions](https://learning.postman.com/docs/getting-started/importing-and-exporting/importing-data/) and [folder run instructions](https://learning.postman.com/docs/tests-and-scripts/running-collections/intro-to-collection-runs/) describe Postman's controls.

### Query a scenario with prepared data

In **Collection → Variables**, set `server_email` to the username from your access card and `server_password` to its password. Clear `server_access_token` and `server_refresh_token`. Run **login**, then **GET /v1/workspaces**; copy the assigned group's ID into `server_workspace_id` before running the query. That group's photos and records are already loaded; the public account cannot access them.

<details>
<summary><strong>Optional: test your localhost installation</strong></summary>

Complete the [Windows setup](DEPLOYMENT_LOCALHOST.md) first. Then run this once from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\local\Enable-PostmanDemo.ps1
```

Run **Localhost requests → 00 Quick start**. This folder uses the included `http://localhost:8080`, `postman-local@realityos.example.test` and `RealityOS-Postman-Local-2026!`. Setup creates an independent local query account and empty workspace. It does not copy server scenarios or credentials.

</details>

<details>
<summary><strong>Optional: environments and your own account</strong></summary>

Downloadable environments contain the same demo variables and are optional. An active environment overrides the collection: edit its values or return to **No environment** to avoid mixing accounts. Tokens are saved after login; they are not published on GitHub. A new personal account requires confirmation through a real email address. [Postman variable scopes](https://learning.postman.com/docs/sending-requests/variables/variables/).

</details>

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

Every variable starts with `server_` or `localhost_`. Each folder exclusively references its prefix, including tokens, IDs and write controls. Additional local routes only appear under **Localhost requests → Local installation only**.

| Variable (add the prefix) | Value or purpose |
| --- | --- |
| `base_url` | Preconfigured origin without `/v1`. If you change `LOCAL_HTTP_PORT`, update `localhost_base_url`. |
| `email`, `username`, `password`, `display_name` | Preconfigured demo account; replace with your own account if needed. |
| `access_token`, `refresh_token` | Saved per target after successful login/refresh, even without an active environment. |
| `user_id`, `workspace_id` | Demo account and workspace IDs; independent per target. |
| `query`, `language` | Editable example question and language (`en` or `es`). |
| `new_email`, `new_password` | New address/password for correcting or recovering your own account; distinct from current credentials. |
| Other IDs | Declared and described; fill from authorized responses. No invented IDs for nonexistent media or records. |
| `device_id`, `device_key`, `integration_key`, `facebook_access_token`, `token` | Issued by device/integration provisioning, Facebook login or an action link; not demo credentials. |
| `enable_write_requests` | Initially `false`; independent per target. |

[Prepare the Windows installation](DEPLOYMENT_LOCALHOST.md). The collection does not install the local backend.

## Files, examples and execution

- In **Body → form-data**, choose your file in the File field. Enable it if it is optional and disabled. Postman supplies the multipart `Content-Type` and boundary.
- Image queries: JPEG/PNG/WebP; audio queries: WAV. Captures accept images and video according to the contract. CV uploads accept PDF/DOCX.
- Included bodies are synthetic templates: complete fields and replace IDs before sending. For face search, choose an authorized photo/video or existing media; reusing an enrollment photo tests integration only.
- Writes are skipped while `server_enable_write_requests=false` / `localhost_enable_write_requests=false`. Explicitly enable it for capture, enrollment or administration tests. Start with individual requests; running the entire collection includes creation, revocation and deletion operations.
- AI queries, transcription and speech can use provider credits even when they do not create evidence. Importing the collection sends no requests.
- A 200 may contain `found=false`, partial results or `simulated`. Inspect the body, source and date. Facial similarity is not identity probability.

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

<p align="center"><a href="../../en/api/API_REFERENCE.md"><img src="../../assets/readme/language-en-active.svg" alt="English" height="32"></a> <a href="../../es/api/API_REFERENCE.md"><img src="../../assets/readme/language-es.svg" alt="Español" height="32"></a></p>

# Operation reference

[← API](API.md) · [Postman](../../postman/RealityOS.reference.postman_collection.json)

Generated from the contract. Operation and field names preserve API identifiers. ✓ = required. Examples need your own identifiers and files; they are not captured production responses.

Reference examples use unprefixed variables. The downloadable collection includes Server requests and Localhost requests folders and prefixes each variable with `server_` or `localhost_`, with demo credentials and workspace IDs preconfigured.

Bearer = user session; device = device credentials; integration = integration key; signed = temporary link; none = no transport credentials.

## Access

| Operation | Summary | Access | Required fields | Manual |
| --- | --- | --- | --- | --- |
| `POST /v1/auth/login` | Login | none | `email`, `password` | — |
| `POST /v1/auth/refresh` | Refresh | none | `refresh_token` | — |
| `GET /v1/auth/me` | Me | bearer | — | — |
| `POST /v1/auth/register` | Register | none | `username`, `email`, `display_name`, `password` | ✓ |
| `POST /v1/auth/resend-confirmation` | Resend | none | `email` | ✓ |
| `POST /v1/auth/change-pending-email` | Change Pending Email | none | `username`, `email`, `password` | ✓ |
| `POST /v1/auth/confirm-email` | Confirm | none | `token` | ✓ |
| `POST /v1/auth/forgot-password` | Forgot | none | `email` | ✓ |
| `POST /v1/auth/reset-password` | Reset | none | `token`, `password` | ✓ |
| `GET /v1/auth/account-session` | Account Session | bearer | — | — |
| `POST /v1/auth/account-capture-profile` | Capture Profile | bearer | — | ✓ |
| `POST /v1/auth/logout` | Logout | bearer | — | ✓ |
| `POST /v1/auth/facebook` | Facebook Login | none | `access_token` | ✓ |
| `POST /v1/auth/guest` | Guest Login | none | `device_id` | ✓ |

<details>

<summary>POST /v1/auth/login</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `email` | body | ✓ | `string` | `{"maxLength": 320, "minLength": 3}` |
| `password` | body | ✓ | `string` | `{"maxLength": 512, "minLength": 1}` |

```json

{
  "email": "{{email}}",
  "password": "{{password}}"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/auth/refresh</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `refresh_token` | body | ✓ | `string` | `{"minLength": 20}` |

```json

{
  "refresh_token": "{{refresh_token}}"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/auth/me</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>POST /v1/auth/register</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `username` | body | ✓ | `string` | `{"pattern": "^[a-zA-Z][a-zA-Z0-9_.-]{2,63}$"}` |
| `email` | body | ✓ | `string` | `{"maxLength": 320, "minLength": 5}` |
| `display_name` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 1}` |
| `password` | body | ✓ | `string` | `{"maxLength": 512, "minLength": 12}` |

```json

{
  "username": "{{username}}",
  "email": "{{email}}",
  "display_name": "{{display_name}}",
  "password": "{{password}}"
}

```

Declared responses: `202`, `422`.

</details>

<details>

<summary>POST /v1/auth/resend-confirmation</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `email` | body | ✓ | `string` | `{"maxLength": 320, "minLength": 3}` |

```json

{
  "email": "{{email}}"
}

```

Declared responses: `202`, `422`.

</details>

<details>

<summary>POST /v1/auth/change-pending-email</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `username` | body | ✓ | `string` | `{"maxLength": 320, "minLength": 3}` |
| `email` | body | ✓ | `string` | `{"maxLength": 320, "minLength": 5}` |
| `password` | body | ✓ | `string` | `{"maxLength": 512, "minLength": 1}` |

```json

{
  "username": "{{username}}",
  "email": "{{new_email}}",
  "password": "{{password}}"
}

```

Declared responses: `202`, `422`.

</details>

<details>

<summary>POST /v1/auth/confirm-email</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `token` | body | ✓ | `string` | `{"maxLength": 128, "minLength": 32}` |

```json

{
  "token": "{{token}}"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/auth/forgot-password</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `email` | body | ✓ | `string` | `{"maxLength": 320, "minLength": 3}` |

```json

{
  "email": "{{email}}"
}

```

Declared responses: `202`, `422`.

</details>

<details>

<summary>POST /v1/auth/reset-password</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `token` | body | ✓ | `string` | `{"maxLength": 128, "minLength": 32}` |
| `password` | body | ✓ | `string` | `{"maxLength": 512, "minLength": 12}` |

```json

{
  "token": "{{token}}",
  "password": "{{new_password}}"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/auth/account-session</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>POST /v1/auth/account-capture-profile</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>POST /v1/auth/logout</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>POST /v1/auth/facebook</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `access_token` | body | ✓ | `string` | `{"maxLength": 4096, "minLength": 1}` |
| `device_id` | body | — | `string / null` | `{}` |

```json

{
  "access_token": "{{facebook_access_token}}"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/auth/guest</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `device_id` | body | ✓ | `string` | `{"maxLength": 128, "minLength": 1}` |

```json

{
  "device_id": "{{device_id}}"
}

```

Declared responses: `200`, `422`.

</details>

## Workspaces and records

| Operation | Summary | Access | Required fields | Manual |
| --- | --- | --- | --- | --- |
| `GET /v1/workspaces` | List Workspaces | bearer | — | — |
| `POST /v1/workspaces` | Create Workspace | bearer | `name` | ✓ |
| `GET /v1/workspaces/{workspace_id}/zones` | List Zones | bearer | `workspace_id` | — |
| `POST /v1/workspaces/{workspace_id}/zones` | Create Zone | bearer | `workspace_id`, `name` | ✓ |
| `POST /v1/workspaces/{workspace_id}/connections` | Create Connection | bearer | `workspace_id`, `name` | ✓ |
| `GET /v1/workspaces/{workspace_id}/connections` | Connections | bearer | `workspace_id` | — |
| `DELETE /v1/workspaces/{workspace_id}/connections/{connection_id}` | Revoke Connection | bearer | `workspace_id`, `connection_id` | ✓ |
| `POST /v1/integrations/imports` | Ingest | integration | `request_key`, `records` | ✓ |
| `GET /v1/integrations/imports/{run_id}` | Import Status | integration | `run_id` | — |
| `GET /v1/workspaces/{workspace_id}/records` | Records | bearer | `workspace_id` | — |
| `GET /v1/workspaces/{workspace_id}/records/{record_id}` | Record Detail | bearer | `workspace_id`, `record_id` | — |
| `POST /v1/workspaces/{workspace_id}/records/{record_id}/notes` | Add Note | bearer | `workspace_id`, `record_id`, `text`, `occurred_at` | ✓ |
| `GET /v1/workspaces/{workspace_id}/records/{record_id}/revisions` | Revisions | bearer | `workspace_id`, `record_id` | — |
| `POST /v1/workspaces/{workspace_id}/records/{record_id}/publications` | Link Publication | bearer | `workspace_id`, `record_id`, `publication_id` | ✓ |
| `POST /v1/workspaces/{workspace_id}/records/{person_id}/medication-check` | Medication Check | bearer | `workspace_id`, `person_id`, `prescription_id`, `observed_ingredient`, `observed_concentration`, `checked_at` | ✓ |
| `POST /v1/integrations/records/{record_id}/media` | Upload | integration | `record_id`, `external_id`, `file` | ✓ |
| `POST /v1/integrations/records/{record_id}/index` | Retry Index | integration | `record_id` | ✓ |
| `GET /v1/workspaces/{workspace_id}/record-media/{link_id}` | Media | bearer | `workspace_id`, `link_id` | — |
| `POST /v1/workspaces/{workspace_id}/test-workers` | Provision | bearer | `workspace_id`, `username`, `display_name` | ✓ |
| `POST /v1/workspaces/{workspace_id}/records/search` | Search Records | bearer | `workspace_id`, `question` | — |
| `POST /v1/workspaces/{workspace_id}/connections/{connection_id}/sync` | Sync | bearer | `workspace_id`, `connection_id` | ✓ |

<details>

<summary>GET /v1/workspaces</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>POST /v1/workspaces</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `name` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 2}` |
| `description` | body | — | `string / null` | `{}` |

```json

{
  "name": "example-name"
}

```

Declared responses: `201`, `422`.

</details>

<details>

<summary>GET /v1/workspaces/{workspace_id}/zones</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/workspaces/{workspace_id}/zones</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `name` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 1}` |
| `parent_id` | body | — | `string / null` | `{}` |
| `kind` | body | — | `string` | `{"maxLength": 32, "minLength": 1, "default": "zone"}` |
| `sort_order` | body | — | `integer` | `{"maximum": 9999.0, "minimum": 0.0, "default": 0}` |

```json

{
  "name": "example-name"
}

```

Declared responses: `201`, `422`.

</details>

<details>

<summary>POST /v1/workspaces/{workspace_id}/connections</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `name` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 2}` |
| `source_url` | body | — | `string / null` | `{}` |
| `source_token` | body | — | `string / null` | `{}` |

```json

{
  "name": "example-name"
}

```

Declared responses: `201`, `422`.

</details>

<details>

<summary>GET /v1/workspaces/{workspace_id}/connections</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>DELETE /v1/workspaces/{workspace_id}/connections/{connection_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `connection_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/integrations/imports</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `request_key` | body | ✓ | `string` | `{"maxLength": 128, "minLength": 1}` |
| `records` | body | ✓ | `array` | `{}` |

```json

{
  "request_key": "example-request_key",
  "records": [
    {
      "external_id": "{{external_id}}",
      "kind": "person",
      "title": "example-title",
      "version": 1.0,
      "occurred_at": "2026-11-03T12:00:00Z"
    }
  ]
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/integrations/imports/{run_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `run_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/workspaces/{workspace_id}/records</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `q` | query | — | `string` | `{"maxLength": 200, "default": ""}` |
| `kind` | query | — | `string / null` | `{}` |
| `offset` | query | — | `integer` | `{"minimum": 0, "default": 0}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/workspaces/{workspace_id}/records/{record_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `record_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/workspaces/{workspace_id}/records/{record_id}/notes</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `record_id` | path | ✓ | `string` | `{}` |
| `text` | body | ✓ | `string` | `{"maxLength": 10000, "minLength": 1}` |
| `occurred_at` | body | ✓ | `string` | `{}` |

```json

{
  "text": "Where were the documents last seen?",
  "occurred_at": "2026-11-03T12:00:00Z"
}

```

Declared responses: `201`, `422`.

</details>

<details>

<summary>GET /v1/workspaces/{workspace_id}/records/{record_id}/revisions</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `record_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/workspaces/{workspace_id}/records/{record_id}/publications</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `record_id` | path | ✓ | `string` | `{}` |
| `publication_id` | body | ✓ | `string` | `{}` |

```json

{
  "publication_id": "{{publication_id}}"
}

```

Declared responses: `201`, `422`.

</details>

<details>

<summary>POST /v1/workspaces/{workspace_id}/records/{person_id}/medication-check</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `person_id` | path | ✓ | `string` | `{}` |
| `prescription_id` | body | ✓ | `string` | `{}` |
| `observed_ingredient` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 1}` |
| `observed_concentration` | body | ✓ | `string` | `{"maxLength": 80, "minLength": 1}` |
| `patient_confirmed` | body | — | `boolean` | `{"default": false}` |
| `checked_at` | body | ✓ | `string` | `{}` |

```json

{
  "prescription_id": "{{prescription_id}}",
  "observed_ingredient": "example-observed_ingredient",
  "observed_concentration": "example-observed_concentration",
  "checked_at": "2026-11-03T12:00:00Z"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/integrations/records/{record_id}/media</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `record_id` | path | ✓ | `string` | `{}` |
| `external_id` | body | ✓ | `string` | `{"maxLength": 160}` |
| `publish` | body | — | `boolean` | `{"default": false}` |
| `author_id` | body | — | `string / null` | `{}` |
| `file` | body | ✓ | `string` | `{}` |

Declared responses: `201`, `422`.

</details>

<details>

<summary>POST /v1/integrations/records/{record_id}/index</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `record_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/workspaces/{workspace_id}/record-media/{link_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `link_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/workspaces/{workspace_id}/test-workers</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `username` | body | ✓ | `string` | `{"pattern": "^[a-z][a-z0-9_.-]{2,63}$"}` |
| `display_name` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 2}` |
| `role` | body | — | `string` | `{"enum": ["admin", "register", "query"]}` |

```json

{
  "username": "{{username}}",
  "display_name": "{{display_name}}"
}

```

Declared responses: `201`, `422`.

</details>

<details>

<summary>POST /v1/workspaces/{workspace_id}/records/search</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `question` | body | ✓ | `string` | `{"maxLength": 1000, "minLength": 2}` |
| `language` | body | — | `string` | `{"pattern": "^(es\|en)$", "default": "es"}` |
| `record_id` | body | — | `string / null` | `{}` |

```json

{
  "question": "{{query}}",
  "language": "{{language}}"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/workspaces/{workspace_id}/connections/{connection_id}/sync</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `connection_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

## Facial recognition

| Operation | Summary | Access | Required fields | Manual |
| --- | --- | --- | --- | --- |
| `GET /v1/faces/consent` | Read Consent | bearer | — | — |
| `POST /v1/faces/consent` | Grant Consent | bearer | `confirm` | ✓ |
| `DELETE /v1/faces/consent` | Revoke Consent | bearer | — | ✓ |
| `POST /v1/faces/verify-identity` | Verify Identity | bearer | — | ✓ |
| `POST /v1/faces/profile-photo` | Upload Profile Photo | bearer | `file` | ✓ |
| `POST /v1/faces/enroll` | Enroll Media | bearer | `media_id` | ✓ |
| `GET /v1/faces/enrollments` | List Own Enrollments | bearer | — | — |
| `POST /v1/faces/record-enroll` | Enroll Record Media | bearer | `record_id` | ✓ |
| `GET /v1/faces/record-enrollments` | List Record Enrollments | bearer | `workspace_id` | — |
| `DELETE /v1/faces/record-enrollments/{enrollment_id}` | Delete Record Enrollment | bearer | `enrollment_id` | ✓ |
| `POST /v1/faces/search` | Search Faces | bearer | `workspace_id` | — |
| `GET /v1/faces/enrollments/{enrollment_id}/thumbnail` | Enrollment Thumbnail | bearer | `enrollment_id` | — |
| `GET /v1/faces/record-enrollments/{enrollment_id}/thumbnail` | Record Enrollment Thumbnail | bearer | `enrollment_id` | — |
| `POST /v1/faces/reference-photos` | Add Reference | bearer | `file` | ✓ |
| `DELETE /v1/faces/reference-photos/{enrollment_id}` | Remove Reference | bearer | `enrollment_id` | ✓ |
| `GET /v1/faces/setup` | Status | bearer | — | — |
| `POST /v1/faces/setup/complete` | Complete | bearer | — | ✓ |

<details>

<summary>GET /v1/faces/consent</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>POST /v1/faces/consent</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `confirm` | body | ✓ | `boolean` | `{}` |

```json

{
  "confirm": false
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>DELETE /v1/faces/consent</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>POST /v1/faces/verify-identity</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>POST /v1/faces/profile-photo</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `file` | body | ✓ | `string` | `{}` |

Declared responses: `201`, `422`.

</details>

<details>

<summary>POST /v1/faces/enroll</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `media_id` | body | ✓ | `string` | `{}` |

```json

{
  "media_id": "{{media_id}}"
}

```

Declared responses: `201`, `422`.

</details>

<details>

<summary>GET /v1/faces/enrollments</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>POST /v1/faces/record-enroll</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `record_id` | body | ✓ | `string` | `{}` |
| `media_id` | body | — | `string / null` | `{}` |
| `record_media_id` | body | — | `string / null` | `{}` |
| `biometric_basis` | body | — | `string / null` | `{}` |

```json

{
  "record_id": "{{record_id}}"
}

```

Declared responses: `201`, `422`.

</details>

<details>

<summary>GET /v1/faces/record-enrollments</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | query | ✓ | `string` | `{}` |
| `record_id` | query | — | `string / null` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>DELETE /v1/faces/record-enrollments/{enrollment_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `enrollment_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/faces/search</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | body | ✓ | `string` | `{}` |
| `media_id` | body | — | `string / null` | `{}` |
| `probe` | body | — | `string / null` | `{}` |
| `include_records` | body | — | `boolean` | `{"default": true}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/faces/enrollments/{enrollment_id}/thumbnail</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `enrollment_id` | path | ✓ | `string` | `{}` |
| `full_size` | query | — | `boolean` | `{"default": true}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/faces/record-enrollments/{enrollment_id}/thumbnail</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `enrollment_id` | path | ✓ | `string` | `{}` |
| `full_size` | query | — | `boolean` | `{"default": true}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/faces/reference-photos</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `file` | body | ✓ | `string` | `{}` |

Declared responses: `201`, `422`.

</details>

<details>

<summary>DELETE /v1/faces/reference-photos/{enrollment_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `enrollment_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/faces/setup</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>POST /v1/faces/setup/complete</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

## Capture and processing

| Operation | Summary | Access | Required fields | Manual |
| --- | --- | --- | --- | --- |
| `POST /v1/sessions` | Create Session | bearer | `workspace_id`, `consent_confirmed` | ✓ |
| `GET /v1/sessions/{session_id}` | Get Session | bearer | `session_id` | — |
| `POST /v1/sessions/{session_id}/close` | Close Session | bearer | `session_id` | ✓ |
| `POST /v1/captures` | Create Capture | bearer | `session_id`, `file` | ✓ |
| `GET /v1/captures/{capture_id}` | Get Capture | bearer | `capture_id` | — |
| `POST /v1/captures/{capture_id}/process` | Process Capture | bearer | `capture_id` | ✓ |
| `GET /v1/jobs/{job_id}` | Get Job | bearer | `job_id` | — |

<details>

<summary>POST /v1/sessions</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | body | ✓ | `string` | `{}` |
| `zone_id` | body | — | `string / null` | `{}` |
| `consent_confirmed` | body | ✓ | `boolean` | `{}` |

```json

{
  "workspace_id": "{{workspace_id}}",
  "consent_confirmed": false
}

```

Declared responses: `201`, `422`.

</details>

<details>

<summary>GET /v1/sessions/{session_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `session_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/sessions/{session_id}/close</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `session_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/captures</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `session_id` | body | ✓ | `string` | `{}` |
| `captured_at` | body | — | `string / null` | `{}` |
| `file` | body | ✓ | `string` | `{}` |

Declared responses: `201`, `422`.

</details>

<details>

<summary>GET /v1/captures/{capture_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `capture_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/captures/{capture_id}/process</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `capture_id` | path | ✓ | `string` | `{}` |

```json

{}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/jobs/{job_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `job_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

## Queries and evidence

| Operation | Summary | Access | Required fields | Manual |
| --- | --- | --- | --- | --- |
| `GET /v1/objects` | List Objects | bearer | `workspace_id` | — |
| `GET /v1/objects/{object_id}` | Get Object | bearer | `object_id` | — |
| `POST /v1/objects/{object_id}/aliases` | Create Object Alias | bearer | `object_id`, `alias` | ✓ |
| `GET /v1/objects/{object_id}/history` | Object History | bearer | `object_id` | — |
| `GET /v1/objects/{object_id}/facts` | Object Facts | bearer | `object_id` | — |
| `PATCH /v1/facts/{fact_id}` | Verify Fact | bearer | `fact_id`, `verification_status` | ✓ |
| `GET /v1/objects/{object_id}/tracks` | Object Tracks | bearer | `object_id` | — |
| `GET /v1/tracks/{track_id}/frames` | Track Frames | bearer | `track_id` | — |
| `PATCH /v1/observations/{observation_id}` | Verify Observation | bearer | `observation_id`, `verification_status` | ✓ |
| `POST /v1/observations/{observation_id}/segment` | Request Observation Segmentation | bearer | `observation_id` | ✓ |
| `POST /v1/queries` | Query | bearer | `workspace_id`, `question` | — |
| `POST /v1/queries/image` | Image Query | bearer | `workspace_id`, `image` | — |
| `POST /v1/search/classify` | Classify Search Probe | bearer | `workspace_id`, `image` | — |
| `POST /v1/search/route` | Route Search Text | bearer | `text` | — |
| `POST /v1/queries/audio` | Audio Query | bearer | `workspace_id`, `audio` | — |
| `GET /v1/media/{media_id}` | Get Media | bearer | `media_id` | — |
| `GET /v1/observations/{observation_id}/highlighted` | Highlighted Observation | bearer | `observation_id` | — |
| `GET /v1/media/{media_id}/highlighted` | Highlighted Media | bearer | `media_id` | — |
| `GET /v1/me/storage-connections/{connection_id}/objects` | Objects | bearer | `connection_id` | — |
| `GET /v1/profiles/{user_id}/media` | Profile Media Page | bearer | `user_id` | — |
| `GET /v1/gallery/{post_id}/media` | Media | bearer | `post_id` | — |

<details>

<summary>GET /v1/objects</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | query | ✓ | `string` | `{}` |
| `q` | query | — | `string / null` | `{}` |
| `category` | query | — | `string / null` | `{}` |
| `zone_id` | query | — | `string / null` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/objects/{object_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `object_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/objects/{object_id}/aliases</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `object_id` | path | ✓ | `string` | `{}` |
| `alias` | body | ✓ | `string` | `{"maxLength": 240, "minLength": 2}` |

```json

{
  "alias": "example-alias"
}

```

Declared responses: `201`, `422`.

</details>

<details>

<summary>GET /v1/objects/{object_id}/history</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `object_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/objects/{object_id}/facts</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `object_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>PATCH /v1/facts/{fact_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `fact_id` | path | ✓ | `string` | `{}` |
| `verification_status` | body | ✓ | `string` | `{"enum": ["verified", "rejected"]}` |
| `value_text` | body | — | `string / null` | `{}` |
| `normalized_value` | body | — | `string / null` | `{}` |

```json

{
  "verification_status": "verified"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/objects/{object_id}/tracks</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `object_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/tracks/{track_id}/frames</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `track_id` | path | ✓ | `string` | `{}` |
| `offset` | query | — | `integer` | `{"default": 0}` |
| `limit` | query | — | `integer` | `{"default": 240}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>PATCH /v1/observations/{observation_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `observation_id` | path | ✓ | `string` | `{}` |
| `verification_status` | body | ✓ | `string` | `{"enum": ["verified", "rejected"]}` |
| `spatial_description` | body | — | `string / null` | `{}` |

```json

{
  "verification_status": "verified"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/observations/{observation_id}/segment</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `observation_id` | path | ✓ | `string` | `{}` |

Declared responses: `202`, `422`.

</details>

<details>

<summary>POST /v1/queries</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | body | ✓ | `string` | `{}` |
| `question` | body | ✓ | `string` | `{"maxLength": 500, "minLength": 2}` |
| `language` | body | — | `string` | `{"maxLength": 16, "default": "en"}` |
| `search_scope` | body | — | `string` | `{"enum": ["auto", "gallery", "registry"], "default": "auto"}` |

```json

{
  "workspace_id": "{{workspace_id}}",
  "question": "{{query}}",
  "language": "{{language}}"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/queries/image</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | body | ✓ | `string` | `{}` |
| `image` | body | ✓ | `string` | `{}` |
| `question` | body | — | `string` | `{"default": ""}` |
| `language` | body | — | `string` | `{"default": "en"}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/search/classify</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | body | ✓ | `string` | `{}` |
| `image` | body | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/search/route</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `text` | body | ✓ | `string` | `{"maxLength": 2000, "minLength": 2}` |

```json

{
  "text": "Where were the documents last seen?"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/queries/audio</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | body | ✓ | `string` | `{}` |
| `audio` | body | ✓ | `string` | `{}` |
| `language` | body | — | `string` | `{"default": "en"}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/media/{media_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `media_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/observations/{observation_id}/highlighted</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `observation_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/media/{media_id}/highlighted</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `media_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/me/storage-connections/{connection_id}/objects</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |
| `prefix` | query | — | `string` | `{"default": ""}` |
| `cursor` | query | — | `string / null` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/profiles/{user_id}/media</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `user_id` | path | ✓ | `string` | `{}` |
| `limit` | query | — | `integer` | `{"default": 12}` |
| `cursor` | query | — | `string / null` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/gallery/{post_id}/media</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `post_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

## Profiles and social

| Operation | Summary | Access | Required fields | Manual |
| --- | --- | --- | --- | --- |
| `POST /v1/tts` | Speech Audio | bearer | `text`, `language` | ✓ |
| `GET /v1/me/storage-connections` | Connections | bearer | — | — |
| `POST /v1/me/storage-connections` | Create | bearer | `name`, `endpoint`, `bucket` | ✓ |
| `PUT /v1/me/storage-connections/{connection_id}` | Update | bearer | `connection_id`, `name`, `endpoint`, `bucket` | ✓ |
| `DELETE /v1/me/storage-connections/{connection_id}` | Disconnect | bearer | `connection_id` | ✓ |
| `POST /v1/me/storage-connections/{connection_id}/test` | Test | bearer | `connection_id` | ✓ |
| `GET /v1/me/storage-connections/{connection_id}/content` | Content | bearer | `connection_id`, `key` | — |
| `POST /v1/me/storage-connections/{connection_id}/cv` | Cv | bearer | `connection_id`, `key` | ✓ |
| `POST /v1/me/storage-connections/{connection_id}/imports` | Start Import | bearer | `connection_id`, `request_key`, `keys` | ✓ |
| `GET /v1/me/storage-connections/{connection_id}/imports` | Imports | bearer | `connection_id` | — |
| `POST /v1/me/storage-connections/{connection_id}/imports/{run_id}/retry` | Retry | bearer | `connection_id`, `run_id` | ✓ |
| `GET /v1/me/storage-connections/{connection_id}/syncs` | Syncs | bearer | `connection_id` | — |
| `POST /v1/me/storage-connections/{connection_id}/syncs` | Create Sync | bearer | `connection_id` | ✓ |
| `POST /v1/me/storage-connections/{connection_id}/syncs/{rule_id}/run` | Run Sync | bearer | `connection_id`, `rule_id` | ✓ |
| `DELETE /v1/me/storage-connections/{connection_id}/syncs/{rule_id}` | Stop Sync | bearer | `connection_id`, `rule_id` | ✓ |
| `POST /v1/me/profile/avatar` | Upload Avatar | bearer | `file` | ✓ |
| `GET /v1/me/social-capabilities` | Capabilities | bearer | — | — |
| `GET /v1/groups/{workspace_id}/members` | Members | bearer | `workspace_id` | — |
| `POST /v1/groups/{workspace_id}/members/{member_id}/invite-permission` | Set Invite Permission | bearer | `workspace_id`, `member_id` | ✓ |
| `POST /v1/groups/{workspace_id}/members/{member_id}/remove` | Remove Member | bearer | `workspace_id`, `member_id` | ✓ |
| `POST /v1/groups` | Create Group | bearer | — | ✓ |
| `GET /v1/groups/{workspace_id}/pin` | Group Pin | bearer | `workspace_id` | — |
| `POST /v1/groups/{workspace_id}/pin/rotate` | Rotate Group Pin | bearer | `workspace_id` | ✓ |
| `DELETE /v1/groups/{workspace_id}` | Delete Group | bearer | `workspace_id` | ✓ |
| `POST /v1/groups/join-by-pin` | Join By Pin | bearer | `pin` | ✓ |
| `POST /v1/chat/append` | Chat Append | bearer | `text` | ✓ |
| `GET /v1/chat/history` | Chat History | bearer | — | — |
| `POST /v1/chat/audio` | Chat Audio Upload | bearer | `message_id`, `audio` | ✓ |
| `GET /v1/chat/audio/{audio_id}` | Chat Audio Download | bearer | `audio_id` | — |
| `POST /v1/notes/merge` | Merge Notes | bearer | `texts` | ✓ |
| `POST /v1/groups/{workspace_id}/invite` | Invite | bearer | `workspace_id` | ✓ |
| `POST /v1/groups/join` | Join | bearer | — | ✓ |
| `POST /v1/gallery/{post_id}/remove` | Remove Publication | bearer | `post_id` | ✓ |
| `POST /v1/assistant` | Assistant | bearer | `text` | ✓ |
| `POST /v1/gallery/{post_id}/share` | Share | bearer | `post_id`, `audience` | ✓ |
| `GET /v1/groups/{workspace_id}/reports` | Reports | bearer | `workspace_id` | — |
| `POST /v1/groups/{workspace_id}/hide/{post_id}` | Hide | bearer | `workspace_id`, `post_id` | ✓ |
| `GET /v1/me/facebook-profile` | Own Facebook Profile | bearer | — | — |
| `GET /v1/me/profile` | Own Profile | bearer | — | — |
| `PATCH /v1/me/profile` | Update Profile | bearer | — | ✓ |
| `GET /v1/profiles/{user_id}` | Public Profile | bearer | `user_id` | — |
| `GET /v1/profiles/{user_id}/avatar` | Profile Avatar | bearer | `user_id` | — |
| `POST /v1/me/profile/cv` | Upload Cv | bearer | `file` | ✓ |
| `DELETE /v1/me/profile/cv` | Delete Cv | bearer | — | ✓ |
| `POST /v1/notes/transcribe` | Transcribe Note | bearer | `audio` | ✓ |
| `POST /v1/me/profile/publications` | Upload Profile Publication | bearer | `file`, `workspace_id` | ✓ |
| `POST /v1/me/work-publications` | Upload Work Publication | bearer | `workspace_id`, `file` | ✓ |
| `POST /v1/me/profile/cv/retry` | Retry Cv | bearer | — | ✓ |
| `POST /v1/profiles/search` | Search Profiles | bearer | `question` | — |
| `GET /v1/gallery/page` | Gallery Page | bearer | — | — |
| `GET /v1/gallery` | Gallery | bearer | — | — |
| `POST /v1/gallery` | Publish | bearer | `media_id` | ✓ |
| `POST /v1/me/capture-profile` | Capture Profile | bearer | — | ✓ |
| `GET /v1/gallery/{post_id}/thumbnail` | Thumbnail | bearer | `post_id` | — |
| `GET /v1/gallery/{post_id}/boxed` | Boxed Thumbnail | bearer | `post_id` | — |
| `POST /v1/gallery/{post_id}/interactions` | Interact | bearer | `post_id`, `action` | ✓ |
| `GET /v1/gallery/{post_id}/comments` | Comments | bearer | `post_id` | — |
| `GET /v1/me/preferences` | Read Preferences | bearer | — | — |
| `PATCH /v1/me/preferences` | Update Preferences | bearer | `preferred_language` | ✓ |
| `POST /v1/chat/history/prepare` | Prepare History | bearer | `message_ids` | ✓ |
| `GET /v1/chat/history/translations` | Read History Translations | bearer | `ids` | — |
| `POST /v1/gallery/evidence/information` | Evidence Information | bearer | `items` | — |
| `POST /v1/gallery/evidence/information/prepare` | Prepare Evidence Information | bearer | `items` | ✓ |
| `GET /v1/gallery/evidence/{evidence_id}` | Evidence Image | bearer | `evidence_id` | — |
| `POST /v1/me/publication-uploads` | Prepare Publication Upload | bearer | `file`, `request_key` | ✓ |
| `GET /v1/me/publication-uploads/{upload_id}` | Publication Upload Status | bearer | `upload_id` | — |
| `GET /v1/me/publication-uploads/{upload_id}/preview` | Publication Upload Preview | bearer | `upload_id` | — |
| `POST /v1/me/publication-uploads/{upload_id}/confirm` | Publication Upload Confirm | bearer | `upload_id` | ✓ |
| `POST /v1/me/publication-uploads/{upload_id}/cancel` | Publication Upload Cancel | bearer | `upload_id` | ✓ |
| `POST /v1/me/publication-uploads/{upload_id}/retry` | Publication Upload Retry | bearer | `upload_id` | ✓ |
| `POST /v1/groups/{workspace_id}/publications/import` | Import Group Publications | bearer | `workspace_id`, `publication_ids` | ✓ |

<details>

<summary>POST /v1/tts</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `text` | body | ✓ | `string` | `{"maxLength": 4000, "minLength": 1}` |
| `language` | body | ✓ | `string` | `{"enum": ["es", "en"]}` |

```json

{
  "text": "Where were the documents last seen?",
  "language": "{{language}}"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/me/storage-connections</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>POST /v1/me/storage-connections</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `name` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 2}` |
| `provider` | body | — | `string` | `{"enum": ["r2", "s3"], "default": "r2"}` |
| `endpoint` | body | ✓ | `string` | `{"maxLength": 2048}` |
| `bucket` | body | ✓ | `string` | `{"pattern": "^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$"}` |
| `region` | body | — | `string` | `{"pattern": "^[a-zA-Z0-9-]{1,80}$", "default": "auto"}` |
| `prefix` | body | — | `string` | `{"maxLength": 1024, "default": ""}` |
| `access_key` | body | — | `string / null` | `{}` |
| `secret_key` | body | — | `string / null` | `{}` |
| `workspace_id` | body | — | `string / null` | `{}` |

```json

{
  "name": "example-name",
  "endpoint": "example-endpoint",
  "bucket": "example-bucket"
}

```

Declared responses: `201`, `422`.

</details>

<details>

<summary>PUT /v1/me/storage-connections/{connection_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |
| `name` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 2}` |
| `provider` | body | — | `string` | `{"enum": ["r2", "s3"], "default": "r2"}` |
| `endpoint` | body | ✓ | `string` | `{"maxLength": 2048}` |
| `bucket` | body | ✓ | `string` | `{"pattern": "^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$"}` |
| `region` | body | — | `string` | `{"pattern": "^[a-zA-Z0-9-]{1,80}$", "default": "auto"}` |
| `prefix` | body | — | `string` | `{"maxLength": 1024, "default": ""}` |
| `access_key` | body | — | `string / null` | `{}` |
| `secret_key` | body | — | `string / null` | `{}` |
| `workspace_id` | body | — | `string / null` | `{}` |

```json

{
  "name": "example-name",
  "endpoint": "example-endpoint",
  "bucket": "example-bucket"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>DELETE /v1/me/storage-connections/{connection_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/storage-connections/{connection_id}/test</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/me/storage-connections/{connection_id}/content</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |
| `key` | query | ✓ | `string` | `{"maxLength": 1024}` |
| `preview` | query | — | `boolean` | `{"default": false}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/storage-connections/{connection_id}/cv</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |
| `key` | body | ✓ | `string` | `{"maxLength": 1024, "minLength": 1}` |

```json

{
  "key": "example-key"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/storage-connections/{connection_id}/imports</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |
| `request_key` | body | ✓ | `string` | `{"maxLength": 128, "minLength": 1}` |
| `keys` | body | ✓ | `array` | `{}` |
| `audience` | body | — | `string` | `{"default": "work"}` |
| `workspace_id` | body | — | `string / null` | `{}` |

```json

{
  "request_key": "example-request_key",
  "keys": [
    "example-keys"
  ]
}

```

Declared responses: `202`, `422`.

</details>

<details>

<summary>GET /v1/me/storage-connections/{connection_id}/imports</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/storage-connections/{connection_id}/imports/{run_id}/retry</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |
| `run_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/me/storage-connections/{connection_id}/syncs</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/storage-connections/{connection_id}/syncs</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |
| `prefix` | body | — | `string` | `{"maxLength": 1024, "default": ""}` |
| `audience` | body | — | `string` | `{"default": "work"}` |
| `workspace_id` | body | — | `string / null` | `{}` |
| `interval_minutes` | body | — | `integer` | `{"enum": [15, 60, 1440], "default": 15}` |
| `enabled` | body | — | `boolean` | `{"default": false}` |

```json

{}

```

Declared responses: `201`, `422`.

</details>

<details>

<summary>POST /v1/me/storage-connections/{connection_id}/syncs/{rule_id}/run</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |
| `rule_id` | path | ✓ | `string` | `{}` |

Declared responses: `202`, `422`.

</details>

<details>

<summary>DELETE /v1/me/storage-connections/{connection_id}/syncs/{rule_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |
| `rule_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/profile/avatar</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `file` | body | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/me/social-capabilities</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>GET /v1/groups/{workspace_id}/members</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/groups/{workspace_id}/members/{member_id}/invite-permission</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `member_id` | path | ✓ | `string` | `{}` |
| `allowed` | body | — | `boolean` | `{"default": false}` |

```json

{}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/groups/{workspace_id}/members/{member_id}/remove</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `member_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/groups</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `name` | body | — | `string` | `{"maxLength": 160, "default": ""}` |
| `code` | body | — | `string` | `{"maxLength": 128, "default": ""}` |

```json

{}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/groups/{workspace_id}/pin</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/groups/{workspace_id}/pin/rotate</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>DELETE /v1/groups/{workspace_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/groups/join-by-pin</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `pin` | body | ✓ | `string` | `{"maxLength": 16, "minLength": 9}` |

```json

{
  "pin": "example-pin"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/chat/append</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `response_language` | body | — | `string / null` | `{}` |
| `role` | body | — | `string` | `{"enum": ["user", "ai"], "default": "user"}` |
| `kind` | body | — | `string` | `{"default": "text"}` |
| `text` | body | ✓ | `string` | `{"maxLength": 4000, "minLength": 1}` |
| `evidence_url` | body | — | `string / null` | `{}` |
| `gallery` | body | — | `array` | `{}` |
| `simulated` | body | — | `boolean` | `{"default": false}` |
| `quick_replies` | body | — | `array` | `{}` |
| `face_action` | body | — | `boolean` | `{"default": false}` |

```json

{
  "text": "Where were the documents last seen?"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/chat/history</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `limit` | query | — | `integer` | `{"default": 10}` |
| `before_id` | query | — | `integer / null` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/chat/audio</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `message_id` | body | ✓ | `integer` | `{}` |
| `duration_ms` | body | — | `integer` | `{"default": 0}` |
| `audio` | body | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/chat/audio/{audio_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `audio_id` | path | ✓ | `integer` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/notes/merge</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `texts` | body | ✓ | `array` | `{}` |

```json

{
  "texts": [
    "example-texts"
  ]
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/groups/{workspace_id}/invite</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/groups/join</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `name` | body | — | `string` | `{"maxLength": 160, "default": ""}` |
| `code` | body | — | `string` | `{"maxLength": 128, "default": ""}` |

```json

{}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/gallery/{post_id}/remove</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `post_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/assistant</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `language` | body | — | `string / null` | `{}` |
| `text` | body | ✓ | `string` | `{"maxLength": 500, "minLength": 2}` |
| `audience` | body | — | `string` | `{"enum": ["home", "public", "work"], "default": "home"}` |
| `workspace_id` | body | — | `string / null` | `{}` |
| `post_id` | body | — | `string / null` | `{}` |

```json

{
  "language": "{{language}}",
  "text": "Where were the documents last seen?"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/gallery/{post_id}/share</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `post_id` | path | ✓ | `string` | `{}` |
| `audience` | body | ✓ | `string` | `{"enum": ["home", "public", "work"]}` |
| `workspace_id` | body | — | `string / null` | `{}` |

```json

{
  "audience": "home"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/groups/{workspace_id}/reports</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/groups/{workspace_id}/hide/{post_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `post_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/me/facebook-profile</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>GET /v1/me/profile</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>PATCH /v1/me/profile</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `display_name` | body | — | `string / null` | `{}` |
| `birthday` | body | — | `string / null` | `{}` |
| `gender` | body | — | `string / null` | `{}` |
| `hometown` | body | — | `string / null` | `{}` |
| `location` | body | — | `string / null` | `{}` |
| `headline` | body | — | `string` | `{"maxLength": 240, "default": ""}` |
| `biography` | body | — | `string` | `{"maxLength": 4000, "default": ""}` |
| `phone` | body | — | `string` | `{"maxLength": 64, "default": ""}` |
| `website` | body | — | `string` | `{"maxLength": 1024, "default": ""}` |
| `social_links` | body | — | `array` | `{}` |

```json

{}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/profiles/{user_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `user_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/profiles/{user_id}/avatar</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `user_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/profile/cv</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `file` | body | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>DELETE /v1/me/profile/cv</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>POST /v1/notes/transcribe</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `audio` | body | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/profile/publications</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `file` | body | ✓ | `string` | `{}` |
| `caption` | body | — | `string` | `{"maxLength": 4000, "default": ""}` |
| `note_text` | body | — | `string` | `{"maxLength": 4000, "default": ""}` |
| `note_source` | body | — | `string` | `{"default": ""}` |
| `workspace_id` | body | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/work-publications</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | body | ✓ | `string` | `{}` |
| `caption` | body | — | `string` | `{"maxLength": 4000, "default": ""}` |
| `note_text` | body | — | `string` | `{"maxLength": 4000, "default": ""}` |
| `note_source` | body | — | `string` | `{"default": ""}` |
| `file` | body | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/profile/cv/retry</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>POST /v1/profiles/search</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `language` | body | — | `string / null` | `{}` |
| `question` | body | ✓ | `string` | `{"maxLength": 500, "minLength": 2}` |
| `user_id` | body | — | `string / null` | `{}` |

```json

{
  "language": "{{language}}",
  "question": "{{query}}"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/gallery/page</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `audience` | query | — | `string` | `{"enum": ["home", "work"], "default": "work"}` |
| `workspace_id` | query | — | `string / null` | `{}` |
| `limit` | query | — | `integer` | `{"default": 12}` |
| `cursor` | query | — | `string / null` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/gallery</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `audience` | query | — | `string` | `{"enum": ["home", "public", "work"], "default": "work"}` |
| `offset` | query | — | `integer` | `{"default": 0}` |
| `workspace_id` | query | — | `string / null` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/gallery</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `media_id` | body | ✓ | `string` | `{}` |
| `audience` | body | — | `string` | `{"default": "work"}` |
| `caption` | body | — | `string` | `{"maxLength": 4000, "default": ""}` |
| `workspace_id` | body | — | `string / null` | `{}` |

```json

{
  "media_id": "{{media_id}}"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/capture-profile</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>GET /v1/gallery/{post_id}/thumbnail</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `post_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/gallery/{post_id}/boxed</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `post_id` | path | ✓ | `string` | `{}` |
| `labels` | query | — | `string` | `{"default": ""}` |
| `full_size` | query | — | `boolean` | `{"default": false}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/gallery/{post_id}/interactions</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `post_id` | path | ✓ | `string` | `{}` |
| `action` | body | ✓ | `string` | `{"enum": ["like", "unlike", "comment", "report"]}` |
| `text` | body | — | `string` | `{"maxLength": 2000, "default": ""}` |
| `parent_id` | body | — | `string / null` | `{}` |

```json

{
  "action": "like"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/gallery/{post_id}/comments</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `post_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/me/preferences</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>PATCH /v1/me/preferences</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `initialize` | query | — | `boolean` | `{"default": false}` |
| `preferred_language` | body | ✓ | `string` | `{"enum": ["en", "es"]}` |

```json

{
  "preferred_language": "en"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/chat/history/prepare</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `message_ids` | body | ✓ | `array` | `{}` |

```json

{
  "message_ids": [
    1
  ]
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/chat/history/translations</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `ids` | query | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/gallery/evidence/information</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `language` | body | — | `string` | `{"maxLength": 16, "default": "en"}` |
| `items` | body | ✓ | `array` | `{}` |

```json

{
  "language": "{{language}}",
  "items": [
    {
      "evidence_id": "{{evidence_id}}",
      "labels": [
        "example-labels"
      ]
    }
  ]
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/gallery/evidence/information/prepare</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `language` | body | — | `string` | `{"maxLength": 16, "default": "en"}` |
| `items` | body | ✓ | `array` | `{}` |

```json

{
  "language": "{{language}}",
  "items": [
    {
      "evidence_id": "{{evidence_id}}",
      "labels": [
        "example-labels"
      ]
    }
  ]
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/gallery/evidence/{evidence_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `evidence_id` | path | ✓ | `string` | `{}` |
| `labels` | query | — | `string` | `{"default": ""}` |
| `full_size` | query | — | `boolean` | `{"default": false}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/publication-uploads</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `file` | body | ✓ | `string` | `{}` |
| `request_key` | body | ✓ | `string` | `{"maxLength": 64}` |
| `audience` | body | — | `string` | `{"default": "work"}` |
| `workspace_id` | body | — | `string / null` | `{}` |
| `caption` | body | — | `string` | `{"maxLength": 4000, "default": ""}` |
| `note_text` | body | — | `string` | `{"maxLength": 4000, "default": ""}` |
| `note_source` | body | — | `string` | `{"default": ""}` |

Declared responses: `202`, `422`.

</details>

<details>

<summary>GET /v1/me/publication-uploads/{upload_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `upload_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/me/publication-uploads/{upload_id}/preview</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `upload_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/publication-uploads/{upload_id}/confirm</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `upload_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/publication-uploads/{upload_id}/cancel</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `upload_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/publication-uploads/{upload_id}/retry</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `upload_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/groups/{workspace_id}/publications/import</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `publication_ids` | body | ✓ | `array` | `{}` |

```json

{
  "publication_ids": [
    "00000000-0000-4000-8000-000000000001"
  ]
}

```

Declared responses: `200`, `422`.

</details>

## Devices and Display

| Operation | Summary | Access | Required fields | Manual |
| --- | --- | --- | --- | --- |
| `POST /v1/virtual-devices/bootstrap` | Bootstrap Virtual Device | none | `X-RealityOS-Installation-ID` | ✓ |
| `GET /v1/device/zones` | List Device Zones | device | — | — |
| `POST /v1/device/sessions` | Create Device Session | device | — | ✓ |
| `POST /v1/device/sessions/{session_id}/close` | Close Device Session | device | `session_id` | ✓ |
| `POST /v1/device/captures` | Create Device Capture | device | `session_id`, `file` | ✓ |
| `POST /v1/device/captures/{capture_id}/process` | Process Device Capture | device | `capture_id` | ✓ |
| `GET /v1/device/jobs/{job_id}` | Get Device Job | device | `job_id` | — |
| `POST /v1/device/queries` | Device Query | device | `workspace_id`, `question` | — |
| `GET /v1/device/observations/{observation_id}/highlighted` | Device Highlighted Observation | device | `observation_id` | — |
| `GET /v1/device/display/observations/{observation_id}/highlighted` | Display Highlighted Observation | signed | `observation_id`, `token` | — |
| `POST /v1/display/media-links` | Media Link | bearer | `kind`, `resource_id` | ✓ |
| `GET /v1/display/media` | Display Media | signed | `token` | — |
| `POST /v1/display/face-group-links` | Face Group Link | bearer | `marks`, `probe` | ✓ |
| `GET /v1/display/face-group` | Face Group Media | signed | `token` | — |

<details>

<summary>POST /v1/virtual-devices/bootstrap</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `X-RealityOS-Installation-ID` | header | ✓ | `string` | `{}` |

Declared responses: `201`, `422`.

</details>

<details>

<summary>GET /v1/device/zones</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>POST /v1/device/sessions</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `zone_id` | body | — | `string / null` | `{}` |

```json

{}

```

Declared responses: `201`, `422`.

</details>

<details>

<summary>POST /v1/device/sessions/{session_id}/close</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `session_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/device/captures</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `session_id` | body | ✓ | `string` | `{}` |
| `captured_at` | body | — | `string / null` | `{}` |
| `file` | body | ✓ | `string` | `{}` |

Declared responses: `201`, `422`.

</details>

<details>

<summary>POST /v1/device/captures/{capture_id}/process</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `capture_id` | path | ✓ | `string` | `{}` |

```json

{}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/device/jobs/{job_id}</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `job_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/device/queries</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | body | ✓ | `string` | `{}` |
| `question` | body | ✓ | `string` | `{"maxLength": 500, "minLength": 2}` |
| `language` | body | — | `string` | `{"maxLength": 16, "default": "en"}` |
| `search_scope` | body | — | `string` | `{"enum": ["auto", "gallery", "registry"], "default": "auto"}` |

```json

{
  "workspace_id": "{{workspace_id}}",
  "question": "{{query}}",
  "language": "{{language}}"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/device/observations/{observation_id}/highlighted</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `observation_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/device/display/observations/{observation_id}/highlighted</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `observation_id` | path | ✓ | `string` | `{}` |
| `token` | query | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/display/media-links</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `kind` | body | ✓ | `string` | `{"enum": ["evidence", "upload", "publication", "face_enrollment", "face_record_enrollment", "avatar"]}` |
| `resource_id` | body | ✓ | `string` | `{}` |
| `labels` | body | — | `array` | `{}` |

```json

{
  "kind": "evidence",
  "resource_id": "{{resource_id}}"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/display/media</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `token` | query | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/display/face-group-links</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `marks` | body | ✓ | `string` | `{}` |
| `probe` | body | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/display/face-group</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `token` | query | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

## Administration

| Operation | Summary | Access | Required fields | Manual |
| --- | --- | --- | --- | --- |
| `GET /v1/admin/devices` | List Devices | bearer | `workspace_id` | — |
| `POST /v1/admin/devices` | Enroll Device | bearer | `workspace_id`, `device_identifier`, `label` | ✓ |
| `POST /v1/admin/devices/{device_id}/rotate` | Rotate Device Credential | bearer | `device_id` | ✓ |
| `POST /v1/admin/devices/{device_id}/revoke` | Revoke Device | bearer | `device_id` | ✓ |
| `GET /v1/admin/devices/{device_id}/assignments` | List Device Assignments | bearer | `device_id` | — |
| `POST /v1/admin/devices/{device_id}/assignments` | Assign Device | bearer | `device_id`, `operator_label`, `notice_version` | ✓ |
| `GET /v1/admin/analytics/inventory` | Inventory Analytics | bearer | `workspace_id` | — |
| `GET /v1/moderation/reports` | Moderation Reports | bearer | — | — |
| `POST /v1/moderation/{post_id}/hide` | Moderate Hide | bearer | `post_id` | ✓ |

<details>

<summary>GET /v1/admin/devices</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | query | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/admin/devices</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | body | ✓ | `string` | `{}` |
| `device_identifier` | body | ✓ | `string` | `{"maxLength": 96, "minLength": 3, "pattern": "^[A-Za-z0-9._:-]+$"}` |
| `label` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 2}` |
| `metadata` | body | — | `object` | `{}` |

```json

{
  "workspace_id": "{{workspace_id}}",
  "device_identifier": "example-device_identifier",
  "label": "example-label"
}

```

Declared responses: `201`, `422`.

</details>

<details>

<summary>POST /v1/admin/devices/{device_id}/rotate</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `device_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/admin/devices/{device_id}/revoke</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `device_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/admin/devices/{device_id}/assignments</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `device_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>POST /v1/admin/devices/{device_id}/assignments</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `device_id` | path | ✓ | `string` | `{}` |
| `operator_label` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 1}` |
| `external_reference` | body | — | `string / null` | `{}` |
| `notice_version` | body | ✓ | `string` | `{"maxLength": 80, "minLength": 1}` |

```json

{
  "operator_label": "example-operator_label",
  "notice_version": "example-notice_version"
}

```

Declared responses: `201`, `422`.

</details>

<details>

<summary>GET /v1/admin/analytics/inventory</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `workspace_id` | query | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/moderation/reports</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>POST /v1/moderation/{post_id}/hide</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `post_id` | path | ✓ | `string` | `{}` |

Declared responses: `200`, `422`.

</details>

## Health

| Operation | Summary | Access | Required fields | Manual |
| --- | --- | --- | --- | --- |
| `GET /health/live` | Live | none | — | — |
| `GET /health/ready` | Ready | none | — | — |

<details>

<summary>GET /health/live</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

<details>

<summary>GET /health/ready</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>

## Local installation only

| Operation | Summary | Access | Required fields | Manual |
| --- | --- | --- | --- | --- |
| `POST /v1/auth/local-login` | Local login (local realm only) | none | `email`, `password` | — |
| `GET /v1/auth/local-session` | Check local realm | bearer | — | — |

<details>

<summary>POST /v1/auth/local-login</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| `email` | body | ✓ | `string` | `{"maxLength": 320, "minLength": 3}` |
| `password` | body | ✓ | `string` | `{"maxLength": 512, "minLength": 1}` |

```json

{
  "email": "{{email}}",
  "password": "{{password}}"
}

```

Declared responses: `200`, `422`.

</details>

<details>

<summary>GET /v1/auth/local-session</summary>

| Field | Location | Required | Type | Constraints |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Declared responses: `200`.

</details>



<p align="center"><a href="WORKSPACE_DATA.md"><img src="../../assets/readme/language-en-active.svg" alt="English" height="32"></a> <a href="../../es/guides/WORKSPACE_DATA.md"><img src="../../assets/readme/language-es.svg" alt="Español" height="32"></a></p>

# Accounts, records and imports

[← Documentation](../INDEX.md) · [API / Postman](../api/API.md)

## Reading guide

| Topic | What to know |
| --- | --- |
| **Account** | Register with username, email, name and password; confirm email before access. Login accepts email or username in `email`. |
| **Correct email** | `POST /v1/auth/change-pending-email` accepts the existing username or current email in `username`, verifies its password, preserves its ID and invalidates previous links. Confirmed, active and provisioned accounts are excluded. |
| **Personal details** | Email accounts edit their name, current location, hometown, birthday and gender in `PATCH /v1/me/profile`. Facebook identities keep these fields read-only and refresh them at each Facebook login. Birthday uses `YYYY-MM-DD`; age is derived. Omitted PATCH fields are preserved. |
| **Connection** | An admin creates a connection; the integration key is shown once and sent in `X-RealityOS-Integration-Key`. |
| **Batch** | Up to 100 records and 2 MiB; increasing versions, external-ID relations and atomic transaction. Same key/content returns the original result; different content returns 409. |
| **Kinds** | `person`, `case`, `event`, `object`. Draft/deleted records are excluded from queries. |
| **Biometrics** | Importing a person creates neither a user nor an enrollment. Traceable authorization and explicit portrait enrollment are required. |

```mermaid
flowchart LR
    N0["Source"] --> N1["Versioned batch"] --> N2["Workspace"] --> N3["Authorized query"]
```

[API ](../api/API.md) · [DEMO ](DEMO.md) · [DATABASE ](../architecture/DATABASE.md)

To bring photos, videos or a CV from R2/S3, use [My connections](STORAGE_CONNECTIONS.md). That media connection belongs to the account; the record integrations described above import structured records into a workspace. Both retain their permission checks.

## Local data and account selection

The local composition initializes two groups, six access accounts, 16 records and 25 publications from the versioned SQL in `simulator/database/`. The separate social initialization adds thirteen synthetic searchable profiles through the existing protected workflow. Original graphics are organized under `simulator/media/` and imported into PostgreSQL BYTEA.

`GET /v1/auth/local-accounts` and `POST /v1/auth/local-select` read eligible accounts and memberships from the database. Selection is restricted to the local realm; no passwords or active server credentials are published. Server registration and external record integrations remain server capabilities.

All groups use the same record, publication and media tables. Prepared copy uses natural operational descriptions, with bilingual fields and internal provenance retained in the database. Initialization receipts preserve edits and deletions on restart. There are no per-feature JSON databases, account lists or publication manifests serving application queries.

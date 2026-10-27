# REST API

OpenAPI is served at /v1/openapi.json and interactive documentation at /docs.
All routes use Bearer access tokens and workspace membership.

| Area | Routes |
| --- | --- |
| Auth | login, refresh, me |
| Workspaces | list/create workspaces; list/create zones |
| Sessions | create, read and close capture sessions |
| Captures/jobs | upload/read capture; request processing; inspect job |
| Objects | list/read/history; add a normalized alias; verify or reject observation. `GET /v1/objects` requires `workspace_id` and accepts `q` (name or alias), `category`, and `zone_id` filters. |
| Query/media | text/audio query; original/highlighted media |
| System | health live and ready |

Only admin and register members open sessions or upload. Only admin and query
members call query endpoints. A retrieved image is authorized again at its media
endpoint. Audio query accepts WAV because Meta file transcription requires it.
Captures accept JPEG, PNG, WebP, MP4, MOV and WebM. `MAX_VIDEO_BYTES=0` and
`MAX_VIDEO_SECONDS=0` disable application-level caps by default; physical
PostgreSQL BYTEA and server capacity still apply. Long videos are logically
partitioned by `VIDEO_SEGMENT_SECONDS`, and derived frames retain a
`parent_asset_id`, segment metadata and approximate timestamp while the original
clip remains the BYTEA source of truth. Text query accepts any input language;
the Live provider can select only terms already known in the authorized
workspace before local evidence retrieval.

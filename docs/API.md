# REST API

OpenAPI is served at /v1/openapi.json and interactive documentation at /docs.
All routes use Bearer access tokens and workspace membership.

| Area | Routes |
| --- | --- |
| Auth | login, refresh, me |
| Workspaces | list/create workspaces; list/create zones |
| Sessions | create, read and close capture sessions |
| Captures/jobs | upload/read capture; request processing; inspect analysis or explicit SAM-refinement jobs |
| Objects | list/read/history; add a normalized alias; verify or reject observation. `GET /v1/objects` requires `workspace_id` and accepts `q` (name or alias), `category`, and `zone_id` filters. |
| Query/media | text/audio query; original media; observation-specific highlighted evidence |
| System | health live and ready |

Only admin and register members open sessions or upload. Only admin and query
members call query endpoints. A retrieved image is authorized again at its media
endpoint. Audio query accepts WAV because Meta file transcription requires it.
Captures accept JPEG, PNG, WebP, MP4, MOV and WebM. `MAX_VIDEO_BYTES=0` and
`MAX_VIDEO_SECONDS=0` disable application-level caps by default. Videos above
`VIDEO_INLINE_BYTES` are stored as ordered `media_asset_chunks` BYTEA values in
PostgreSQL, so no external file path or bucket becomes the source of truth.
Long videos are logically partitioned by `VIDEO_SEGMENT_SECONDS`, and derived frames retain a
`parent_asset_id`, segment metadata and approximate timestamp while the original
clip remains the BYTEA source of truth. Text query accepts any input language;
the Live provider can select only terms already known in the authorized
workspace before local evidence retrieval.

`POST /v1/observations/{id}/segment` creates or reuses the one SAM refinement
job for a verified observation. It is restricted to `admin` and `register`.
`query` remains read-only and includes `highlight_quality`, `segmentation_status`,
`segmentation_job_id` and `can_refine`. Its highlighted URL identifies the
observation, rather than only the photo, so the correct object is overlaid when
one image contains several observations.

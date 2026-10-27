# REST API

OpenAPI is served at /v1/openapi.json and interactive documentation at /docs.
Administrative routes use Bearer access tokens and workspace membership.
Device ingestion routes use `X-RealityOS-Device-ID` and
`X-RealityOS-Device-Key`.

| Area | Routes |
| --- | --- |
| Auth | login, refresh, me |
| Workspaces | list/create workspaces; list/create zones |
| Sessions | create, read and close capture sessions |
| Captures/jobs | upload/read capture; request processing; inspect analysis or explicit SAM-refinement jobs |
| Objects | list/read/history; add a normalized alias; verify or reject observation. `GET /v1/objects` requires `workspace_id` and accepts `q` (name or alias), `category`, and `zone_id` filters. |
| Query/media | text/audio query; original media; observation-specific highlighted evidence |
| Devices (admin) | enroll/list/assign/rotate/revoke workspace devices; key material is returned only at enrollment or rotation |
| Device ingestion | list authorized zones; open/close a device session; upload/process a device capture; make a read-only text query; retrieve header-authenticated evidence |
| DAT Display evidence | a device query also returns `display_media_url`: a five-minute, observation-scoped bearer URL issued only for an active enrolled device, so the Display renderer can fetch without exposing device credentials |
| Inventory intelligence (admin) | evidence facts, fact verification, aggregate inventory/brand/condition/use/device metrics and video tracks |
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

`POST /v1/captures/{id}/process` accepts optional `profile` (`basic` or
`detailed`) and `priority_terms`. Basic processing samples video with Muse
Spark. Detailed mode explicitly tracks the listed objects with SAM Video and
persists per-frame PTS, visibility, boxes and RLE masks rather than a JPEG copy
of every frame.

`GET /v1/objects/{id}/facts`, `/v1/objects/{id}/tracks`,
`/v1/tracks/{id}/frames` and `/v1/admin/analytics/inventory` are
administrator-only. Facts are `pending`, `verified` or `rejected`; verified
facts form the main aggregate while provisional results remain separate.

`POST /v1/observations/{id}/segment` creates or reuses the one SAM refinement
job for a verified observation. It is restricted to `admin` and `register`.
`query` remains read-only and includes `highlight_quality`, `segmentation_status`,
`segmentation_job_id` and `can_refine`. Its highlighted URL identifies the
observation, rather than only the photo, so the correct object is overlaid when
one image contains several observations.

`GET /v1/device/zones` is scoped only to the enrolled device workspace. For a
DAT Display query, `display_media_url` is deliberately not a replacement for
device authentication: it is a short-lived signed renderer URL for one verified
highlighted observation. Treat it as a bearer URL while it is valid; it expires
according to `DISPLAY_EVIDENCE_TOKEN_MINUTES`, cannot call any JSON API, and is
invalidated when its issuing enrolled device is revoked.

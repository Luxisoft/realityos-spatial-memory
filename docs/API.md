# REST API

OpenAPI is served at /v1/openapi.json and interactive documentation at /docs.
All routes use Bearer access tokens and workspace membership.

| Area | Routes |
| --- | --- |
| Auth | login, refresh, me |
| Workspaces | list/create workspaces; list/create zones |
| Sessions | create, read and close capture sessions |
| Captures/jobs | upload/read capture; request processing; inspect job |
| Objects | list/read/history; verify or reject observation. `GET /v1/objects` requires `workspace_id` and accepts `q` (name or alias), `category`, and `zone_id` filters. |
| Query/media | text/audio query; original/highlighted media |
| System | health live and ready |

Only admin and register members open sessions or upload. Only admin and query
members call query endpoints. A retrieved image is authorized again at its media
endpoint. Audio query accepts WAV because Meta file transcription requires it.

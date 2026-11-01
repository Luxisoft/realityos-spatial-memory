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
| Query/media | text/audio query; ephemeral image-to-object query; original media; observation-specific highlighted evidence |
| Devices (admin) | enroll/list/assign/rotate/revoke workspace devices; key material is returned only at enrollment or rotation |
| Virtual Display bootstrap | `POST /v1/virtual-devices/bootstrap` issues a rate-limited, short-lived real device identity for an Android virtual-glasses installation only when Live mode is explicitly enabled |
| Device ingestion | list authorized zones; open/close a device session; upload/process a device capture; make a read-only text query; retrieve header-authenticated evidence |
| DAT Display evidence | a device query also returns `display_media_url`: a five-minute, observation-scoped bearer URL issued only for an active enrolled device, so the Display renderer can fetch without exposing device credentials |
| Inventory intelligence (admin) | evidence facts, fact verification, aggregate inventory/brand/condition/use/device metrics and video tracks |
| Faces (consented members) | grant/read/revoke biometric consent; enroll from owned media or profile photo; list own enrollments; read-only ranked search by probe or media; boxed evidence thumbnails |
| Facebook sync | login syncs profile fields, counts, granted scopes, latest 25 uploaded photos + separate profile picture, latest 5 videos and latest 50 posts; worker imports bytes to BYTEA and enrolls faces; owner-only synced-profile read and explicit availability diagnostics |
| Profiles/media | authenticated public profile reads; owner edits; one replaceable private PDF/DOCX CV; cursor-paged profile media and home/work feeds; natural-language people/profile questions with authorized media matches without exposing CV contents |
| Identity verify | mandatory selfie per login is matched against the account Facebook faces; failures stay in place for direct retry with remaining-attempt count; 5 failures lock for 30 min; attempts are audited |
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

`POST /v1/queries/image` accepts one JPEG, PNG or WebP probe plus an
authorized `workspace_id` and optional question. The probe is decoded and sent
to Muse only to identify candidate object terms, then the normal read-only
query path retrieves existing verified evidence. Probe bytes are never stored
as a capture, media asset or observation. Both query endpoints accept an
optional `language` (BCP-47; en/es/pt/fr/de/it, English fallback) and render
the answer sentence in it; stored facts stay untranslated.
`POST /v1/search/classify` accepts the same probe plus `workspace_id` and
returns a face count with candidate object labels so the mobile app can route
the capture to people search, object search, or a disambiguation prompt. Probe
bytes stay ephemeral.
`POST /v1/search/route` accepts free text and returns the AI intent
(`person`, `object` or `ask`) so chat requests route without scope buttons;
the text stays ephemeral.
`POST /v1/chat/append` stores one chat turn (`user`/`ai`, text/voice/image,
optional evidence URL) for the authenticated profile; `GET /v1/chat/history`
returns newest-first pages (`limit`, `before_id`, `has_more`) scoped to that
profile. Capture bytes and audio stay ephemeral; only text loads back.
`POST /v1/auth/guest` accepts a `device_id` and creates or resumes the guest
user bound to that device; `POST /v1/auth/facebook` accepts an optional
`device_id` to record the Meta account binding. Guests get 403 on face search
and enrollment, and only see themselves and fellow guests in profiles, feeds
and media. Work groups carry a 9-digit `join_pin` returned at creation. The creator is
the administrator: only the admin (or members granted `can_invite` at
`POST /v1/groups/{id}/members/{member_id}/invite-permission`) can invite via
`POST /v1/groups/{id}/invite`, read the PIN at `GET /v1/groups/{id}/pin`,
rotate it at `POST /v1/groups/{id}/pin/rotate` (old PIN dies), list members or
remove them; only the creator deletes the group at `DELETE /v1/groups/{id}`
(personal spaces refuse, group publications become personal). Any
authenticated user joins with `POST /v1/groups/join-by-pin`.
`GET /v1/workspaces` exposes `created_by_me` and `can_invite` per membership.

`GET/PATCH /v1/me/profile` manages owner-editable profile fields.
`POST /v1/me/profile/cv` replaces the user's one active private PDF/DOCX CV
(10 MiB maximum), clearing all previously extracted context before processing;
`POST /retry` reprocesses the current file and `DELETE` erases file and derived
context. The owner projection returns the persisted analysis summary, status
and file metadata, but never CV bytes or extracted source text.
`POST /v1/me/profile/publications` accepts one JPEG, PNG or WebP image, stores
the original as BYTEA and creates a private owner publication.
`POST /v1/me/work-publications` accepts the same image plus a `workspace_id`
form field and publishes it into that work workspace for members only.
Both publication endpoints accept optional mobile-only `note_text`
(`voice` or `text` in `note_source`); `POST /v1/notes/transcribe` turns a
short voice recording (WAV, M4A, MP4, 3GP, WebM, MP3) into that note text
without storing audio bytes. No request pins a language: recognition follows
the device speech locale on the phone and the transcription model detects the
spoken language itself.
`GET /v1/profiles/{user_id}` exposes the authenticated public
projection but never CV bytes/text/context, permissions or import diagnostics.
`POST /v1/profiles/search` answers either an app-wide people question or a
question about one profile. CV context may ground the transient answer but is
never exposed through another user's public profile or persisted in search
answers; Mock answers are labelled simulated.
`GET /v1/profiles/{user_id}/media` returns newest-first cursor pagination; an
owner can read their private imports while another user receives only public
media. `GET /v1/gallery/page` provides the same stable cursor contract for
`home` or membership-scoped `work` feeds. Profile search may return
`media_matches`, but only from public, caller-owned, or shared-work media.

`GET /v1/gallery/{post_id}/boxed?labels=drill` returns the small annotated
preview (up to 360 × 480). Add `full_size=true` for the image viewer to keep
the original pixel dimensions and the same label-filtered boxes. Both sizes
enforce the publication's existing access rules and leave the original bytes
unchanged. Videos continue to return their still thumbnail.

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

Face search is an isolated arm (`backend/app/faces.py`, migration
`20261028_0009`): `POST /v1/faces/consent`, `GET /v1/faces/consent` and
`DELETE /v1/faces/consent` manage the versioned biometric notice; revocation
deletes the user's enrollments. `POST /v1/faces/profile-photo` and
`POST /v1/faces/enroll` enroll only caller-owned media (video enrolls from its
extracted frames). `POST /v1/faces/search` is read-only: it accepts an
ephemeral probe photo or video (never persisted) or an authorized stored media
id, and returns consenting workspace members ranked by cosine similarity with
boxed evidence at `/v1/faces/enrollments/{id}/thumbnail`. Video probes sample
up to `FACE_VIDEO_PROBE_FRAMES` frames evenly across the clip; only the best
`FACE_PROBE_MAX_FACES` probe faces are ranked. Probe faces and enrollments
pass the same usable-geometry and minimum-quality filter (`FACE_MIN_QUALITY`,
`FACE_MIN_BOX_AREA`); dropped items are reported as `probe_faces_skipped` and
`enrollments_skipped`, and analyzed frames as `probe_frames`. Search runs in
sequential stages (1: face captures, 2: Facebook photos, 3: videos); the first
stage with matches wins and each match carries `direct` or
`possible_acquaintance` type. Scores are similarity, not calibrated
probability; mock results are labelled simulated. Thumbnails accept
`full_size=false` for a 360×480 preview (default keeps source pixels). With
the live engine, capture uploads additionally pass passive anti-spoof
heuristics (tiny face, blur, moire, glare) and are rejected at 422 above
`FACE_SPOOF_MAX_RISK`.


### Reviewed uploads and search evidence (2026-10-30)

`POST /v1/me/publication-uploads` accepts multipart image `file`, idempotency
`request_key`, `audience` (home/work/public), optional work `workspace_id`,
caption and note fields. It returns 202 with owner-only upload id and status.
The worker checks duplicates with Meta and grounds detections before publishing.
`GET /v1/me/publication-uploads/{id}` returns pending, duplicate, published,
failed or cancelled; the payload includes authorized previews and result id.
`POST .../{id}/confirm` replaces a confirmed same-owner/destination duplicate,
retaining publication identity, comments and reactions. `cancel` and `retry`
are explicit POST operations. Legacy image-upload routes return 409 for
repeated photos instead of adding another publication.

Query `gallery_matches` now includes immutable `evidence_id`, media id,
annotated `image_url` at full size, annotated thumbnail, source MIME type,
matched labels, visual confidence, note and source publication date. Video
matches include the decoder's `frame_timestamp_ms`; only one representative
frame per video is selected. `GET /v1/gallery/evidence/{id}?labels=...` renders
only exact stored labels, returns 404 without matching geometry and checks
publication access on every request. `full_size=true` preserves source pixel
dimensions. Unversioned chat gallery entries are not rendered by the new APK.

Search is read-only: indexing, duplicate retirement and segmentation run on
uploads or explicitly queued worker jobs, never from a query. Text-only
matches are not returned as object images.


### Estado de recuperación visual de Query (2026-10-30)

`QueryResponse` añade `gallery_search_status`: `not_searched`, `ready`,
`indexing`, `unavailable` o `no_match`, y `gallery_pending_count`. `found` sigue
reservado a la observación verificada; `gallery_matches` puede contener
resultados aunque `found=false`. Un resultado incluye `match_kind` opcional
(`exact`, `family`, `similar`) y `localization_quality` opcional (`sam`,
`approximate_box`). El historial de chat conserva estos campos. Las etiquetas
son las realmente detectadas y el tipo de relación no representa confianza de
que el objeto permanezca allí ahora.

La consulta solo utiliza evidencia inmutable localizada y autorizada, deduplica
medios y ordena exactos antes de familiares y similares. La evidencia aproximada
v1 permite consultar cajas anteriores mientras termina SAM v2. Las URLs
`thumbnail_url` e `image_url` mantienen la misma señalización; `image_url` usa
`/v1/gallery/evidence/{id}?labels=...&full_size=true` a la resolución guardada.
La materialización v1 es una operación administrativa explícita, ajena a Query.


### Información bilingüe preparada al publicar (2026-10-30)

Las publicaciones nuevas preparan y guardan español e inglés antes de completar
la publicación. Títulos, notas y etiquetas se conservan en
`publication_translations`, por publicación, idioma y hash del texto original.
Un cambio de texto genera traducciones nuevas; las anteriores permiten consultar
la evidencia que permanece en el historial. Los originales y recuadros no cambian.

`gallery_matches` añade `localized_information`, con entradas `en` y `es`, cada
una con `title`, `note_text`, `matched_labels` y `simulated`. El historial de chat
conserva este mapa. Android lee directamente el idioma elegido, sin inferencia
ni espera de traducción al abrir el recurso.

`POST /v1/gallery/evidence/information` se conserva para historial antiguo.
Recibe `language` (`en`/`es`, incluidas variantes regionales) e `items` de uno a
seis, con `evidence_id` y `labels`. Autoriza cada recurso y consulta únicamente
las traducciones persistidas; nunca llama a Meta, escribe filas ni encola tareas.
Devuelve `ready` si todos están preparados y `pending` con los que estén listos
si falta alguno. No sustituye un idioma ausente por inglés. La aplicación
muestra un estado finito de información pendiente o error, con reintento manual.

Preparación administrativa reanudable de datos existentes:
`PYTHONPATH=/app python /scripts/prepare_publication_languages.py --apply`.
El modo sin `--apply` solo informa pendientes. Este proceso es independiente
de la visualización, conserva avances por lote y prepara ambos idiomas.

Los resultados se ordenan por confianza visual descendente antes de deduplicar
y aplicar límites. Los empates usan relación exacta/familiar/similar, calidad
de localización y publicación reciente; Android mantiene ese orden y la
identidad del recurso pulsado.


### Recuperación de recursos del historial

`GET /v1/chat/history` actualiza la representación de los recursos desde la
publicación y evidencia autorizadas, incluyendo los mapas `en`/`es`. Resuelve
referencias antiguas `/gallery/{id}/boxed` a evidencia inmutable existente;
no genera cajas, captura ni traducciones durante la lectura. Las referencias
originales que no se puedan recuperar se conservan en el almacenamiento.

`POST /v1/gallery/evidence/information/prepare` es la acción explícita de
recuperación si falta una traducción en el historial. Recibe el mismo cuerpo
que `/information`, autoriza todo el lote, prepara los textos ausentes, revisa
el acceso otra vez, guarda ambos idiomas y devuelve la información lista.
También actualiza las copias de recursos de los mensajes del usuario. Si ya
existen las traducciones, responde directamente sin inferencia. Un fallo no
guarda resultados parciales. Las rutas Query y la lectura `/information`
continúan siendo de solo lectura.

Android consulta primero lo guardado y llama a esta acción únicamente ante
`pending`. Muestra el progreso de preparación y reemplaza el contenido en la
misma apertura; los siguientes accesos usan los datos guardados. Refresca los
mensajes ya cargados conservando sus identificadores locales, adjuntos y orden.

## Account language and assistant history (2026-10-31)

`GET /v1/me/preferences` returns the authenticated account's nullable
`preferred_language`. `PATCH /v1/me/preferences` saves `en` or `es` (regional
variants normalize to their base). `?initialize=true` only fills an unset value;
it never overwrites a preference saved by another installation.

For human queries, the account preference takes precedence over request
`language`; accounts without a preference retain existing request/default
behavior. Text, image, WAV audio, assistant and textual profile answers report
`response_language`. Device queries retain their explicit language because a
device credential is a workspace identity, not a human account.

`POST /v1/chat/append` accepts optional `response_language` and prepares persistent
English/Spanish versions of AI turns. Original `text` remains unchanged.
History adds `localized_text`, `localized_quick_replies`, `response_language`,
`source_language`, `translation_status` (`ready`, `pending`, `failed`) and an
optional `translation_simulated`. User turns retain their original text.

`POST /v1/chat/history/prepare` takes `{"message_ids":[28,30]}` (1–50 owned turns),
materializes exact known templates without a provider and queues missing free
text translations. Duplicate jobs reuse a per-message lock and content hash.
`GET /v1/chat/history/translations?ids=28,30` reads the current language/status
without writes or model calls. Unauthorized selections return 404. Failed or
expired jobs can be retried explicitly; successful versions remain cached.

## Partial gallery search and staged analysis (2026-10-31)

Query responses add `gallery_failed_count`, `gallery_search_reason` (`none`,
`incomplete_index`, `semantic_unavailable`, `storage_unavailable`) and the
`partial` value of `gallery_search_status`. Usable annotated matches remain
visible while other authorized files require analysis/review. Failed files are
counted separately from queued/unindexed files. `unavailable` indicates failure
of the current search without usable matches; stored errors from unrelated
publications cannot turn an otherwise working search into an outage. Messages
and TTS use the account language.

Gallery SAM box prompts are split into groups of at most 16. Every group must
complete before activation. Gallery index runs checkpoint completed video
frames, preserve the previous active set and activate evidence plus bilingual
information atomically. Historical evidence IDs remain immutable/readable after
normal authorization. Staged or failed-run evidence cannot be rendered or read
through information/history endpoints.


### Meta Display: fuentes, video y medios temporales (2026-10-31)

`QueryRequest.search_scope` admite `auto` (valor anterior, predeterminado),
`gallery` (solo publicaciones autorizadas de la app) y `registry` (solo objetos
verificados por ubicación, sin fallback a galería). `gallery` exige identidad
humana; `/v1/device/queries` rechaza ese modo con 403. La consulta permanece
solo lectura y no inicia captura ni indexación.

`POST /v1/me/publication-uploads` acepta también `video/mp4`. Verifica el
contenedor y duración mediante FFprobe: máximo 120 segundos o el límite del
servidor si es menor; respeta `max_video_bytes` cuando está configurado.
Conserva el MP4 original en BYTEA, analiza fotogramas con el pipeline existente
y guarda evidencia señalizada con `frame_timestamp_ms` y traducciones. Los
videos duplicados se comparan por SHA-256 dentro del mismo propietario/destino;
solo la confirmación explícita reemplaza la publicación. Fotos conservan su
revisión visual actual. Idempotencia y estados de carga permanecen compatibles.

`POST /v1/display/media-links` requiere Bearer humano y recibe
`{kind: "evidence" | "upload" | "publication", resource_id: UUID, labels: string[]}`.
Valida permisos y devuelve `{url, expires_at}`. Para evidencia, `labels` solo
puede señalar detecciones existentes. `GET /v1/display/media?token=...` vuelve
a validar usuario, recurso y acceso vigente antes de servir una imagen JPEG
contenida en 600×280, sin recortar ni alterar originales. El permiso firmado
caduca con `display_evidence_token_minutes`, sirve únicamente ese recurso y
no da acceso a otras rutas; respuesta `private, no-store` y `no-referrer`.

## Agent response audio (2026-11-01)

`POST /v1/tts` accepts `{ "text": "Hello.", "language": "en" }` and returns
`audio/wav` (mono PCM16, `Cache-Control: no-store`). Text is required, nonblank,
and limited to 4000 characters; language is `en` or `es`. Extra fields, including
workspace/message/media references and arbitrary provider URLs, are rejected.

Authenticate with the existing account bearer token or the existing device
ID/key headers. Devices require an active workspace assignment. This stateless
endpoint speaks only supplied text; it never queries another account's history,
retrieves evidence, creates captures or stores generated audio. Errors: 401 for
invalid credentials, 403 for an unassigned device, 422 for invalid input and 503
when synthesis cannot complete. Mock mode never calls the speech provider.

The backend allows one transient retry within a 30-second overall deadline.
Android and both browser clients then use their existing device voice if audio
is unavailable. Caller authentication errors are not retried or spoken through
fallback. Existing query schemas and `tts_text` remain compatible. See [TTS](TTS.md).

# Database

Alembic revision 20261026_0001 creates all core tables, UUID keys, foreign keys
and indexes. It enables pg_trgm on PostgreSQL; SQLAlchemy metadata creates the
schema in migration context, including enum types.

media_assets.original_bytes is BYTEA/LargeBinary and is the source of truth for
images and inline video. Oversized video is retained in ordered
media_asset_chunks.content BYTEA rows, still entirely inside PostgreSQL; its
media_assets row records the full SHA-256, byte size and chunk metadata. SHA-256
and a capture-session/hash unique constraint avoid duplicate processing. Child
masks/crops use parent_asset_id.

tracked_objects is logical identity. object_observations is evidence; the last
location comes from verified observations ordered by seen_at, not a mutable
column. `muse_bounding_box` retains initial approximate geometry. A successful
on-demand SAM refinement updates the best box and links `mask_asset_id` to a
one-bit PNG in `media_assets`, while retaining the original bytes and the Muse
box. `processing_jobs.operation` separates initial analysis from explicit
segmentation and its workspace-scoped idempotency key prevents duplicate paid
requests. The current MVP matcher is encapsulated in services.object_candidates.

`devices` stores a workspace-bound public identifier and a peppered hash of its
generated upload credential. `device_assignments` preserves administrator
labels and notification-attestation history. Device-created capture sessions
retain their device and assignment snapshot.

`object_facts` is the evidence source for observed brand, model, visible count,
condition and usage state. Each claim records confidence, provenance, model,
geometry and review status. `tracked_objects.attributes` is only a convenience
summary. `object_tracks`, `object_track_segments` and `object_track_frames`
retain detailed SAM Video PTS, visibility, geometry and compact RLE masks while
the original video stays in PostgreSQL.

`face_enrollments` stores one BYTEA float32 embedding per detected face with its
model version, evidence media, bounding box, quality and source
(`profile`, `capture` or `frame`); only same-model embeddings are ever
compared. `biometric_consents` records the notice version, consent timestamp
and optional revocation per user. Both tables belong to the isolated
face-search arm and its `20261028_0009` migration. Revision `20261103_0032`
adds `face_record_enrollments` (record, workspace, media, optional record-media
link, embedding, box, quality, `record-portrait`/`record-frame` source and
authorizing worker) plus explicit `biometric_authorized/basis/by/at` columns on
`workspace_records`; only active person rows with authorization are searchable,
and enrollments are explicit, never automatic. Revision `20261103_0033` keeps
only the ORM-named indexes on that table (0032 had duplicated one workspace
index because Alembic also honors `index=True`).

`facebook_profiles` stores one synced row per user (email, birthday, age
range, gender, hometown, location, link, picture, friends/likes/photos/videos
counts, granted scopes and import status); missing scopes stay NULL, never
fabricated. `facebook_media` inventories photo/video ids, source URLs and
import pointers; imported bytes become regular `media_assets` rows (origin
`facebook-import`) with face enrollments, keeping BYTEA the source of truth.
`facebook_posts` keeps raw post material for future personality analysis.
`face_verifications` audits internal identity-verification attempts
(result, score, threshold, engine) without exposing them to clients.

Revision `20261028_0014` adds `user_profiles` and `facebook_friends`.
`user_profiles` contains the public owner-edited fields and exactly one current
private CV as BYTEA together with its hash, extracted text, private model
context and processing state. Uploading a replacement clears the previous
derived values before processing, and deletion removes the file and every
derivative. Public profile responses never serialize those private columns.
`facebook_friends` contains only friends actually returned by Graph for the
app-scoped login; missing friend details are never inferred from a count or ID.

Revision `20261028_0015` unifies profile and publication media. Publications
gain source identity, searchable text and source publication time plus stable
newest-first indexes; `(owner_id, source, source_ref)` makes Facebook import
idempotent. `user_profiles.avatar_media_id` points at a BYTEA-backed media
asset, and `facebook_profiles.sync_diagnostics` records whether each Graph
edge was ready, empty or unavailable without fabricating content.

Run migrations with `make migrate`. The device, fact and detailed-track
migrations (`20261027_0005` and `20261027_0006`) were applied to the production
PostgreSQL 16 instance and verified at revision `20261027_0006` on 2026-10-27.


Revision `20261030_0026` adds `publications.evidence_version` (default 0),
immutable `gallery_evidence` (oriented JPEG derivatives, detections and exact
video-frame milliseconds), owner-scoped `publication_uploads` with original
BYTEA pending automatic review, `publication_revisions` and reversible
`publication_duplicates` aliases. The original captured MediaAsset BYTEA is
never removed by this flow. Duplicate retirement hides redundant publications
inside the same owner/destination and retains their originals and reversal map.
The production rollback keeps this additive schema and runs the previous API
without invoking its older Alembic startup; do not downgrade populated evidence
tables merely to roll back application code.


### Traducciones persistidas de publicaciones — `20261030_0027`

`publication_translations` almacena `post_id`, `language` (`en` o `es`),
`text_hash` (SHA-256 del texto original), `translated_text`, `simulated` y
`created_at`. La clave primaria compuesta permite reintentos sin duplicados y
conservar traducciones de etiquetas anteriores para historial. La FK de
publicación elimina estas filas al retirar definitivamente la publicación.
La autorización se realiza mediante la publicación/evidencia antes de consultar
sus textos. La migración solo añade esta tabla; no altera BYTEA ni notas.

### Account/chat languages — `20261031_0028`

Additive migration: nullable `users.preferred_language`, nullable
`chat_messages.response_language` and `template_data`; original turn text stays
intact. `chat_message_translations` uses `(message_id, language, source_hash)` as
its primary key, with cascading message ownership, translated text/quick replies,
status, simulation marker and update timestamp. Content hashes include reply
labels so edited sources cannot reuse stale translations. The API exposes queued
jobs as pending; expired pending jobs become retryable. Publication translations
and evidence metadata retain their existing storage.

### Safe gallery analysis — `20261031_0029`

`gallery_index_runs` records the source publication/media/hash, stage, status,
attempt, worker lease, structured failure and JSON progress (completed frames,
prior objects, review decisions/details). `gallery_evidence.index_run_id` links
staged immutable image/frame evidence to a run. Nullable
`publications.active_index_run_id` selects a completed generation; older rows
retain their existing behavior until repaired. Activation updates this pointer,
legacy detection mirrors and both language maps together. Interrupted runs keep
completed frame evidence for an explicit resumed attempt. Neither schema upgrade
nor image rollback deletes media or historical evidence.

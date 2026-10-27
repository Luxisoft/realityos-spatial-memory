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
column. The current MVP matcher is encapsulated in services.object_candidates.

Run migrations with make migrate. The migration was not run against PostgreSQL
in this workspace because Docker is unavailable here.

"""Convert one explicitly named legacy video BYTEA into ordered PostgreSQL chunks.

Use this only after the media_asset_chunks migration has been applied. It runs
the split inside PostgreSQL, so the oversized source BYTEA is never fetched
into the script process.
"""

from __future__ import annotations

import argparse
import uuid

from app.config import get_settings
from app.db import Database
from sqlalchemy import text

CHUNKED_STORAGE = "chunked_postgres_bytea"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-id", required=True, type=uuid.UUID)
    parser.add_argument("--chunk-bytes", type=int, default=8 * 1024 * 1024)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.chunk_bytes < 1024 * 1024:
        raise SystemExit("--chunk-bytes must be at least 1 MiB.")
    database = Database(get_settings().database_url)
    with database.session_factory() as db:
        row = db.execute(
            text(
                "SELECT id, kind::text AS kind, byte_size, metadata, octet_length(original_bytes) AS stored_bytes "
                "FROM media_assets WHERE id = :asset_id FOR UPDATE"
            ),
            {"asset_id": args.asset_id},
        ).mappings().one_or_none()
        if row is None:
            raise SystemExit("Media asset was not found.")
        if row["kind"] != "VIDEO":
            raise SystemExit("Only VIDEO media assets can be chunked.")
        if (row["metadata"] or {}).get("storage") == CHUNKED_STORAGE:
            raise SystemExit("Media asset is already stored as PostgreSQL chunks.")
        if row["stored_bytes"] != row["byte_size"]:
            raise SystemExit("Stored media size does not match recorded byte size.")
        chunk_count = (row["byte_size"] + args.chunk_bytes - 1) // args.chunk_bytes
        db.execute(
            text(
                "INSERT INTO media_asset_chunks (asset_id, chunk_index, content, byte_size) "
                "SELECT asset.id, parts.chunk_index, "
                "substring(asset.original_bytes FROM parts.chunk_index * :chunk_bytes + 1 FOR :chunk_bytes), "
                "octet_length(substring(asset.original_bytes FROM parts.chunk_index * :chunk_bytes + 1 FOR :chunk_bytes)) "
                "FROM media_assets AS asset "
                "CROSS JOIN generate_series(0, :chunk_count - 1) AS parts(chunk_index) "
                "WHERE asset.id = :asset_id"
            ),
            {
                "asset_id": args.asset_id,
                "chunk_bytes": args.chunk_bytes,
                "chunk_count": chunk_count,
            },
        )
        totals = db.execute(
            text(
                "SELECT count(*) AS chunk_count, coalesce(sum(byte_size), 0) AS byte_size "
                "FROM media_asset_chunks WHERE asset_id = :asset_id"
            ),
            {"asset_id": args.asset_id},
        ).mappings().one()
        if totals["chunk_count"] != chunk_count or totals["byte_size"] != row["byte_size"]:
            raise SystemExit("Chunk verification failed; transaction will roll back.")
        db.execute(
            text(
                "UPDATE media_assets SET original_bytes = '\\x'::bytea, "
                "metadata = (coalesce(metadata::jsonb, '{}'::jsonb) || "
                "jsonb_build_object('storage', :storage, 'chunk_size_bytes', :chunk_bytes, "
                "'chunk_count', :chunk_count))::json "
                "WHERE id = :asset_id"
            ),
            {
                "asset_id": args.asset_id,
                "storage": CHUNKED_STORAGE,
                "chunk_bytes": args.chunk_bytes,
                "chunk_count": chunk_count,
            },
        )
        db.commit()
    print(f"asset_id={args.asset_id} chunks={chunk_count} byte_size={row['byte_size']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

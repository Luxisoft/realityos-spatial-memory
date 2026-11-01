from __future__ import annotations

import hashlib
import tempfile
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    MediaAsset,
    MediaAssetChunk,
)

CHUNKED_POSTGRES_BYTEA = "chunked_postgres_bytea"


def media_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def media_is_chunked(asset: MediaAsset) -> bool:
    return asset.extra_metadata.get("storage") == CHUNKED_POSTGRES_BYTEA


def add_postgres_bytea_chunks(
    db: Session, asset: MediaAsset, content: bytes, chunk_bytes: int
) -> None:
    """Keep an oversized original entirely in PostgreSQL without one huge BYTEA."""

    if chunk_bytes < 1:
        raise ValueError("chunk_bytes must be positive.")
    if not content:
        raise ValueError("content must not be empty.")
    asset.original_bytes = b""
    asset.extra_metadata = {
        **asset.extra_metadata,
        "storage": CHUNKED_POSTGRES_BYTEA,
        "chunk_size_bytes": chunk_bytes,
        "chunk_count": (len(content) + chunk_bytes - 1) // chunk_bytes,
    }
    db.add_all(
        MediaAssetChunk(
            asset_id=asset.id,
            chunk_index=index,
            content=content[offset : offset + chunk_bytes],
            byte_size=min(chunk_bytes, len(content) - offset),
        )
        for index, offset in enumerate(range(0, len(content), chunk_bytes))
    )


@contextmanager
def materialized_media_file(db: Session, asset: MediaAsset):
    """Materialize BYTEA chunks only in a scoped worker temp file for FFmpeg."""

    with tempfile.TemporaryDirectory(prefix="realityos-media-") as directory:
        path = Path(directory) / "source-media"
        with path.open("wb") as output:
            if media_is_chunked(asset):
                chunks = db.scalars(
                    select(MediaAssetChunk.content)
                    .where(MediaAssetChunk.asset_id == asset.id)
                    .order_by(MediaAssetChunk.chunk_index)
                )
                total = 0
                for chunk in chunks:
                    output.write(chunk)
                    total += len(chunk)
                if total != asset.byte_size:
                    raise ValueError("Stored media chunks do not match the recorded byte size.")
            else:
                output.write(asset.original_bytes)
        yield path

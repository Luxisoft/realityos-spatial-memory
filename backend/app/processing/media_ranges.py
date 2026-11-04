"""Single HTTP byte ranges and bounded reads of PostgreSQL media chunks."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session


def _parse_range(value: str, total: int) -> tuple[int, int] | None:
    """Parse a single ``bytes=`` range into inclusive (start, end) offsets."""

    if total <= 0 or not value.startswith("bytes="):
        return None
    spec = value.removeprefix("bytes=").strip()
    if "," in spec:
        return None
    start_text, dash, end_text = spec.partition("-")
    if not dash:
        return None
    try:
        if not start_text:
            suffix = int(end_text)
            if suffix <= 0:
                return None
            start = max(0, total - suffix)
            return (start, total - 1)
        start = int(start_text)
        end = int(end_text) if end_text else total - 1
    except ValueError:
        return None
    if start < 0 or end < start or start >= total:
        return None
    return (start, min(end, total - 1))


def _chunked_slice(db: Session, asset_id: uuid.UUID, start: int, end: int) -> bytes:
    from app.models import MediaAssetChunk

    sizes = list(
        db.execute(
            select(MediaAssetChunk.chunk_index, MediaAssetChunk.byte_size)
            .where(MediaAssetChunk.asset_id == asset_id)
            .order_by(MediaAssetChunk.chunk_index)
        )
    )
    first_index = last_index = -1
    first_start = 0
    offset = 0
    for chunk_index, byte_size in sizes:
        chunk_start, chunk_end = offset, offset + byte_size - 1
        if chunk_end >= start and chunk_start <= end:
            if first_index < 0:
                first_index = chunk_index
                first_start = chunk_start
            last_index = chunk_index
        offset += byte_size
    if first_index < 0:
        return b""
    parts = db.scalars(
        select(MediaAssetChunk.content)
        .where(
            MediaAssetChunk.asset_id == asset_id,
            MediaAssetChunk.chunk_index >= first_index,
            MediaAssetChunk.chunk_index <= last_index,
        )
        .order_by(MediaAssetChunk.chunk_index)
    )
    joined = b"".join(parts)
    return joined[start - first_start : end - first_start + 1]

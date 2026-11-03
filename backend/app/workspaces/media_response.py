"""Serve authorized record originals, including ranged and chunked video playback."""

from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select

from app.models import MediaAssetChunk
from app.services import media_is_chunked
from app.social_features.gallery import _chunked_slice, _parse_range


def media_response(db, asset, range_header):
    total = asset.byte_size
    headers = {
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff",
        "Accept-Ranges": "bytes",
    }
    if range_header:
        bounds = _parse_range(range_header.strip(), total)
        if bounds is None:
            return Response(
                status_code=416, headers=headers | {"Content-Range": f"bytes */{total}"}
            )
        start, end = bounds
        body = (
            _chunked_slice(db, asset.id, start, end)
            if media_is_chunked(asset)
            else asset.original_bytes[start : end + 1]
        )
        return Response(
            body,
            status_code=206,
            media_type=asset.mime_type,
            headers=headers | {"Content-Range": f"bytes {start}-{end}/{total}"},
        )
    if media_is_chunked(asset):

        def chunks():
            yield from db.scalars(
                select(MediaAssetChunk.content)
                .where(MediaAssetChunk.asset_id == asset.id)
                .order_by(MediaAssetChunk.chunk_index)
            )

        return StreamingResponse(
            chunks(), media_type=asset.mime_type, headers=headers | {"Content-Length": str(total)}
        )
    return Response(asset.original_bytes, media_type=asset.mime_type, headers=headers)

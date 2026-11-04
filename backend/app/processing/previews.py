"""Ephemeral image/video previews; original PostgreSQL evidence stays immutable."""

import io
import subprocess

from PIL import Image, ImageOps

from app.processing.storage import materialized_media_file


def image_thumbnail(raw: bytes, size: tuple[int, int], quality: int = 85) -> bytes:
    with Image.open(io.BytesIO(raw)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail(size)
        output = io.BytesIO()
        image.save(output, "JPEG", quality=quality)
        return output.getvalue()


def video_thumbnail(db, asset) -> bytes:
    with materialized_media_file(db, asset) as source:
        result = subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-i",
                str(source),
                "-frames:v",
                "1",
                "-vf",
                "scale=360:480:force_original_aspect_ratio=decrease",
                "-f",
                "image2pipe",
                "-vcodec",
                "mjpeg",
                "pipe:1",
            ],
            capture_output=True,
            timeout=15,
            check=True,
        )
        return result.stdout

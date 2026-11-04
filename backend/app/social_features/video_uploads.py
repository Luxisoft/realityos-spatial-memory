"""Bounded MP4 publication review, without coupling to the object registry."""

import hashlib
import io
import subprocess
import tempfile
from pathlib import Path

from fastapi import HTTPException
from PIL import Image

from app.models import MediaAsset, MediaKind
from app.social_features.evidence_index import frames
from app.social_features.models import Publication
from app.social_features.visual import ground, normalize
from app.video import VideoProcessingError, probe_video_file


def validate_video(raw, settings):
    if len(raw) < 12 or raw[4:8] != b"ftyp":
        raise HTTPException(422, "Invalid MP4 container.")
    with tempfile.TemporaryDirectory(prefix="publication-probe-") as directory:
        path = Path(directory) / "source.mp4"
        path.write_bytes(raw)
        try:
            info = probe_video_file(path)
        except (VideoProcessingError, ValueError, OSError) as error:
            raise HTTPException(422, "Invalid MP4 video.") from error
    maximum = min(120, settings.max_video_seconds or 120)
    if info.duration_seconds > maximum:
        raise HTTPException(413, f"Video exceeds {maximum} seconds.")


def preview_bytes(upload):
    if upload.mime_type != "video/mp4":
        return upload.original_bytes
    with tempfile.TemporaryDirectory(prefix="publication-preview-") as directory:
        path = Path(directory) / "source.mp4"
        path.write_bytes(upload.original_bytes)
        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-i",
                    str(path),
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
                timeout=20,
                check=True,
            )
            with Image.open(io.BytesIO(result.stdout)) as image:
                image.verify()
            return result.stdout
        except (subprocess.SubprocessError, ValueError, OSError) as error:
            raise HTTPException(422, "Video preview unavailable.") from error


def analyze_video(db, upload, client):
    from app.social_features.localizations import prepare_languages
    from app.social_features.upload_service import same_scope

    digest = hashlib.sha256(upload.original_bytes).hexdigest()
    match = db.scalar(
        same_scope(db, upload.owner_id, upload.workspace_id)
        .join(MediaAsset, Publication.media_id == MediaAsset.id)
        .where(MediaAsset.kind == MediaKind.VIDEO, MediaAsset.sha256 == digest)
    )
    source = MediaAsset(
        kind=MediaKind.VIDEO, original_bytes=upload.original_bytes, extra_metadata={}
    )
    analyzed = []
    for raw, timestamp in frames(db, source):
        _, pixel, _, detections = ground(client, raw)
        analyzed.append({"timestamp": timestamp, "hash": pixel, "detections": detections})
    if not analyzed:
        raise ValueError("Video has no decodable frames.")
    detections = [d for frame in analyzed for d in frame["detections"]]
    translations = prepare_languages(
        client, [upload.caption or "", upload.note_text or "", *[d["label"] for d in detections]]
    )
    return match, {
        "frames": analyzed,
        "detections": detections,
        "fingerprint": {"visual_identity": digest},
        "localizations": translations,
        "simulated": client.__class__.__name__.startswith("Mock"),
    }


def analyzed_frames(db, upload):
    """Recreate saved frame pixels without repeating model inference."""
    wanted = {frame["timestamp"]: frame for frame in upload.analysis["frames"]}
    source = MediaAsset(
        kind=MediaKind.VIDEO, original_bytes=upload.original_bytes, extra_metadata={}
    )
    found = set()
    for raw, timestamp in frames(db, source):
        frame = wanted.get(timestamp)
        if frame is None:
            continue
        image, _, _, digest, _ = normalize(raw)
        if digest != frame["hash"]:
            raise ValueError("Video frame changed during review. Retry analysis.")
        found.add(timestamp)
        yield image, digest, timestamp, frame["detections"]
    if found != set(wanted):
        raise ValueError("Video frames changed during review. Retry analysis.")

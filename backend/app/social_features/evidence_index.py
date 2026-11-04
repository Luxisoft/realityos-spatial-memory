"""Background-only gallery grounding. Search never starts analysis or capture."""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path

from app.models import MediaAsset, MediaKind
from app.services import materialized_media_file
from app.social_features.evidence_models import GalleryEvidence
from app.social_features.visual import INDEX_VERSION, ground


def frames(db, asset):
    from app.video import probe_video_file

    with materialized_media_file(db, asset) as source:
        info = probe_video_file(source)
        maximum = max(1, min(120, int(os.environ.get("GALLERY_MAX_VIDEO_FRAMES", "120"))))
        sampled_count = max(1, maximum * 3 // 4)
        scene_count = maximum - sampled_count
        interval = max(
            float(os.environ.get("GALLERY_VIDEO_STEP_SECONDS", "2")),
            info.duration_seconds / sampled_count,
        )
        seen = set()
        with tempfile.TemporaryDirectory(prefix="gallery-grounding-") as directory:
            for mode, expression, limit in (
                (
                    "sample",
                    f"isnan(prev_selected_t)+gte(t-prev_selected_t,{interval})",
                    sampled_count,
                ),
                ("scene", "gt(scene,0.35)", scene_count),
            ):
                if limit < 1:
                    continue
                pattern = str(Path(directory) / f"{mode}-%04d.jpg")
                escaped = expression.replace(",", r"\,")
                # Bound frame size so uploads and model inference stay within
                # the detection timeout; boxes are normalized so grounding
                # stays valid at any resolution.
                filters = (
                    f"setpts=PTS-STARTPTS,select={escaped},"
                    r"scale=min(iw\,1280):-2,showinfo"
                )
                command = [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "info",
                    "-i",
                    str(source),
                    "-vf",
                    filters,
                    "-fps_mode",
                    "vfr",
                    "-frames:v",
                    str(limit),
                    "-q:v",
                    "2",
                    pattern,
                ]
                try:
                    result = subprocess.run(
                        command,
                        capture_output=True,
                        timeout=max(120, int(info.duration_seconds * 3)),
                        check=False,
                    )
                except (subprocess.SubprocessError, OSError) as error:
                    raise ValueError("Video frame extraction failed.") from error
                output_files = sorted(Path(directory).glob(f"{mode}-*.jpg"))
                if result.returncode:
                    if mode == "scene" and not output_files:
                        continue
                    raise ValueError("Video frames could not be decoded.")
                times = [
                    float(v)
                    for v in re.findall(
                        r"pts_time:([\d.e+-]+)", result.stderr.decode(errors="replace")
                    )
                ]
                files = sorted(Path(directory).glob(f"{mode}-*.jpg"))
                # showinfo may log one additional frame while the encoder drains.
                if len(times) < len(files):
                    raise ValueError("Frame timestamps missing")
                for path, seconds in zip(files, times):
                    milliseconds = round(seconds * 1000)
                    if milliseconds in seen:
                        continue
                    seen.add(milliseconds)
                    yield path.read_bytes(), milliseconds


def stage_evidence(db, post, client, run, checkpoint):
    asset = db.get(MediaAsset, post.media_id)
    items = frames(db, asset) if asset.kind == MediaKind.VIDEO else [(asset.original_bytes, None)]
    completed = set(run.progress.get("completed_frames", []))
    for raw, timestamp in items:
        key = timestamp if timestamp is not None else -1
        if key in completed:
            continue
        run.stage = "detection"
        image, digest, phash, detections = ground(client, raw)
        if detections:
            db.add(
                GalleryEvidence(
                    post_id=post.id,
                    media_id=asset.id,
                    image_bytes=image,
                    content_hash=digest,
                    frame_timestamp_ms=timestamp,
                    detections=detections,
                    version=INDEX_VERSION,
                    index_run_id=run.id,
                )
            )
        completed.add(key)
        run.progress = {**run.progress, "completed_frames": sorted(completed)}
        if timestamp is None:
            run.progress = {**run.progress, "visual_hash": phash, "pixel_hash": digest}
        checkpoint()
    run.progress = {**run.progress, "frames_complete": True}
    checkpoint()


def index_evidence(db, post, client):
    # Compatibility entry point for explicit background/test operations.
    from app.social_features.index_runs import process_run

    return process_run(db, post, client)

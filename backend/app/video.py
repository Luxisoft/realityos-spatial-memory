"""Bounded, traceable video probing and representative-frame extraction."""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


class VideoProcessingError(RuntimeError):
    """A safe error for an invalid or unavailable video-processing toolchain."""


@dataclass(frozen=True)
class VideoInfo:
    duration_seconds: float
    width: int | None
    height: int | None


def probe_video(video: bytes) -> VideoInfo:
    """Read duration and dimensions without persisting an external copy."""

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "format=duration:stream=width,height",
                "-of",
                "json",
                "-i",
                "pipe:0",
            ],
            input=video,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise VideoProcessingError("Video processing is unavailable: ffprobe is not installed.") from exc
    except subprocess.TimeoutExpired as exc:
        raise VideoProcessingError("Video inspection timed out.") from exc
    if result.returncode:
        raise VideoProcessingError("Invalid or unsupported video data.")
    try:
        payload = json.loads(result.stdout)
        duration = float(payload["format"]["duration"])
        stream = payload.get("streams", [{}])[0]
        width = int(stream["width"]) if stream.get("width") else None
        height = int(stream["height"]) if stream.get("height") else None
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise VideoProcessingError("Video metadata could not be read.") from exc
    if duration <= 0:
        raise VideoProcessingError("Video must contain a positive duration.")
    return VideoInfo(duration_seconds=duration, width=width, height=height)


def extract_representative_frames(
    video: bytes, info: VideoInfo, max_frames: int
) -> list[tuple[float, bytes]]:
    """Extract no more than ``max_frames`` JPEGs and retain only temporary files."""

    if max_frames < 1:
        raise ValueError("max_frames must be positive.")
    # Sampling rate bounds processing even for a valid maximum-length clip.
    frame_rate = max_frames / info.duration_seconds
    with tempfile.TemporaryDirectory(prefix="realityos-video-") as directory:
        pattern = str(Path(directory) / "frame-%03d.jpg")
        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-i",
                    "pipe:0",
                    "-vf",
                    f"fps={frame_rate:.9f},scale='min(1280,iw)':-2",
                    "-frames:v",
                    str(max_frames),
                    "-q:v",
                    "3",
                    pattern,
                ],
                input=video,
                capture_output=True,
                check=False,
                timeout=max(30, int(info.duration_seconds * 2) + 10),
            )
        except FileNotFoundError as exc:
            raise VideoProcessingError("Video processing is unavailable: ffmpeg is not installed.") from exc
        except subprocess.TimeoutExpired as exc:
            raise VideoProcessingError("Video frame extraction timed out.") from exc
        if result.returncode:
            raise VideoProcessingError("Representative video frames could not be extracted.")
        files = sorted(Path(directory).glob("frame-*.jpg"))
        if not files:
            raise VideoProcessingError("Video contains no decodable frames.")
        # Frames are intentionally a uniform approximation. Their timestamps
        # remain traceable but are not presented as exact frame timestamps.
        return [
            (info.duration_seconds * index / len(files), path.read_bytes())
            for index, path in enumerate(files)
        ]

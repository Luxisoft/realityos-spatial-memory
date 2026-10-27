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


@dataclass(frozen=True)
class VideoSegment:
    """A bounded logical section of an original video kept in PostgreSQL."""

    index: int
    start_seconds: float
    duration_seconds: float


@dataclass(frozen=True)
class ExtractedFrame:
    """A representative image and its approximate place in the parent video."""

    index: int
    segment: VideoSegment
    timestamp_seconds: float
    bytes: bytes


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


def video_segments(info: VideoInfo, segment_seconds: int) -> list[VideoSegment]:
    """Partition arbitrary-length video without changing the source evidence."""

    if segment_seconds < 1:
        raise ValueError("segment_seconds must be positive.")
    segments: list[VideoSegment] = []
    start = 0.0
    index = 0
    while start < info.duration_seconds:
        duration = min(float(segment_seconds), info.duration_seconds - start)
        segments.append(
            VideoSegment(index=index, start_seconds=start, duration_seconds=duration)
        )
        start += duration
        index += 1
    return segments


def extract_representative_frames(
    video: bytes,
    info: VideoInfo,
    *,
    segment_seconds: int,
    frames_per_segment: int,
) -> list[ExtractedFrame]:
    """Sample each logical video segment and delete all transient files afterward.

    The original clip is never split or rewritten as source evidence. Temporary
    decoding is only used so FFmpeg can seek efficiently within a long upload.
    """

    if frames_per_segment < 1:
        raise ValueError("frames_per_segment must be positive.")
    segments = video_segments(info, segment_seconds)
    extracted: list[ExtractedFrame] = []
    with tempfile.TemporaryDirectory(prefix="realityos-video-") as directory:
        source = Path(directory) / "source-video"
        source.write_bytes(video)
        for segment in segments:
            pattern = str(Path(directory) / f"segment-{segment.index:04d}-frame-%03d.jpg")
            frame_rate = frames_per_segment / segment.duration_seconds
            try:
                result = subprocess.run(
                    [
                        "ffmpeg",
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-ss",
                        f"{segment.start_seconds:.3f}",
                        "-i",
                        str(source),
                        "-t",
                        f"{segment.duration_seconds:.3f}",
                        "-vf",
                        f"fps={frame_rate:.9f},scale='min(1280,iw)':-2",
                        "-frames:v",
                        str(frames_per_segment),
                        "-q:v",
                        "3",
                        pattern,
                    ],
                    capture_output=True,
                    check=False,
                    timeout=max(30, int(segment.duration_seconds * 2) + 10),
                )
            except FileNotFoundError as exc:
                raise VideoProcessingError(
                    "Video processing is unavailable: ffmpeg is not installed."
                ) from exc
            except subprocess.TimeoutExpired as exc:
                raise VideoProcessingError("Video frame extraction timed out.") from exc
            if result.returncode:
                raise VideoProcessingError("Representative video frames could not be extracted.")
            files = sorted(Path(directory).glob(f"segment-{segment.index:04d}-frame-*.jpg"))
            if not files:
                raise VideoProcessingError("Video contains no decodable frames.")
            for frame_number, path in enumerate(files):
                extracted.append(
                    ExtractedFrame(
                        index=len(extracted),
                        segment=segment,
                        # Frame timestamps remain deliberately approximate.
                        timestamp_seconds=(
                            segment.start_seconds
                            + segment.duration_seconds * frame_number / len(files)
                        ),
                        bytes=path.read_bytes(),
                    )
                )
    return extracted

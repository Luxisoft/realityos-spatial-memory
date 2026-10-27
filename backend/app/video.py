"""Bounded, traceable video probing and representative-frame extraction."""

from __future__ import annotations

import json
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


class VideoProcessingError(RuntimeError):
    """A safe error for an invalid or unavailable video-processing toolchain."""


@dataclass(frozen=True)
class VideoInfo:
    duration_seconds: float
    width: int | None
    height: int | None
    frame_rate: float | None = None
    frame_count: int | None = None


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


@dataclass(frozen=True)
class VideoClip:
    """A temporary MP4 interval sent to SAM; source evidence remains untouched."""

    segment: VideoSegment
    path: Path
    frame_count: int
    source_frame_offset: int
    frame_pts_seconds: tuple[float, ...]


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
                "format=duration:stream=width,height,avg_frame_rate,nb_frames",
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
    return _video_info_from_probe(result)


def probe_video_file(path: Path) -> VideoInfo:
    """Probe a scoped worker file without reading a whole large video into RAM."""

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "format=duration:stream=width,height,avg_frame_rate,nb_frames",
                "-of",
                "json",
                "-i",
                str(path),
            ],
            capture_output=True,
            check=False,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise VideoProcessingError("Video processing is unavailable: ffprobe is not installed.") from exc
    except subprocess.TimeoutExpired as exc:
        raise VideoProcessingError("Video inspection timed out.") from exc
    return _video_info_from_probe(result)


def _video_info_from_probe(result: subprocess.CompletedProcess[bytes]) -> VideoInfo:
    if result.returncode:
        raise VideoProcessingError("Invalid or unsupported video data.")
    try:
        payload = json.loads(result.stdout)
        duration = float(payload["format"]["duration"])
        stream = payload.get("streams", [{}])[0]
        width = int(stream["width"]) if stream.get("width") else None
        height = int(stream["height"]) if stream.get("height") else None
        frame_rate = _fraction_or_none(stream.get("avg_frame_rate"))
        frame_count = int(stream["nb_frames"]) if stream.get("nb_frames", "").isdigit() else None
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise VideoProcessingError("Video metadata could not be read.") from exc
    if duration <= 0:
        raise VideoProcessingError("Video must contain a positive duration.")
    return VideoInfo(
        duration_seconds=duration,
        width=width,
        height=height,
        frame_rate=frame_rate,
        frame_count=frame_count or (round(duration * frame_rate) if frame_rate else None),
    )


def _fraction_or_none(value: object) -> float | None:
    if not isinstance(value, str) or not value or value == "0/0":
        return None
    try:
        numerator, denominator = value.split("/", 1)
        result = float(numerator) / float(denominator)
    except (ValueError, ZeroDivisionError):
        return None
    return result if result > 0 else None


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


def _clip_frame_count(path: Path) -> int:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-count_frames",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=nb_read_frames",
                "-of",
                "default=nokey=1:noprint_wrappers=1",
                str(path),
            ],
            capture_output=True,
            check=False,
            timeout=60,
        )
        return int(result.stdout.strip()) if result.returncode == 0 else 0
    except (FileNotFoundError, ValueError, subprocess.TimeoutExpired):
        return 0


def _clip_frame_pts(path: Path) -> tuple[float, ...]:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_frames",
                "-show_entries",
                "frame=best_effort_timestamp_time",
                "-of",
                "csv=p=0",
                str(path),
            ],
            capture_output=True,
            check=False,
            timeout=120,
        )
        if result.returncode:
            return ()
        values: list[float] = []
        for line in result.stdout.decode(errors="replace").splitlines():
            try:
                values.append(float(line.strip().split(",", 1)[0]))
            except ValueError:
                continue
        return tuple(values)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ()


@contextmanager
def materialized_video_clips(
    source: Path, info: VideoInfo, *, segment_seconds: int
):
    """Generate bounded faststart MP4 clips and remove them after provider processing."""

    with tempfile.TemporaryDirectory(prefix="realityos-video-clips-") as directory:
        clips: list[VideoClip] = []
        offset = 0
        for segment in video_segments(info, segment_seconds):
            path = Path(directory) / f"segment-{segment.index:04d}.mp4"
            try:
                result = subprocess.run(
                    [
                        "ffmpeg",
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-ss",
                        f"{segment.start_seconds:.6f}",
                        "-i",
                        str(source),
                        "-t",
                        f"{segment.duration_seconds:.6f}",
                        "-map",
                        "0:v:0",
                        "-an",
                        "-c:v",
                        "libx264",
                        "-preset",
                        "veryfast",
                        "-crf",
                        "18",
                        "-movflags",
                        "+faststart",
                        "-y",
                        str(path),
                    ],
                    capture_output=True,
                    check=False,
                    timeout=max(60, int(segment.duration_seconds * 3) + 30),
                )
            except FileNotFoundError as exc:
                raise VideoProcessingError("Video processing is unavailable: ffmpeg is not installed.") from exc
            except subprocess.TimeoutExpired as exc:
                raise VideoProcessingError("Video clip creation timed out.") from exc
            if result.returncode or not path.exists():
                raise VideoProcessingError("Video clip creation failed.")
            count = _clip_frame_count(path)
            if count < 1:
                raise VideoProcessingError("Video clip has no decodable frames.")
            clips.append(
                VideoClip(
                    segment=segment,
                    path=path,
                    frame_count=count,
                    source_frame_offset=offset,
                    frame_pts_seconds=_clip_frame_pts(path),
                )
            )
            offset += count
        yield clips


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
    with tempfile.TemporaryDirectory(prefix="realityos-video-") as directory:
        source = Path(directory) / "source-video"
        source.write_bytes(video)
        return extract_representative_frames_from_file(
            source,
            info,
            segment_seconds=segment_seconds,
            frames_per_segment=frames_per_segment,
        )


def extract_representative_frames_from_file(
    source: Path,
    info: VideoInfo,
    *,
    segment_seconds: int,
    frames_per_segment: int,
) -> list[ExtractedFrame]:
    """Sample a worker-local source path while retaining only JPEG derivatives."""

    if frames_per_segment < 1:
        raise ValueError("frames_per_segment must be positive.")
    segments = video_segments(info, segment_seconds)
    extracted: list[ExtractedFrame] = []
    with tempfile.TemporaryDirectory(prefix="realityos-video-frames-") as directory:
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

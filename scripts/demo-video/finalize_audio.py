#!/usr/bin/env python3
"""Mix an existing video with an original music bed and master its audio.

The video stream is copied unchanged. Audio uses a measured two-pass loudnorm
process, while the music fades during the last four seconds of the delivery.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def run(command: list[str], timeout: float = 600) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command, check=False, capture_output=True, text=True, timeout=timeout
    )
    if result.returncode:
        raise RuntimeError(
            f"{Path(command[0]).name} exited {result.returncode}: "
            f"{result.stderr[-4000:]}"
        )
    return result


def probe(path: Path) -> dict[str, Any]:
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ]
    )
    return json.loads(result.stdout)


def measurement(log: str) -> dict[str, Any]:
    blocks = re.findall(r'\{\s*"input_i".*?\}', log, flags=re.DOTALL)
    if not blocks:
        raise RuntimeError("FFmpeg did not return loudness measurements.")
    values = json.loads(blocks[-1])
    for key in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset"):
        if not math.isfinite(float(values[key])):
            raise ValueError(f"Non-finite loudness measurement: {key}.")
    return values


def validate(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    if not math.isfinite(args.duration) or args.duration <= 0:
        raise ValueError("--duration must be a positive finite number of seconds.")
    for executable in ("ffmpeg", "ffprobe"):
        if not shutil.which(executable):
            raise ValueError(f"Required executable is unavailable: {executable}.")
    for path in (args.input, args.music):
        if not path.is_file():
            raise ValueError(f"Input file does not exist: {path}.")
    destinations = {args.output.resolve(), args.report.resolve()}
    if len(destinations) != 2:
        raise ValueError("--output and --report must be different files.")
    if destinations & {args.input.resolve(), args.music.resolve()}:
        raise ValueError("Output/report must not overwrite either input.")
    if args.output.suffix.lower() != ".mp4":
        raise ValueError("--output must have the .mp4 extension.")
    video, music = probe(args.input), probe(args.music)
    kinds = {stream.get("codec_type") for stream in video["streams"]}
    if not {"video", "audio"}.issubset(kinds):
        raise ValueError("Input video must contain both video and narration audio.")
    if not any(s.get("codec_type") == "audio" for s in music["streams"]):
        raise ValueError("Music file must contain an audio stream.")
    for label, metadata in (("Video", video), ("Music", music)):
        length = float(metadata["format"]["duration"])
        if not math.isfinite(length) or length + 0.075 < args.duration:
            raise ValueError(f"{label} is shorter than the requested duration.")
    return video, music


def master(args: argparse.Namespace) -> dict[str, Any]:
    source_probe, music_probe = validate(args)
    seconds = f"{args.duration:.6f}"
    fade_length = min(4.0, args.duration)
    fade_start = f"{args.duration - fade_length:.6f}"
    common_audio = (
        "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
        f"apad,atrim=duration={seconds},asetpts=PTS-STARTPTS"
    )
    mix = (
        f"[0:a:0]{common_audio}[voice];"
        f"[1:a:0]{common_audio},"
        f"afade=t=out:st={fade_start}:d={fade_length:.6f}[music];"
        "[voice][music]amix=inputs=2:duration=first:normalize=0[mixed];"
    )
    target = "loudnorm=I=-16:TP=-1.5:LRA=11"
    inputs = [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-nostats",
        "-y",
        "-i",
        str(args.input),
        "-i",
        str(args.music),
    ]
    first_command = inputs + [
        "-filter_complex",
        mix + f"[mixed]{target}:print_format=json[mastered]",
        "-map",
        "[mastered]",
        "-t",
        seconds,
        "-f",
        "null",
        "-",
    ]
    first = measurement(run(first_command).stderr)
    second_filter = (
        f"{target}:measured_I={first['input_i']}:"
        f"measured_TP={first['input_tp']}:measured_LRA={first['input_lra']}:"
        f"measured_thresh={first['input_thresh']}:offset={first['target_offset']}:"
        "linear=true:print_format=json"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=args.output.stem + "-", suffix=".mp4", dir=args.output.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        second_command = inputs + [
            "-filter_complex",
            mix + f"[mixed]{second_filter}[mastered]",
            "-map",
            "0:v:0",
            "-map",
            "[mastered]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-t",
            seconds,
            "-movflags",
            "+faststart",
            str(temporary),
        ]
        second = measurement(run(second_command).stderr)
        final_probe = probe(temporary)
        if abs(float(final_probe["format"]["duration"]) - args.duration) > 0.075:
            raise RuntimeError("Final duration differs from the requested duration.")
        os.replace(temporary, args.output)
    finally:
        temporary.unlink(missing_ok=True)
    # Record the deliverable path, not the transient atomic-output pathname.
    second_command[-1] = str(args.output)
    final_probe["format"]["filename"] = str(args.output)
    report = {
        "input": str(args.input),
        "music": str(args.music),
        "output": str(args.output),
        "duration_seconds": args.duration,
        "target": {"integrated_lufs": -16, "true_peak_dbtp": -1.5, "lra_lu": 11},
        "music_fade": {"start": float(fade_start), "duration": fade_length},
        "first_pass": first,
        "second_pass": second,
        "commands": [first_command, second_command],
        "source_probe": source_probe,
        "music_probe": music_probe,
        "output_probe": final_probe,
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--music", type=Path, required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = master(args)
    except (
        OSError,
        ValueError,
        KeyError,
        RuntimeError,
        subprocess.TimeoutExpired,
    ) as exc:
        print(f"Audio mastering failed: {exc}", file=sys.stderr)
        return 1
    print(
        f"Mastered {report['output']} ({args.duration:g}s); "
        f"loudness report: {args.report}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

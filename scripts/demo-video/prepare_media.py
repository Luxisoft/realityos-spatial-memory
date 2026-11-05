"""Normalize the owner's demo sources and reproduce real recording detail crops.

Run from any directory with Python 3, ffmpeg/ffprobe and ImageMagick installed.
Outputs stay in .runtime/video-production; original demo-video files are read-only.
Existing normalized copies are reused when their source/output hashes still match.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    "police_auth": "intro_auth_police.mp4",
    "social_auth": "intro_auth_social_media.mp4",
    "police_search": "search_with_photos_person_with_outstanding_arrest_warrants.mp4",
    "display_search": "search_with_meta_rayban_display_preview.mp4",
    "police_concept": "policial_case.mp4",
    "social_concept": "profile_found.mp4",
    "nursing_concept": "nurse_case.mp4",
    "memory_concept": "memory.mp4",
}
# Coordinates use the native resolution of the normalized source, not a preview.
DETAILS = {
    "police-response": ("police_search", 29, (26, 570, 674, 590)),
    "police-record": ("police_search", 48, (16, 920, 690, 600)),
    "social-profile": ("display_search", 32, (0, 116, 1080, 1480)),
    "social-profile-summary": ("display_search", 32, (0, 116, 1080, 1080)),
}
CUTS = {
    "police_auth": ([(3, 9), (11.5, 13), (15.8, 20.1)], 15),
    "social_auth": ([(7, 10), (16, 22.4)], 12),
    "police_search": ([(19, 57.7)], 40),
    "display_search": ([(3, 9.5), (14, 36.8)], 34),
    "police_concept": ([(0, 5.5)], None),
    "social_concept": ([(0, 3.6), (7, 9)], None),
    "nursing_concept": ([(2.8, 4.1)], None),
    "memory_concept": ([(0, 3.3), (13, 16.2)], None),
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def ffmpeg() -> list[str]:
    prefix = ["nice", "-n", "8"] if shutil.which("nice") else []
    return prefix + [
        "ffmpeg",
        "-v",
        "error",
        "-nostdin",
        "-threads",
        "1",
        "-filter_threads",
        "1",
    ]


def probe(path: Path) -> dict:
    result = json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=codec_type,width,height,nb_frames,avg_frame_rate:format=duration",
                "-of",
                "json",
                str(path),
            ]
        )
    )
    video = next(s for s in result["streams"] if s["codec_type"] == "video")
    if video["avg_frame_rate"] != "30/1":
        raise ValueError(f"Expected 30fps: {path}")
    if any(s["codec_type"] == "audio" for s in result["streams"]):
        raise ValueError(f"Unexpected source audio in normalized output: {path}")
    return {
        "duration": float(result["format"]["duration"]),
        "width": video["width"],
        "height": video["height"],
        "fps": video["avg_frame_rate"],
        "frames": int(video["nb_frames"]),
    }


def normalize(key: str, media: Path, previous: dict, force: bool) -> tuple[str, dict]:
    source = ROOT / "demo-video" / SOURCES[key]
    output = media / f"{key}.mp4"
    source_hash = digest(source)
    cached = previous.get(key, {})
    reusable = (
        not force
        and output.exists()
        and cached.get("sourceSha256") == source_hash
        and cached.get("sha256") == digest(output)
    )
    if not reusable:
        temporary = media / f"{key}.preparing.mp4"
        run(
            ffmpeg()
            + [
                "-i",
                str(source),
                "-map",
                "0:v:0",
                "-an",
                "-vf",
                "fps=30",
                "-c:v",
                "libx264",
                "-threads",
                "1",
                "-preset",
                "fast",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                "-y",
                str(temporary),
            ]
        )
        probe(temporary)
        temporary.replace(output)
    row = {
        "file": str(output),
        **probe(output),
        "sha256": digest(output),
        "source": str(source),
        "sourceSha256": source_hash,
        "audio": False,
        "provenance": (
            "Owner-created Higgsfield concept video"
            if key.endswith("concept")
            else "Owner-recorded Android app walkthrough"
        ),
    }
    print(
        f"{key}: {row['duration']:.3f}s ({'reused' if reusable else 'normalized'})",
        flush=True,
    )
    return key, row


def make_details(media: Path, assets: dict, image_command: str) -> dict:
    details = {}
    for name, (asset, seconds, (x, y, width, height)) in DETAILS.items():
        source = Path(assets[asset]["file"])
        frame = media / f"{name}-full.png"
        output = media / f"{name}.jpg"
        run(
            ffmpeg()
            + [
                "-ss",
                str(seconds),
                "-i",
                str(source),
                "-frames:v",
                "1",
                "-threads",
                "1",
                "-y",
                str(frame),
            ]
        )
        run(
            [
                image_command,
                str(frame),
                "-crop",
                f"{width}x{height}+{x}+{y}",
                "+repage",
                "-quality",
                "96",
                str(output),
            ]
        )
        details[name] = {
            "file": str(output),
            "sourceAsset": asset,
            "sourceSeconds": seconds,
            "crop": {"x": x, "y": y, "width": width, "height": height},
            "sha256": digest(output),
            "normalizedSourceSha256": assets[asset]["sha256"],
            "label": "Detail — actual app recording",
            "displayFit": "contain",
            "contentsAltered": False,
        }
    return details


def recommended_cuts() -> dict:
    result = {}
    for asset, (segments, target) in CUTS.items():
        duration = round(sum(end - start for start, end in segments), 3)
        result[asset] = {
            "segments": [
                {"asset": asset, "in": start, "out": end} for start, end in segments
            ],
            "contentSeconds": duration,
        }
        if target is not None:
            result[asset].update(
                targetSeconds=target, holdFinalSeconds=round(target - duration, 3)
            )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, choices=(1, 2), default=2)
    parser.add_argument(
        "--force", action="store_true", help="Rebuild existing normalized copies."
    )
    args = parser.parse_args()
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            parser.error(f"Required command is missing: {tool}")
    image_command = shutil.which("magick") or shutil.which("convert")
    if not image_command:
        parser.error(
            "ImageMagick (magick or convert) is required for the detail JPEG crops."
        )
    for filename in SOURCES.values():
        if not (ROOT / "demo-video" / filename).is_file():
            parser.error(f"Missing original: demo-video/{filename}")
    work = ROOT / ".runtime/video-production"
    media = work / "media"
    media.mkdir(parents=True, exist_ok=True)
    previous = read_json(media / "assets.json").get("assets", {})
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        assets = dict(
            pool.map(lambda key: normalize(key, media, previous, args.force), SOURCES)
        )
    write_json(media / "assets.json", {"assets": assets})
    report = read_json(work / "source-review.json")
    report.update(assets=assets, details=make_details(media, assets, image_command))
    report.setdefault("recommendedCuts", recommended_cuts())
    report.setdefault("review", {}).update(
        {
            "timebase": "All cuts refer to normalized 30fps copies; outpoints are exclusive.",
            "normalization": {
                "video": "H264 libx264",
                "crf": 18,
                "preset": "fast",
                "fps": 30,
                "audioRemoved": True,
                "nativeDimensionsPreserved": True,
                "maximumParallelJobs": args.jobs,
                "encoderThreadsPerJob": 1,
            },
            "editorialNotes": [
                "Keep the Police response uncertainty visible; it does not confirm a photo match.",
                "The Meta Display recording is explicitly a simulated Android preview.",
                "Concept clips illustrate possible uses; they are not implemented-product evidence.",
                "Review cut positions again if original recordings are replaced.",
            ],
        }
    )
    write_json(work / "source-review.json", report)
    print(f"Prepared {len(assets)} sources and {len(DETAILS)} details in {media}")


if __name__ == "__main__":
    main()

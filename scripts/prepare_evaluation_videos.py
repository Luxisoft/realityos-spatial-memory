"""Prepare complete licensed actions for the independent video acceptance suite.

Reference questions are deliberately kept in a separate evaluation manifest.
Existing photographs and the previous release's video bytes are never rewritten.
"""

import argparse
import concurrent.futures
import hashlib
import json
import subprocess
from fractions import Fraction
from pathlib import Path

import numpy as np
from prepare_real_scenes import download, probe

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "simulator/real-scenes"
CACHE = ROOT / ".runtime/stock-recordings"


def prepare(item):
    if item["kind"] != "video":
        raise ValueError("This release replaces only videos")
    stem = f"{item['group']}-{item['id']}"
    raw = CACHE / f"{item['id']}.mp4"
    target = BASE / "assets" / f"{stem}.mp4"
    url = item.get("download")
    if not raw.exists():
        candidates = (
            [url]
            if url
            else [
                f"https://videos.pexels.com/video-files/{item['id']}/{item['id']}-hd_{size}_{fps}fps.mp4"
                for size in (
                    "1280_720",
                    "1366_720",
                    "720_1280",
                    "720_1366",
                    "1920_1080",
                    "1080_1920",
                )
                for fps in (25, 30, 24, 50, 60)
            ]
        )
        for url in candidates:
            if download(url, raw):
                raw.with_suffix(".url").write_text(url)
                break
        else:
            raise RuntimeError(f"No download found for {item['source']}")
    elif url is None and raw.with_suffix(".url").exists():
        url = raw.with_suffix(".url").read_text()
    previous = BASE / "video-candidate-manifest.json"
    if previous.exists() and target.exists():
        cached = next(
            (
                row
                for row in json.loads(previous.read_text())["items"]
                if row["id"] == item["id"] and row["group"] == item["group"]
            ),
            None,
        )
        if (
            cached
            and all(cached.get(key) == value for key, value in item.items())
            and hashlib.sha256(raw.read_bytes()).hexdigest()
            == cached.get("source_sha256")
            and hashlib.sha256(target.read_bytes()).hexdigest() == cached["sha256"]
        ):
            print(f"Reused verified recording {stem}", flush=True)
            return cached
    original = probe(raw)
    stream = original["streams"][0]
    duration = float(original["format"]["duration"])
    if duration <= 0 or min(stream["width"], stream["height"]) < 720:
        raise RuntimeError(f"A decodable, native HD recording is required: {stem}")
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(raw),
            "-an",
            "-vf",
            "scale='if(gte(iw,ih),-2,min(iw,1080))':'if(gte(iw,ih),min(ih,1080),-2)'",
            "-c:v",
            "libx264",
            "-threads",
            "2",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(target),
        ],
        check=True,
    )
    rendered = probe(target)
    stream = rendered["streams"][0]
    if abs(float(rendered["format"]["duration"]) - duration) > 0.15:
        raise RuntimeError(f"Normalization changed the full action duration: {stem}")
    sample = subprocess.check_output(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(target),
            "-vf",
            "fps=2,scale=96:96",
            "-pix_fmt",
            "gray",
            "-f",
            "rawvideo",
            "-",
        ]
    )
    frames = np.frombuffer(sample, dtype=np.uint8).reshape(-1, 96, 96).astype(float)
    differences = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2))
    # Pauses can contain the strongest evidence. Motion is diagnostic; usefulness
    # is accepted separately through pre-annotated queries and visual review.
    if len(frames) < 2 or not np.any(differences > 0.35):
        raise RuntimeError(f"No visible action in recording: {stem}")
    result = {
        **item,
        "path": target.relative_to(ROOT).as_posix(),
        "source_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
        "width": stream["width"],
        "height": stream["height"],
        "fps": float(Fraction(stream["avg_frame_rate"])),
        "frames": int(stream["nb_frames"]),
        "duration": float(rendered["format"]["duration"]),
        "source_duration": duration,
        "complete_recording": True,
        "mean_frame_change": round(float(differences.mean()), 3),
        "changing_sample_ratio": round(float((differences > 0.35).mean()), 3),
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "bytes": target.stat().st_size,
    }
    if url:
        result["download"] = url
    print(f"Prepared complete action {stem}: {duration:g} seconds", flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=BASE / "video-candidates.json")
    parser.add_argument(
        "--manifest", type=Path, default=BASE / "video-candidate-manifest.json"
    )
    args = parser.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    (BASE / "assets").mkdir(parents=True, exist_ok=True)
    catalog = json.loads(args.catalog.read_text())
    completed, errors = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(prepare, item): item for item in catalog["items"]}
        for future in concurrent.futures.as_completed(futures):
            try:
                completed.append(future.result())
            except Exception as error:  # noqa: BLE001 - report every failed candidate, then fail the batch
                errors.append(
                    {"source": futures[future]["source"], "error": str(error)}
                )
    args.manifest.write_text(
        json.dumps(
            {
                "notice": catalog["notice"],
                "items": sorted(completed, key=lambda i: (i["group"], i["id"])),
                "errors": errors,
            },
            indent=2,
        )
        + "\n"
    )
    if errors:
        raise SystemExit(
            f"{len(errors)} recordings need replacement; inspect the manifest"
        )


if __name__ == "__main__":
    main()

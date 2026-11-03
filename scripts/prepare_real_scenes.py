"""Download, normalize and validate licensed recordings for fictional demo workspaces.

No credentials or customer media. Sources and licenses are in the public catalog;
the output manifest includes hashes, dimensions, frame counts and temporal change.
"""

import concurrent.futures
import hashlib
import json
import subprocess
from pathlib import Path

import httpx
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "simulator/real-scenes"
CACHE = ROOT / ".runtime/stock-recordings"


def probe(path):
    return json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(path),
            ]
        )
    )


def download(url, path):
    with httpx.stream("GET", url, follow_redirects=True, timeout=45) as response:
        if response.status_code in {403, 404}:
            return False
        response.raise_for_status()
        with path.open("wb") as output:
            for block in response.iter_bytes():
                output.write(block)
    return True


def prepare(item):
    stem = f"{item['group']}-{item['id']}"
    target = BASE / "assets" / (stem + (".jpg" if item["kind"] == "image" else ".mp4"))
    raw = CACHE / (str(item["id"]) + (".jpg" if item["kind"] == "image" else ".mp4"))
    url = item.get("download")
    if not raw.exists():
        if item["kind"] == "video":
            candidates = (
                [item["download"]]
                if item.get("download")
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
                    for fps in (25, 30, 24)
                ]
            )
            for url in candidates:
                if download(url, raw):
                    break
            else:
                raise RuntimeError(f"No download found for {item['source']}")
        elif not download(url, raw):
            raise RuntimeError(f"Unavailable photo: {item['source']}")
    result = {
        **item,
        "path": target.relative_to(ROOT).as_posix(),
        "source_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
    }
    if url:
        result["download"] = url
    if item["kind"] == "image":
        with Image.open(raw) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.thumbnail((1600, 1600))
            image.save(target, "JPEG", quality=91)
            result.update(width=image.width, height=image.height)
    else:
        data = probe(raw)
        duration = float(data["format"]["duration"])
        if duration < 10:
            raise RuntimeError(
                f"Recording shorter than 10 seconds: {stem} ({duration})"
            )
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-i",
                str(raw),
                "-t",
                "15",
                "-an",
                "-vf",
                "scale='if(gte(iw,ih),-2,720)':'if(gte(iw,ih),720,-2)',fps=24",
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
        # A static still or a duplicate-frame slideshow fails even with a valid MP4 header.
        if (
            len(frames) < 20
            or np.count_nonzero(differences > 0.35) < len(differences) * 0.7
        ):
            raise RuntimeError(f"Insufficient continuous movement: {stem}")
        result.update(
            width=stream["width"],
            height=stream["height"],
            fps=24,
            frames=int(stream["nb_frames"]),
            duration=float(rendered["format"]["duration"]),
            mean_frame_change=round(float(differences.mean()), 3),
            changing_sample_ratio=round(float((differences > 0.35).mean()), 3),
        )
    result.update(
        sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        bytes=target.stat().st_size,
    )
    print(f"Verified {stem}: {result['bytes']} bytes", flush=True)
    return result


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    (BASE / "assets").mkdir(exist_ok=True)
    catalog = json.loads((BASE / "catalog.json").read_text())
    if catalog.get("video_release"):
        raise ValueError(
            "Use prepare_evaluation_videos.py; preserve the accepted photos and full recordings"
        )
    completed, errors = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(prepare, item): item for item in catalog["items"]}
        for future in concurrent.futures.as_completed(futures):
            try:
                completed.append(future.result())
            except Exception as error:  # noqa: BLE001 - record every failed asset, fail the overall build
                errors.append(
                    {"source": futures[future]["source"], "error": str(error)}
                )
                print(f"FAILED {futures[future]['id']}: {error}", flush=True)
    completed.sort(key=lambda item: (item["group"], item["kind"], item["id"]))
    (BASE / "manifest.json").write_text(
        json.dumps(
            {"notice": catalog["notice"], "items": completed, "errors": errors},
            indent=2,
        )
        + "\n"
    )
    if errors:
        raise SystemExit(f"{len(errors)} resources need replacement; see manifest")
    for group in {item["group"] for item in completed}:
        assert (
            sum(i["group"] == group and i["kind"] == "image" for i in completed) >= 12
        )
        assert sum(i["group"] == group and i["kind"] == "video" for i in completed) >= 4


if __name__ == "__main__":
    main()

"""Replace 5 photos per directory profile with group takes (owner + companions).

Companions are generated identities WITHOUT profiles: they exist only as
reference portraits under ``simulator/social-directory/companions/`` and as
faces inside owners' photos. Each companion appears in several owners'
photos so cross-profile face search can be tested (find a face inside
third-party profiles).

Replaced slots per profile: photo-02, photo-04, photo-06, photo-08, photo-10
(same scene briefs, group framing). Files are overwritten in place and
``muse/<slug>/manifest.json`` records the replacement. Refuses to run unless
``META_MODE=live`` and ``muse-image-1.0`` is listed. Resumable.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _extra in (ROOT / "backend", ROOT / "scripts"):
    if _extra.is_dir() and str(_extra) not in sys.path:
        sys.path.append(str(_extra))

from PIL import Image  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.faces import build_face_engine, cosine_similarity  # noqa: E402
from generate_directory_photos import (  # noqa: E402
    MODEL,
    CallBudget,
    MuseImage,
    contact_sheet,
    dhash,
    hamming,
    reference_data_url,
    scene_body,
)
from seed_social_directory import PROFILE_ROWS  # noqa: E402

GROUP_SLOTS = (1, 3, 5, 7, 9)  # 0-based scene indexes -> photo-02..10
OWNER_THRESHOLD = 0.5
COMPANION_THRESHOLD = 0.45  # companions render smaller inside group takes
MIN_DHASH_DISTANCE = 10
MAX_CALLS = 160

# Fixed companion identities: (slug, portrait prompt). Diverse on purpose.
COMPANIONS = (
    (
        "compa-lucia",
        "Photorealistic portrait of an original woman in her early 30s, warm "
        "brown skin, long black braided hair, soft smile, small gold hoops, "
        "plain light-gray studio backdrop, facing the camera, head and "
        "shoulders. Natural amateur photo feel, no watermark, no text.",
    ),
    (
        "compa-marco",
        "Photorealistic portrait of an original man in his late 20s, light "
        "olive skin, short curly dark hair, trimmed beard, friendly expression, "
        "plain light-gray studio backdrop, facing the camera, head and "
        "shoulders. Natural amateur photo feel, no watermark, no text.",
    ),
    (
        "compa-ana",
        "Photorealistic portrait of an original woman in her mid 40s, fair "
        "skin with freckles, auburn hair in a low bun, subtle smile, plain "
        "light-gray studio backdrop, facing the camera, head and shoulders. "
        "Natural amateur photo feel, no watermark, no text.",
    ),
    (
        "compa-david",
        "Photorealistic portrait of an original young man around 22, deep "
        "brown skin, short faded haircut, clean shaven, relaxed smile, plain "
        "light-gray studio backdrop, facing the camera, head and shoulders. "
        "Natural amateur photo feel, no watermark, no text.",
    ),
    (
        "compa-sofia",
        "Photorealistic portrait of an original woman in her late 20s, "
        "tan skin, shoulder-length wavy chestnut hair, nose stud, cheerful "
        "expression, plain light-gray studio backdrop, facing the camera, "
        "head and shoulders. Natural amateur photo feel, no watermark, "
        "no text.",
    ),
    (
        "compa-jorge",
        "Photorealistic portrait of an original man in his mid 30s, medium "
        "brown skin, straight black hair with a side part, mustache, calm "
        "expression, plain light-gray studio backdrop, facing the camera, "
        "head and shoulders. Natural amateur photo feel, no watermark, "
        "no text.",
    ),
    (
        "compa-priya",
        "Photorealistic portrait of an original woman around 26, medium "
        "olive-brown skin, long straight black hair, small bindi, gentle "
        "smile, plain light-gray studio backdrop, facing the camera, head "
        "and shoulders. Natural amateur photo feel, no watermark, no text.",
    ),
    (
        "compa-tomas",
        "Photorealistic portrait of an original teenage boy around 17, light "
        "skin, messy blond hair, braces-free open smile, plain light-gray "
        "studio backdrop, facing the camera, head and shoulders. Natural "
        "amateur photo feel, no watermark, no text.",
    ),
    (
        "compa-rosa",
        "Photorealistic portrait of an original older woman around 60, warm "
        "tan skin with wrinkles, silver hair in a braid, kind eyes, plain "
        "light-gray studio backdrop, facing the camera, head and shoulders. "
        "Natural amateur photo feel, no watermark, no text.",
    ),
    (
        "compa-ivan",
        "Photorealistic portrait of an original man around 40, pale skin, "
        "bald with a short graying beard, glasses, neutral friendly "
        "expression, plain light-gray studio backdrop, facing the camera, "
        "head and shoulders. Natural amateur photo feel, no watermark, "
        "no text.",
    ),
)


def companions_for(profile_index: int, group_position: int) -> list[int]:
    """Deterministic companions: 2 on even positions, 1 on odd ones."""

    first = (profile_index + group_position) % len(COMPANIONS)
    if group_position % 2:
        return [first]
    second = (profile_index * 3 + group_position * 2 + 1) % len(COMPANIONS)
    return [first, second] if second != first else [first]


def group_prompt(
    scene_text: str, count: int, retry_variant: int = 0,
) -> str:
    refs = "the first reference image" + (
        "".join(
            f" and the person from reference image {position}"
            for position in range(2, count + 1)
        )
    )
    prompt = (
        "Photorealistic candid amateur group photo of the SAME people from "
        f"{refs}: identical faces, same ages, same facial features, skin "
        "tones and hairstyles as their references. "
        f"They are together: {scene_text} "
        "Group framing with everyone clearly visible, every face unobstructed "
        "and in focus, natural poses (arms around shoulders where natural). "
        "The background must be free of other recognizable people: empty "
        "street, blurred faceless shapes at most. "
        "Natural imperfections, subtle grain, authentic snapshot feel, no "
        "watermark, no text, no logos."
    )
    if retry_variant == 1:
        prompt += " Choose a clearly different camera angle and arrangement."
    elif retry_variant >= 2:
        prompt += (
            " Completely empty background: absolutely no other people, "
            "no faces besides the group, quiet location."
        )
    return prompt


def best_matches(
    anchors: list[bytes], faces: list, threshold: float
) -> tuple[bool, list[float]]:
    """Greedily match each anchor to its best remaining face above threshold."""

    remaining = list(range(len(faces)))
    scores: list[float] = []
    for anchor in anchors:
        scored = sorted(
            ((cosine_similarity(anchor, faces[i].embedding), i) for i in remaining),
            reverse=True,
        )
        if not scored or scored[0][0] < threshold:
            return False, scores
        scores.append(round(scored[0][0], 4))
        remaining.remove(scored[0][1])
    return True, scores


def ensure_companions(
    client: MuseImage, engine, companions_root: Path, budget: CallBudget
) -> dict[str, bytes]:
    """Generate one reference portrait per companion; return slug -> embedding."""

    companions_root.mkdir(parents=True, exist_ok=True)
    manifest_path = companions_root / "manifest.json"
    manifest: dict = (
        json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    )
    portraits = manifest.setdefault("portraits", {})
    embeddings: dict[str, bytes] = {}
    for slug, prompt in COMPANIONS:
        path = companions_root / f"{slug}.jpg"
        entry = portraits.get(slug, {})
        if entry.get("status") == "done" and path.exists():
            faces = engine.detect_faces(path.read_bytes())
            embeddings[slug] = max(faces, key=lambda face: face.quality).embedding
            continue
        attempts = int(entry.get("attempts", 0))
        while attempts <= 1:
            budget.spend()
            attempts += 1
            try:
                response_id, raw, usage = MuseImage.extract_image(
                    client.create({"model": MODEL, "input": prompt})
                )
                faces = engine.detect_faces(raw)
                if len(faces) != 1:
                    raise RuntimeError(f"expected 1 face, detected {len(faces)}.")
            except Exception as exc:
                print(f"[{slug}] attempt {attempts} rejected: {exc}")
                time.sleep(2)
                continue
            path.write_bytes(raw)
            embeddings[slug] = faces[0].embedding
            portraits[slug] = {
                "response_id": response_id,
                "prompt": prompt,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "usage": usage,
                "attempts": attempts,
                "status": "done",
            }
            manifest_path.write_text(json.dumps(manifest, indent=2))
            print(f"[{slug}] portrait ready")
            time.sleep(2)
            break
        else:
            raise RuntimeError(f"[{slug}] portrait failed.")
    return embeddings


def generate_profile_groups(
    client: MuseImage,
    engine,
    threshold_owner: float,
    profile_index: int,
    row: tuple,
    source_root: Path,
    muse_root: Path,
    companions_root: Path,
    companion_embeddings: dict[str, bytes],
    budget: CallBudget,
    known_hashes: set[str],
) -> None:
    slug, _name, profession, region, _gender, _tags = row
    source = source_root / f"{slug}.png"
    directory = muse_root / slug
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    scenes = manifest["scenes"]

    owner_faces = engine.detect_faces(source.read_bytes())
    owner_anchor = max(owner_faces, key=lambda face: face.quality).embedding
    owner_ref = reference_data_url(source)

    sibling_hashes = {
        entry["dhash"]
        for key, entry in scenes.items()
        if entry.get("status") in {"done", "group-done"}
        and isinstance(entry.get("dhash"), int)
    }
    for position, scene_index in enumerate(GROUP_SLOTS):
        key = f"photo-{scene_index + 1:02d}"
        entry = scenes.get(key, {})
        if entry.get("status") == "group-done" and (directory / f"{key}.jpg").exists():
            continue
        companion_ids = companions_for(profile_index, position)
        slugs = [COMPANIONS[cid][0] for cid in companion_ids]
        scene_name, body = scene_body(profile_index, scene_index, profession, region)
        content = [
            {"type": "input_image", "image_url": owner_ref},
        ] + [
            {
                "type": "input_image",
                "image_url": reference_data_url(companions_root / f"{comp}.jpg"),
            }
            for comp in slugs
        ]
        attempts = int(entry.get("group_attempts", 0))
        while attempts <= 2:
            prompt = group_prompt(body, 1 + len(slugs), retry_variant=attempts)
            content_text = {"type": "input_text", "text": prompt}
            budget.spend()
            attempts += 1
            try:
                payload = {
                    "model": MODEL,
                    "input": [{"role": "user", "content": [content_text, *content]}],
                }
                response_id, raw, usage = MuseImage.extract_image(client.create(payload))
                with Image.open(io.BytesIO(raw)) as picture:
                    width, height = picture.size
                    picture.load()
                digest = hashlib.sha256(raw).hexdigest()
                if digest in known_hashes:
                    raise RuntimeError("duplicate bytes already generated.")
                faces = engine.detect_faces(raw)
                if len(faces) != 1 + len(slugs):
                    raise RuntimeError(
                        f"expected {1 + len(slugs)} faces, detected {len(faces)}."
                    )
                ok_owner, owner_scores = best_matches(
                    [owner_anchor], faces, threshold_owner
                )
                if not ok_owner:
                    raise RuntimeError("owner identity not present.")
                ok_comp, comp_scores = best_matches(
                    [companion_embeddings[comp] for comp in slugs],
                    faces,
                    COMPANION_THRESHOLD,
                )
                if not ok_comp:
                    raise RuntimeError("a companion identity drifted.")
                digest_dhash = dhash(raw)
                others = sibling_hashes - {entry.get("dhash")}
                nearest = (
                    min(hamming(digest_dhash, other) for other in others)
                    if others
                    else 64
                )
                if nearest < MIN_DHASH_DISTANCE:
                    raise RuntimeError(f"too similar to a sibling (dhash {nearest}).")
            except Exception as exc:
                print(f"[{slug}] {key} group attempt {attempts} rejected: {exc}")
                time.sleep(2)
                continue
            (directory / f"{key}.jpg").write_bytes(raw)
            known_hashes.add(digest)
            sibling_hashes.discard(entry.get("dhash"))
            sibling_hashes.add(digest_dhash)
            entry.update(
                {
                    "previous_sha256": entry.get("sha256"),
                    "response_id": response_id,
                    "prompt": prompt,
                    "sha256": digest,
                    "bytes": len(raw),
                    "width": width,
                    "height": height,
                    "faces": len(faces),
                    "similarity": owner_scores[0],
                    "companion_similarities": dict(zip(slugs, comp_scores)),
                    "companions": slugs,
                    "dhash": digest_dhash,
                    "usage": usage,
                    "group_attempts": attempts,
                    "status": "group-done",
                    "generated_at": datetime.now(UTC).isoformat(),
                }
            )
            manifest_path.write_text(json.dumps(manifest, indent=2))
            print(f"[{slug}] {key} group done owner={owner_scores[0]} comp={comp_scores}")
            time.sleep(2)
            break
        else:
            entry["group_attempts"] = attempts
            manifest_path.write_text(json.dumps(manifest, indent=2))
            raise RuntimeError(f"[{slug}] {key} group failed.")
    contact_sheet(directory, slug)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", default=str(ROOT / "simulator/social-directory/source"))
    parser.add_argument("--muse-root", default=str(ROOT / "simulator/social-directory/muse"))
    parser.add_argument(
        "--companions-root",
        default=str(ROOT / "simulator/social-directory/companions"),
    )
    parser.add_argument("--slugs", default="", help="Comma-separated subset.")
    parser.add_argument("--companions-only", action="store_true")
    parser.add_argument("--max-calls", type=int, default=MAX_CALLS)
    args = parser.parse_args()
    source_root = Path(args.source_root)
    muse_root = Path(args.muse_root)
    companions_root = Path(args.companions_root)

    wanted = {slug.strip() for slug in args.slugs.split(",") if slug.strip()}
    rows = [
        (index, row)
        for index, row in enumerate(PROFILE_ROWS)
        if not wanted or row[0] in wanted
    ]
    if not rows and not args.companions_only:
        raise SystemExit("No profiles selected.")
    client = MuseImage()
    engine = build_face_engine(client.settings)
    if engine.simulated:
        raise RuntimeError("Refusing to generate: face engine is simulated.")
    budget = CallBudget(companions_root / "calls.json", limit=args.max_calls)

    companion_embeddings = ensure_companions(client, engine, companions_root, budget)
    print(f"companions ready: {len(companion_embeddings)}")
    if args.companions_only:
        print(f"done: {budget.used} Muse calls spent")
        return

    known_hashes: set[str] = set()
    for slug_dir in muse_root.iterdir():
        manifest_path = slug_dir / "manifest.json"
        if not manifest_path.is_file():
            continue
        try:
            scenes = json.loads(manifest_path.read_text()).get("scenes", {})
        except ValueError:
            continue
        for entry in scenes.values():
            if entry.get("sha256"):
                known_hashes.add(entry["sha256"])
    for profile_index, row in rows:
        generate_profile_groups(
            client,
            engine,
            client.settings.face_match_threshold,
            profile_index,
            row,
            source_root,
            muse_root,
            companions_root,
            companion_embeddings,
            budget,
            known_hashes,
        )
    print(f"done: {budget.used} Muse calls spent")


if __name__ == "__main__":
    main()

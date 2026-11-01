"""Generate the Mechanic Workshop group content: takes of one same shop.

One Muse conversation anchors the shop identity; 15 forked turns render
different takes and perspectives (9 daylight, 6 night) so group members can
demo cross-shift object search. No face validation: takes focus on tools and
bays, with workers incidental at most.

Output goes to ``simulator/social-directory/workshop/`` with a manifest the
publisher consumes (owner, shift, caption, visible tools). Refuses to run
unless ``META_MODE=live`` and ``muse-image-1.0`` is listed. Resumable.
"""

from __future__ import annotations

import argparse
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

from generate_directory_photos import (  # noqa: E402
    MODEL,
    CallBudget,
    MuseImage,
    dhash,
    hamming,
)

SHOP_IDENTITY = (
    "the same neighborhood mechanic workshop from the previous image: "
    "'Rivera Auto Repair' in Cali, two hydraulic lifts, red rolling tool "
    "chests, a long workbench wall with hanging hand tools, parts shelves, a "
    "tire rack, a small diagnostics corner with a monitor, oil-stained "
    "concrete floor, corrugated metal and painted block walls, one big rolling "
    "door. Keep the layout, wall color, chests and lifts identical."
)
SUFFIX = (
    " Photorealistic amateur smartphone snapshot, natural imperfections, "
    "subtle grain, no watermark, no text overlays, no logos besides the shop "
    "sign. Tools and equipment clearly visible."
)

# (file, shift, owner_slug, take, tools, body)
BRIEFS = (
    ("day-01", "day", "__jose__", "lift bay wide",
     "hydraulic lift, sedan, jack stands, oil drain pan",
     "wide take of the main lift bay with a silver sedan raised on the lift, "
     "jack stands and an oil drain pan underneath, daylight flooding through "
     "the open rolling door"),
    ("day-02", "day", "diego-mendoza", "diagnostics corner",
     "diagnostic tablet, OBD scanner, multimeter, laptop cart",
     "close take of the diagnostics corner: a tablet on a rolling cart plugged "
     "into a car, OBD scanner and multimeter on the cart, morning daylight"),
    ("day-03", "day", "martin-quintero", "workbench tools wall",
     "wrench set, socket set, hammers, screwdrivers",
     "straight-on take of the workbench wall with hanging wrenches, socket "
     "rails, hammers and screwdrivers above a cluttered bench, bright daylight"),
    ("day-04", "day", "__jose__", "engine bay service",
     "engine bay, socket wrench, oil filter, funnel",
     "over-the-fender take of an open engine bay mid-service, socket wrench "
     "resting on the frame, new oil filter and funnel beside it, daylight"),
    ("day-05", "day", "diego-mendoza", "tire station",
     "tire changer, wheel balancer, lug wrench, stacked tires",
     "take of the tire station with the changer holding a wheel, balancer "
     "behind, lug wrench on a stool, stacked tires along the wall, daylight"),
    ("day-06", "day", "martin-quintero", "welding corner",
     "welder, angle grinder, clamps, steel stock",
     "take of the fabrication corner with the MIG welder, angle grinder on a "
     "stand, clamped steel pieces, sparks-free idle moment, daylight"),
    ("day-07", "day", "__jose__", "parts shelves aisle",
     "brake pads, filters, belts, bottled oil",
     "down-the-aisle take of the parts shelves stocked with brake pad boxes, "
     "filters, belts and oil bottles, rolling door light from behind"),
    ("day-08", "day", "diego-mendoza", "bench vise close-up",
     "bench vise, caliper, wire strippers, soldering iron",
     "close-up take of the bench vise holding a small bracket, digital caliper, "
     "wire strippers and soldering iron around it, window daylight"),
    ("day-09", "day", "martin-quintero", "second lift brakes",
     "lift, brake discs, impact drill, torque wrench",
     "take of the second lift with a pickup truck, fresh brake discs on a tray, "
     "impact drill and torque wrench on the lift arm, afternoon daylight"),
    ("night-01", "night", "kwame-mensah", "receiving inventory",
     "parts boxes, clipboard, barcode labels, hand truck",
     "take of the receiving corner at night with stacked parts boxes, a "
     "clipboard and hand truck, harsh fluorescent ceiling light, dark windows"),
    ("night-02", "night", "omar-benali", "electrical bench",
     "battery charger, test lamp, fuse kit, wiring spools",
     "take of the electrical bench at night: battery on charger, test lamp "
     "glowing, fuse kit open, wiring spools, warm work-lamp pools of light"),
    ("night-03", "night", "kwame-mensah", "tool chest audit",
     "tool chest drawers, socket rails, labeled bins",
     "take of the open red tool chest at night with labeled drawers pulled out, "
     "socket rails and bins mid-audit, overhead fluorescents"),
    ("night-04", "night", "omar-benali", "under-dash wiring",
     "headlamp, zip ties, crimping tool, wiring loom",
     "take inside a car footwell at night: headlamp beam on the wiring loom, "
     "crimping tool and zip ties beside it, dark shop behind"),
    ("night-05", "night", "kwame-mensah", "tire rack count",
     "tire rack, chalk marks, pressure gauge",
     "take of the tire rack at night with chalk marks on sidewalls, pressure "
     "gauge hanging nearby, single fluorescent tube above"),
    ("night-06", "night", "omar-benali", "closed shop overview",
     "lifts lowered, covered engine, floor jack, night shadows",
     "wide take of the quiet shop at night: lifts lowered, a covered engine on "
     "a stand, floor jack parked, long shadows, rolling door closed"),
)

MIN_DHASH_DISTANCE = 8
MAX_CALLS = 40


def scene_prompt(brief_index: int, retry_variant: int = 0) -> tuple[dict, str]:
    file, shift, owner, take, tools, body = BRIEFS[brief_index]
    if retry_variant:
        body += " Choose a clearly different camera angle and framing."
    prompt = (
        f"Photorealistic candid photo of {SHOP_IDENTITY} {body}."
        + SUFFIX
    )
    caption = (
        f"Mechanic Workshop · {take} · {shift} shift · visible: {tools}"
    )
    meta = {
        "file": file,
        "shift": shift,
        "owner": owner,
        "take": take,
        "tools": tools,
        "caption": caption,
    }
    return meta, prompt


def contact_sheet(directory: Path) -> None:
    thumbs: list[Image.Image] = []
    for brief in BRIEFS:
        path = directory / f"{brief[0]}.jpg"
        with Image.open(path) as picture:
            thumbs.append(picture.convert("RGB").resize((256, 192), Image.Resampling.LANCZOS))
    sheet = Image.new("RGB", (256 * 5, 192 * 3), "white")
    for position, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((position % 5) * 256, (position // 5) * 192))
    sheet.save(directory / "contact-sheet.jpg", quality=85, optimize=True)
    print("workshop contact sheet ready")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        default=str(ROOT / "simulator/social-directory/workshop"),
    )
    args = parser.parse_args()
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    client = MuseImage()
    budget = CallBudget(output_root / "calls.json", limit=MAX_CALLS)
    manifest_path = output_root / "manifest.json"
    manifest: dict = (
        json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    )
    scenes = manifest.setdefault("scenes", {})

    anchor_response_id = manifest.get("anchor_response_id")
    if not anchor_response_id or not (output_root / "anchor.jpg").exists():
        budget.spend()
        payload = {
            "model": MODEL,
            "input": (
                "Photorealistic wide establishing photo of a small neighborhood "
                "mechanic workshop interior, 'Rivera Auto Repair' painted sign on "
                "the back wall: two hydraulic lifts, red rolling tool chests, a "
                "long workbench wall with hanging hand tools, parts shelves, a "
                "tire rack, a small diagnostics corner with a monitor, "
                "oil-stained concrete floor, corrugated metal and painted block "
                "walls, one big open rolling door with daylight. Empty shop, no "
                "people, no vehicles on the lifts. This frame fixes the shop "
                "identity for the series." + SUFFIX
            ),
        }
        response_id, raw, usage = MuseImage.extract_image(client.create(payload))
        (output_root / "anchor.jpg").write_bytes(raw)
        manifest["anchor_response_id"] = response_id
        manifest["anchor_usage"] = usage
        manifest_path.write_text(json.dumps(manifest, indent=2))
        anchor_response_id = response_id
        print(f"anchor ready ({response_id})")
        time.sleep(2)
    else:
        print(f"reusing anchor {anchor_response_id}")

    known_hashes = {
        entry["sha256"] for entry in scenes.values() if entry.get("status") == "done"
    }
    sibling_hashes = {
        entry["dhash"]
        for entry in scenes.values()
        if entry.get("status") == "done" and isinstance(entry.get("dhash"), int)
    }
    for brief_index in range(len(BRIEFS)):
        meta, _ = scene_prompt(brief_index)
        key = meta["file"]
        entry = scenes.get(key, {})
        if entry.get("status") == "done" and (output_root / f"{key}.jpg").exists():
            continue
        attempts = int(entry.get("attempts", 0))
        while attempts <= 1:
            _meta, prompt = scene_prompt(brief_index, retry_variant=attempts)
            budget.spend()
            attempts += 1
            try:
                payload = {
                    "model": MODEL,
                    "previous_response_id": anchor_response_id,
                    "input": prompt,
                }
                response_id, raw, usage = MuseImage.extract_image(client.create(payload))
                with Image.open(io.BytesIO(raw)) as picture:
                    width, height = picture.size
                    picture.load()
                with Image.open(io.BytesIO(raw)) as picture:
                    picture.verify()
                digest = hashlib.sha256(raw).hexdigest()
                if digest in known_hashes:
                    raise RuntimeError("duplicate bytes already generated.")
                digest_dhash = dhash(raw)
                nearest = (
                    min(hamming(digest_dhash, other) for other in sibling_hashes)
                    if sibling_hashes
                    else 64
                )
                if nearest < MIN_DHASH_DISTANCE:
                    raise RuntimeError(f"too similar to a sibling take (dhash {nearest}).")
            except Exception as exc:
                print(f"{key} attempt {attempts} rejected: {exc}")
                time.sleep(2)
                continue
            (output_root / f"{key}.jpg").write_bytes(raw)
            known_hashes.add(digest)
            sibling_hashes.add(digest_dhash)
            scenes[key] = {
                **meta,
                "response_id": response_id,
                "prompt": prompt,
                "sha256": digest,
                "bytes": len(raw),
                "width": width,
                "height": height,
                "dhash": digest_dhash,
                "usage": usage,
                "attempts": attempts,
                "status": "done",
                "generated_at": datetime.now(UTC).isoformat(),
            }
            manifest_path.write_text(json.dumps(manifest, indent=2))
            print(f"{key} done dhash_min={nearest} attempts={attempts}")
            time.sleep(2)
            break
        else:
            scenes[key] = {**meta, "attempts": attempts, "status": "failed"}
            manifest_path.write_text(json.dumps(manifest, indent=2))
            raise RuntimeError(f"{key} failed after {attempts} attempts.")
    contact_sheet(output_root)
    print(f"done: {budget.used} Muse calls spent")


if __name__ == "__main__":
    main()
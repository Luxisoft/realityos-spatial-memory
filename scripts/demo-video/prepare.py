"""Prepare the editorial assets and OpenMontage inputs, without touching app data."""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / ".runtime/video-production"
PROJECT = WORK / "project"
PUBLIC = PROJECT / "public"
PUBLIC.mkdir(parents=True, exist_ok=True)
SOURCES = ROOT / "demo-video/production"
if not (WORK / "narration.json").exists():
    shutil.copy2(SOURCES / "narration.json", WORK / "narration.json")
if not (WORK / "audio").exists():
    shutil.copytree(SOURCES / "audio", WORK / "audio")
for name in ["media", "audio"]:
    destination = PUBLIC / name
    if not destination.exists():
        destination.symlink_to(WORK / name, target_is_directory=True)
for source, name in [
    (ROOT / "android/app/src/main/res/drawable-nodpi/icon_app.png", "icon_app.png"),
    (Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"), "font-regular.ttf"),
    (Path("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"), "font-bold.ttf"),
]:
    shutil.copy2(source, PUBLIC / name)

data = json.loads((WORK / "narration.json").read_text())


def clips(*entries):
    return [
        {"asset": asset, "start": start, "length": length}
        for asset, start, length in entries
    ]


META = [
    (
        "hook",
        "Your world.\nWithin reach.",
        "REALITYOS",
        "A photo. A question.\nThe context you need.",
        clips(("display_search", 21.8, 5), ("display_search", 27.5, 7)),
    ),
    (
        "overview",
        "Context, when\nit matters.",
        "THE IDEA",
        "Visual search, authorized records\nand shared context.",
        [],
    ),
    (
        "policeauth",
        "One workspace.\nShared context.",
        "01 / PUBLIC SAFETY",
        "A local account opens the records\nshared with its work group.",
        clips(
            ("police_auth", 3, 6),
            ("police_auth", 11.5, 1.5),
            ("police_auth", 15.8, 4.3),
        ),
    ),
    (
        "police",
        "From a photo\nto case records.",
        "02 / SEARCH + REVIEW",
        "Ask a question. Inspect the results.",
        clips(("police_search", 19, 38.7)),
    ),
    (
        "socialauth",
        "A shared space\nfor connection.",
        "03 / META SOCIAL MEDIA",
        "Profiles, publications and context\ninside an authorized group.",
        clips(("social_auth", 7, 3), ("social_auth", 16, 6.4)),
    ),
    (
        "display",
        "See. Search.\nOpen the profile.",
        "04 / GLASSES PREVIEW",
        "The interaction, demonstrated\ninside the Android app.",
        clips(("display_search", 3, 6.5), ("display_search", 14, 22.8)),
    ),
    (
        "models",
        "Meta AI,\nwith a purpose.",
        "UNDER THE HOOD",
        "Each model has a distinct role\nin the broader system.",
        [],
    ),
    (
        "contributions",
        "What I built\nduring the event.",
        "HACKATHON CONTRIBUTIONS",
        "An existing foundation.\nConcrete additions you can inspect.",
        [],
    ),
    (
        "concepts",
        "One foundation.\nMore possibilities.",
        "BEYOND THESE TWO CASES",
        "Context can support many different\npeople, places and workflows.",
        [],
    ),
    ("closing", "", "", "", []),
]
for variant in ["main", "x"]:
    scenes = data[variant]["scenes"]
    indices = list(range(10)) if variant == "main" else [0, 1, 2, 3, 4, 5, 6, 7, 9]
    for scene, index in zip(scenes, indices):
        kind, title, eyebrow, body, media = META[index]
        scene.update(kind=kind, title=title, eyebrow=eyebrow, body=body, clips=media)
        if variant == "x":
            if index == 0:
                scene["clips"] = clips(
                    ("display_search", 21.8, 4), ("display_search", 27.5, 6)
                )
            if index == 2:
                scene["clips"] = clips(
                    ("police_auth", 11.5, 1.5), ("police_auth", 15.8, 4.3)
                )
            if index == 3:
                scene["clips"] = clips(
                    ("police_search", 19, 5.8),
                    ("police_search", 27, 7),
                    ("police_search", 42.8, 14.9),
                )
            if index == 4:
                scene["clips"] = clips(("social_auth", 7, 3), ("social_auth", 17, 5.4))
            if index == 5:
                scene["clips"] = clips(
                    ("display_search", 3, 6.5),
                    ("display_search", 14, 11),
                    ("display_search", 27, 9.8),
                )
        assert sum(c["length"] for c in scene["clips"]) <= scene["duration"] + 0.01
        assert scene["audio_duration"] <= scene["duration"]
    props = {
        "duration": data[variant]["duration"],
        "variant": variant,
        "scenes": scenes,
    }
    props_file = PROJECT / f"{variant}.json"
    props_file.write_text(json.dumps(props, indent=2))
    inputs = {
        "operation": "render",
        "output_path": str(WORK / "exports" / f"realityos-{variant}.mp4"),
        "edit_decisions": {
            "version": "1.0",
            "cuts": [],
            "render_runtime": "remotion",
            "composition_mode": "atelier",
            "bespoke": {
                "entry": str(ROOT / "scripts/demo-video/RealityOS.tsx"),
                "composition_id": "RealityOS",
                "props_path": str(props_file),
                "public_dir": str(PUBLIC),
                "art_direction": "RealityOS dark graphite and muted blue. Real Android footage, legible editorial panels, English synchronized narration and subtitles. Preserve original results and distinguish simulated previews.",
                "crf": 20,
                "concurrency": 2,
            },
        },
        "proposal_packet": {"production_plan": {"render_runtime": "remotion"}},
    }
    (PROJECT / f"{variant}-inputs.json").write_text(json.dumps(inputs, indent=2))
print("Prepared main (180 s) and X (135 s) OpenMontage inputs.")

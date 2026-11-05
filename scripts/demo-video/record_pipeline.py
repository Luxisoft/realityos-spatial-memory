"""Record the real OpenMontage screen-demo pipeline for prepared RealityOS videos.

Run with OpenMontage's isolated Python, after prepare.py:
  .runtime/video-production/openmontage/.venv/bin/python \
      scripts/demo-video/record_pipeline.py

Optional: --render-result main=/absolute/result.json (repeat for x).
Use --final-output main=/absolute/mastered.mp4 for a separate finished master.
Final approval is recorded only when --review-evidence points to a JSON object
whose variant entry records status=pass, reviewer=user, visual_review_completed,
notes, and the output's sha256 after the user's actual review.
This script never renders, changes creative inputs, or publishes to a service.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / ".runtime/video-production"
OPENMONTAGE = WORK / "openmontage"
PROJECT = WORK / "project"
PIPELINE = PROJECT / "pipeline"
sys.path.insert(0, str(OPENMONTAGE))

from lib.checkpoint import init_project, validate_checkpoint, write_checkpoint
from schemas.artifacts import validate_artifact


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decision(
    number: int, category: str, subject: str, selected: str, reason: str
) -> dict:
    return {
        "decision_id": f"d-{number:03d}",
        "stage": "idea",
        "category": category,
        "subject": subject,
        "options_considered": [
            {"option_id": selected, "label": selected, "score": 1, "reason": reason}
        ],
        "selected": selected,
        "reason": reason,
        "user_visible": True,
        "user_approved": True,
    }


def record_variant(
    variant: str,
    result_path: Path | None,
    evidence: dict,
    final_output: Path | None = None,
) -> dict:
    props_path = PROJECT / f"{variant}.json"
    inputs_path = PROJECT / f"{variant}-inputs.json"
    props, inputs = read_json(props_path), read_json(inputs_path)
    output = final_output or Path(inputs["output_path"])
    sources = read_json(WORK / "source-review.json")
    narration = read_json(WORK / "narration.json")
    scenes = props["scenes"]
    project_id = f"realityos-{variant}"
    title = "RealityOS — Your world. Within reach."
    directory = init_project(
        project_id, title=title, pipeline_type="screen-demo", pipeline_dir=PIPELINE
    )
    artifact_dir = directory / "artifacts"
    approval = {
        "source": "User-approved production plan followed by: Implement the plan.",
        "scope": "Produce the agreed English videos from supplied recordings, Jose Marin ElevenLabs voice, OpenMontage and bespoke Remotion composition.",
        "final_output_review": "Separate verification required after render; not implied by creative approval.",
    }
    art_direction = inputs["edit_decisions"]["bespoke"]["art_direction"]
    brief = {
        "version": "1.0",
        "title": title,
        "hook": scenes[0]["text"],
        "key_points": [
            "Build for Your World: useful context from a photo and a question.",
            "Demonstrate actual Police and Meta Social Media app workflows.",
            "Explain distinct Meta model roles and event contributions.",
            "Keep conceptual footage and the simulated glasses preview identified.",
        ],
        "core_message": "RealityOS connects visual search with authorized shared context.",
        "cta": "What would you build with RealityOS?",
        "tone": "Clear, grounded, concise English",
        "style": art_direction,
        "target_audience": "Hackathon judges" if variant == "main" else "X audience",
        "target_platform": "generic",
        "target_duration_seconds": props["duration"],
        "reference_material": [v["source"] for v in sources["assets"].values()],
        "metadata": {
            "production_mode": "real_capture",
            "track": "Build for Your World",
            "variant": variant,
            "approval": approval,
        },
    }
    decisions = {
        "version": "1.0",
        "project_id": project_id,
        "decisions": [
            decision(
                1,
                "pipeline_selection",
                "Existing app recordings",
                "screen-demo",
                "The owner supplied working Android captures and authorized their use.",
            ),
            decision(
                2,
                "render_runtime_selection",
                "OpenMontage render runtime",
                "remotion",
                "Approved bespoke animated panels, synchronized English captions, and real phone footage.",
            ),
            decision(
                3,
                "composition_mode",
                "Composition implementation",
                "atelier",
                "The approved plan uses project-specific RealityOS art direction.",
            ),
            decision(
                4,
                "voice_selection",
                "English narration voice",
                narration["voice"]["name"],
                "The owner expressly selected Jose Marin's ElevenLabs voice.",
            ),
            decision(
                5,
                "approval_policy",
                "Existing production authorization",
                "approved-plan",
                "The user requested implementation of the complete plan; final output review remains pending.",
            ),
        ],
    }
    script = {
        "version": "1.0",
        "title": title,
        "total_duration_seconds": props["duration"],
        "voice_performance": {
            "performance_intent": "English explanation by Jose Marin",
            "pacing_profile": "conversational",
            "pause_policy": "Allow viewers time to inspect real UI results.",
            "provider_notes": {
                "provider": "ElevenLabs",
                "voice": narration["voice"]["name"],
            },
        },
        "sections": [
            {
                "id": s["id"],
                "label": s["kind"],
                "text": s["text"],
                "start_seconds": s["start"],
                "end_seconds": s["start"] + s["duration"],
                "source_ref": str(WORK / "source-review.json"),
                "speaker_directions": "Natural English; preserve uncertainty and distinguish concepts.",
            }
            for s in scenes
        ],
        "metadata": {"voice": narration["voice"], "props_path": str(props_path)},
    }
    scene_plan = {
        "version": "1.0",
        "scenes": [
            {
                "id": s["id"],
                "type": "screen_recording" if s["clips"] else "animation",
                "description": f"{s['kind']}: {s['title'].replace(chr(10), ' ')} {s['body'].replace(chr(10), ' ')}",
                "start_seconds": s["start"],
                "end_seconds": s["start"] + s["duration"],
                "script_section_id": s["id"],
                "framing": "1920x1080 landscape; portrait app footage contained beside editorial panels.",
                "movement": "Project-authored entrances; source actions remain visible.",
                "overlay_notes": "English titles and timed captions; actual app detail crops retain original content.",
                "required_assets": [
                    {"type": "video", "description": c["asset"], "source": "provided"}
                    for c in s["clips"]
                ],
            }
            for s in scenes
        ],
        "metadata": {"timeline_source": str(props_path), "fps": 30},
    }
    assets = []
    for name, source in sources["assets"].items():
        assets.append(
            {
                "id": name,
                "type": "video",
                "path": os.path.relpath(source["file"], directory),
                "source_tool": "owner_recording"
                if "concept" not in name
                else "owner_higgsfield_asset",
                "scene_id": ",".join(
                    s["id"]
                    for s in scenes
                    if any(c["asset"] == name for c in s["clips"])
                )
                or "concept-panels",
                "duration_seconds": source["duration"],
                "resolution": f"{source['width']}x{source['height']}",
                "format": "mp4",
                "generation_summary": source["provenance"],
            }
        )
    for name, detail in sources.get("details", {}).items():
        assets.append(
            {
                "id": name,
                "type": "image",
                "path": os.path.relpath(detail["file"], directory),
                "source_tool": "ffmpeg_frame_crop",
                "scene_id": "detail-panels",
                "format": "jpg",
                "generation_summary": f"Unaltered crop from {detail['sourceAsset']} at {detail['sourceSeconds']}s.",
            }
        )
    for s in scenes:
        assets.append(
            {
                "id": f"voice-{s['id']}",
                "type": "narration",
                "path": os.path.relpath(PROJECT / "public" / s["audio"], directory),
                "source_tool": "elevenlabs",
                "scene_id": s["id"],
                "provider": "ElevenLabs",
                "model": narration["voice"]["model"],
                "duration_seconds": s["audio_duration"],
                "format": "mp3",
                "generation_summary": "Owner-selected Jose Marin voice; pitch-preserving tempo adjustment.",
            }
        )
    for filename, asset_type in [
        ("icon_app.png", "image"),
        ("font-regular.ttf", "font"),
        ("font-bold.ttf", "font"),
    ]:
        assets.append(
            {
                "id": filename,
                "type": asset_type,
                "path": os.path.relpath(PROJECT / "public" / filename, directory),
                "source_tool": "existing_project_asset",
                "scene_id": "all",
            }
        )
    for asset in assets:
        if not (directory / asset["path"]).is_file():
            raise FileNotFoundError(asset["path"])
    asset_manifest = {
        "version": "1.0",
        "assets": assets,
        "metadata": {
            "source_review": str(WORK / "source-review.json"),
            "voice": narration["voice"],
        },
    }
    edit_decisions = json.loads(json.dumps(inputs["edit_decisions"]))
    edit_decisions["metadata"] = {
        "target_duration_seconds": props["duration"],
        "proposal_render_runtime": "remotion",
        "source_props_sha256": sha256(props_path),
        "cut_timing_source": "The immutable props file passed to the atelier renderer.",
        "scenes": [
            {k: s[k] for k in ("id", "start", "duration", "clips")} for s in scenes
        ],
    }
    final_review = {
        "version": "1.0",
        "output_path": str(output),
        "status": "revise",
        "checks": {
            name: {"issues": ["Final rendered output has not yet been reviewed."]}
            for name in (
                "technical_probe",
                "visual_spotcheck",
                "audio_spotcheck",
                "promise_preservation",
                "subtitle_check",
            )
        },
        "issues_found": ["Final rendered output review is pending."],
        "recommended_action": "block",
        "metadata": {"state": "pending_final_render_review"},
    }
    artifacts = {
        "brief": brief,
        "decision_log": decisions,
        "script": script,
        "scene_plan": scene_plan,
        "asset_manifest": asset_manifest,
        "edit_decisions": edit_decisions,
        "final_review": final_review,
    }
    render_report = None
    if result_path:
        result = read_json(result_path)
        if not output.is_file() or not result.get("data", {}).get("final_review"):
            raise ValueError(f"Render result/output missing for {variant}")
        if final_output:
            probe = json.loads(
                subprocess.check_output(
                    [
                        "ffprobe",
                        "-v",
                        "error",
                        "-show_format",
                        "-show_streams",
                        "-of",
                        "json",
                        str(output),
                    ],
                    text=True,
                    timeout=30,
                )
            )
            video = next(s for s in probe["streams"] if s.get("codec_type") == "video")
            final_review["checks"]["technical_probe"] = {
                "valid_container": True,
                "duration_seconds": float(probe["format"]["duration"]),
                "resolution": f"{video['width']}x{video['height']}",
                "fps": float(Fraction(video["r_frame_rate"])),
                "has_audio": any(
                    s.get("codec_type") == "audio" for s in probe["streams"]
                ),
                "codec": video["codec_name"],
                "file_size_bytes": output.stat().st_size,
                "issues": [],
            }
            final_review["metadata"]["source_render_review"] = result["data"][
                "final_review"
            ]
            final_review["metadata"]["verification_scope"] = (
                "Final master ffprobe only; visual review belongs to the user."
            )
        else:
            final_review = result["data"]["final_review"]
        technical = final_review["checks"]["technical_probe"]
        render_report = {
            "version": "1.0",
            "outputs": [
                {
                    "path": str(output),
                    "format": "mp4",
                    "resolution": technical["resolution"],
                    "duration_seconds": technical["duration_seconds"],
                    "fps": technical["fps"],
                    "codec": technical["codec"],
                    "file_size_bytes": output.stat().st_size,
                    "platform_target": "hackathon" if variant == "main" else "X",
                }
            ],
            "render_time_seconds": result["duration_seconds"],
            "render_grammar": "screen-demo",
            "verification_notes": [
                "OpenMontage VideoCompose executed; final technical details refer to the explicitly selected output."
            ],
            "metadata": {
                "native_result": str(result_path),
                "source_render": inputs["output_path"],
                "final_output_override": final_output is not None,
                "sha256": sha256(output),
            },
        }
        review_evidence = evidence.get(variant, {})
        approved = (
            review_evidence.get("status") == "pass"
            and review_evidence.get("reviewer") == "user"
            and review_evidence.get("visual_review_completed") is True
            and review_evidence.get("notes")
            and review_evidence.get("sha256") == sha256(output)
        )
        if approved:
            final_review["status"] = "pass"
            final_review["recommended_action"] = "present_to_user"
            final_review.setdefault("metadata", {})["user_review_evidence"] = (
                review_evidence
            )
        else:
            final_review["status"] = "revise"
            final_review["recommended_action"] = "block"
            final_review.setdefault("issues_found", []).append(
                "User visual review is pending, as requested; technical probes do not constitute visual approval."
            )
            final_review.setdefault("metadata", {})["visual_review_status"] = (
                "pending_user"
            )
            final_review["checks"]["visual_spotcheck"] = {
                "issues": [
                    "User visual review is pending; no human visual pass is recorded."
                ]
            }
        artifacts["final_review"] = final_review
        artifacts["render_report"] = render_report
    for name, artifact in artifacts.items():
        validate_artifact(name, artifact)
        write_json(artifact_dir / f"{name}.json", artifact)
    for stage, names in [
        ("idea", ["brief", "decision_log"]),
        ("script", ["script"]),
        ("scene_plan", ["scene_plan"]),
        ("assets", ["asset_manifest"]),
        ("edit", ["edit_decisions"]),
    ]:
        write_checkpoint(
            PIPELINE,
            project_id,
            stage,
            "completed",
            {name: artifacts[name] for name in names},
            pipeline_type="screen-demo",
            human_approved=True,
            metadata={"approval_evidence": approval},
        )
    complete = (
        artifacts["final_review"]["status"] == "pass" and render_report is not None
    )
    compose_artifacts = {"final_review": artifacts["final_review"]}
    if render_report:
        compose_artifacts["render_report"] = render_report
    write_checkpoint(
        PIPELINE,
        project_id,
        "compose",
        "completed" if complete else "in_progress",
        compose_artifacts,
        pipeline_type="screen-demo",
        metadata={"state": "reviewed" if complete else "pending_final_review"},
    )
    publish_log = {
        "version": "1.0",
        "entries": [
            {
                "platform": "hackathon" if variant == "main" else "X",
                "status": "exported" if complete else "pending_review",
                "timestamp": datetime.now(UTC).isoformat(),
                "export_path": str(output),
            }
        ],
        "metadata": {"external_upload_performed": False},
    }
    validate_artifact("publish_log", publish_log)
    write_json(artifact_dir / "publish_log.json", publish_log)
    write_checkpoint(
        PIPELINE,
        project_id,
        "publish",
        "completed" if complete else "in_progress",
        {"publish_log": publish_log},
        pipeline_type="screen-demo",
        human_approved=bool(complete),
        metadata={"external_upload_performed": False, "approval_evidence": approval},
    )
    write_json(directory / "renderer_request.json", inputs)
    write_json(directory / "source-review.json", sources)
    for checkpoint in directory.glob("checkpoint_*.json"):
        validate_checkpoint(read_json(checkpoint))
    return {
        "project_id": project_id,
        "artifact_count": len(artifacts) + 1,
        "checkpoint_count": 7,
        "asset_count": len(assets),
        "final_review": artifacts["final_review"]["status"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--render-result", action="append", default=[], metavar="VARIANT=PATH"
    )
    parser.add_argument("--review-evidence", type=Path)
    parser.add_argument(
        "--final-output", action="append", default=[], metavar="VARIANT=PATH"
    )
    args = parser.parse_args()
    results = dict(item.split("=", 1) for item in args.render_result)
    final_outputs = dict(item.split("=", 1) for item in args.final_output)
    if (set(results) | set(final_outputs)) - {"main", "x"}:
        parser.error("Variants must be main or x.")
    if set(final_outputs) - set(results):
        parser.error("Each --final-output requires a matching --render-result.")
    evidence = read_json(args.review_evidence) if args.review_evidence else {}
    variants = [
        record_variant(
            name,
            Path(results[name]).resolve() if name in results else None,
            evidence,
            Path(final_outputs[name]).resolve() if name in final_outputs else None,
        )
        for name in ("main", "x")
    ]
    provenance = {
        "created_at": datetime.now(UTC).isoformat(),
        "openmontage": {
            "repository": "https://github.com/calesthio/OpenMontage",
            "pinned_commit": subprocess.check_output(
                ["git", "-C", str(OPENMONTAGE), "rev-parse", "HEAD"], text=True
            ).strip(),
            "path": str(OPENMONTAGE),
            "pipeline": "screen-demo",
            "composition_mode": "atelier",
            "render_runtime": "remotion",
        },
        "node": subprocess.check_output(["node", "--version"], text=True).strip(),
        "python_packages": subprocess.check_output(
            [sys.executable, "-m", "pip", "freeze"], text=True
        ).splitlines(),
        "package_lock_sha256": sha256(
            OPENMONTAGE / "remotion-composer/package-lock.json"
        ),
        "sources": {
            str(p.relative_to(ROOT)): sha256(p)
            for p in [
                ROOT / "scripts/demo-video/RealityOS.tsx",
                PROJECT / "main.json",
                PROJECT / "x.json",
                WORK / "narration.json",
                WORK / "source-review.json",
            ]
        },
        "variants": variants,
        "validated_with": "OpenMontage schemas.artifacts and lib.checkpoint",
    }
    write_json(PIPELINE / "run-provenance.json", provenance)
    print(
        json.dumps(
            {"pipeline": str(PIPELINE), "variants": variants, "validation": "passed"}
        )
    )


if __name__ == "__main__":
    main()

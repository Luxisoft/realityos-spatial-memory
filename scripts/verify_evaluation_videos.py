"""Measure existing video evidence through the public API; never seed answers."""

import argparse
import concurrent.futures
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
KINDS = ("positive", "negative", "isolation", "originals")


def save(path, receipt):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    temp.chmod(0o600)
    temp.replace(path)


def check_match(reply, post_id, interval, language):
    match = next(
        (m for m in reply.get("gallery_matches", []) if m["post_id"] == post_id), None
    )
    if match is None:
        return False, None
    timestamp = match.get("frame_timestamp_ms")
    passed = (
        isinstance(timestamp, int)
        and interval[0] <= timestamp <= interval[1]
        and match.get("evidence_id") is not None
        and match.get("mime_type") == "video/mp4"
        and match.get("localization_quality") == "sam"
        and not match.get("simulated", True)
        and reply.get("response_language") == language
        and bool(match.get("boxed_url"))
        and bool(match.get("matched_labels"))
    )
    return passed, match


def complete(receipt, groups=3):
    return all(
        len(receipt[kind]) == groups * per_group
        and all(row["passed"] for row in receipt[kind])
        for kind, per_group in zip(KINDS, (16, 2, 2, 4))
    )


def parallel(args):
    """Independent account preferences and receipt files for each work group."""

    def run(group):
        output = args.output.parent / group / args.output.name
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--journal",
            str(args.journal),
            "--output",
            str(output),
            "--group",
            group,
        ]
        if args.resume:
            command.append("--resume")
        result = subprocess.run(command, check=False)
        receipt = json.loads(output.read_text())
        receipt["process_exit_code"] = result.returncode
        for row in receipt["positive"]:
            if row.get("evidence_file"):
                row["evidence_file"] = group + "/" + row["evidence_file"]
        return receipt

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        parts = list(pool.map(run, ("security", "nursing", "memory")))
    result = dict(parts[0])
    for kind in KINDS:
        result[kind] = [row for part in parts for row in part[kind]]
    result["sources"] = {
        key: value for part in parts for key, value in part["sources"].items()
    }
    journal = json.loads(args.journal.read_text())
    expected = {row["id"]: row["item"]["sha256"] for row in journal["created"]}
    result["passed"] = (
        complete(result)
        and result["sources"] == expected
        and all(p["process_exit_code"] == 0 for p in parts)
    )
    result["finished_at"] = datetime.now(UTC).isoformat()
    result["visual_review_passed"] = False
    save(args.output, result)
    if not result["passed"]:
        raise SystemExit("The complete acceptance matrix has unresolved failures.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--group", choices=("security", "nursing", "memory"))
    parser.add_argument("--parallel", action="store_true")
    parser.add_argument(
        "--video",
        type=int,
        action="append",
        help="Check selected candidates during indexing; partial runs cannot pass acceptance",
    )
    args = parser.parse_args()
    if args.parallel:
        if args.group or args.video:
            parser.error("--parallel evaluates all three groups and all videos")
        parallel(args)
        return
    journal = json.loads(args.journal.read_text())
    evaluation = json.loads(
        (ROOT / "simulator/real-scenes/video-evaluation.json").read_text()
    )
    jury = json.loads((ROOT / "simulator/postman/jury.json").read_text())
    scenarios = {
        s["prefix"] if s["prefix"] != "hospital" else "nursing": s["values"]
        for s in jury["scenarios"]
    }
    staged = {r["item"]["id"]: r for r in journal["created"]}
    sources = {
        r["id"]: r["item"]["sha256"]
        for r in journal["created"]
        if not args.group or r["item"]["group"] == args.group
    }
    receipt = {
        "release": journal["release"],
        "sources": sources,
        "positive": [],
        "negative": [],
        "isolation": [],
        "originals": [],
        "passed": False,
        "visual_review_passed": False,
        "started_at": datetime.now(UTC).isoformat(),
    }
    prior = (
        json.loads(args.output.read_text())
        if args.resume and args.output.exists()
        else {}
    )
    # A changed video invalidates that group's vocabulary, while other groups
    # remain isolated and can reuse their measured results and image hashes.
    previous_sources = prior.get("sources", {})
    reusable = (
        {key: previous_sources.get(key) for key in sources} == sources
        if args.group
        else previous_sources == sources
    )
    previous = {r["key"]: r for r in prior.get("positive", [])} if reusable else {}
    frames = args.output.parent / "evidence"
    frames.mkdir(exist_ok=True)
    with httpx.Client(base_url=jury["base_url"], timeout=180) as client:
        headers = {}
        for group, account in scenarios.items():
            if args.group and group != args.group:
                continue
            response = client.post(
                "/v1/auth/login",
                json={"email": account["username"], "password": account["password"]},
            )
            response.raise_for_status()
            headers[group] = {
                "Authorization": "Bearer " + response.json()["access_token"]
            }
        for group, account in scenarios.items():
            if args.group and group != args.group:
                continue
            header = headers[group]
            preferences = client.get("/v1/me/preferences", headers=header)
            preferences.raise_for_status()
            original_language = preferences.json()["preferred_language"]
            try:
                for language in ("es", "en"):
                    if original_language:
                        changed = client.patch(
                            "/v1/me/preferences",
                            headers=header,
                            json={"preferred_language": language},
                        )
                        changed.raise_for_status()
                    for video in (
                        v
                        for v in evaluation["videos"]
                        if v["group"] == group
                        and (not args.video or v["id"] in args.video)
                    ):
                        row = staged[video["id"]]
                        if language == "es":
                            media = client.get(
                                f"/v1/gallery/{row['id']}/media", headers=header
                            )
                            receipt["originals"].append(
                                {
                                    "id": video["id"],
                                    "status": media.status_code,
                                    "passed": media.status_code == 200
                                    and hashlib.sha256(media.content).hexdigest()
                                    == row["item"]["sha256"],
                                }
                            )
                        for number, query in enumerate(video["queries"]):
                            key = f"{video['id']}:{number}:{language}"
                            cached = previous.get(key)
                            if (
                                cached
                                and cached.get("passed")
                                and cached["question"] == query[language]
                                and cached.get("target") == query["target"]
                                and cached.get("expected_interval_ms")
                                == query["visible_ms"]
                                and cached.get("evidence_file")
                                and (
                                    args.output.parent / cached["evidence_file"]
                                ).is_file()
                                and hashlib.sha256(
                                    (
                                        args.output.parent / cached["evidence_file"]
                                    ).read_bytes()
                                ).hexdigest()
                                == cached.get("evidence_sha256")
                            ):
                                receipt["positive"].append(cached)
                                continue
                            response = client.post(
                                "/v1/queries",
                                headers=header,
                                json={
                                    "workspace_id": account["workspace_id"],
                                    "search_scope": "gallery",
                                    "question": query[language],
                                    "language": language,
                                },
                            )
                            response.raise_for_status()
                            reply = response.json()
                            passed, match = check_match(
                                reply, row["id"], query["visible_ms"], language
                            )
                            result = {
                                "key": key,
                                "id": video["id"],
                                "group": group,
                                "username": account["username"],
                                "language": language,
                                "question": query[language],
                                "target": query["target"],
                                "post_id": row["id"],
                                "expected_interval_ms": query["visible_ms"],
                                "passed": passed,
                                "status": reply.get("gallery_search_status"),
                                "response_language": reply.get("response_language"),
                                "found": reply.get("found"),
                                "returned": [
                                    {
                                        k: m.get(k)
                                        for k in (
                                            "post_id",
                                            "frame_timestamp_ms",
                                            "matched_labels",
                                            "confidence",
                                        )
                                    }
                                    for m in reply.get("gallery_matches", [])
                                ],
                            }
                            if match:
                                result.update(
                                    {
                                        k: match.get(k)
                                        for k in (
                                            "evidence_id",
                                            "frame_timestamp_ms",
                                            "matched_labels",
                                            "localization_quality",
                                            "simulated",
                                        )
                                    }
                                )
                                evidence = client.get(
                                    match.get("image_url") or match["boxed_url"],
                                    headers=header,
                                )
                                result["passed"] = (
                                    passed and evidence.status_code == 200
                                )
                                if evidence.status_code == 200:
                                    filename = key.replace(":", "-") + ".jpg"
                                    (frames / filename).write_bytes(evidence.content)
                                    result["evidence_file"] = "evidence/" + filename
                                    result["evidence_sha256"] = hashlib.sha256(
                                        evidence.content
                                    ).hexdigest()
                            receipt["positive"].append(result)
                            print(
                                json.dumps(
                                    {
                                        "case": key,
                                        "passed": result["passed"],
                                        "status": result["status"],
                                        "labels": result.get("matched_labels"),
                                    }
                                ),
                                flush=True,
                            )
                            save(args.output, receipt)
                    question = next(
                        q for q in evaluation["negative"] if q["group"] == group
                    )[language]
                    response = client.post(
                        "/v1/queries",
                        headers=header,
                        json={
                            "workspace_id": account["workspace_id"],
                            "search_scope": "gallery",
                            "question": question,
                            "language": language,
                        },
                    )
                    response.raise_for_status()
                    reply = response.json()
                    receipt["negative"].append(
                        {
                            "group": group,
                            "language": language,
                            "question": question,
                            "status": reply.get("gallery_search_status"),
                            "passed": not reply.get("gallery_matches")
                            and reply.get("gallery_search_status") == "no_match"
                            and reply.get("response_language") == language,
                        }
                    )
            finally:
                if original_language:
                    restored = client.patch(
                        "/v1/me/preferences",
                        headers=header,
                        json={"preferred_language": original_language},
                    )
                    restored.raise_for_status()
            for foreign, other in scenarios.items():
                if foreign == group:
                    continue
                target = next(
                    r for r in journal["created"] if r["item"]["group"] == foreign
                )
                response = client.get(
                    f"/v1/gallery/{target['id']}/media", headers=header
                )
                query = client.post(
                    "/v1/queries",
                    headers=header,
                    json={
                        "workspace_id": other["workspace_id"],
                        "question": "keys",
                        "search_scope": "gallery",
                    },
                )
                receipt["isolation"].append(
                    {
                        "group": group,
                        "foreign_group": foreign,
                        "media_status": response.status_code,
                        "query_status": query.status_code,
                        "passed": response.status_code in (403, 404)
                        and query.status_code == 403,
                    }
                )
            save(args.output, receipt)
    receipt["finished_at"] = datetime.now(UTC).isoformat()
    receipt["passed"] = complete(receipt, 1 if args.group else 3)
    save(args.output, receipt)
    print(
        json.dumps(
            {
                kind: sum(r["passed"] for r in receipt[kind])
                for kind in ("positive", "negative", "isolation", "originals")
            }
        )
    )
    if not receipt["passed"]:
        raise SystemExit(
            "Some evaluation cases need correction; previous videos have not been retired."
        )


if __name__ == "__main__":
    main()

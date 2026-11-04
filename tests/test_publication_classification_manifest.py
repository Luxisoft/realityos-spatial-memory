"""The reviewed backfill is bounded to the existing licensed publication set."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_classification_review_covers_existing_originals_exactly():
    media = json.loads((ROOT / "simulator/real-scenes/manifest.json").read_text())[
        "items"
    ]
    review = json.loads(
        (ROOT / "simulator/real-scenes/publication-classification.json").read_text()
    )["items"]
    originals = {row["post_id"]: row for row in media}
    assert len(review) == len({row["post_id"] for row in review})
    assert {row["post_id"] for row in review} == set(originals)
    for row in review:
        assert row["media_sha256"] == originals[row["post_id"]]["sha256"]
        assert row["category"].strip()
        assert 1 <= len(row["tags"]) <= 20
        assert len(row["tags"]) == len({tag.casefold() for tag in row["tags"]})
        assert all(tag.strip() and len(tag) <= 80 for tag in row["tags"])


def test_review_uses_only_existing_jury_groups():
    jury = json.loads((ROOT / "simulator/postman/jury.json").read_text())
    catalog = json.loads((ROOT / "simulator/local/catalog.json").read_text())
    assert {s["values"]["workspace_id"] for s in jury["scenarios"]} == {
        g["id"] for g in catalog["groups"]
    }
    manifest = json.loads((ROOT / "simulator/real-scenes/manifest.json").read_text())[
        "items"
    ]
    groups = {item["group"] for item in manifest}
    review = json.loads(
        (ROOT / "simulator/real-scenes/publication-classification.json").read_text()
    )["items"]
    assert groups == {g["media_group"] for g in catalog["groups"] if g["publications"]}
    assert len({row["workspace_id"] for row in review}) == len(groups)
    assert {row["post_id"] for row in review} == {item["post_id"] for item in manifest}

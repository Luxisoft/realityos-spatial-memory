"""Published examples use installed SQL resources and never expose credentials."""

import json
import sys
import uuid
from pathlib import Path

from app.models import User
from app.social_features.models import Publication
from app.workspaces.models import Record

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from postman_dataset import (
    evaluation_dataset,
    local_evaluation_database,
    scenarios_from_database,
)


def test_local_scenario_identifiers_match_installed_sql_and_follow_database_edits():
    annotations = json.loads(
        (ROOT / "tests/fixtures/video-evaluation.json").read_text()
    )
    with local_evaluation_database() as db:
        scenarios = scenarios_from_database(db, annotations)
        assert len(scenarios) == 3
        for scenario in scenarios:
            values = scenario["values"]
            user = db.get(User, uuid.UUID(values["user_id"]))
            publication = db.get(Publication, uuid.UUID(values["post_id"]))
            assert user.display_name == values["display_name"]
            assert str(publication.workspace_id) == values["workspace_id"]
            if values["record_id"]:
                record = db.get(Record, uuid.UUID(values["record_id"]))
                assert str(record.workspace_id) == values["workspace_id"]
            assert values["password"] == values["email"] == ""
        first = scenarios[0]["values"]
        user = db.get(User, uuid.UUID(first["user_id"]))
        record = db.get(Record, uuid.UUID(first["record_id"]))
        user.display_name = "Updated local operator"
        record.title = "Updated local record"
        db.flush()
        refreshed = scenarios_from_database(db, annotations)[0]["values"]
        assert refreshed["display_name"] == "Updated local operator"
        assert (
            refreshed["record_question"]
            == "Summarize the record for Updated local record."
        )


def test_video_qa_matrix_resolves_original_hashes_without_operational_ids():
    annotations = json.loads(
        (ROOT / "tests/fixtures/video-evaluation.json").read_text()
    )
    assert all(
        "post_id" not in case
        for key in ("videos", "rejected_videos")
        for case in annotations[key]
    )
    dataset = evaluation_dataset()
    videos = [
        video for scenario in dataset["scenarios"] for video in scenario["videos"]
    ]
    assert {video["sha256"] for video in videos} == {
        video["sha256"] for video in annotations["videos"]
    }
    assert all(video["post_id"] for video in videos)


def test_collection_has_one_enabled_local_destination():
    data = json.loads(
        (ROOT / "docs/postman/RealityOS.postman_collection.json").read_text()
    )
    assert [f["name"] for f in data["item"]] == [
        "Localhost requests",
        "Server requests",
    ]
    assert "skipRequest" in str(data["item"][1]["event"])
    variables = {v["key"]: v["value"] for v in data["variable"]}
    assert variables["localhost_base_url"] == "http://localhost:8080"
    assert variables["localhost_auth_mode"] == "local-select"
    assert variables["server_base_url"] == ""
    assert all(
        not value
        for key, value in variables.items()
        if key.endswith(("_password", "_access_token", "_refresh_token"))
    )

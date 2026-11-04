"""Synthetic social provisioning preserves consent, privacy and workspace scope."""

import hashlib
import struct
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.faces import BiometricConsent, DetectedFace, FaceEnrollment
from app.local_catalog import FIXTURES, accounts, catalog, local_id
from app.local_models import LocalEvaluationState
from app.local_seed import fixture_file
from app.models import MediaAsset, User, Workspace, WorkspaceMember
from app.security import create_access_token
from app.social_features.models import (
    FacebookIdentity,
    FacebookMedia,
    FacebookProfile,
    Publication,
)
from sqlalchemy import select
from test_local_evaluation import evaluation as evaluation  # noqa: PLC0414


@pytest.fixture
def provision(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    import seed_local_social

    return seed_local_social


class FixtureEngine:
    name = "fixture-unit-test"
    simulated = True

    def __init__(self, manifest):
        self.embeddings = {}
        for i, profile in enumerate(manifest["profiles"]):
            vector = struct.pack("<10f", *[float(j == i) for j in range(10)])
            for asset in [profile["avatar"], *profile["references"]]:
                self.embeddings[asset["sha256"]] = vector

    def detect_faces(self, data):
        return [
            DetectedFace(
                {"x": 0.2, "y": 0.2, "width": 0.5, "height": 0.5},
                self.embeddings[hashlib.sha256(data).hexdigest()],
                0.99,
            )
        ]


def seed(evaluation, provision):
    manifest = provision.preflight_social()
    engine = FixtureEngine(manifest)
    with evaluation.app.state.database.session_factory() as db:
        result = provision.seed_local_social(
            db, evaluation.app.state.settings, engine=engine
        )
        db.commit()
    assert result == {
        "initialized": True,
        "profiles": 10,
        "avatars": 10,
        "references": 30,
        "enrollments": 30,
    }
    return manifest, engine


def headers(client, user_id):
    return {
        "Authorization": "Bearer "
        + create_access_token(uuid.UUID(str(user_id)), client.app.state.settings)
    }


def test_directory_counts_and_restart_preserve_changes(evaluation, provision):
    manifest, engine = seed(evaluation, provision)
    user_id = local_id("social-user", manifest["profiles"][0]["slug"])
    with evaluation.app.state.database.session_factory() as db:
        assert db.query(Workspace).count() == 3
        assert db.query(User).count() == 19
        assert len(accounts()) == 9
        assert (
            db.query(WorkspaceMember)
            .filter_by(workspace_id=provision.WORKSPACE)
            .count()
            == 13
        )
        assert db.query(FacebookIdentity).count() == 10
        assert db.query(FacebookMedia).count() == 30
        assert db.query(FaceEnrollment).count() == 30
        assert (
            db.query(MediaAsset).filter_by(workspace_id=provision.WORKSPACE).count()
            == 43
        )
        assert (
            db.query(Publication).filter_by(workspace_id=provision.WORKSPACE).count()
            == 0
        )
        assert all(p.imported_photos == 3 for p in db.scalars(select(FacebookProfile)))
        db.get(User, user_id).display_name = "Edited"
        db.get(BiometricConsent, user_id).revoked_at = datetime.now(UTC)
        removed = db.scalar(
            select(FaceEnrollment).where(FaceEnrollment.user_id == user_id)
        )
        removed_id = removed.id
        db.delete(removed)
        db.commit()
        assert (
            provision.seed_local_social(
                db, evaluation.app.state.settings, engine=engine
            )["initialized"]
            is False
        )
        assert db.get(User, user_id).display_name == "Edited"
        assert db.get(BiometricConsent, user_id).revoked_at is not None
        assert db.get(FaceEnrollment, removed_id) is None


def test_search_permissions_private_references_and_revocation(
    evaluation, provision, monkeypatch
):
    manifest, engine = seed(evaluation, provision)
    monkeypatch.setattr("app.faces.build_face_engine", lambda settings: engine)
    group = catalog()["groups"][1]
    target = manifest["profiles"][0]
    target_id = local_id("social-user", target["slug"])
    probe = fixture_file(FIXTURES, target["avatar"]["path"]).read_bytes()

    def search(auth, workspace=group["id"]):
        return evaluation.request(
            "POST",
            "/v1/faces/search",
            headers=auth,
            data={"workspace_id": workspace, "include_records": "false"},
            files={"probe": ("avatar.png", probe, "image/png")},
        )

    for operator in group["users"]:
        auth = headers(evaluation, operator["id"])
        assert search(auth).status_code == 403
        assert (
            evaluation.post(
                "/v1/faces/consent", headers=auth, json={"confirm": True}
            ).status_code
            == 200
        )
        result = search(auth)
        assert result.status_code == 200, result.text
        assert result.json()["matches"][0]["user_id"] == str(target_id)
        profile = evaluation.get(f"/v1/profiles/{target_id}", headers=auth).json()
        assert profile["profile_source"] == "facebook"
        assert profile["counts"]["photos"] == 3
        assert evaluation.get(profile["picture_url"], headers=auth).status_code == 200
        assert search(auth, catalog()["groups"][0]["id"]).status_code == 403
    with evaluation.app.state.database.session_factory() as db:
        reference = db.scalar(
            select(FaceEnrollment).where(FaceEnrollment.user_id == target_id)
        )
        reference_id, media_id = reference.id, reference.media_asset_id
        consent = db.get(BiometricConsent, target_id)
        consent.revoked_at = datetime.now(UTC)
        db.commit()
    assert evaluation.get(f"/v1/media/{media_id}", headers=auth).status_code == 404
    assert (
        evaluation.get(f"/v1/media/{media_id}/content", headers=auth).status_code == 404
    )
    assert (
        evaluation.get(
            f"/v1/faces/enrollments/{reference_id}/thumbnail", headers=auth
        ).status_code
        == 404
    )
    assert search(auth).json()["matches"] == []
    outsider = headers(evaluation, catalog()["groups"][0]["users"][0]["id"])
    evaluation.post("/v1/faces/consent", headers=outsider, json={"confirm": True})
    assert search(outsider).status_code == 403
    assert search(outsider, catalog()["groups"][0]["id"]).json()["matches"] == []


def test_local_guard_and_bad_faces_roll_back(evaluation, provision):
    settings = evaluation.app.state.settings
    with evaluation.app.state.database.session_factory() as db:
        with pytest.raises(ValueError, match="local"):
            provision.seed_local_social(
                db, settings.model_copy(update={"environment": "production"})
            )
        engine = FixtureEngine(provision.preflight_social())
        engine.detect_faces = lambda data: []
        with pytest.raises(ValueError, match="Three usable"):
            provision.seed_local_social(db, settings, engine=engine)
        db.rollback()
        assert db.query(User).count() == 9
        assert db.query(FaceEnrollment).count() == 0
        assert db.get(LocalEvaluationState, provision.RECEIPT) is None

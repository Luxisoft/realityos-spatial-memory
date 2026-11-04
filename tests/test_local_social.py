"""Synthetic directory installation preserves consent, privacy and workspace scope."""

import hashlib
import struct
import uuid
from datetime import UTC, datetime

import pytest
from app.faces import BiometricConsent, DetectedFace, FaceEnrollment
from app.local.social_bootstrap import RECEIPT, WORKSPACE, seed_local_social
from app.local_models import LocalEvaluationState
from app.models import MediaAsset, User, Workspace, WorkspaceMember
from app.security import create_access_token
from app.social_features.models import (
    FacebookIdentity,
    FacebookMedia,
    FacebookProfile,
    Publication,
    UserProfile,
)
from local_support import catalog
from sqlalchemy import select


class FixtureEngine:
    """Deterministic test engine keyed by persisted synthetic media ownership."""

    name = "fixture-unit-test"
    simulated = True

    def __init__(self, database):
        self.database = database
        self.transaction = None
        self.embeddings = {}

    def detect_faces(self, data):
        digest = hashlib.sha256(data).hexdigest()
        if digest not in self.embeddings:
            session = self.transaction or self.database.session_factory()
            try:
                asset = session.scalar(
                    select(MediaAsset).where(MediaAsset.sha256 == digest)
                )
                owner = uuid.UUID(asset.extra_metadata["owner_id"])
                # Stable unit vectors survive additive profile revisions without
                # changing the embeddings of previously enrolled identities.
                values = [
                    (1.0 if owner.int & (1 << bit) else -1.0) / (128**0.5)
                    for bit in range(128)
                ]
                self.embeddings[digest] = struct.pack("<128f", *values)
            finally:
                if self.transaction is None:
                    session.close()
        return [
            DetectedFace(
                {"x": 0.2, "y": 0.2, "width": 0.5, "height": 0.5},
                self.embeddings[digest],
                0.99,
            )
        ]


def seed(client):
    database = client.app.state.database
    engine = FixtureEngine(database)
    with database.session_factory() as db:
        engine.transaction = db
        result = seed_local_social(db, client.app.state.settings, engine=engine)
        target_id = db.scalar(
            select(FacebookProfile.user_id).order_by(FacebookProfile.user_id)
        )
        db.commit()
        engine.transaction = None
    assert result == {
        "initialized": True,
        "profiles": 13,
        "avatars": 13,
        "references": 39,
        "enrollments": 39,
    }
    return target_id, engine


def headers(client, user_id):
    return {
        "Authorization": "Bearer "
        + create_access_token(uuid.UUID(str(user_id)), client.app.state.settings)
    }


def test_directory_counts_and_restart_preserve_changes(evaluation):
    user_id, engine = seed(evaluation)
    assert len(evaluation.get("/v1/auth/local-accounts").json()["accounts"]) == 6
    with evaluation.app.state.database.session_factory() as db:
        assert db.query(Workspace).count() == 2
        assert db.query(User).count() == 19
        assert db.query(WorkspaceMember).filter_by(workspace_id=WORKSPACE).count() == 16
        assert db.query(FacebookIdentity).count() == 13
        assert db.query(FacebookMedia).count() == 39
        assert db.query(FaceEnrollment).count() == 39
        assert db.query(MediaAsset).filter_by(workspace_id=WORKSPACE).count() == 58
        assert db.query(Publication).filter_by(workspace_id=WORKSPACE).count() == 6
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
            seed_local_social(db, evaluation.app.state.settings, engine=engine)[
                "initialized"
            ]
            is False
        )
        assert db.get(User, user_id).display_name == "Edited"
        assert db.get(BiometricConsent, user_id).revoked_at is not None
        assert db.get(FaceEnrollment, removed_id) is None


def test_search_permissions_private_references_and_revocation(evaluation, monkeypatch):
    target_id, engine = seed(evaluation)
    monkeypatch.setattr("app.faces.build_face_engine", lambda settings: engine)
    groups = catalog(evaluation)["groups"]
    group = groups[1]
    with evaluation.app.state.database.session_factory() as db:
        profile = db.get(UserProfile, target_id)
        probe = db.get(MediaAsset, profile.avatar_media_id).original_bytes

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
        assert search(auth, groups[0]["id"]).status_code == 403
    with evaluation.app.state.database.session_factory() as db:
        reference = db.scalar(
            select(FaceEnrollment).where(FaceEnrollment.user_id == target_id)
        )
        reference_id, media_id = reference.id, reference.media_asset_id
        db.get(BiometricConsent, target_id).revoked_at = datetime.now(UTC)
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
    outsider = headers(evaluation, groups[0]["users"][0]["id"])
    evaluation.post("/v1/faces/consent", headers=outsider, json={"confirm": True})
    assert search(outsider).status_code == 403
    assert search(outsider, groups[0]["id"]).json()["matches"] == []


def test_local_guard_and_bad_faces_roll_back(evaluation):
    settings = evaluation.app.state.settings
    with evaluation.app.state.database.session_factory() as db:
        with pytest.raises(ValueError, match="local"):
            seed_local_social(
                db, settings.model_copy(update={"environment": "production"})
            )
        engine = FixtureEngine(evaluation.app.state.database)
        engine.detect_faces = lambda data: []
        with pytest.raises(ValueError, match="Three usable"):
            seed_local_social(db, settings, engine=engine)
        db.rollback()
        assert db.query(User).count() == 6
        assert db.query(FaceEnrollment).count() == 0
        assert db.get(LocalEvaluationState, RECEIPT) is None

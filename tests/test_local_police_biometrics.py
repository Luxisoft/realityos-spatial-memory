"""Police portraits are enrolled once so biometric search finds case subjects."""

from __future__ import annotations

import hashlib
import struct
import uuid

from app.faces import DetectedFace, FaceEngine
from app.local.police_biometrics import (
    AUTHORIZED_BY,
    RECEIPT,
    WORKSPACE,
    seed_police_biometrics,
)
from app.local_models import LocalEvaluationState
from app.models import MediaAsset
from app.security import create_access_token
from app.workspaces.models import Record, RecordMedia
from sqlalchemy import select


class FixtureEngine(FaceEngine):
    """Deterministic embeddings from image bytes: same bytes match exactly."""

    name = "fixture-police-v1"
    embedding_dim = 128
    simulated = True

    def detect_faces(self, image: bytes):
        raw = b"".join(
            hashlib.sha256(b"police-fixture" + bytes([part]) + image).digest()
            for part in range(4)
        )
        values = [(1.0 if byte & 1 else -1.0) / (128**0.5) for byte in raw[:128]]
        return [
            DetectedFace(
                {"x": 0.2, "y": 0.2, "width": 0.5, "height": 0.5},
                struct.pack("<128f", *values),
                0.99,
            )
        ]


def seed(db, settings):
    result = seed_police_biometrics(db, settings, engine=FixtureEngine())
    db.commit()
    return result


def headers(client, user_id):
    return {
        "Authorization": "Bearer "
        + create_access_token(uuid.UUID(str(user_id)), client.app.state.settings)
    }


def test_seed_enrolls_sixteen_portraits_once(evaluation):
    database = evaluation.app.state.database
    with database.session_factory() as db:
        result = seed(db, evaluation.app.state.settings)
        assert result == {"initialized": True, "records": 16, "enrollments": 16}
        rows = list(
            db.scalars(
                select(Record).where(
                    Record.workspace_id == WORKSPACE,
                    Record.kind == "person",
                    Record.status == "active",
                )
            )
        )
        assert len(rows) == 16
        for row in rows:
            assert row.biometric_authorized is True
            assert "Owner-ordered fictional-case enrollment" in row.biometric_basis
            assert row.biometric_authorized_by == AUTHORIZED_BY
            assert row.biometric_authorized_at is not None
        links = db.scalars(
            select(RecordMedia).where(
                RecordMedia.record_id.in_([row.id for row in rows]),
                RecordMedia.publication_id.is_not(None),
            )
        ).all()
        assert len(links) == 16
        assert db.get(LocalEvaluationState, RECEIPT) is not None
        again = seed_police_biometrics(db, evaluation.app.state.settings)
        assert again == {"initialized": False}


def test_enrolled_record_found_by_probe_without_strangers(evaluation, monkeypatch):

    engine = FixtureEngine()
    monkeypatch.setattr("app.faces.build_face_engine", lambda settings: engine)
    database = evaluation.app.state.database
    with database.session_factory() as db:
        seed(db, evaluation.app.state.settings)
        target = db.scalar(
            select(Record).where(
                Record.workspace_id == WORKSPACE, Record.title == "Esteban Pardo"
            )
        )
        link = db.scalar(
            select(RecordMedia).where(
                RecordMedia.record_id == target.id,
                RecordMedia.publication_id.is_not(None),
            )
        )
        probe = db.get(MediaAsset, link.media_id).original_bytes
    maya = uuid.UUID("002698d6-5b51-5f23-a6b7-8f9ac69767a8")
    consent = evaluation.post(
        "/v1/faces/consent", headers=headers(evaluation, maya), json={"confirm": True}
    )
    assert consent.status_code in (200, 201), consent.text
    response = evaluation.request(
        "POST",
        "/v1/faces/search",
        headers=headers(evaluation, maya),
        data={"workspace_id": str(WORKSPACE)},
        files={"probe": ("probe.png", probe, "image/png")},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["found"] is True
    assert [item["title"] for item in payload["matches_records"]] == ["Esteban Pardo"]
    assert payload["matches_records"][0]["similarity"] == 1.0
    assert payload["matches"] == []

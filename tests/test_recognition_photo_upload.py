import hashlib
import io
import struct
import uuid
from pathlib import Path

import pytest
from app.faces import DetectedFace, FaceEngine, assess_spoof_risk
from app.models import MediaAsset
from PIL import Image, ImageFilter, ImageOps

PORTRAIT = (
    Path(__file__).resolve().parents[1]
    / "simulator/media/regression/portraits/maya-patel.png"
)
BOX = {"x": 0.25, "y": 0.15, "width": 0.5, "height": 0.5}


class PortraitEngine(FaceEngine):
    name = "test-portrait-engine"
    simulated = False

    def detect_faces(self, image):
        return [DetectedFace(BOX, struct.pack("<2f", 1.0, 0.0), 0.99)]


def jpeg(picture, orientation=1):
    output = io.BytesIO()
    exif = Image.Exif()
    exif[274] = orientation
    picture.save(output, "JPEG", quality=95, exif=exif)
    return output.getvalue()


def test_high_resolution_portrait_is_not_rejected_as_blurry(
    client, auth_headers, monkeypatch
):
    monkeypatch.setattr("app.faces.build_face_engine", lambda _: PortraitEngine())
    client.post("/v1/faces/consent", headers=auth_headers, json={"confirm": True})
    with Image.open(PORTRAIT) as source:
        original = source.convert("RGB")
    for factor in (1, 3):
        raw = jpeg(original.resize((original.width * factor, original.height * factor)))
        assessment = assess_spoof_risk(raw, BOX)
        assert "blurry" not in assessment.reasons
        assert assessment.risk <= client.app.state.settings.face_spoof_max_risk
        response = client.post(
            "/v1/faces/profile-photo",
            headers=auth_headers,
            files={"file": ("portrait.jpg", raw, "image/jpeg")},
        )
        assert response.status_code == 201, response.text
        assert response.json()["faces_enrolled"] == 1
        with client.app.state.database.session_factory() as db:
            asset = db.get(MediaAsset, uuid.UUID(response.json()["media_id"]))
            assert asset.original_bytes == raw
            assert asset.sha256 == hashlib.sha256(raw).hexdigest()
        assert (
            client.get(
                f"/v1/media/{response.json()['media_id']}", headers=auth_headers
            ).status_code
            == 404
        )


@pytest.mark.parametrize("orientation", range(1, 9))
def test_profile_dimensions_and_visible_avatar_follow_exif(
    client, auth_headers, monkeypatch, orientation
):
    monkeypatch.setattr("app.faces.build_face_engine", lambda _: PortraitEngine())
    client.post("/v1/faces/consent", headers=auth_headers, json={"confirm": True})
    with Image.open(PORTRAIT) as source:
        raw = jpeg(source.convert("RGB"), orientation)
    response = client.post(
        "/v1/faces/profile-photo",
        headers=auth_headers,
        files={"file": ("portrait.jpg", raw, "image/jpeg")},
    )
    assert response.status_code == 201, response.text
    with Image.open(io.BytesIO(raw)) as original:
        expected = ImageOps.exif_transpose(original).convert("RGB")
    with client.app.state.database.session_factory() as db:
        asset = db.get(MediaAsset, uuid.UUID(response.json()["media_id"]))
        assert (asset.width, asset.height) == expected.size
        assert asset.original_bytes == raw
    avatar = client.post(
        "/v1/me/profile/avatar",
        headers=auth_headers,
        files={"file": ("portrait.jpg", raw, "image/jpeg")},
    )
    assert avatar.status_code == 200, avatar.text
    downloaded = client.get(avatar.json()["picture_url"], headers=auth_headers)
    assert downloaded.status_code == 200
    expected.thumbnail((512, 512))
    with Image.open(io.BytesIO(downloaded.content)) as actual:
        assert actual.size == expected.size
        assert actual.getexif().get(274, 1) == 1
        # Compare the oriented image, not just its dimensions: mirrors and 180°
        # rotations must also be correct. Allow the avatar's JPEG recompression.
        import numpy as np

        difference = np.abs(
            np.asarray(actual, dtype=float) - np.asarray(expected, dtype=float)
        )
        assert difference.mean() < 6


def test_photo_validation_still_requires_consent_and_rejects_tiny_faces(
    client, auth_headers, monkeypatch
):
    engine = PortraitEngine()
    monkeypatch.setattr("app.faces.build_face_engine", lambda _: engine)
    with Image.open(PORTRAIT) as source:
        raw = jpeg(source.convert("RGB"))
    upload = {
        "headers": auth_headers,
        "files": {"file": ("portrait.jpg", raw, "image/jpeg")},
    }
    assert client.post("/v1/faces/profile-photo", **upload).status_code == 403
    client.post("/v1/faces/consent", headers=auth_headers, json={"confirm": True})
    monkeypatch.setattr(
        engine,
        "detect_faces",
        lambda _: [
            DetectedFace({"x": 0.4, "y": 0.4, "width": 0.01, "height": 0.01}, b"", 0.99)
        ],
    )
    assert client.post("/v1/faces/profile-photo", **upload).status_code == 422
    with client.app.state.database.session_factory() as db:
        assert db.query(MediaAsset).count() == 0


@pytest.fixture
def email_account(client):
    from app.accounts.models import PasswordAccount
    from app.models import User
    from sqlalchemy import select

    with client.app.state.database.session_factory() as db:
        user = db.scalar(select(User).where(User.email == "admin@example.test"))
        db.add(PasswordAccount(user_id=user.id, username="photo-test"))
        db.commit()
        return user.id


def test_email_setup_accepts_saved_photos_without_claiming_live_verification(
    client, auth_headers, email_account, monkeypatch
):
    from app.faces import FaceEnrollment, FaceVerification
    from app.social import FacebookProfile

    monkeypatch.setattr("app.faces.build_face_engine", lambda _: PortraitEngine())
    with Image.open(PORTRAIT) as source:
        # Phone smoothing/compression can trip the texture heuristic while a
        # recognizable face remains. A reference is not a live-camera challenge.
        pictures = [
            jpeg(source.convert("RGB").filter(ImageFilter.GaussianBlur(r)))
            for r in (3, 3.2, 3.4, 3.6)
        ]
    assert (
        assess_spoof_risk(pictures[0], BOX).risk
        > client.app.state.settings.face_spoof_max_risk
    )
    upload = lambda path, raw: client.post(
        path, headers=auth_headers, files={"file": ("portrait.jpg", raw, "image/jpeg")}
    )
    assert upload("/v1/faces/profile-photo", pictures[0]).status_code == 403
    client.post("/v1/faces/consent", headers=auth_headers, json={"confirm": True})
    primary = upload("/v1/faces/profile-photo", pictures[0])
    assert primary.status_code == 201, primary.text
    assert primary.json()["faces_enrolled"] == 1
    assert upload("/v1/me/profile/avatar", pictures[0]).status_code == 200
    assert upload("/v1/faces/reference-photos", pictures[0]).status_code == 422
    for count, raw in enumerate(pictures[1:], 1):
        response = upload("/v1/faces/reference-photos", raw)
        assert response.status_code == 201, response.text
        assert response.json()["accepted_photos"] == count
    assert upload("/v1/faces/reference-photos", pictures[1]).json()["duplicate"]
    complete = client.post("/v1/faces/setup/complete", headers=auth_headers)
    assert complete.status_code == 200, complete.text
    assert complete.json()["complete"]
    with client.app.state.database.session_factory() as db:
        assert db.query(FaceEnrollment).count() == 4
        assert db.query(FaceVerification).count() == 0
        assets = db.query(MediaAsset).filter(MediaAsset.kind == "image").all()
        private_ids = [
            str(a.id)
            for a in assets
            if (a.extra_metadata or {}).get("face_profile")
            or (a.extra_metadata or {}).get("purpose") == "biometric-reference"
        ]
        # A later Facebook link must not turn saved references into login proof.
        db.add(FacebookProfile(user_id=email_account, import_status="done"))
        db.commit()
    for media_id in private_ids:
        assert (
            client.get(f"/v1/media/{media_id}", headers=auth_headers).status_code == 404
        )
    verification = client.post("/v1/faces/verify-identity", headers=auth_headers)
    assert verification.status_code == 409
    assert (
        verification.json()["detail"]
        == "A face capture is required before verification."
    )


@pytest.mark.parametrize(
    "case", ["none", "multiple", "tiny", "low_quality", "no_embedding"]
)
def test_saved_profile_still_rejects_unusable_faces(
    client, auth_headers, email_account, monkeypatch, case
):
    faces = {
        "none": [],
        "multiple": [DetectedFace(BOX, b"x", 0.99)] * 2,
        "tiny": [
            DetectedFace(
                {"x": 0.4, "y": 0.4, "width": 0.01, "height": 0.01}, b"x", 0.99
            )
        ],
        "low_quality": [DetectedFace(BOX, b"x", 0.1)],
        "no_embedding": [DetectedFace(BOX, b"", 0.99)],
    }[case]
    engine = PortraitEngine()
    monkeypatch.setattr(engine, "detect_faces", lambda _: faces)
    monkeypatch.setattr("app.faces.build_face_engine", lambda _: engine)
    client.post("/v1/faces/consent", headers=auth_headers, json={"confirm": True})
    response = client.post(
        "/v1/faces/profile-photo",
        headers=auth_headers,
        files={"file": ("photo.png", PORTRAIT.read_bytes(), "image/png")},
    )
    assert response.status_code == 422, response.text
    with client.app.state.database.session_factory() as db:
        assert db.query(MediaAsset).count() == 0


def test_saved_references_require_same_identity_and_usable_face(
    client, auth_headers, email_account, monkeypatch
):
    from app.faces import FaceEnrollment

    engine = PortraitEngine()
    monkeypatch.setattr("app.faces.build_face_engine", lambda _: engine)
    client.post("/v1/faces/consent", headers=auth_headers, json={"confirm": True})
    with Image.open(PORTRAIT) as picture:
        raw = jpeg(picture)
    response = client.post(
        "/v1/faces/profile-photo",
        headers=auth_headers,
        files={"file": ("photo.jpg", raw, "image/jpeg")},
    )
    assert response.status_code == 201
    for face, expected in (
        (
            DetectedFace(BOX, struct.pack("<2f", 0.0, 1.0), 0.99),
            "This photo does not match the registered face.",
        ),
        (
            DetectedFace(BOX, struct.pack("<2f", 1.0, 0.0), 0.1),
            "The face is too small or unclear. Choose a sharper photo.",
        ),
    ):
        monkeypatch.setattr(engine, "detect_faces", lambda _, face=face: [face])
        response = client.post(
            "/v1/faces/reference-photos",
            headers=auth_headers,
            files={"file": ("photo.png", PORTRAIT.read_bytes(), "image/png")},
        )
        assert response.status_code == 422
        assert response.json()["detail"] == expected
    with client.app.state.database.session_factory() as db:
        assert db.query(FaceEnrollment).count() == 1
        assert db.query(MediaAsset).count() == 1


@pytest.mark.parametrize("linked_password", [False, True])
def test_facebook_capture_keeps_its_existing_spoof_check(
    client, auth_headers, monkeypatch, linked_password
):
    from app.accounts.models import PasswordAccount
    from app.models import User
    from app.social import FacebookProfile
    from sqlalchemy import select

    with client.app.state.database.session_factory() as db:
        user = db.scalar(select(User).where(User.email == "admin@example.test"))
        db.add(FacebookProfile(user_id=user.id, import_status="done"))
        if linked_password:
            db.add(PasswordAccount(user_id=user.id, username="linked-account"))
        db.commit()
    monkeypatch.setattr("app.faces.build_face_engine", lambda _: PortraitEngine())
    client.post("/v1/faces/consent", headers=auth_headers, json={"confirm": True})
    with Image.open(PORTRAIT) as picture:
        raw = jpeg(picture.filter(ImageFilter.GaussianBlur(3)))
    response = client.post(
        "/v1/faces/profile-photo",
        headers=auth_headers,
        files={"file": ("photo.jpg", raw, "image/jpeg")},
    )
    assert response.status_code == 422
    assert response.json()["detail"].startswith("No live face could be verified")

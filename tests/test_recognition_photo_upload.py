import hashlib
import io
import struct
import uuid
from pathlib import Path

import pytest
from app.faces import DetectedFace, FaceEngine, assess_spoof_risk
from app.models import MediaAsset
from PIL import Image, ImageOps

PORTRAIT = (
    Path(__file__).resolve().parents[1]
    / "simulator/social-directory/source/maya-patel.png"
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
    monkeypatch.setattr("app.faces._face_engine_or_503", lambda _: PortraitEngine())
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
    monkeypatch.setattr("app.faces._face_engine_or_503", lambda _: PortraitEngine())
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
    monkeypatch.setattr("app.faces._face_engine_or_503", lambda _: engine)
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

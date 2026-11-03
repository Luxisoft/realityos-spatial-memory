"""Display badges stay outside every face, including tiny and crowded probes."""

import io
import json

from app.social_features.display_annotations import render_face_group
from app.social_features.display_media import FaceGroupMark
from PIL import Image


def mark(x, y, width, height, number=1, color="#F0BF24"):
    return FaceGroupMark(
        box={"x": x, "y": y, "width": width, "height": height},
        number=number,
        color=color,
    )


def test_tiny_face_interiors_are_preserved():
    source = Image.new("RGB", (600, 256), (184, 134, 94))
    marks = [mark(0.4, 0.3, 0.015, 0.04), mark(0.43, 0.3, 0.015, 0.04, 2, "#22D3EE")]
    picture = render_face_group(source, marks)
    assert picture.size == (600, 280)
    for item in marks:
        x = round((item.box["x"] + item.box["width"] / 2) * 600)
        y = round((item.box["y"] + item.box["height"] / 2) * 256)
        assert picture.getpixel((x, y)) == source.getpixel((x, y))


def test_full_frame_face_uses_label_band_instead_of_covering_face():
    source = Image.new("RGB", (600, 256), "white")
    picture = render_face_group(source, [mark(0, 0, 1, 1)])
    assert picture.getpixel((300, 120)) == (255, 255, 255)
    assert picture.crop((4, 4, 596, 252)).getextrema() == ((255, 255),) * 3
    assert any(
        pixel != (0, 0, 0) for pixel in picture.crop((0, 256, 600, 280)).getdata()
    )


def test_crowded_labels_cannot_cover_neighbouring_faces():
    source = Image.new("RGB", (600, 256), "white")
    marks = [mark(index / 20, 0, 1 / 20, 1, index + 1) for index in range(20)]
    picture = render_face_group(source, marks)
    for index in range(20):
        assert picture.getpixel((index * 30 + 15, 128)) == (255, 255, 255)
        # With no free photo space, each number occupies its own bottom slot.
        assert picture.getpixel((4 + index * 28 + 4, 262)) != (0, 0, 0)


def test_display_endpoint_preserves_face_center_and_does_not_store_probe(
    client, auth_headers
):
    from app.models import MediaAsset
    from sqlalchemy import func, select

    raw = io.BytesIO()
    Image.new("RGB", (600, 280), "white").save(raw, "PNG")
    with client.app.state.database.session_factory() as db:
        count = db.scalar(select(func.count()).select_from(MediaAsset))
    response = client.post(
        "/v1/display/face-group-links",
        headers=auth_headers,
        data={"marks": json.dumps([mark(0.4, 0.3, 0.03, 0.15).model_dump()])},
        files={"probe": ("probe.png", raw.getvalue(), "image/png")},
    )
    assert response.status_code == 200, response.text
    rendered = client.get(response.json()["url"])
    assert rendered.status_code == 200
    with Image.open(io.BytesIO(rendered.content)) as picture:
        # The old 30px filled badge painted this central face pixel gold.
        assert all(value > 235 for value in picture.getpixel((253, 96)))
    with client.app.state.database.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(MediaAsset)) == count


def test_enrollment_thumbnail_border_cannot_fill_a_small_face(
    client, auth_headers, monkeypatch
):
    import uuid

    from app.faces import FaceEnrollment, MockFaceEngine

    from .test_meta_display import _face_pair

    owner_headers = _face_pair(client, auth_headers)
    engine = MockFaceEngine()
    detect = engine.detect_faces
    monkeypatch.setattr(engine, "detect_faces", lambda image: detect(image)[:1])
    monkeypatch.setattr("app.faces.build_face_engine", lambda settings: engine)
    raw = io.BytesIO()
    Image.new("RGB", (2000, 2000), "white").save(raw, "PNG")
    enrolled = client.post(
        "/v1/faces/profile-photo",
        headers=owner_headers,
        files={"file": ("portrait.png", raw.getvalue(), "image/png")},
    )
    assert enrolled.status_code == 201, enrolled.text
    enrollment_id = uuid.UUID(enrolled.json()["enrollment_ids"][0])
    with client.app.state.database.session_factory() as db:
        db.get(FaceEnrollment, enrollment_id).bounding_box = {
            "x": 0.5,
            "y": 0.5,
            "width": 0.004,
            "height": 0.004,
        }
        db.commit()
    response = client.get(
        f"/v1/faces/enrollments/{enrollment_id}/thumbnail", headers=auth_headers
    )
    assert response.status_code == 404, response.text

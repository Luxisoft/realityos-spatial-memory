import io
import uuid

import numpy as np
import pytest
from app.models import MediaAsset
from app.social_features.models import Publication
from PIL import Image, ImageOps

from .test_evidence_uploads import upload


def oriented_photo(orientation, size=(720, 480)):
    image = Image.new("RGB", size)
    width, height = size
    for color, box in (
        ("red", (0, 0, width // 2, height // 2)),
        ("green", (width // 2, 0, width, height // 2)),
        ("blue", (0, height // 2, width // 2, height)),
        ("yellow", (width // 2, height // 2, width, height)),
    ):
        image.paste(color, box)
    exif = Image.Exif()
    exif[274] = orientation
    output = io.BytesIO()
    image.save(output, "JPEG", quality=95, exif=exif)
    return output.getvalue()


@pytest.mark.parametrize("orientation", range(1, 9))
def test_publication_previews_and_thumbnails_are_upright_without_changing_original(
    client, auth_headers, orientation
):
    raw = oriented_photo(orientation)
    response = upload(client, auth_headers, raw=raw)
    assert response.status_code == 202, response.text
    result = response.json()
    assert result["status"] == "published"
    with client.app.state.database.session_factory() as db:
        post = db.get(Publication, uuid.UUID(result["result_id"]))
        assert db.get(MediaAsset, post.media_id).original_bytes == raw
    for path in (
        result["preview_url"],
        f"/v1/gallery/{result['result_id']}/thumbnail",
        f"/v1/gallery/{result['result_id']}/boxed?labels=absent",
    ):
        response = client.get(path, headers=auth_headers)
        assert response.status_code == 200, response.text
        with Image.open(io.BytesIO(raw)) as source:
            expected = ImageOps.exif_transpose(source).convert("RGB")
            expected.thumbnail((360, 480))
        with Image.open(io.BytesIO(response.content)) as actual:
            assert actual.size == expected.size
            assert actual.getexif().get(274, 1) == 1
            difference = np.abs(
                np.asarray(actual, dtype=float) - np.asarray(expected, dtype=float)
            )
            assert difference.mean() < 6


def test_high_resolution_publication_is_not_subject_to_face_validation(
    client, auth_headers
):
    raw = oriented_photo(6, size=(3600, 2400))
    response = upload(client, auth_headers, raw=raw)
    assert response.status_code == 202, response.text
    assert response.json()["status"] == "published"
    from app.faces import FaceEnrollment

    with client.app.state.database.session_factory() as db:
        assert db.query(FaceEnrollment).count() == 0
        post = db.get(Publication, uuid.UUID(response.json()["result_id"]))
        assert db.get(MediaAsset, post.media_id).original_bytes == raw


def test_publication_without_group_still_returns_destination_validation(
    client, auth_headers
):
    response = client.post(
        "/v1/me/publication-uploads",
        headers=auth_headers,
        data={
            "request_key": str(uuid.uuid4()),
            "category_id": str(uuid.uuid4()),
            "tag_ids": '["' + str(uuid.uuid4()) + '"]',
        },
        files={"file": ("photo.jpg", oriented_photo(6), "image/jpeg")},
    )
    assert response.status_code == 422
    assert any(
        error["loc"] == ["body", "workspace_id"] for error in response.json()["detail"]
    )

"""Execute generated write examples only against an isolated mock-provider database."""

import io
import json
import re
import uuid
from pathlib import Path

import pytest
from app.models import User
from app.security import create_access_token
from app.social_features.models import Publication
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(params=["server", "localhost"])
def requests(request):
    collection = json.loads(
        (ROOT / "docs/postman/RealityOS.postman_collection.json").read_text()
    )
    target = collection["item"][0 if request.param == "server" else 1]
    return {
        item["name"]: item["request"]
        for folder in target["item"]
        if folder["name"] not in {"00 Quick start", "00 Live scenarios"}
        for item in folder["item"]
    }


def resolve(value, **variables):
    def substitute(match):
        return variables[match[1].split("_", 1)[1]]

    return re.sub(r"{{([^}]+)}}", substitute, value)


def body(requests, name, **variables):
    return json.loads(resolve(requests[name]["body"]["raw"], **variables))


def test_publication_examples_use_authorized_work_group(client, auth_headers, requests):
    created = client.post(
        "/v1/groups", headers=auth_headers, json=body(requests, "POST /v1/groups")
    )
    assert created.status_code == 200, created.text
    workspace_id = created.json()["id"]
    upload = requests["POST /v1/me/publication-uploads"]
    data = {
        field["key"]: resolve(field["value"], workspace_id=workspace_id)
        for field in upload["body"]["formdata"]
        if field["type"] == "text" and not field.get("disabled")
    }
    output = io.BytesIO()
    Image.new("RGB", (64, 64), "red").save(output, "PNG")
    files = {"file": ("photo.png", output.getvalue(), "image/png")}
    with client.app.state.database.session_factory() as db:
        outsider = User(
            email="outside@example.test", display_name="Outside", password_hash="unused"
        )
        db.add(outsider)
        db.commit()
        other_headers = {
            "Authorization": "Bearer "
            + create_access_token(outsider.id, client.app.state.settings)
        }
    assert (
        client.post("/v1/me/publication-uploads", data=data, files=files).status_code
        == 401
    )
    denied = client.post(
        "/v1/me/publication-uploads", headers=other_headers, data=data, files=files
    )
    assert denied.status_code == 403
    accepted = client.post(
        "/v1/me/publication-uploads", headers=auth_headers, data=data, files=files
    )
    assert accepted.status_code == 202, accepted.text
    assert accepted.json()["status"] == "published"
    post_id = accepted.json()["result_id"]
    with client.app.state.database.session_factory() as db:
        media_id = str(db.get(Publication, uuid.UUID(post_id)).media_id)
    published = client.post(
        "/v1/gallery",
        headers=auth_headers,
        json=body(
            requests, "POST /v1/gallery", media_id=media_id, workspace_id=workspace_id
        ),
    )
    assert published.status_code == 200, published.text
    for route, payload in (
        (
            f"/v1/gallery/{post_id}/share",
            body(
                requests, "POST /v1/gallery/{post_id}/share", workspace_id=workspace_id
            ),
        ),
        (
            f"/v1/groups/{workspace_id}/publications/import",
            body(
                requests,
                "POST /v1/groups/{workspace_id}/publications/import",
                post_id=post_id,
            ),
        ),
    ):
        response = client.post(route, headers=auth_headers, json=payload)
        assert response.status_code == 200, response.text
    feed = client.get(
        f"/v1/gallery?workspace_id={workspace_id}", headers=auth_headers
    ).json()
    assert feed and all(item["workspace_id"] == workspace_id for item in feed)


def test_account_photo_examples_use_separate_file_uploads(requests):
    for path in (
        "/v1/me/profile/avatar",
        "/v1/faces/profile-photo",
        "/v1/faces/reference-photos",
    ):
        request = requests["POST " + path]
        assert request["body"]["mode"] == "formdata"
        assert request["body"]["formdata"] == [
            {"key": "file", "type": "file", "disabled": False, "src": ""}
        ]
        assert not any(h["key"].lower() == "content-type" for h in request["header"])
    assert body(requests, "POST /v1/faces/consent") == {"confirm": False}
    probe = requests["POST /v1/faces/search"]["body"]["formdata"]
    assert next(f for f in probe if f["key"] == "probe")["disabled"] is False


def test_group_invitation_example_uses_returned_code(client, auth_headers, requests):
    group = client.post(
        "/v1/groups", headers=auth_headers, json=body(requests, "POST /v1/groups")
    ).json()
    invite = client.post(
        f"/v1/groups/{group['id']}/invite", headers=auth_headers
    ).json()
    response = client.post(
        "/v1/groups/join",
        headers=auth_headers,
        json=body(requests, "POST /v1/groups/join", invite_code=invite["code"]),
    )
    assert response.status_code == 200, response.text
    assert response.json()["workspace_id"] == group["id"]

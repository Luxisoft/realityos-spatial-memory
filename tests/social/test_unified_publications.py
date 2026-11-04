"""The gallery is one group-scoped contract, including every write entrypoint."""

import io
import uuid

from catalog_support import classification_for
from PIL import Image
from sqlalchemy import inspect


def upload(client, headers, group=None):
    image = io.BytesIO()
    Image.new("RGB", (80, 60), "red").save(image, "PNG")
    fields = {"request_key": str(uuid.uuid4())}
    if group:
        fields.update(
            workspace_id=group, **classification_for(client, group, multipart=True)
        )
    return client.post(
        "/v1/me/publication-uploads",
        headers=headers,
        data=fields,
        files={"file": ("capture.png", image.getvalue(), "image/png")},
    )


def test_group_required_and_single_cursor_feed(client, auth_headers):
    assert upload(client, auth_headers).status_code == 422
    group = client.post(
        "/v1/groups", headers=auth_headers, json={"name": "Care team"}
    ).json()["id"]
    response = upload(client, auth_headers, group)
    assert response.status_code == 202, response.text
    assert response.json()["status"] == "published", response.text
    post_id = response.json()["result_id"]
    page = client.get(
        f"/v1/gallery/page?workspace_id={group}", headers=auth_headers
    ).json()
    assert [post["id"] for post in page["items"]] == [post_id]
    assert page["next_cursor"] is None
    assert "audience" not in page["items"][0]
    owner = page["items"][0]["owner"]["user_id"]
    assert (
        client.get(f"/v1/gallery/page?owner_ids={owner}", headers=auth_headers).json()[
            "items"
        ][0]["id"]
        == post_id
    )
    assert (
        client.get(f"/v1/profiles/{owner}/media", headers=auth_headers).status_code
        == 404
    )
    assert client.get("/v1/gallery", headers=auth_headers).status_code == 405
    for route in ("/v1/me/profile/publications", "/v1/me/work-publications"):
        assert client.post(route, headers=auth_headers).status_code == 404
    schema = inspect(client.app.state.database.engine)
    fields = {field["name"]: field for field in schema.get_columns("publications")}
    assert "audience" not in fields
    assert not fields["workspace_id"]["nullable"]


def test_non_member_cannot_read_or_upload_to_group(client, auth_headers):
    group = client.post(
        "/v1/groups", headers=auth_headers, json={"name": "Private care team"}
    ).json()["id"]
    uploaded = upload(client, auth_headers, group).json()
    outsider = client.post(
        "/v1/auth/guest", json={"device_id": "unified-outsider"}
    ).json()
    headers = {"Authorization": "Bearer " + outsider["access_token"]}
    assert client.get("/v1/gallery/page", headers=headers).json()["items"] == []
    assert client.get(
        f"/v1/gallery/page?workspace_id={group}", headers=headers
    ).status_code in (403, 404)
    assert upload(client, headers, group).status_code in (403, 404)
    assert (
        client.get(
            f"/v1/gallery/{uploaded['result_id']}/media", headers=headers
        ).status_code
        == 404
    )


def test_obsolete_destination_fields_cannot_silently_publish_to_a_group(
    client, auth_headers
):
    group = client.post(
        "/v1/groups", headers=auth_headers, json={"name": "Explicit destination"}
    ).json()["id"]
    raw = io.BytesIO()
    Image.new("RGB", (80, 60), "red").save(raw, "PNG")
    response = client.post(
        "/v1/me/publication-uploads",
        headers=auth_headers,
        data={
            "workspace_id": group,
            "request_key": str(uuid.uuid4()),
            "audience": "home",
            **classification_for(client, group, multipart=True),
        },
        files={"file": ("capture.png", raw.getvalue(), "image/png")},
    )
    assert response.status_code == 422
    assert client.get("/v1/gallery/page", headers=auth_headers).json()["items"] == []


def test_public_moderation_routes_are_retired(client, auth_headers):
    for path in ("/v1/moderation/reports", "/v1/me/social-capabilities"):
        assert client.get(path, headers=auth_headers).status_code == 404

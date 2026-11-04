import io
import json
import uuid
from datetime import UTC, datetime, timedelta

from app.models import MediaAsset, MediaKind, Role, User, WorkspaceMember
from app.security import create_access_token
from app.social_features.classification import set_classification
from app.social_features.models import Publication
from PIL import Image
from sqlalchemy import select


def catalog(client, headers, name="Operations"):
    response = client.post(
        "/v1/groups",
        headers=headers,
        json={
            "name": name,
            "categories": ["Equipment", "Supplies"],
            "tags": ["Reviewed", "Ready"],
        },
    )
    assert response.status_code == 200, response.text
    group = response.json()["id"]
    values = client.get(
        f"/v1/groups/{group}/publication-catalog", headers=headers
    ).json()
    return group, {
        "category_id": values["categories"][0]["id"],
        "tag_ids": [values["tags"][0]["id"]],
    }


def photo():
    output = io.BytesIO()
    Image.new("RGB", (96, 96), "red").save(output, "PNG")
    return output.getvalue()


def upload(client, headers, group, selection, key="classified"):
    return client.post(
        "/v1/me/publication-uploads",
        headers=headers,
        data={
            "workspace_id": group,
            "request_key": key,
            **selection,
            "tag_ids": json.dumps(selection.get("tag_ids", [])),
        },
        files={"file": ("photo.png", photo(), "image/png")},
    )


def test_catalog_owner_scope_archive_and_required_publication(client, auth_headers):
    group, selection = catalog(client, auth_headers)
    other_group, foreign = catalog(client, auth_headers, "Other")
    with client.app.state.database.session_factory() as db:
        member = User(
            email="member@unit.invalid", display_name="Member", password_hash="disabled"
        )
        db.add(member)
        db.flush()
        db.add(
            WorkspaceMember(
                user_id=member.id, workspace_id=uuid.UUID(group), role=Role.ADMIN
            )
        )
        db.commit()
        member_headers = {
            "Authorization": "Bearer "
            + create_access_token(member.id, client.app.state.settings)
        }
    assert (
        client.get(
            f"/v1/groups/{group}/publication-catalog", headers=member_headers
        ).status_code
        == 200
    )
    assert (
        client.get(
            f"/v1/groups/{other_group}/publication-catalog", headers=member_headers
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/v1/groups/{group}/publication-catalog/tag",
            headers=member_headers,
            json={"name": "Unauthorized"},
        ).status_code
        == 403
    )
    assert upload(client, auth_headers, group, {}).status_code == 422
    assert upload(client, auth_headers, group, foreign).status_code == 422
    created = upload(client, auth_headers, group, selection)
    assert created.status_code == 202, created.text
    assert created.json()["status"] == "published", created.text
    post = created.json()["result_id"]
    archived = client.request(
        "PATCH",
        f"/v1/groups/{group}/publication-catalog/{selection['category_id']}",
        headers=auth_headers,
        json={"name": "Equipment", "active": False},
    )
    assert archived.status_code == 200, archived.text
    page = client.get(
        f"/v1/gallery/page?workspace_id={group}", headers=auth_headers
    ).json()["items"]
    assert page[0]["id"] == post
    assert page[0]["category"]["active"] is False
    assert (
        upload(client, auth_headers, group, selection, key="archived").status_code
        == 422
    )


def test_copy_requires_destination_classification_and_preserves_original(
    client, auth_headers
):
    group, selection = catalog(client, auth_headers)
    target, destination = catalog(client, auth_headers, "Destination")
    created = upload(client, auth_headers, group, selection).json()
    post = created["result_id"]
    path = f"/v1/groups/{target}/publications/import"
    assert (
        client.post(
            path, headers=auth_headers, json={"publication_ids": [post]}
        ).status_code
        == 422
    )
    bad = client.post(
        path,
        headers=auth_headers,
        json={"publication_ids": [post], "classifications": {post: selection}},
    )
    assert bad.status_code == 422
    payload = {"publication_ids": [post], "classifications": {post: destination}}
    copied = client.post(path, headers=auth_headers, json=payload)
    assert copied.status_code == 200, copied.text
    again = client.post(path, headers=auth_headers, json=payload)
    assert again.json()["items"][0]["status"] == "existing"
    source = client.get(
        f"/v1/gallery/page?workspace_id={group}", headers=auth_headers
    ).json()["items"][0]
    copy = client.get(
        f"/v1/gallery/page?workspace_id={target}", headers=auth_headers
    ).json()["items"][0]
    assert source["category"]["id"] == selection["category_id"]
    assert copy["category"]["id"] == destination["category_id"]
    assert copy["original_id"] == source["id"]
    assert (
        client.get("/v1/" + copy["media_url"], headers=auth_headers).content == photo()
    )


def test_filters_cover_all_pages_combine_and_escape_text(client, auth_headers):
    group, selection = catalog(client, auth_headers)
    with client.app.state.database.session_factory() as db:
        owner = db.scalar(select(User))
        asset = MediaAsset(
            workspace_id=uuid.UUID(group),
            kind=MediaKind.IMAGE,
            mime_type="image/png",
            original_bytes=photo(),
            sha256="a" * 64,
            byte_size=len(photo()),
        )
        db.add(asset)
        db.flush()
        for index in range(35):
            post = Publication(
                owner_id=owner.id,
                media_id=asset.id,
                workspace_id=uuid.UUID(group),
                caption="100% ready_" if index == 34 else "Other",
                note_text="Visible note",
                published_at=datetime(2026, 10, 1, tzinfo=UTC) + timedelta(days=index),
            )
            db.add(post)
            db.flush()
            set_classification(db, post, selection["category_id"], selection["tag_ids"])
        db.commit()
        owner_id = str(owner.id)
    path = f"/v1/gallery/page?workspace_id={group}"
    assert (
        len(client.get(path + "&limit=30", headers=auth_headers).json()["items"]) == 30
    )
    query = f"&category_ids={selection['category_id']}&tag_ids={selection['tag_ids'][0]}&owner_ids={owner_id}&description_q=100%25"
    result = client.get(path + query, headers=auth_headers)
    assert len(result.json()["items"]) == 1, result.text
    page = client.get(
        f"/v1/gallery/page?workspace_id={group}" + query, headers=auth_headers
    ).json()
    assert page["items"][0]["id"] == result.json()["items"][0]["id"]
    assert page["next_cursor"] is None
    assert (
        len(
            client.get(
                path + "&description_q=visible&limit=30", headers=auth_headers
            ).json()["items"]
        )
        == 30
    )
    assert (
        len(
            client.get(
                path
                + "&published_from=2026-10-01T00:00:00Z&published_before=2026-10-02T00:00:00Z",
                headers=auth_headers,
            ).json()["items"]
        )
        == 1
    )
    assert (
        client.get(
            path
            + "&published_from=2026-10-02T00:00:00Z&published_before=2026-10-01T00:00:00Z",
            headers=auth_headers,
        ).status_code
        == 422
    )
    options = client.get(
        f"/v1/gallery/filter-options?workspace_id={group}", headers=auth_headers
    ).json()
    assert (
        len(options["categories"])
        == len(options["tags"])
        == len(options["owners"])
        == 1
    )


def test_upload_idempotency_includes_classification(client, auth_headers):
    group, selection = catalog(client, auth_headers)
    first = upload(client, auth_headers, group, selection)
    assert first.status_code == 202, first.text
    assert upload(client, auth_headers, group, selection).json() == first.json()
    options = client.get(
        f"/v1/groups/{group}/publication-catalog", headers=auth_headers
    ).json()
    changed = {**selection, "tag_ids": [options["tags"][1]["id"]]}
    assert upload(client, auth_headers, group, changed).status_code == 409
    post = first.json()["result_id"]
    update = client.request(
        "PATCH",
        f"/v1/gallery/{post}/classification",
        headers=auth_headers,
        json=changed,
    )
    assert update.status_code == 200, update.text
    assert update.json()["tags"][0]["id"] == changed["tag_ids"][0]

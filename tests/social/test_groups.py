import io
import uuid

from app.models import (
    MediaAsset,
    Role,
    User,
    Workspace,
    WorkspaceMember,
)
from app.security import create_access_token, hash_password
from app.social import Publication
from catalog_support import classification_for, published_item
from PIL import Image

from .support import (
    _group_member_ids,
    _guest_headers,
    _guest_id,
    _work_post,
)


def test_member_uploads_work_publication_into_workspace(client, auth_headers):
    output = io.BytesIO()
    Image.new("RGB", (48, 32), "red").save(output, format="PNG")
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).first()
        workspace = Workspace(name="Taller demo", created_by_id=owner.id)
        db.add(workspace)
        db.flush()
        db.add(
            WorkspaceMember(
                workspace_id=workspace.id, user_id=owner.id, role=Role.ADMIN
            )
        )
        other = User(
            email="work-outsider@test.invalid",
            display_name="Work outsider",
            password_hash=hash_password("password123456"),
        )
        db.add(other)
        db.commit()
        workspace_id = str(workspace.id)
        other_headers = {
            "Authorization": "Bearer "
            + create_access_token(other.id, client.app.state.settings)
        }

    denied = client.post(
        "/v1/me/publication-uploads",
        headers=other_headers,
        files={"file": ("taller.png", output.getvalue(), "image/png")},
        data={
            "workspace_id": workspace_id,
            **classification_for(client, workspace_id, multipart=True),
            "request_key": str(uuid.uuid4()),
        },
    )
    assert denied.status_code == 403, denied.text

    rejected = client.post(
        "/v1/me/publication-uploads",
        headers=auth_headers,
        files={"file": ("taller.txt", b"not an image", "text/plain")},
        data={
            "workspace_id": workspace_id,
            **classification_for(client, workspace_id, multipart=True),
            "request_key": str(uuid.uuid4()),
        },
    )
    assert rejected.status_code == 415, rejected.text

    response = client.post(
        "/v1/me/publication-uploads",
        headers=auth_headers,
        files={"file": ("taller.png", output.getvalue(), "image/png")},
        data={
            "workspace_id": workspace_id,
            **classification_for(client, workspace_id, multipart=True),
            "caption": "Avance del turno",
            "request_key": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 202, response.text
    payload = published_item(client, auth_headers, response)
    assert "audience" not in payload
    assert payload["workspace_id"] == workspace_id
    assert payload["caption"] == "Avance del turno"
    assert payload["owned"] is True

    feed = client.get(
        f"/v1/gallery/page?workspace_id={workspace_id}",
        headers=auth_headers,
    ).json()["items"]
    assert any(item["id"] == payload["id"] for item in feed)

    with client.app.state.database.session_factory() as db:
        publication = db.get(Publication, uuid.UUID(payload["id"]))
        assert publication is not None
        asset = db.get(MediaAsset, publication.media_id)
        assert asset is not None
        assert asset.original_bytes == output.getvalue()
        assert asset.workspace_id == publication.workspace_id


def test_group_pin_create_read_and_join(client, auth_headers):
    first = client.post("/v1/groups", headers=auth_headers, json={"name": "Taller PIN"})
    assert first.status_code == 200, first.text
    pin = first.json()["join_pin"]
    assert len(pin) == 9 and pin.isdigit()
    workspace_id = first.json()["id"]

    second = client.post(
        "/v1/groups", headers=auth_headers, json={"name": "Otro taller"}
    )
    assert second.json()["join_pin"] != pin

    shown = client.get(f"/v1/groups/{workspace_id}/pin", headers=auth_headers)
    assert shown.status_code == 200, shown.text
    assert shown.json()["join_pin"] == pin

    guest = _guest_headers(client)
    assert (
        client.get(f"/v1/groups/{workspace_id}/pin", headers=guest).status_code == 403
    )

    joined = client.post("/v1/groups/join-by-pin", headers=guest, json={"pin": pin})
    assert joined.status_code == 200, joined.text
    assert joined.json()["workspace_id"] == workspace_id

    again = client.post(
        "/v1/groups/join-by-pin", headers=guest, json={"pin": f"{pin[:3]} {pin[3:]}"}
    )
    assert again.status_code == 200, again.text

    assert (
        client.post(
            "/v1/groups/join-by-pin", headers=guest, json={"pin": "000000000"}
        ).status_code
        == 404
    )
    with client.app.state.database.session_factory() as db:
        memberships = (
            db.query(WorkspaceMember)
            .filter(WorkspaceMember.workspace_id == uuid.UUID(workspace_id))
            .all()
        )
        assert len(memberships) == 2


def test_join_by_pin_rejects_home_workspaces(client, auth_headers):
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).first()
        home = Workspace(
            name=f"home:{owner.id}", created_by_id=owner.id, join_pin="111111111"
        )
        db.add(home)
        db.commit()
    guest = _guest_headers(client, "pin-guest-home")
    assert (
        client.post(
            "/v1/groups/join-by-pin", headers=guest, json={"pin": "111111111"}
        ).status_code
        == 404
    )


def test_invite_permission_matrix(client, auth_headers):
    created = client.post(
        "/v1/groups", headers=auth_headers, json={"name": "Taller permisos"}
    )
    workspace_id = created.json()["id"]
    pin = created.json()["join_pin"]
    first = _guest_headers(client, "perm-guest-first")
    second = _guest_headers(client, "perm-guest-second")
    assert (
        client.post(
            "/v1/groups/join-by-pin", headers=first, json={"pin": pin}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/v1/groups/join-by-pin", headers=second, json={"pin": pin}
        ).status_code
        == 200
    )
    first_id = _guest_id(client, first)
    second_id = _guest_id(client, second)

    assert (
        client.get(f"/v1/groups/{workspace_id}/pin", headers=first).status_code == 403
    )
    assert (
        client.post(
            f"/v1/groups/{workspace_id}/invite", headers=first, json={}
        ).status_code
        == 403
    )
    assert (
        client.get(f"/v1/groups/{workspace_id}/members", headers=first).status_code
        == 403
    )
    assert (
        client.post(
            f"/v1/groups/{workspace_id}/members/{second_id}/remove",
            headers=first,
            json={},
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/v1/groups/{workspace_id}/pin/rotate", headers=first, json={}
        ).status_code
        == 403
    )

    granted = client.post(
        f"/v1/groups/{workspace_id}/members/{first_id}/invite-permission",
        headers=auth_headers,
        json={"allowed": True},
    )
    assert granted.status_code == 200, granted.text
    assert granted.json()["can_invite"] is True

    assert (
        client.get(f"/v1/groups/{workspace_id}/pin", headers=first).status_code == 200
    )
    assert (
        client.post(
            f"/v1/groups/{workspace_id}/invite", headers=first, json={}
        ).status_code
        == 200
    )
    rows = _group_member_ids(client, first, workspace_id)
    assert rows[first_id]["can_invite"] is True
    assert rows[second_id]["can_invite"] is False
    assert (
        client.post(
            f"/v1/groups/{workspace_id}/members/{first_id}/invite-permission",
            headers=first,
            json={"allowed": True},
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/v1/groups/{workspace_id}/members/{second_id}/remove",
            headers=first,
            json={},
        ).status_code
        == 200
    )

    revoked = client.post(
        f"/v1/groups/{workspace_id}/members/{first_id}/invite-permission",
        headers=auth_headers,
        json={"allowed": False},
    )
    assert revoked.json()["can_invite"] is False
    assert (
        client.post(
            f"/v1/groups/{workspace_id}/invite", headers=first, json={}
        ).status_code
        == 403
    )


def test_group_pin_rotation_invalidates_previous(client, auth_headers):
    created = client.post(
        "/v1/groups", headers=auth_headers, json={"name": "Taller rotación"}
    )
    workspace_id = created.json()["id"]
    old_pin = created.json()["join_pin"]
    rotated = client.post(
        f"/v1/groups/{workspace_id}/pin/rotate", headers=auth_headers, json={}
    )
    assert rotated.status_code == 200, rotated.text
    new_pin = rotated.json()["join_pin"]
    assert len(new_pin) == 9 and new_pin.isdigit() and new_pin != old_pin

    guest = _guest_headers(client, "perm-guest-rotate")
    assert (
        client.post(
            "/v1/groups/join-by-pin", headers=guest, json={"pin": old_pin}
        ).status_code
        == 404
    )
    joined = client.post("/v1/groups/join-by-pin", headers=guest, json={"pin": new_pin})
    assert joined.status_code == 200, joined.text


def test_group_delete_is_creator_only_and_keeps_publications(client, auth_headers):
    created = client.post(
        "/v1/groups", headers=auth_headers, json={"name": "Taller borrar"}
    )
    workspace_id = created.json()["id"]
    guest = _guest_headers(client, "perm-guest-delete")
    assert (
        client.post(
            "/v1/groups/join-by-pin",
            headers=guest,
            json={"pin": created.json()["join_pin"]},
        ).status_code
        == 200
    )
    post_id = _work_post(client, auth_headers, workspace_id, "red")

    assert (
        client.request(
            "DELETE", f"/v1/groups/{workspace_id}", headers=guest
        ).status_code
        == 403
    )
    deleted = client.request(
        "DELETE", f"/v1/groups/{workspace_id}", headers=auth_headers
    )
    assert deleted.status_code == 200, deleted.text
    assert (
        client.request(
            "DELETE", f"/v1/groups/{workspace_id}", headers=auth_headers
        ).status_code
        == 404
    )
    with client.app.state.database.session_factory() as db:
        assert db.get(Workspace, uuid.UUID(workspace_id)).join_pin is None
        assert (
            db.query(WorkspaceMember)
            .filter(WorkspaceMember.workspace_id == uuid.UUID(workspace_id))
            .count()
            == 0
        )
        publication = db.get(Publication, uuid.UUID(post_id))
        assert publication is not None
        assert publication.workspace_id == uuid.UUID(workspace_id)
        assert publication.hidden


def test_group_delete_rejects_personal_spaces(client, auth_headers):
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).first()
        home = Workspace(name=f"home:{owner.id}", created_by_id=owner.id)
        db.add(home)
        db.flush()
        db.add(WorkspaceMember(workspace_id=home.id, user_id=owner.id, role=Role.ADMIN))
        db.commit()
        home_id = str(home.id)
    assert (
        client.request(
            "DELETE", f"/v1/groups/{home_id}", headers=auth_headers
        ).status_code
        == 409
    )


def test_workspaces_expose_group_creator(client, auth_headers):
    created = client.post(
        "/v1/groups", headers=auth_headers, json={"name": "Taller creador"}
    )
    workspace_id = created.json()["id"]
    guest = _guest_headers(client, "perm-guest-creator")
    assert (
        client.post(
            "/v1/groups/join-by-pin",
            headers=guest,
            json={"pin": created.json()["join_pin"]},
        ).status_code
        == 200
    )
    mine = {
        row["id"]: row
        for row in client.get("/v1/workspaces", headers=auth_headers).json()
    }
    assert mine[workspace_id]["created_by_me"] is True
    assert mine[workspace_id]["can_invite"] is True
    theirs = {
        row["id"]: row for row in client.get("/v1/workspaces", headers=guest).json()
    }
    assert theirs[workspace_id]["created_by_me"] is False
    assert theirs[workspace_id]["can_invite"] is False

"""The explicitly published account can query only its own demo workspace."""

import importlib.util
import json
import re
import uuid
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from app.models import MediaAsset, Role, User, Workspace, WorkspaceMember
from app.security import hash_password, verify_password
from sqlalchemy import func, select

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "postman_provision", ROOT / "simulator/postman/provision.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
DEMO = json.loads((ROOT / "simulator/postman/demo.json").read_text())


@pytest.mark.parametrize("realm", ["server", "localhost"])
def test_public_demo_auth_refresh_workspace_permissions_and_idempotence(
    client, auth_headers, realm
):
    settings = client.app.state.settings
    if realm == "localhost":
        settings.environment = "local"
        settings.local_login_enabled = True
    private_id = client.post(
        "/v1/workspaces", headers=auth_headers, json={"name": "Private owner workspace"}
    ).json()["id"]
    with client.app.state.database.session_factory() as db:
        assert MODULE.provision(db, settings, realm, DEMO)["created"]
        db.commit()
        original_hash = db.get(User, uuid.UUID(DEMO[realm]["user_id"])).password_hash
        assert not MODULE.provision(db, settings, realm, DEMO)["created"]
        db.commit()
        assert (
            db.get(User, uuid.UUID(DEMO[realm]["user_id"])).password_hash
            == original_hash
        )
        assert db.scalar(select(func.count()).select_from(MediaAsset)) == 0
    data = DEMO[realm]
    login = client.post(
        "/v1/auth/login", json={"email": data["email"], "password": data["password"]}
    )
    assert login.status_code == 200
    tokens = login.json()
    refreshed = client.post(
        "/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refreshed.status_code == 200
    headers = {"Authorization": "Bearer " + refreshed.json()["access_token"]}
    assert client.get("/v1/auth/me", headers=headers).json()["id"] == data["user_id"]
    workspaces = client.get("/v1/workspaces", headers=headers).json()
    assert [w["id"] for w in workspaces] == [data["workspace_id"]]
    assert (
        client.get(
            f"/v1/workspaces/{data['workspace_id']}/zones", headers=headers
        ).json()
        == []
    )
    assert (
        client.get(f"/v1/workspaces/{private_id}/zones", headers=headers).status_code
        == 403
    )
    assert (
        client.post(
            f"/v1/workspaces/{data['workspace_id']}/zones",
            headers=headers,
            json={"name": "Forbidden", "kind": "zone"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/v1/sessions",
            headers=headers,
            json={"workspace_id": data["workspace_id"], "consent_confirmed": True},
        ).status_code
        == 403
    )
    assert client.get(f"/v1/workspaces/{data['workspace_id']}/zones").status_code == 401


def test_demo_never_replaces_an_existing_account_or_publishes_its_password(client):
    data = DEMO["server"]
    with client.app.state.database.session_factory() as db:
        user = User(
            email=data["email"],
            display_name="Existing",
            password_hash=hash_password("KeepPrivatePassword123!"),
        )
        db.add(user)
        db.commit()
        with pytest.raises(ValueError, match="nothing was changed"):
            MODULE.provision(db, client.app.state.settings, "server", DEMO)
        assert verify_password("KeepPrivatePassword123!", user.password_hash)
        assert db.scalar(select(func.count()).select_from(Workspace)) == 0


def test_demo_refuses_wrong_realm_and_unexpected_workspace_membership(client):
    settings = client.app.state.settings
    with client.app.state.database.session_factory() as db:
        with pytest.raises(ValueError, match="installation"):
            MODULE.provision(db, settings, "localhost", DEMO)
        MODULE.provision(db, settings, "server", DEMO)
        db.commit()
        user_id = uuid.UUID(DEMO["server"]["user_id"])
        extra = Workspace(name="Unexpected access", created_by_id=user_id)
        db.add(extra)
        db.flush()
        db.add(WorkspaceMember(workspace_id=extra.id, user_id=user_id, role=Role.ADMIN))
        db.commit()
        with pytest.raises(ValueError, match="nothing was changed"):
            MODULE.provision(db, settings, "server", DEMO)


def test_other_targets_credentials_and_disabled_local_setup_are_rejected(client):
    settings = client.app.state.settings
    with client.app.state.database.session_factory() as db:
        MODULE.provision(db, settings, "server", DEMO)
        db.commit()
    assert (
        client.post(
            "/v1/auth/login",
            json={
                "email": DEMO["server"]["email"],
                "password": DEMO["localhost"]["password"],
            },
        ).status_code
        == 401
    )
    settings.environment = "local"
    settings.local_login_enabled = False
    with client.app.state.database.session_factory() as db:
        with pytest.raises(ValueError, match="installation"):
            MODULE.provision(db, settings, "localhost", DEMO)
        assert db.get(User, uuid.UUID(DEMO["localhost"]["user_id"])) is None


def test_published_localhost_quick_start_runs_with_its_preconfigured_values(client):
    settings = client.app.state.settings
    settings.environment = "local"
    settings.local_login_enabled = True
    with client.app.state.database.session_factory() as db:
        MODULE.provision(db, settings, "localhost", DEMO)
        db.commit()
    collection = json.loads(
        (ROOT / "docs/postman/RealityOS.postman_collection.json").read_text()
    )
    values = {v["key"]: v["value"] for v in collection["variable"]}
    target = next(f for f in collection["item"] if f["name"] == "Localhost requests")
    quick = next(f["item"] for f in target["item"] if f["name"] == "00 Quick start")
    for item in quick:
        request = json.loads(
            re.sub(
                r"{{([^}]+)}}",
                lambda match: values[match[1]],
                json.dumps(item["request"]),
            )
        )
        url = urlsplit(request["url"]["raw"])
        assert url.netloc == "localhost:8080"
        headers = {}
        if request["auth"]["type"] == "bearer":
            headers["Authorization"] = "Bearer " + request["auth"]["bearer"][0]["value"]
        options = {"headers": headers}
        if request.get("body", {}).get("mode") == "raw":
            options["json"] = json.loads(request["body"]["raw"])
        response = client.request(request["method"], url.path, **options)
        assert response.status_code == 200, (item["name"], response.text)
        if url.path == "/v1/auth/login":
            values["localhost_access_token"] = response.json()["access_token"]
        elif url.path == "/v1/workspaces":
            assert [w["id"] for w in response.json()] == [
                values["localhost_workspace_id"]
            ]
        elif url.path == "/v1/auth/me":
            assert response.json()["id"] == values["localhost_user_id"]

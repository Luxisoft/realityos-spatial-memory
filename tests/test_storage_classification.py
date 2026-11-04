import uuid

from app.models import User
from app.security import create_access_token
from app.social_features.evidence_models import PublicationUpload
from app.social_features.models import Publication
from catalog_support import classification_for
from sqlalchemy import select
from storage_support import BASE, image_bytes
from storage_support import remote as remote  # noqa: PLC0414 -- pytest fixture export
from storage_support import source as source  # noqa: PLC0414 -- pytest fixture export


def test_unclassified_import_stays_private_until_owner_review(
    client, auth_headers, source, remote
):
    path = f"{BASE}/{source['id']}/imports"
    body = {
        "request_key": "review",
        "keys": ["photos/a.png"],
        "workspace_id": source["workspace_id"],
    }
    response = client.post(path, headers=auth_headers, json=body)
    assert response.status_code == 202, response.text
    item = response.json()["items"][0]
    assert item["status"] == "awaiting_classification"
    assert item["publication_id"] is None
    with client.app.state.database.session_factory() as db:
        upload = db.get(PublicationUpload, uuid.UUID(item["upload_id"]))
        assert upload.original_bytes == image_bytes()
        assert db.scalar(select(Publication.id)) is None
        outsider = User(
            email="outsider@unit.invalid",
            display_name="Outsider",
            password_hash="disabled",
        )
        db.add(outsider)
        db.commit()
        outsider_headers = {
            "Authorization": "Bearer "
            + create_access_token(outsider.id, client.app.state.settings)
        }
    approve = f"/v1/me/publication-uploads/{item['upload_id']}/classify"
    selection = classification_for(client, source["workspace_id"])
    assert (
        client.post(approve, headers=outsider_headers, json=selection).status_code
        == 404
    )
    assert client.get(item["preview_url"], headers=outsider_headers).status_code == 404
    assert (
        client.post(
            approve,
            headers=auth_headers,
            json={"category_id": selection["category_id"], "tag_ids": []},
        ).status_code
        == 422
    )
    # Import retries and repeated scans cannot substitute for a human selection.
    repeated = client.post(path, headers=auth_headers, json=body)
    assert repeated.json()["items"][0]["status"] == "awaiting_classification"
    retry = client.post(
        path + "/" + response.json()["id"] + "/retry", headers=auth_headers
    )
    assert retry.json()["items"][0]["status"] == "awaiting_classification"
    assert len(remote) == 1
    reviewed = client.post(approve, headers=auth_headers, json=selection)
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["status"] == "published", reviewed.text
    repeated = client.post(
        path, headers=auth_headers, json={**body, "request_key": "next-scan"}
    )
    assert repeated.json()["items"][0]["publication_id"] == reviewed.json()["result_id"]
    assert client.post(approve, headers=auth_headers, json=selection).status_code == 409


def test_pending_import_rejects_foreign_catalog_and_retired_source(
    client, auth_headers, source, remote
):
    item = client.post(
        f"{BASE}/{source['id']}/imports",
        headers=auth_headers,
        json={
            "request_key": "pending",
            "keys": ["photos/a.png"],
            "workspace_id": source["workspace_id"],
        },
    ).json()["items"][0]
    group = client.post(
        "/v1/groups", headers=auth_headers, json={"name": "Different group"}
    ).json()["id"]
    foreign = classification_for(client, group)
    approve = f"/v1/me/publication-uploads/{item['upload_id']}/classify"
    assert client.post(approve, headers=auth_headers, json=foreign).status_code == 422
    selection = classification_for(client, source["workspace_id"])
    assert (
        client.request(
            "DELETE", f"{BASE}/{source['id']}", headers=auth_headers
        ).status_code
        == 200
    )
    assert client.post(approve, headers=auth_headers, json=selection).status_code == 409
    with client.app.state.database.session_factory() as db:
        assert db.scalar(select(Publication.id)) is None
        upload = db.get(PublicationUpload, uuid.UUID(item["upload_id"]))
        assert upload.status == "cancelled"
        assert not upload.original_bytes

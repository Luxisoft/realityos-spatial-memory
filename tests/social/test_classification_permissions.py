import uuid

from app.models import Role, User, WorkspaceMember
from app.security import create_access_token
from app.social_features.models import Publication
from sqlalchemy import select

from .test_classification import catalog, upload


def test_filter_options_and_edits_respect_membership_and_authorship(
    client, auth_headers
):
    group, selection = catalog(client, auth_headers)
    other_group, foreign = catalog(client, auth_headers, "Private operations")
    visible = upload(client, auth_headers, group, selection).json()["result_id"]
    private = upload(client, auth_headers, other_group, foreign, key="private").json()[
        "result_id"
    ]
    with client.app.state.database.session_factory() as db:
        member = User(
            email="viewer@unit.invalid", display_name="Viewer", password_hash="disabled"
        )
        db.add(member)
        db.flush()
        db.add(
            WorkspaceMember(
                user_id=member.id, workspace_id=uuid.UUID(group), role=Role.ADMIN
            )
        )
        db.commit()
        headers = {
            "Authorization": "Bearer "
            + create_access_token(member.id, client.app.state.settings)
        }
    options = client.get("/v1/gallery/filter-options", headers=headers).json()
    assert {row["id"] for row in options["categories"]} == {selection["category_id"]}
    assert {row["id"] for row in options["tags"]} == set(selection["tag_ids"])
    assert (
        client.get(
            f"/v1/gallery/filter-options?workspace_id={other_group}", headers=headers
        ).status_code
        == 403
    )
    assert (
        client.get(
            f"/v1/gallery/page?category_ids={foreign['category_id']}", headers=headers
        ).json()["items"]
        == []
    )
    assert (
        client.get(
            f"/v1/gallery/page?tag_ids={foreign['tag_ids'][0]}", headers=headers
        ).json()["items"]
        == []
    )
    for key in (visible, private):
        response = client.request(
            "PATCH",
            f"/v1/gallery/{key}/classification",
            headers=headers,
            json=selection,
        )
        assert response.status_code == 403, response.text
    with client.app.state.database.session_factory() as db:
        membership = db.scalar(
            select(WorkspaceMember).where(WorkspaceMember.user_id == member.id)
        )
        db.delete(membership)
        db.commit()
    assert client.get("/v1/gallery/filter-options", headers=headers).json() == {
        "categories": [],
        "tags": [],
        "owners": [],
    }
    assert client.get("/v1/gallery/page", headers=headers).json()["items"] == []


def test_catalog_renames_keep_ids_and_archived_tags_remain_filterable(
    client, auth_headers
):
    group, selection = catalog(client, auth_headers)
    post = upload(client, auth_headers, group, selection).json()["result_id"]
    path = f"/v1/groups/{group}/publication-catalog"
    tag_id = selection["tag_ids"][0]
    renamed = client.request(
        "PATCH",
        f"{path}/{tag_id}",
        headers=auth_headers,
        json={"name": "  Ready   for shift  ", "active": False},
    )
    assert renamed.status_code == 200, renamed.text
    assert renamed.json()["id"] == tag_id
    assert renamed.json()["name"] == "Ready for shift"
    duplicate = client.post(
        f"{path}/tag", headers=auth_headers, json={"name": "READY FOR SHIFT"}
    )
    assert duplicate.status_code == 409
    items = client.get(
        f"/v1/gallery/page?tag_ids={tag_id}", headers=auth_headers
    ).json()["items"]
    assert [item["id"] for item in items] == [post]
    assert items[0]["tags"][0]["active"] is False
    assert items[0]["tags"][0]["name"] == "Ready for shift"
    assert (
        upload(client, auth_headers, group, selection, key="archived-tag").status_code
        == 422
    )
    restore = client.request(
        "PATCH",
        f"{path}/{tag_id}",
        headers=auth_headers,
        json={"name": "Ready for shift", "active": True},
    )
    assert restore.status_code == 200
    with client.app.state.database.session_factory() as db:
        assert db.get(Publication, uuid.UUID(post)).category_id == uuid.UUID(
            selection["category_id"]
        )

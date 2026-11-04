"""Feed projections stay bounded and expose only the authorized public summary."""

import uuid
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

from app.models import MediaAsset, MediaKind, Role, User, Workspace, WorkspaceMember
from app.social_features.models import (
    FacebookProfile,
    Publication,
    PublicationTag,
    PublicationTerm,
    Reaction,
    UserProfile,
)
from sqlalchemy import event


@contextmanager
def statements(engine):
    queries = []

    def record(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            queries.append(statement)

    event.listen(engine, "before_cursor_execute", record)
    try:
        yield queries
    finally:
        event.remove(engine, "before_cursor_execute", record)


def feed(client):
    with client.app.state.database.session_factory() as db:
        user = db.query(User).one()
        workspace = Workspace(name="Projection workspace", created_by_id=user.id)
        db.add(workspace)
        db.flush()
        db.add(
            WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=Role.ADMIN)
        )
        asset = MediaAsset(
            workspace_id=workspace.id,
            kind=MediaKind.IMAGE,
            mime_type="image/jpeg",
            original_bytes=b"original-must-not-be-read-by-the-feed",
            byte_size=36,
            sha256="a" * 64,
        )
        category = PublicationTerm(
            workspace_id=workspace.id,
            kind="category",
            name="Field work",
            name_key="field work",
        )
        tags = [
            PublicationTerm(
                workspace_id=workspace.id, kind="tag", name=name, name_key=name
            )
            for name in ("zebra", "alpha")
        ]
        db.add_all([asset, category, *tags])
        db.flush()
        db.add(
            UserProfile(
                user_id=user.id,
                avatar_media_id=asset.id,
                headline="Public headline",
                cv_bytes=b"private-resume-must-not-be-read-by-the-feed",
            )
        )
        db.add(
            FacebookProfile(
                user_id=user.id, picture_url="https://example.invalid/avatar"
            )
        )
        now = datetime.now(UTC)
        ids = []
        for i in range(30):
            post = Publication(
                workspace_id=workspace.id,
                owner_id=user.id,
                media_id=asset.id,
                category_id=category.id,
                caption=f"Publication {i}",
                published_at=now - timedelta(seconds=i),
            )
            db.add(post)
            db.flush()
            db.add_all(PublicationTag(post_id=post.id, term_id=tag.id) for tag in tags)
            if i % 2 == 0:
                db.add(Reaction(post_id=post.id, user_id=user.id))
            ids.append(str(post.id))
        db.commit()
        return str(workspace.id), str(user.id), ids


def test_gallery_query_count_is_independent_of_page_size(client, auth_headers):
    workspace, user, ids = feed(client)
    engine = client.app.state.database.engine
    with statements(engine) as one_queries:
        one = client.get(
            f"/v1/gallery/page?workspace_id={workspace}&limit=1", headers=auth_headers
        )
    with statements(engine) as page_queries:
        page = client.get(
            f"/v1/gallery/page?workspace_id={workspace}&limit=30", headers=auth_headers
        )
    assert one.status_code == page.status_code == 200
    assert len(one_queries) == len(page_queries)
    assert len(page_queries) <= 9
    assert all("media_assets.original_bytes" not in sql for sql in page_queries)
    assert all("user_profiles.cv_bytes" not in sql for sql in page_queries)
    items = page.json()["items"]
    assert [item["id"] for item in items] == ids
    assert page.json()["next_cursor"] is None
    for i, item in enumerate(items):
        assert item["likes"] == int(i % 2 == 0)
        assert item["liked"] is (i % 2 == 0)
        assert item["category"]["name"] == "Field work"
        assert [tag["name"] for tag in item["tags"]] == ["alpha", "zebra"]
        assert item["owner"] == {
            "user_id": user,
            "display_name": "Admin Demo",
            "picture_url": f"/v1/profiles/{user}/avatar",
            "headline": "Public headline",
        }
    next_page = client.get(
        f"/v1/gallery/page?workspace_id={workspace}&limit=30&cursor={one.json()['next_cursor']}",
        headers=auth_headers,
    )
    assert [item["id"] for item in next_page.json()["items"]] == ids[1:]


def test_gallery_owner_summary_preserves_avatar_fallback(client, auth_headers):
    workspace, user, _ = feed(client)
    with client.app.state.database.session_factory() as db:
        db.get(UserProfile, uuid.UUID(user)).avatar_media_id = None
        db.commit()
    item = client.get(
        f"/v1/gallery/page?workspace_id={workspace}&limit=1", headers=auth_headers
    ).json()["items"][0]
    assert item["owner"]["picture_url"] == "https://example.invalid/avatar"
    assert "email" not in item["owner"]

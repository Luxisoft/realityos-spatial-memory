"""Identity references stay internal while app publications remain usable."""

import io
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from app.models import (
    CaptureSession,
    MediaAsset,
    MediaKind,
    Role,
    User,
    Workspace,
    WorkspaceMember,
)
from app.social_features.evidence_models import PublicationDuplicate
from app.social_features.models import Publication, UserProfile
from app.social_features.upload_service import duplicate
from PIL import Image
from sqlalchemy import select


def reference_fixture(client):
    output = io.BytesIO()
    Image.new("RGB", (48, 64), "blue").save(output, "PNG")
    raw = output.getvalue()
    with client.app.state.database.session_factory() as db:
        owner = db.scalar(select(User))
        space = Workspace(name="home:visibility", created_by_id=owner.id)
        db.add(space)
        db.flush()
        db.add(
            WorkspaceMember(workspace_id=space.id, user_id=owner.id, role=Role.ADMIN)
        )
        capture = CaptureSession(workspace_id=space.id, created_by_id=owner.id)
        db.add(capture)
        db.flush()
        asset = MediaAsset(
            workspace_id=space.id,
            capture_session_id=capture.id,
            kind=MediaKind.IMAGE,
            mime_type="image/png",
            original_bytes=raw,
            sha256="a" * 64,
            byte_size=len(raw),
            extra_metadata={"origin": "facebook-import"},
        )
        db.add(asset)
        db.flush()
        db.add(UserProfile(user_id=owner.id, avatar_media_id=asset.id))
        posts = []
        for index, source in enumerate(("facebook", "local", "simulator", "local")):
            post = Publication(
                owner_id=owner.id,
                media_id=asset.id,
                source=source,
                audience="home",
                caption=f"post-{index}",
                published_at=datetime.now(UTC) - timedelta(minutes=index),
            )
            db.add(post)
            posts.append(post)
        db.commit()
        return str(owner.id), str(asset.id), [str(p.id) for p in posts], raw


def test_references_filtered_before_cursor_pagination(client, auth_headers):
    owner, _, posts, _ = reference_fixture(client)
    page = client.get(
        f"/v1/profiles/{owner}/media?limit=1", headers=auth_headers
    ).json()
    assert [p["id"] for p in page["items"]] == [posts[1]]
    assert page["next_cursor"]
    page2 = client.get(
        f"/v1/profiles/{owner}/media?limit=1&cursor={page['next_cursor']}",
        headers=auth_headers,
    ).json()
    assert [p["id"] for p in page2["items"]] == [posts[3]]
    assert page2["next_cursor"] is None
    feed = client.get("/v1/gallery", headers=auth_headers).json()
    cursor_feed = client.get("/v1/gallery/page", headers=auth_headers).json()["items"]
    assert {p["id"] for p in feed} == {posts[1], posts[3]}
    assert {p["id"] for p in cursor_feed} == {posts[1], posts[3]}


@pytest.mark.parametrize("source_index", [0, 2])
def test_reference_urls_and_actions_unavailable_even_to_owner(
    client, auth_headers, source_index
):
    _, _, posts, _ = reference_fixture(client)
    post = posts[source_index]
    for suffix in ("media", "thumbnail", "boxed", "comments"):
        assert (
            client.get(f"/v1/gallery/{post}/{suffix}", headers=auth_headers).status_code
            == 404
        )
    assert (
        client.post(
            f"/v1/gallery/{post}/share",
            headers=auth_headers,
            json={"audience": "public"},
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/v1/display/media-links",
            headers=auth_headers,
            json={"kind": "publication", "resource_id": post},
        ).status_code
        == 404
    )


def test_reference_raw_media_denied_avatar_and_explicit_copy_preserved(
    client, auth_headers
):
    owner, asset, posts, raw = reference_fixture(client)
    # An independently published copy remains usable.
    assert (
        client.get(f"/v1/gallery/{posts[1]}/media", headers=auth_headers).content == raw
    )
    with client.app.state.database.session_factory() as db:
        for key in (posts[1], posts[3]):
            db.get(Publication, uuid.UUID(key)).hidden = True
        parent = db.get(MediaAsset, uuid.UUID(asset))
        frame = MediaAsset(
            workspace_id=parent.workspace_id,
            capture_session_id=parent.capture_session_id,
            parent_asset_id=parent.id,
            kind=MediaKind.IMAGE,
            mime_type="image/png",
            original_bytes=raw,
            sha256="b" * 64,
            byte_size=len(raw),
        )
        db.add(frame)
        db.commit()
        frame_id = str(frame.id)
    assert client.get(f"/v1/media/{frame_id}", headers=auth_headers).status_code == 404
    assert client.get(f"/v1/media/{asset}", headers=auth_headers).status_code == 404
    assert (
        client.get(f"/v1/media/{asset}/highlighted", headers=auth_headers).status_code
        == 404
    )
    assert (
        client.get(f"/v1/profiles/{owner}/avatar", headers=auth_headers).content == raw
    )
    # Filtering is non-destructive.
    with client.app.state.database.session_factory() as db:
        assert db.get(MediaAsset, uuid.UUID(asset)).original_bytes == raw
        assert db.get(Publication, uuid.UUID(posts[0])).hidden is False


def test_reference_alias_cannot_bypass_visibility(client, auth_headers):
    _, _, posts, _ = reference_fixture(client)
    with client.app.state.database.session_factory() as db:
        db.add(
            PublicationDuplicate(
                post_id=uuid.UUID(posts[0]),
                canonical_id=uuid.UUID(posts[1]),
            )
        )
        db.commit()
    assert (
        client.get(f"/v1/gallery/{posts[0]}/media", headers=auth_headers).status_code
        == 404
    )


def test_references_excluded_from_retrieval_and_duplicate_candidates(
    client, auth_headers
):
    from app.gallery_index import _visible_scope
    from app.social_features.profiles import _profile_search_text

    owner_id, _, posts, raw = reference_fixture(client)
    with client.app.state.database.session_factory() as db:
        owner = db.get(User, uuid.UUID(owner_id))
        for key in (posts[1], posts[3]):
            db.get(Publication, uuid.UUID(key)).hidden = True
        db.flush()
        assert all(
            p.source not in ("facebook", "simulator")
            for p in db.scalars(_visible_scope(owner, None, None))
        )
        _, _, matches = _profile_search_text(owner, owner, db)
        assert matches == []

        class Comparison:
            def compare_gallery_images(self, image, candidates):
                assert candidates == []

        assert duplicate(db, Comparison(), raw, owner.id, "home", None) is None


def test_work_demo_is_visible_only_to_members_and_references_stay_internal(
    client, auth_headers
):
    from app.security import create_access_token, hash_password

    owner_id, asset_id, posts, _ = reference_fixture(client)
    with client.app.state.database.session_factory() as db:
        owner = db.get(User, uuid.UUID(owner_id))
        group = Workspace(name="Demo workshop", created_by_id=owner.id)
        other = User(
            email="outsider@visibility.test",
            display_name="Other",
            password_hash=hash_password("test-password-1234"),
        )
        db.add_all([group, other])
        db.flush()
        db.add(
            WorkspaceMember(workspace_id=group.id, user_id=owner.id, role=Role.ADMIN)
        )
        for key in (posts[0], posts[2]):
            post = db.get(Publication, uuid.UUID(key))
            post.audience = "work"
            post.workspace_id = group.id
        demo = Publication(
            owner_id=owner.id,
            media_id=uuid.UUID(asset_id),
            audience="work",
            workspace_id=group.id,
            source="simulator-work",
        )
        db.add(demo)
        db.commit()
        group_id, demo_id, other_id = str(group.id), str(demo.id), other.id
        other_headers = {
            "Authorization": "Bearer "
            + create_access_token(other.id, client.app.state.settings)
        }
    url = f"/v1/gallery/page?audience=work&workspace_id={group_id}"
    assert [p["id"] for p in client.get(url, headers=auth_headers).json()["items"]] == [
        demo_id
    ]
    assert client.get(url, headers=other_headers).status_code == 403
    assert (
        client.get(f"/v1/gallery/{demo_id}/media", headers=other_headers).status_code
        == 403
    )
    with client.app.state.database.session_factory() as db:
        db.add(
            WorkspaceMember(
                workspace_id=uuid.UUID(group_id), user_id=other_id, role=Role.QUERY
            )
        )
        db.commit()
    assert [
        p["id"] for p in client.get(url, headers=other_headers).json()["items"]
    ] == [demo_id]
    assert (
        client.get(f"/v1/gallery/{posts[0]}/media", headers=other_headers).status_code
        == 404
    )


def test_reference_indexing_never_runs_the_object_provider(client, auth_headers):
    from app.gallery_index import index_publication

    _, _, posts, _ = reference_fixture(client)
    with client.app.state.database.session_factory() as db:
        # A provider object with no methods proves reference indexing exits before inference.
        for key in (posts[0], posts[2]):
            post = index_publication(db, uuid.UUID(key), object(), force=True)
            assert post.indexed_at is None

"""Owner-requested group publication, private enrollment and source lifecycle."""

import io

from app.faces import build_face_engine
from app.social_features.models import Publication
from PIL import Image


def photo(color):
    stream = io.BytesIO()
    Image.new("RGB", (120, 160), color).save(stream, "PNG")
    return stream.getvalue()


def single_faces(client, count):
    engine = build_face_engine(client.app.state.settings)
    found = []
    for i in range(255):
        raw = photo((i, 37, 91))
        if len(engine.detect_faces(raw)) == 1:
            found.append(raw)
        if len(found) == count:
            return found
    raise AssertionError("Missing deterministic fixtures")


def test_publication_requires_group_even_for_legacy_route(client, auth_headers):
    r = client.post(
        "/v1/me/publication-uploads",
        headers=auth_headers,
        data={"request_key": "orphan", "audience": "home"},
        files={"file": ("test.png", photo("blue"), "image/png")},
    )
    assert r.status_code == 422
    assert (
        client.post(
            "/v1/me/profile/publications",
            headers=auth_headers,
            files={"file": ("test.png", photo("blue"), "image/png")},
        ).status_code
        == 422
    )


def test_group_import_is_idempotent_and_retains_original(client, auth_headers):
    first = client.post(
        "/v1/groups", headers=auth_headers, json={"name": "First group"}
    ).json()["id"]
    second = client.post(
        "/v1/groups", headers=auth_headers, json={"name": "Second group"}
    ).json()["id"]
    post = client.post(
        "/v1/me/work-publications",
        headers=auth_headers,
        data={"workspace_id": first},
        files={"file": ("test.png", photo("blue"), "image/png")},
    )
    assert post.status_code == 200, post.text
    post_id = post.json()["id"]
    route = f"/v1/groups/{second}/publications/import"
    result = client.post(
        route, headers=auth_headers, json={"publication_ids": [post_id]}
    )
    assert result.status_code == 200, result.text
    copied = result.json()["items"][0]["id"]
    assert copied != post_id
    assert (
        client.post(
            route, headers=auth_headers, json={"publication_ids": [post_id]}
        ).json()["items"][0]["id"]
        == copied
    )
    with client.app.state.database.session_factory() as db:
        import uuid

        original = db.get(Publication, uuid.UUID(post_id))
        duplicate = db.get(Publication, uuid.UUID(copied))
        assert str(original.workspace_id) == first
        assert original.media_id == duplicate.media_id
    client.post(
        f"/v1/gallery/{post_id}/interactions",
        headers=auth_headers,
        json={"action": "comment", "text": "Original group comment"},
    )
    client.post(
        f"/v1/gallery/{copied}/interactions",
        headers=auth_headers,
        json={"action": "like"},
    )
    assert (
        client.get(f"/v1/gallery/{copied}/comments", headers=auth_headers).json() == []
    )
    assert (
        len(client.get(f"/v1/gallery/{post_id}/comments", headers=auth_headers).json())
        == 1
    )
    from app.gallery_index import _visible_scope
    from app.models import User, WorkspaceMember
    from sqlalchemy import delete

    with client.app.state.database.session_factory() as db:
        original = db.get(Publication, uuid.UUID(post_id))
        owner = db.get(User, original.owner_id)
        db.execute(
            delete(WorkspaceMember).where(
                WorkspaceMember.workspace_id == original.workspace_id,
                WorkspaceMember.user_id == owner.id,
            )
        )
        db.commit()
        assert (
            db.scalar(
                _visible_scope(owner, None, None).where(Publication.id == original.id)
            )
            is None
        )
    assert (
        client.get(f"/v1/gallery/{post_id}/media", headers=auth_headers).status_code
        == 403
    )
    assert (
        client.get(f"/v1/gallery/{copied}/media", headers=auth_headers).status_code
        == 200
    )


def test_enrollment_resumes_rejects_duplicates_and_hides_originals(
    client, auth_headers
):
    pictures = single_faces(client, 4)
    assert (
        client.post(
            "/v1/faces/reference-photos",
            headers=auth_headers,
            files={"file": ("ref.png", pictures[1], "image/png")},
        ).status_code
        == 403
    )
    client.post("/v1/faces/consent", headers=auth_headers, json={"confirm": True})
    avatar = client.post(
        "/v1/me/profile/avatar",
        headers=auth_headers,
        files={"file": ("avatar.png", pictures[0], "image/png")},
    )
    assert avatar.status_code == 200
    primary = client.post(
        "/v1/faces/profile-photo",
        headers=auth_headers,
        files={"file": ("primary.png", pictures[0], "image/png")},
    )
    assert primary.status_code == 201, primary.text
    assert (
        client.post("/v1/faces/setup/complete", headers=auth_headers).status_code == 409
    )
    for index, raw in enumerate(pictures[1:], 1):
        result = client.post(
            "/v1/faces/reference-photos",
            headers=auth_headers,
            files={"file": ("ref.png", raw, "image/png")},
        )
        assert result.status_code == 201, result.text
        assert result.json()["accepted_photos"] == index
    replay = client.post(
        "/v1/faces/reference-photos",
        headers=auth_headers,
        files={"file": ("ref.png", pictures[1], "image/png")},
    )
    assert replay.json()["duplicate"]
    assert replay.json()["accepted_photos"] == 3
    assert client.post("/v1/faces/setup/complete", headers=auth_headers).json()[
        "complete"
    ]
    assert client.get("/v1/faces/setup", headers=auth_headers).json()["complete"]
    media_id = primary.json()["media_id"]
    assert client.get(f"/v1/media/{media_id}", headers=auth_headers).status_code == 404
    enrollment = primary.json()["enrollment_ids"][0]
    assert (
        client.get(
            f"/v1/faces/enrollments/{enrollment}/thumbnail", headers=auth_headers
        ).status_code
        == 404
    )
    assert (
        client.get(avatar.json()["picture_url"], headers=auth_headers).status_code
        == 200
    )
    from app.social_features.models import UserProfile
    from sqlalchemy import select

    with client.app.state.database.session_factory() as db:
        profile = db.scalar(select(UserProfile))
        profile.avatar_media_id = None
        db.commit()
    fallback = client.get(avatar.json()["picture_url"], headers=auth_headers)
    assert (
        fallback.status_code == 200 and fallback.headers["content-type"] == "image/jpeg"
    )
    assert fallback.content != pictures[0]
    state = client.get("/v1/faces/setup", headers=auth_headers).json()
    removed = client.request(
        "DELETE", f"/v1/faces/reference-photos/{state['reference_ids'][0]}", headers=auth_headers
    )
    assert removed.status_code == 200 and not removed.json()["complete"]
    assert removed.json()["accepted_photos"] == 2

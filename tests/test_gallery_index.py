from __future__ import annotations

import io
import uuid

from app.meta import build_meta_client
from app.models import MediaAsset, MediaKind, Role, User, Workspace, WorkspaceMember
from app.services import media_sha256
from app.social import Publication
from PIL import Image


class _TwoFaceEngine:
    name = "stub"

    def detect_faces(self, image: bytes):
        return [object(), object()]


def _jpeg_bytes() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (16, 16), color=(200, 30, 30)).save(output, format="JPEG")
    return output.getvalue()


def _setup_workspace(db, email: str = "admin@example.test") -> tuple[User, Workspace]:
    from sqlalchemy import select

    user = db.scalar(select(User).where(User.email == email))
    workspace = Workspace(name=f"ws-{uuid.uuid4().hex}", created_by_id=user.id)
    db.add(workspace)
    db.flush()
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=Role.ADMIN))
    db.flush()
    return user, workspace


def _publish_image(
    db, owner: User, workspace: Workspace, caption: str = ""
) -> Publication:
    raw = _jpeg_bytes()
    asset = MediaAsset(
        workspace_id=workspace.id,
        kind=MediaKind.IMAGE,
        mime_type="image/jpeg",
        original_bytes=raw,
        sha256=media_sha256(raw),
        byte_size=len(raw),
    )
    db.add(asset)
    db.flush()
    post = Publication(
        owner_id=owner.id, media_id=asset.id, audience="home", caption=caption
    )
    db.add(post)
    db.flush()
    return post


def test_index_publication_extracts_ai_labels_and_faces(client):
    from app.gallery_index import index_publication

    app = client.app
    with app.state.database.session_factory() as db:
        user, workspace = _setup_workspace(db)
        post = _publish_image(db, user, workspace)
        post_id = post.id
        db.commit()
    with app.state.database.session_factory() as db:
        result = index_publication(
            db, post_id, build_meta_client(app.state.settings), _TwoFaceEngine()
        )
        db.commit()
        assert result is not None
        assert result.face_count == 2
        assert any("yellow drill" in label for label in result.ai_labels)
        assert "yellow drill" in result.search_text
        assert result.indexed_at is not None
        assert result.index_error is None
        assert result.ai_detections[0]["label"] == "yellow drill"
        assert result.ai_detections[0]["box"]["width"] > 0


def test_boxed_thumbnail_marks_matched_detection(client, auth_headers):
    from app.gallery_index import index_publication

    app = client.app
    with app.state.database.session_factory() as db:
        user, workspace = _setup_workspace(db)
        post = _publish_image(db, user, workspace)
        post_id = post.id
        db.commit()
    with app.state.database.session_factory() as db:
        index_publication(db, post_id, build_meta_client(app.state.settings))
        db.commit()
    plain = client.get(f"/v1/gallery/{post_id}/thumbnail", headers=auth_headers)
    assert plain.status_code == 200, plain.text
    boxed = client.get(
        f"/v1/gallery/{post_id}/boxed?labels=yellow%20drill", headers=auth_headers
    )
    assert boxed.status_code == 200, boxed.text
    assert boxed.headers["content-type"] == "image/jpeg"
    assert boxed.content != plain.content


def test_boxed_full_size_preserves_resolution_labels_and_original(client, auth_headers):
    with client.app.state.database.session_factory() as db:
        user, workspace = _setup_workspace(db)
        post = _publish_image(db, user, workspace)
        asset = db.get(MediaAsset, post.media_id)
        output = io.BytesIO()
        Image.new("RGB", (1200, 800), (200, 30, 30)).save(output, format="JPEG")
        original = output.getvalue()
        asset.original_bytes = original
        asset.sha256 = media_sha256(original)
        asset.byte_size = len(original)
        post.ai_detections = [
            {
                "label": "drill",
                "box": {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.25},
            },
            {
                "label": "hammer",
                "box": {"x": 0.65, "y": 0.2, "width": 0.2, "height": 0.25},
            },
        ]
        post_id, media_id = post.id, asset.id
        db.commit()
    url = f"/v1/gallery/{post_id}/boxed?labels=drill"
    preview = client.get(url, headers=auth_headers)
    full = client.get(url + "&full_size=true", headers=auth_headers)
    assert preview.status_code == full.status_code == 200
    assert Image.open(io.BytesIO(preview.content)).size == (360, 240)
    with Image.open(io.BytesIO(full.content)) as image:
        assert image.size == (1200, 800)
        red, green, blue = image.getpixel((122, 162))
        assert red > 210 and green > 150 and blue < 60  # Requested box is yellow.
        red, green, blue = image.getpixel((782, 162))
        assert red > 150 and green < 70 and blue < 70  # Other label stays unmarked.
    with client.app.state.database.session_factory() as db:
        assert db.get(MediaAsset, media_id).original_bytes == original


def test_boxed_full_size_enforces_workspace_access(client, auth_headers):
    from app.security import create_access_token

    with client.app.state.database.session_factory() as db:
        owner, workspace = _setup_workspace(db)
        post = _publish_image(db, owner, workspace)
        post.audience = "work"
        post.workspace_id = workspace.id
        stranger = User(
            email="boxed-other@example.test",
            display_name="Other",
            password_hash="unused",
        )
        db.add(stranger)
        db.flush()
        other_space = Workspace(name="Other workspace", created_by_id=stranger.id)
        db.add(other_space)
        db.flush()
        db.add(
            WorkspaceMember(
                workspace_id=other_space.id, user_id=stranger.id, role=Role.ADMIN
            )
        )
        other_headers = {
            "Authorization": "Bearer "
            + create_access_token(stranger.id, client.app.state.settings)
        }
        post_id = post.id
        db.commit()
    url = f"/v1/gallery/{post_id}/boxed?full_size=true"
    assert client.get(url, headers=auth_headers).status_code == 200
    assert client.get(url).status_code == 401
    assert client.get(url, headers=other_headers).status_code == 403


def test_gallery_search_matches_spanish_synonym_and_respects_visibility(client):
    from app.gallery_index import index_publication, search_gallery

    app = client.app
    with app.state.database.session_factory() as db:
        user, workspace = _setup_workspace(db)
        post = _publish_image(db, user, workspace)
        post_id = post.id
        stranger = User(
            email="stranger@example.test",
            display_name="Stranger",
            password_hash="x",
        )
        db.add(stranger)
        db.flush()
        stranger_post = Publication(
            owner_id=stranger.id,
            media_id=post.media_id,
            audience="home",
            caption="martillo",
        )
        db.add(stranger_post)
        db.commit()
    with app.state.database.session_factory() as db:
        post = index_publication(db, post_id, build_meta_client(app.state.settings))
        # Simulate an AI tag the mock understands as "hammer".
        post.ai_labels = ["hammer"]
        post.search_text = "hammer hand tool"
        db.commit()
    with app.state.database.session_factory() as db:
        from sqlalchemy import select

        viewer = db.scalar(select(User).where(User.email == "admin@example.test"))
        matches = search_gallery(
            db,
            viewer,
            "¿dónde está el martillo?",
            build_meta_client(app.state.settings),
        )
        assert [pub.id for pub, _ in matches] == [post_id]


def test_gallery_search_matches_near_tool_synonym(client):
    from app.gallery_index import index_publication, search_gallery

    app = client.app
    with app.state.database.session_factory() as db:
        user, workspace = _setup_workspace(db)
        post = _publish_image(db, user, workspace)
        post_id = post.id
        db.commit()
    with app.state.database.session_factory() as db:
        post = index_publication(db, post_id, build_meta_client(app.state.settings))
        post.ai_labels = ["crimping tool"]
        post.search_text = "crimping tool hand tool"
        db.commit()
    with app.state.database.session_factory() as db:
        from sqlalchemy import select

        viewer = db.scalar(select(User).where(User.email == "admin@example.test"))
        matches = search_gallery(
            db,
            viewer,
            "Hola, necesito que por favor me ayudes a buscar un alicate.",
            build_meta_client(app.state.settings),
        )
        assert [pub.id for pub, _ in matches] == [post_id]


def test_query_rejects_text_only_gallery_matches(client, auth_headers):
    from app.gallery_index import index_publication

    app = client.app
    with app.state.database.session_factory() as db:
        user, workspace = _setup_workspace(db)
        _publish_image(db, user, workspace, caption="taller")
        db.commit()
        workspace_id = workspace.id
    with app.state.database.session_factory() as db:
        stored = db.query(Publication).order_by(Publication.published_at.desc()).first()
        indexed = index_publication(
            db, stored.id, build_meta_client(app.state.settings)
        )
        indexed.ai_labels = ["hammer"]
        indexed.search_text = "taller hammer hand tool"
        db.commit()
    response = client.post(
        "/v1/queries",
        json={
            "workspace_id": str(workspace_id),
            "question": "martillo",
            "language": "es",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["found"] is False
    assert (
        payload["gallery_matches"] == []
    )  # Text tags alone cannot prove a localized hammer.

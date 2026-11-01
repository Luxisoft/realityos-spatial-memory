import io
import uuid

from app.models import (
    CaptureSession,
    MediaAsset,
    MediaKind,
    Role,
    User,
    Workspace,
    WorkspaceMember,
)
from app.security import create_access_token, hash_password
from app.social import Publication
from PIL import Image

from .support import (
    _range_fixture,
    _wav_bytes,
)


def test_gallery_privacy_and_interactions(client, auth_headers):
    output = io.BytesIO()
    Image.new("RGB", (40, 30), "blue").save(output, format="PNG")
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).first()
        other = User(
            email="other@test.invalid",
            display_name="Other",
            password_hash=hash_password("password123456"),
        )
        db.add(other)
        db.flush()
        workspace = Workspace(name="Private", created_by_id=owner.id)
        db.add(workspace)
        db.flush()
        db.add(
            WorkspaceMember(
                workspace_id=workspace.id, user_id=owner.id, role=Role.ADMIN
            )
        )
        session = CaptureSession(workspace_id=workspace.id, created_by_id=owner.id)
        db.add(session)
        db.flush()
        asset = MediaAsset(
            workspace_id=workspace.id,
            capture_session_id=session.id,
            kind=MediaKind.IMAGE,
            mime_type="image/png",
            original_bytes=output.getvalue(),
            sha256="a" * 64,
            byte_size=5,
        )
        db.add(asset)
        db.flush()
        post = Publication(owner_id=owner.id, media_id=asset.id, audience="home")
        db.add(post)
        db.commit()
        post_id = str(post.id)
        other_headers = {
            "Authorization": "Bearer "
            + create_access_token(other.id, client.app.state.settings)
        }
    assert len(client.get("/v1/gallery", headers=auth_headers).json()) == 1
    preview = client.get(f"/v1/gallery/{post_id}/thumbnail", headers=auth_headers)
    assert preview.status_code == 200
    assert preview.headers["content-type"] == "image/jpeg"
    assert (
        client.get(
            f"/v1/gallery/{post_id}/thumbnail", headers=other_headers
        ).status_code
        == 404
    )
    prepared = client.post(
        "/v1/assistant",
        headers=auth_headers,
        json={"text": "publicar esta foto", "post_id": post_id},
    )
    assert prepared.json()["type"] == "confirm"
    assert client.get("/v1/gallery?audience=public", headers=other_headers).json() == []
    assert client.get("/v1/gallery", headers=other_headers).json() == []
    assert (
        client.get(f"/v1/gallery/{post_id}/media", headers=other_headers).status_code
        == 404
    )
    assert (
        client.post(
            f"/v1/gallery/{post_id}/interactions",
            headers=other_headers,
            json={"action": "like"},
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/v1/gallery/{post_id}/interactions",
            headers=auth_headers,
            json={"action": "comment", "text": "hello", "parent_id": str(uuid.uuid4())},
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/v1/gallery/{post_id}/interactions",
            headers=auth_headers,
            json={"action": "comment", "text": "hello"},
        ).status_code
        == 200
    )
    assert (
        len(client.get(f"/v1/gallery/{post_id}/comments", headers=auth_headers).json())
        == 1
    )
    group = client.post(
        "/v1/groups", headers=auth_headers, json={"name": "Team"}
    ).json()["id"]
    code = client.post(f"/v1/groups/{group}/invite", headers=auth_headers).json()[
        "code"
    ]
    assert (
        client.post(
            "/v1/groups/join", headers=other_headers, json={"code": code}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/v1/groups/join", headers=other_headers, json={"code": code}
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/v1/gallery/{post_id}/share",
            headers=auth_headers,
            json={"audience": "work", "workspace_id": group},
        ).status_code
        == 200
    )
    assert (
        len(client.get("/v1/gallery?audience=work", headers=other_headers).json()) == 1
    )
    assert (
        client.post(f"/v1/groups/{group}/invite", headers=other_headers).status_code
        == 403
    )
    members = client.get(f"/v1/groups/{group}/members", headers=auth_headers).json()
    member_id = next(m["id"] for m in members if not m["self"])
    assert (
        client.post(
            f"/v1/groups/{group}/members/{member_id}/remove", headers=auth_headers
        ).status_code
        == 200
    )
    assert client.get("/v1/gallery?audience=work", headers=other_headers).json() == []
    assert (
        client.get(f"/v1/gallery/{post_id}/media", headers=other_headers).status_code
        == 403
    )
    assert (
        client.get("/v1/moderation/reports", headers=other_headers).status_code == 403
    )


def test_gallery_media_range_inline_and_chunked(client, auth_headers):
    fixture = _range_fixture(client, auth_headers)
    inline_body = fixture["inline_body"]
    total = len(inline_body)

    full = client.get(
        f"/v1/gallery/{fixture['inline_post']}/media", headers=auth_headers
    )
    assert full.status_code == 200
    assert full.headers["accept-ranges"] == "bytes"
    assert full.content == inline_body

    def ranged(post_id, value, headers=None):
        merged = dict(auth_headers)
        if headers:
            merged.update(headers)
        merged["Range"] = value
        return client.request("GET", f"/v1/gallery/{post_id}/media", headers=merged)

    first = ranged(fixture["inline_post"], "bytes=0-99")
    assert first.status_code == 206
    assert first.headers["content-range"] == f"bytes 0-99/{total}"
    assert first.headers["accept-ranges"] == "bytes"
    assert first.content == inline_body[0:100]

    tail = ranged(fixture["inline_post"], "bytes=100-")
    assert tail.status_code == 206
    assert tail.headers["content-range"] == f"bytes 100-{total - 1}/{total}"
    assert tail.content == inline_body[100:]

    suffix = ranged(fixture["inline_post"], "bytes=-50")
    assert suffix.status_code == 206
    assert suffix.headers["content-range"] == f"bytes {total - 50}-{total - 1}/{total}"
    assert suffix.content == inline_body[-50:]

    outside = ranged(fixture["inline_post"], f"bytes={total}-")
    assert outside.status_code == 416
    assert outside.headers["content-range"] == f"bytes */{total}"

    chunked_total = sum(len(part) for part in fixture["chunk_bodies"])
    within = ranged(fixture["chunked_post"], "bytes=10-19")
    assert within.status_code == 206
    assert within.headers["content-range"] == f"bytes 10-19/{chunked_total}"
    assert within.content == bytes([0]) * 10

    across = ranged(fixture["chunked_post"], "bytes=90-209")
    assert across.status_code == 206
    assert across.headers["content-range"] == f"bytes 90-209/{chunked_total}"
    assert across.content == bytes([0]) * 10 + bytes([1]) * 100 + bytes([2]) * 10


def test_gallery_media_work_post_is_denied_to_outsiders(client, auth_headers):
    fixture = _range_fixture(client, auth_headers)
    assert (
        client.get(
            f"/v1/gallery/{fixture['chunked_post']}/media",
            headers=fixture["outsider_headers"],
        ).status_code
        == 403
    )
    assert (
        client.request(
            "GET",
            f"/v1/gallery/{fixture['chunked_post']}/media",
            headers={**fixture["outsider_headers"], "Range": "bytes=0-9"},
        ).status_code
        == 403
    )


def test_voice_note_transcription_is_mock_labelled(client, auth_headers):
    response = client.post(
        "/v1/notes/transcribe",
        headers=auth_headers,
        files={"audio": ("nota.wav", _wav_bytes(), "audio/wav")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["simulated"] is True
    assert response.json()["text"]

    rejected = client.post(
        "/v1/notes/transcribe",
        headers=auth_headers,
        files={"audio": ("nota.txt", b"not audio", "text/plain")},
    )
    assert rejected.status_code == 415, rejected.text

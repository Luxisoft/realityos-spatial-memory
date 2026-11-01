import io
import zipfile

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


def _docx_cv(text: str) -> bytes:
    output = io.BytesIO()
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>"
    )
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", document)
    return output.getvalue()


def _facebook_png(color: str) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (64, 48), color).save(output, format="PNG")
    return output.getvalue()


def _mock_facebook_graph(monkeypatch, photos, videos, posts=None):
    import time

    import httpx

    profile = {
        "id": "sync-subject",
        "name": "Sync User",
        "email": "sync@example.test",
        "birthday": "01/02/1990",
        "age_range": {"min": 21},
        "gender": "female",
        "hometown": {"name": "Lima"},
        "location": {"name": "Madrid"},
        "link": "https://facebook.invalid/sync",
        "picture": {"data": {"url": "https://cdn.invalid/avatar.jpg"}},
    }

    async def provider_get(self, url, **kwargs):
        if url.endswith("debug_token"):
            payload = {
                "data": {
                    "is_valid": True,
                    "app_id": "sync-app",
                    "user_id": "sync-subject",
                    "expires_at": int(time.time()) + 3600,
                    "scopes": ["public_profile", "email", "user_photos", "user_videos"],
                }
            }
        elif url.endswith("/me/friends"):
            payload = {"summary": {"total_count": 12}}
        elif url.endswith("/me/likes"):
            payload = {"summary": {"total_count": 34}}
        elif url.endswith("/me/photos"):
            if kwargs.get("params", {}).get("limit") == 0:
                payload = {"summary": {"total_count": len(photos)}}
            else:
                payload = {"data": photos}
        elif url.endswith("/me/videos"):
            if kwargs.get("params", {}).get("limit") == 0:
                payload = {"summary": {"total_count": len(videos)}}
            else:
                payload = {"data": videos}
        elif url.endswith("/me/posts"):
            payload = {"data": posts or []}
        elif url.endswith("/me"):
            payload = dict(profile)
        else:
            raise AssertionError(f"unexpected graph url {url}")
        return httpx.Response(200, json=payload, request=httpx.Request("GET", url))

    def provider_download(self, url, **kwargs):
        color = "black" if "/p1.jpg" in url else "teal"
        return httpx.Response(
            200,
            content=_facebook_png(color),
            headers={"Content-Type": "application/octet-stream"},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", provider_get)
    monkeypatch.setattr(httpx.Client, "get", provider_download)
    return profile


def _range_fixture(client, auth_headers):
    from app.models import MediaAssetChunk
    from app.services import CHUNKED_POSTGRES_BYTEA

    inline_body = bytes(range(256)) * 4
    chunk_bodies = [bytes([index]) * 100 for index in range(3)]
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).first()
        other = User(
            email="range-outsider@test.invalid",
            display_name="Range Outsider",
            password_hash=hash_password("password123456"),
        )
        db.add(other)
        db.flush()
        workspace = Workspace(name="Range Group", created_by_id=owner.id)
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
        inline = MediaAsset(
            workspace_id=workspace.id,
            capture_session_id=session.id,
            kind=MediaKind.IMAGE,
            mime_type="image/jpeg",
            original_bytes=inline_body,
            sha256="b" * 64,
            byte_size=len(inline_body),
        )
        db.add(inline)
        db.flush()
        chunked = MediaAsset(
            workspace_id=workspace.id,
            capture_session_id=session.id,
            kind=MediaKind.VIDEO,
            mime_type="video/mp4",
            original_bytes=b"",
            sha256="c" * 64,
            byte_size=sum(len(part) for part in chunk_bodies),
            extra_metadata={"storage": CHUNKED_POSTGRES_BYTEA},
        )
        db.add(chunked)
        db.flush()
        for position, part in enumerate(chunk_bodies):
            db.add(
                MediaAssetChunk(
                    asset_id=chunked.id,
                    chunk_index=position,
                    content=part,
                    byte_size=len(part),
                )
            )
        inline_post = Publication(
            owner_id=owner.id, media_id=inline.id, audience="public"
        )
        chunked_post = Publication(
            owner_id=owner.id,
            media_id=chunked.id,
            audience="work",
            workspace_id=workspace.id,
        )
        db.add(inline_post)
        db.add(chunked_post)
        db.commit()
        outsider_headers = {
            "Authorization": "Bearer "
            + create_access_token(other.id, client.app.state.settings)
        }
        return {
            "inline_body": inline_body,
            "chunk_bodies": chunk_bodies,
            "inline_post": str(inline_post.id),
            "chunked_post": str(chunked_post.id),
            "outsider_headers": outsider_headers,
        }


def _wav_bytes() -> bytes:
    import struct

    frames = b"\x00" * 1600
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + len(frames),
        b"WAVE",
        b"fmt ",
        16,
        1,
        1,
        16000,
        32000,
        2,
        16,
        b"data",
        len(frames),
    )
    return header + frames


def _guest_headers(client, device_id="pin-guest-device"):
    response = client.post("/v1/auth/guest", json={"device_id": device_id})
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def _guest_id(client, headers):
    own = client.get("/v1/me/profile", headers=headers)
    assert own.status_code == 200, own.text
    return own.json()["user_id"]


def _work_post(client, headers, workspace_id, color):
    output = io.BytesIO()
    Image.new("RGB", (32, 24), color).save(output, format="PNG")
    response = client.post(
        "/v1/me/work-publications",
        headers=headers,
        files={"file": ("post.png", output.getvalue(), "image/png")},
        data={"workspace_id": workspace_id},
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _group_member_ids(client, auth_headers, workspace_id):
    response = client.get(f"/v1/groups/{workspace_id}/members", headers=auth_headers)
    assert response.status_code == 200, response.text
    return {row["id"]: row for row in response.json()}


def _chat_append(client, headers, role, text, kind="text", evidence_url=None):
    payload = {"role": role, "kind": kind, "text": text}
    if evidence_url:
        payload["evidence_url"] = evidence_url
    response = client.post("/v1/chat/append", headers=headers, json=payload)
    assert response.status_code == 200, response.text
    return response.json()["id"]

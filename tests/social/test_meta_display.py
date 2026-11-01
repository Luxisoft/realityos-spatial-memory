"""Meta Display sources, scoped images and reviewed MP4 publications."""

import hashlib
import io
import subprocess
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from app.models import MediaAsset, MediaKind, Role, User, Workspace, WorkspaceMember
from app.security import create_access_token, hash_password
from app.social_features.evidence_models import GalleryEvidence, PublicationUpload
from app.social_features.models import Publication
from PIL import Image
from sqlalchemy import select

from .test_evidence_uploads import photo, upload


def outsider(client):
    with client.app.state.database.session_factory() as db:
        user = User(
            email=f"{uuid.uuid4()}@example.test",
            display_name="Other",
            password_hash="unused",
        )
        db.add(user)
        db.commit()
        return {
            "Authorization": "Bearer "
            + create_access_token(user.id, client.app.state.settings)
        }


def group(client, headers):
    response = client.post(
        "/v1/groups", headers=headers, json={"name": "Display workshop"}
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def link(client, headers, kind, resource, **fields):
    return client.post(
        "/v1/display/media-links",
        headers=headers,
        json={"kind": kind, "resource_id": str(resource), **fields},
    )


def test_display_images_are_scoped_and_expire(client, auth_headers):
    first = upload(client, auth_headers).json()
    with client.app.state.database.session_factory() as db:
        evidence = db.scalar(select(GalleryEvidence))
        eid, labels = evidence.id, [d["label"] for d in evidence.detections]
    response = link(client, auth_headers, "evidence", eid, labels=labels)
    assert response.status_code == 200, response.text
    url = response.json()["url"]
    image = client.get(url)
    assert image.status_code == 200
    assert image.headers["cache-control"] == "private, no-store"
    assert image.headers["referrer-policy"] == "no-referrer"
    with Image.open(io.BytesIO(image.content)) as picture:
        assert picture.size == (600, 280)
        picture.verify()
    other = outsider(client)
    for kind, resource in [
        ("evidence", eid),
        ("upload", first["id"]),
        ("publication", first["result_id"]),
    ]:
        assert link(client, other, kind, resource, labels=labels).status_code == 404
        assert link(client, {}, kind, resource, labels=labels).status_code == 401
        assert (
            link(client, auth_headers, kind, resource, labels=labels).status_code == 200
        )
    assert (
        link(client, auth_headers, "evidence", eid, labels=["not stored"]).status_code
        == 404
    )
    settings = client.app.state.settings
    token = url.split("token=")[1]
    claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    claims["exp"] = datetime.now(UTC) - timedelta(seconds=1)
    expired = jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    assert client.get("/v1/display/media?token=" + expired).status_code == 404
    assert (
        client.get(
            "/v1/display/media?token=" + auth_headers["Authorization"].split()[1]
        ).status_code
        == 404
    )
    with client.app.state.database.session_factory() as db:
        db.get(Publication, uuid.UUID(first["result_id"])).hidden = True
        db.commit()
    assert client.get(url).status_code == 404


def test_display_rechecks_work_membership_and_user_activity(client, auth_headers):
    workspace = group(client, auth_headers)
    first = upload(client, auth_headers, audience="work", workspace_id=workspace).json()
    url = link(client, auth_headers, "upload", first["id"]).json()["url"]
    with client.app.state.database.session_factory() as db:
        db.delete(
            db.scalar(
                select(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == uuid.UUID(workspace)
                )
            )
        )
        db.commit()
    assert client.get(url).status_code == 403
    assert link(client, auth_headers, "upload", first["id"]).status_code == 403
    own = upload(client, auth_headers, raw=photo("blue")).json()
    url = link(client, auth_headers, "upload", own["id"]).json()["url"]
    with client.app.state.database.session_factory() as db:
        db.scalar(select(User)).is_active = False
        db.commit()
    assert client.get(url).status_code == 404


def test_search_scope_is_explicit_and_gallery_never_uses_registry(
    client, auth_headers, monkeypatch
):
    workspace = group(client, auth_headers)
    upload(client, auth_headers)

    def fail(*args, **kwargs):
        raise AssertionError("Registry must not run for a gallery query")

    with monkeypatch.context() as patch:
        patch.setattr("app.http.common.multilingual_object_candidates", fail)
        result = client.post(
            "/v1/queries",
            headers=auth_headers,
            json={
                "workspace_id": workspace,
                "question": "yellow drill",
                "search_scope": "gallery",
            },
        )
        assert result.status_code == 200, result.text
        assert result.json()["gallery_matches"]
    with monkeypatch.context() as patch:
        patch.setattr("app.http.common._gallery_answer", fail)
        result = client.post(
            "/v1/queries",
            headers=auth_headers,
            json={
                "workspace_id": workspace,
                "question": "yellow drill",
                "search_scope": "registry",
            },
        )
        assert result.status_code == 200, result.text
        assert not result.json()["found"] and result.json()["gallery_matches"] == []
    assert (
        client.post(
            "/v1/queries",
            headers=outsider(client),
            json={
                "workspace_id": workspace,
                "question": "yellow drill",
                "search_scope": "gallery",
            },
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/v1/queries",
            headers=auth_headers,
            json={
                "workspace_id": workspace,
                "question": "yellow drill",
                "search_scope": "other",
            },
        ).status_code
        == 422
    )


@pytest.fixture
def clip(tmp_path):
    path = tmp_path / "synthetic.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=red:s=160x120:r=2",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=mono",
            "-t",
            "1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(path),
        ],
        check=True,
        capture_output=True,
        timeout=20,
    )
    return path.read_bytes()


def video_upload(client, headers, clip, key=None, **fields):
    return client.post(
        "/v1/me/publication-uploads",
        headers=headers,
        data={"request_key": key or str(uuid.uuid4()), **fields},
        files={"file": ("capture.mp4", clip, "video/mp4")},
    )


@pytest.mark.parametrize("audience", ["home", "work"])
def test_reviewed_video_original_frames_and_idempotent_replacement(
    client, auth_headers, clip, audience
):
    fields = {"audience": audience}
    if audience == "work":
        fields["workspace_id"] = group(client, auth_headers)
    key = str(uuid.uuid4())
    response = video_upload(client, auth_headers, clip, key=key, **fields)
    assert response.status_code == 202, response.text
    first = response.json()
    assert first["status"] == "published", first
    assert (
        video_upload(client, auth_headers, clip, key=key, **fields).json()["id"]
        == first["id"]
    )
    with client.app.state.database.session_factory() as db:
        post = db.get(Publication, uuid.UUID(first["result_id"]))
        asset = db.get(MediaAsset, post.media_id)
        assert asset.kind == MediaKind.VIDEO and asset.original_bytes == clip
        assert asset.sha256 == hashlib.sha256(clip).hexdigest()
        evidence = db.scalar(
            select(GalleryEvidence).where(GalleryEvidence.post_id == post.id)
        )
        assert evidence.frame_timestamp_ms == 0 and evidence.detections
        old_media = post.media_id
    spaces = client.get("/v1/workspaces", headers=auth_headers).json()
    workspace = fields.get("workspace_id", spaces[0]["id"])
    result = client.post(
        "/v1/queries",
        headers=auth_headers,
        json={
            "workspace_id": workspace,
            "question": "yellow drill",
            "search_scope": "gallery",
        },
    )
    assert result.status_code == 200, result.text
    matches = result.json()["gallery_matches"]
    assert matches and matches[0]["mime_type"] == "video/mp4"
    assert matches[0]["frame_timestamp_ms"] == 0
    assert (
        link(
            client,
            auth_headers,
            "evidence",
            matches[0]["evidence_id"],
            labels=matches[0]["matched_labels"],
        ).status_code
        == 200
    )
    second = video_upload(client, auth_headers, clip, **fields).json()
    assert (
        second["status"] == "duplicate" and second["duplicate_id"] == first["result_id"]
    )
    assert client.get(second["preview_url"], headers=auth_headers).status_code == 200
    assert (
        client.get(
            link(client, auth_headers, "upload", second["id"]).json()["url"]
        ).status_code
        == 200
    )
    result = client.post(
        f"/v1/me/publication-uploads/{second['id']}/confirm", headers=auth_headers
    )
    assert result.status_code == 200, result.text
    assert result.json()["result_id"] == first["result_id"]
    with client.app.state.database.session_factory() as db:
        assert db.get(Publication, uuid.UUID(first["result_id"])).media_id != old_media
        assert db.get(MediaAsset, old_media).original_bytes == clip


def test_video_validation_permissions_and_cancellation(
    client, auth_headers, clip, monkeypatch
):
    assert video_upload(client, {}, clip).status_code == 401
    assert video_upload(client, auth_headers, b"not mp4").status_code == 422
    settings = client.app.state.settings
    monkeypatch.setattr(settings, "max_video_bytes", len(clip) - 1)
    assert video_upload(client, auth_headers, clip).status_code == 413
    monkeypatch.setattr(settings, "max_video_bytes", 0)
    monkeypatch.setattr(settings, "max_video_seconds", 0.5)
    assert video_upload(client, auth_headers, clip).status_code == 413
    monkeypatch.setattr(settings, "max_video_seconds", 120)
    workspace = group(client, auth_headers)
    assert (
        video_upload(
            client, outsider(client), clip, audience="work", workspace_id=workspace
        ).status_code
        == 403
    )
    monkeypatch.setattr(settings, "enqueue_processing", True)
    monkeypatch.setattr(
        "app.tasks.process_publication_upload.delay", lambda *args: None
    )
    pending = video_upload(
        client, auth_headers, clip, audience="work", workspace_id=workspace
    ).json()
    assert pending["status"] == "pending"
    client.post(
        f"/v1/me/publication-uploads/{pending['id']}/cancel", headers=auth_headers
    )
    from app.meta import build_meta_client
    from app.social_features.upload_service import process_upload

    with client.app.state.database.session_factory() as db:
        result = process_upload(
            db, uuid.UUID(pending["id"]), build_meta_client(settings)
        )
        assert result.status == "cancelled"
        assert db.scalar(select(Publication)) is None
        assert db.get(PublicationUpload, result.id).original_bytes == clip


def test_video_processing_failure_does_not_publish_and_can_retry(
    client, auth_headers, clip, monkeypatch
):
    from app.meta import MetaProviderError
    from app.social_features import video_uploads

    original = video_uploads.ground

    def fail(*args):
        raise MetaProviderError("Provider temporarily unavailable")

    monkeypatch.setattr(video_uploads, "ground", fail)
    failed = video_upload(client, auth_headers, clip).json()
    assert failed["status"] == "failed"
    assert client.get("/v1/gallery", headers=auth_headers).json() == []
    monkeypatch.setattr(video_uploads, "ground", original)
    retried = client.post(
        f"/v1/me/publication-uploads/{failed['id']}/retry", headers=auth_headers
    )
    assert retried.json()["status"] == "published", retried.text


def _face_pair(client, auth_headers):
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).first()
        other = User(
            email="face-display@test.invalid",
            display_name="Face Display",
            password_hash=hash_password("password123456"),
        )
        db.add(other)
        db.flush()
        workspace = Workspace(name="Face Display Team", created_by_id=owner.id)
        db.add(workspace)
        db.flush()
        db.add(
            WorkspaceMember(
                workspace_id=workspace.id, user_id=owner.id, role=Role.ADMIN
            )
        )
        db.add(
            WorkspaceMember(
                workspace_id=workspace.id, user_id=other.id, role=Role.QUERY
            )
        )
        db.commit()
        other_headers = {
            "Authorization": "Bearer "
            + create_access_token(other.id, client.app.state.settings)
        }
    for headers in (auth_headers, other_headers):
        consent = client.post(
            "/v1/faces/consent", headers=headers, json={"confirm": True}
        )
        assert consent.status_code == 200, consent.text
    return other_headers


def _face_enrollment_id(client, headers, color="green"):
    output = io.BytesIO()
    Image.new("RGB", (64, 48), color).save(output, format="PNG")
    enrolled = client.request(
        "POST",
        "/v1/faces/profile-photo",
        headers=headers,
        files={"file": ("face.png", output.getvalue(), "image/png")},
    )
    assert enrolled.status_code == 201, enrolled.text
    assert enrolled.json()["faces_enrolled"] >= 1
    return enrolled.json()["enrollment_ids"][0]


def test_display_face_enrollment_serves_match_thumbnail(client, auth_headers):
    other_headers = _face_pair(client, auth_headers)
    enrollment_id = _face_enrollment_id(client, other_headers)
    response = link(client, auth_headers, "face_enrollment", enrollment_id)
    assert response.status_code == 200, response.text
    image = client.get(response.json()["url"])
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/jpeg"
    with Image.open(io.BytesIO(image.content)) as picture:
        assert picture.size == (600, 280)
    assert (
        link(client, outsider(client), "face_enrollment", enrollment_id).status_code
        == 403
    )
    revoked = client.request("DELETE", "/v1/faces/consent", headers=other_headers)
    assert revoked.status_code == 200, revoked.text
    # Revoking wipes the owner's enrollments, so the match URL is gone too.
    assert (
        link(client, auth_headers, "face_enrollment", enrollment_id).status_code == 404
    )


def _group_marks():
    return [
        {
            "box": {"x": 0.1, "y": 0.1, "width": 0.3, "height": 0.8},
            "color": "#F0BF24",
            "number": 1,
        },
        {
            "box": {"x": 0.6, "y": 0.1, "width": 0.3, "height": 0.8},
            "color": "#22D3EE",
            "number": 2,
        },
    ]


def test_display_face_group_marks_probe_with_numbered_colors(client, auth_headers):
    import json as jsonlib

    probe = photo("red", (600, 280))
    response = client.request(
        "POST",
        "/v1/display/face-group-links",
        headers=auth_headers,
        data={"marks": jsonlib.dumps(_group_marks())},
        files={"probe": ("probe.jpg", probe, "image/jpeg")},
    )
    assert response.status_code == 200, response.text
    image = client.get(response.json()["url"])
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/jpeg"
    with Image.open(io.BytesIO(image.content)) as picture:
        assert picture.size == (600, 280)
        pixels = list(picture.convert("RGB").getdata())
        gold = sum(1 for r, g, b in pixels if r > 200 and 150 <= g <= 220 and b < 110)
        cyan = sum(1 for r, g, b in pixels if r < 110 and g > 150 and b > 200)
        assert gold > 50
        assert cyan > 50
    assert client.get("/v1/display/face-group?token=bogus").status_code == 404
    denied = client.request(
        "POST",
        "/v1/display/face-group-links",
        data={"marks": "[]"},
        files={"probe": ("probe.jpg", probe, "image/jpeg")},
    )
    assert denied.status_code == 401
    bad = client.request(
        "POST",
        "/v1/display/face-group-links",
        headers=auth_headers,
        data={
            "marks": jsonlib.dumps(
                [
                    {
                        "box": {"x": 9.0, "y": 0.0, "width": 0.1, "height": 0.1},
                        "color": "red",
                        "number": 1,
                    }
                ]
            )
        },
        files={"probe": ("probe.jpg", probe, "image/jpeg")},
    )
    assert bad.status_code == 422


def test_device_cannot_choose_human_gallery_source(client, auth_headers):
    workspace = group(client, auth_headers)
    enrolled = client.post(
        "/v1/admin/devices",
        headers=auth_headers,
        json={
            "workspace_id": workspace,
            "device_identifier": "meta-scope-test",
            "label": "Display",
        },
    )
    assert enrolled.status_code == 201, enrolled.text
    headers = {
        "X-RealityOS-Device-ID": "meta-scope-test",
        "X-RealityOS-Device-Key": enrolled.json()["device_key"],
    }
    result = client.post(
        "/v1/device/queries",
        headers=headers,
        json={
            "workspace_id": workspace,
            "question": "yellow drill",
            "search_scope": "gallery",
        },
    )
    assert result.status_code == 403
    assert (
        client.post(
            "/v1/device/queries",
            headers=headers,
            json={
                "workspace_id": workspace,
                "question": "yellow drill",
                "search_scope": "registry",
            },
        ).status_code
        == 200
    )

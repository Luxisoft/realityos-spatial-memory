from app.models import (
    MediaAsset,
    MediaKind,
    User,
)
from app.social import Publication

from .support import (
    _facebook_png,
    _guest_headers,
    _guest_id,
    _mock_facebook_graph,
    _work_post,
)


def test_facebook_requires_configuration(client):
    client.app.state.settings.facebook_app_id = None
    client.app.state.settings.facebook_app_secret = None
    assert (
        client.post("/v1/auth/facebook", json={"access_token": "invalid"}).status_code
        == 503
    )


def test_facebook_identity_is_verified_and_scoped_to_app(client, monkeypatch):
    import time

    import httpx
    from app.social import FacebookIdentity

    settings = client.app.state.settings
    settings.facebook_app_id = "new-app"
    settings.facebook_app_secret = "synthetic-test-secret"
    reported_app_id = "wrong-app"

    async def provider_get(self, url, **kwargs):
        if url.endswith("debug_token"):
            payload = {
                "data": {
                    "is_valid": True,
                    "app_id": reported_app_id,
                    "user_id": "synthetic-subject",
                    "expires_at": int(time.time()) + 3600,
                    "scopes": ["public_profile", "email", "user_photos"],
                }
            }
        elif url.endswith("/me"):
            payload = {"id": "synthetic-subject", "name": "Synthetic Facebook User"}
        elif url.endswith(("/me/friends", "/me/likes", "/me/photos", "/me/videos")):
            payload = {"data": [], "summary": {"total_count": 0}}
        elif url.endswith("/me/posts"):
            payload = {"data": []}
        else:
            raise AssertionError(f"unexpected graph url {url}")
        return httpx.Response(200, json=payload, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", provider_get)
    assert (
        client.post("/v1/auth/facebook", json={"access_token": "synthetic"}).status_code
        == 401
    )
    reported_app_id = "new-app"
    first = client.post("/v1/auth/facebook", json={"access_token": "synthetic"})
    second = client.post("/v1/auth/facebook", json={"access_token": "synthetic"})
    assert first.status_code == second.status_code == 200
    assert first.json()["granted_scopes"] == ["public_profile", "email", "user_photos"]
    assert (
        client.get(
            "/v1/auth/me",
            headers={"Authorization": "Bearer " + first.json()["access_token"]},
        ).status_code
        == 200
    )
    with client.app.state.database.session_factory() as db:
        assert db.get(FacebookIdentity, "new-app:synthetic-subject") is not None
        assert db.query(FacebookIdentity).count() == 1
    settings.facebook_app_id = "another-app"
    reported_app_id = "another-app"
    assert (
        client.post("/v1/auth/facebook", json={"access_token": "synthetic"}).status_code
        == 200
    )
    with client.app.state.database.session_factory() as db:
        assert db.query(FacebookIdentity).count() == 2


def test_facebook_login_syncs_profile_and_imports_photos(client, monkeypatch):
    from app.faces import FaceEnrollment
    from app.social import FacebookMedia, FacebookProfile

    photos = [
        {
            "id": f"photo-{index}",
            "created_time": "2024-05-01T10:00:00+0000",
            "name": f"Beach {index}",
            "images": [
                {
                    "source": f"https://cdn.invalid/p{index}.jpg",
                    "width": 64,
                    "height": 48,
                }
            ],
        }
        for index in range(2)
    ]
    photos.append(
        {
            "id": "photo-duplicate",
            "created_time": "2024-05-02T10:00:00+0000",
            "name": "Beach again",
            "images": [
                {"source": "https://cdn.invalid/p2.jpg", "width": 64, "height": 48}
            ],
        }
    )
    _mock_facebook_graph(monkeypatch, photos, [])
    settings = client.app.state.settings
    settings.facebook_app_id = "sync-app"
    settings.facebook_app_secret = "synthetic-test-secret"

    response = client.post("/v1/auth/facebook", json={"access_token": "synthetic"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["profile_synced"] is True
    assert body["import_status"] == "done"
    headers = {"Authorization": "Bearer " + body["access_token"]}

    with client.app.state.database.session_factory() as db:
        profile = db.query(FacebookProfile).one()
        user_id = str(profile.user_id)
        assert profile.email == "sync@example.test"
        assert profile.birthday == "01/02/1990"
        assert profile.age_min == 21
        assert profile.hometown == "Lima"
        assert profile.location == "Madrid"
        assert profile.profile_link == "https://facebook.invalid/sync"
        assert profile.picture_url == "https://cdn.invalid/avatar.jpg"
        assert profile.friends_count == 12
        assert profile.likes_count == 34
        assert profile.granted_scopes == [
            "public_profile",
            "email",
            "user_photos",
            "user_videos",
        ]
        # The profile picture is an avatar, not one of the bounded gallery photos.
        assert profile.imported_photos == 3
        assert profile.picture_imported is True
        assert db.query(FacebookMedia).count() == 3
        imported = [
            asset
            for asset in db.query(MediaAsset).all()
            if (asset.extra_metadata or {}).get("origin") == "facebook-import"
        ]
        assert len(imported) == 2
        assert (
            db.query(Publication).filter(Publication.source == "facebook").count() == 0
        )
        assert (
            db.query(FaceEnrollment)
            .filter(FaceEnrollment.source == "facebook-photo")
            .count()
            >= 2
        )

    own = client.get("/v1/me/facebook-profile", headers=headers)
    assert own.status_code == 200
    assert own.json()["email"] == "sync@example.test"
    assert own.json()["media"] == []
    assert own.json()["references_private"] is True
    assert "source_url" not in own.text
    page = client.get(f"/v1/profiles/{user_id}/media?limit=2", headers=headers)
    assert page.status_code == 200
    assert page.json()["items"] == []
    assert page.json()["next_cursor"] is None


def test_facebook_video_import_enrolls_from_frames(client, monkeypatch, tmp_path):
    import shutil
    import subprocess

    import httpx
    import pytest

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("ffmpeg and ffprobe are required for video import tests")
    output = tmp_path / "fb-clip.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=64x48:d=1",
            "-pix_fmt",
            "yuv420p",
            str(output),
        ],
        check=True,
    )
    clip = output.read_bytes()
    videos = [
        {
            "id": "video-1",
            "description": "Workshop clip",
            "source": "https://cdn.invalid/v1.mp4",
            "created_time": "2024-06-01T10:00:00+0000",
        }
    ]
    _mock_facebook_graph(monkeypatch, [], videos)

    def clip_download(self, url, **kwargs):
        return httpx.Response(200, content=clip, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.Client, "get", clip_download)
    settings = client.app.state.settings
    settings.facebook_app_id = "sync-app"
    settings.facebook_app_secret = "synthetic-test-secret"

    response = client.post("/v1/auth/facebook", json={"access_token": "synthetic"})
    assert response.status_code == 200, response.text
    assert response.json()["import_status"] == "done"

    from app.faces import FaceEnrollment
    from app.social import FacebookProfile

    with client.app.state.database.session_factory() as db:
        profile = db.query(FacebookProfile).one()
        assert profile.imported_videos == 1
        assert profile.videos_count == 1
        assert (
            db.query(MediaAsset).filter(MediaAsset.kind == MediaKind.FRAME).count() >= 1
        )
        assert (
            db.query(FaceEnrollment)
            .filter(FaceEnrollment.source == "facebook-video")
            .count()
            >= 1
        )


def test_facebook_login_syncs_posts(client, monkeypatch):
    from app.social import FacebookPost

    posts = [
        {
            "id": f"post-{index}",
            "message": f"Workshop notes {index}",
            "created_time": "2024-07-01T10:00:00+0000",
            "permalink_url": f"https://facebook.invalid/post-{index}",
        }
        for index in range(2)
    ]
    _mock_facebook_graph(monkeypatch, [], [], posts)
    settings = client.app.state.settings
    settings.facebook_app_id = "sync-app"
    settings.facebook_app_secret = "synthetic-test-secret"

    response = client.post("/v1/auth/facebook", json={"access_token": "synthetic"})
    assert response.status_code == 200, response.text
    headers = {"Authorization": "Bearer " + response.json()["access_token"]}
    with client.app.state.database.session_factory() as db:
        assert db.query(FacebookPost).count() == 2
    own = client.get("/v1/me/facebook-profile", headers=headers)
    assert len(own.json()["posts"]) == 2
    assert own.json()["posts"][0]["message"] == "Workshop notes 0"


def test_login_keeps_previous_selfie_but_imports_new_photos(client, monkeypatch):
    from app.faces import FaceEnrollment

    photos = [
        {
            "id": "stable-photo",
            "created_time": "2024-05-01T10:00:00+0000",
            "images": [{"source": "https://cdn.invalid/stable.jpg"}],
        }
    ]
    _mock_facebook_graph(monkeypatch, photos, [])
    settings = client.app.state.settings
    settings.facebook_app_id = "sync-app"
    settings.facebook_app_secret = "synthetic-test-secret"

    first = client.post("/v1/auth/facebook", json={"access_token": "synthetic"})
    assert first.status_code == 200
    headers = {"Authorization": "Bearer " + first.json()["access_token"]}
    assert (
        client.post(
            "/v1/faces/consent", headers=headers, json={"confirm": True}
        ).status_code
        == 200
    )
    capture = client.request(
        "POST",
        "/v1/faces/profile-photo",
        headers=headers,
        files={"file": ("face.png", _facebook_png("teal"), "image/png")},
    )
    assert capture.status_code == 201
    with client.app.state.database.session_factory() as db:
        user_id = db.query(User).filter(User.display_name == "Sync User").one().id
        assert (
            db.query(FaceEnrollment)
            .filter(
                FaceEnrollment.user_id == user_id, FaceEnrollment.source == "profile"
            )
            .count()
            >= 1
        )

    photos.append(
        {
            "id": "fresh-photo",
            "created_time": "2024-08-01T10:00:00+0000",
            "images": [{"source": "https://cdn.invalid/fresh.jpg"}],
        }
    )
    second = client.post("/v1/auth/facebook", json={"access_token": "synthetic"})
    assert second.status_code == 200
    assert second.json()["import_status"] == "done"
    with client.app.state.database.session_factory() as db:
        assert (
            db.query(FaceEnrollment)
            .filter(
                FaceEnrollment.user_id == user_id, FaceEnrollment.source == "profile"
            )
            .count()
            >= 1
        )
        fresh = [
            asset
            for asset in db.query(MediaAsset).all()
            if (asset.extra_metadata or {}).get("facebook_id") == "fresh-photo"
        ]
        assert len(fresh) == 1


def test_guest_login_creates_and_resumes_device_user(client):
    first = client.post("/v1/auth/guest", json={"device_id": "android-device-1"})
    assert first.status_code == 200, first.text
    assert first.json()["token_type"] == "bearer"
    assert first.json()["is_guest"] is True
    headers = {"Authorization": "Bearer " + first.json()["access_token"]}

    own = client.get("/v1/me/profile", headers=headers)
    assert own.status_code == 200, own.text
    assert own.json()["is_guest"] is True
    user_id = own.json()["user_id"]

    second = client.post("/v1/auth/guest", json={"device_id": "android-device-1"})
    assert second.status_code == 200, second.text
    again = client.get(
        "/v1/me/profile",
        headers={"Authorization": "Bearer " + second.json()["access_token"]},
    )
    assert again.json()["user_id"] == user_id

    other = client.post("/v1/auth/guest", json={"device_id": "android-device-2"})
    assert other.status_code == 200, other.text
    with client.app.state.database.session_factory() as db:
        guests = db.query(User).filter(User.is_guest.is_(True)).all()
        assert len(guests) == 2
        assert {guest.device_id for guest in guests} == {
            "android-device-1",
            "android-device-2",
        }


def test_facebook_login_records_device_binding(client, monkeypatch):
    import time

    import httpx

    settings = client.app.state.settings
    settings.facebook_app_id = "binding-app"
    settings.facebook_app_secret = "synthetic-test-secret"

    async def provider_get(self, url, **kwargs):
        if url.endswith("debug_token"):
            payload = {
                "data": {
                    "is_valid": True,
                    "app_id": "binding-app",
                    "user_id": "binding-subject",
                    "expires_at": int(time.time()) + 3600,
                    "scopes": [],
                }
            }
        elif url.endswith("/me"):
            payload = {"id": "binding-subject", "name": "Binding User"}
        elif url.endswith(("/me/friends", "/me/likes", "/me/photos", "/me/videos")):
            payload = {"data": [], "summary": {"total_count": 0}}
        elif url.endswith("/me/posts"):
            payload = {"data": []}
        else:
            raise AssertionError(f"unexpected graph url {url}")
        return httpx.Response(200, json=payload, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", provider_get)
    response = client.post(
        "/v1/auth/facebook",
        json={"access_token": "synthetic", "device_id": "meta-phone-9"},
    )
    assert response.status_code == 200, response.text
    headers = {"Authorization": "Bearer " + response.json()["access_token"]}
    assert client.get("/v1/me/profile", headers=headers).json()["is_guest"] is False
    with client.app.state.database.session_factory() as db:
        user = db.query(User).filter(User.display_name == "Binding User").one()
        assert user.device_id == "meta-phone-9"
        assert user.is_guest is False


def test_guest_profiles_see_only_self_and_guest_teammates(client, auth_headers):
    created = client.post(
        "/v1/groups", headers=auth_headers, json={"name": "Equipo mixto"}
    )
    pin = created.json()["join_pin"]
    guest1 = _guest_headers(client, "scope-guest-1")
    guest2 = _guest_headers(client, "scope-guest-2")
    assert (
        client.post(
            "/v1/groups/join-by-pin", headers=guest1, json={"pin": pin}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/v1/groups/join-by-pin", headers=guest2, json={"pin": pin}
        ).status_code
        == 200
    )
    with client.app.state.database.session_factory() as db:
        owner_id = str(db.query(User).first().id)
    guest2_id = _guest_id(client, guest2)

    assert client.get(f"/v1/profiles/{owner_id}", headers=guest1).status_code == 404
    assert client.get(f"/v1/profiles/{guest2_id}", headers=guest1).status_code == 200
    assert (
        client.post(
            "/v1/profiles/search",
            headers=guest1,
            json={"question": "Quien es?", "user_id": owner_id},
        ).status_code
        == 404
    )
    teammate = client.post(
        "/v1/profiles/search",
        headers=guest1,
        json={"question": "Quien es?", "user_id": guest2_id},
    )
    assert teammate.status_code == 200, teammate.text
    assert (
        client.get(f"/v1/profiles/{guest2_id}", headers=auth_headers).status_code == 200
    )


def test_guest_gallery_hides_meta_owned_posts(client, auth_headers):
    created = client.post(
        "/v1/groups", headers=auth_headers, json={"name": "Taller filtro"}
    )
    pin = created.json()["join_pin"]
    workspace_id = created.json()["id"]
    guest = _guest_headers(client, "scope-guest-gallery")
    assert (
        client.post(
            "/v1/groups/join-by-pin", headers=guest, json={"pin": pin}
        ).status_code
        == 200
    )
    meta_post = _work_post(client, auth_headers, workspace_id, "blue")
    guest_post = _work_post(client, guest, workspace_id, "green")

    feed = client.get(
        f"/v1/gallery?audience=work&workspace_id={workspace_id}", headers=guest
    ).json()
    ids = {item["id"] for item in feed}
    assert guest_post in ids
    assert meta_post not in ids

    owner_feed = client.get(
        f"/v1/gallery?audience=work&workspace_id={workspace_id}", headers=auth_headers
    ).json()
    assert {meta_post, guest_post} <= {item["id"] for item in owner_feed}
    assert (
        client.get(f"/v1/gallery/{meta_post}/thumbnail", headers=guest).status_code
        == 404
    )

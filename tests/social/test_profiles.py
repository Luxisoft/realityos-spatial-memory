import io
import uuid

from app.models import (
    MediaAsset,
    User,
)
from app.security import create_access_token, hash_password
from app.social import Publication
from PIL import Image

from .support import (
    _docx_cv,
)


def test_public_profile_and_single_replaceable_private_cv(client, auth_headers):
    first = client.request(
        "PATCH",
        "/v1/me/profile",
        headers=auth_headers,
        json={
            "headline": "Spatial systems architect",
            "biography": "Builds evidence-first operational software.",
            "phone": "+57 300 000 0000",
            "website": "https://example.test",
            "social_links": [
                {"label": "LinkedIn", "url": "https://linkedin.com/in/demo"}
            ],
        },
    )
    assert first.status_code == 200, first.text
    user_id = first.json()["user_id"]

    uploaded = client.request(
        "POST",
        "/v1/me/profile/cv",
        headers=auth_headers,
        files={
            "file": (
                "architecture.docx",
                _docx_cv(
                    "Enterprise architecture Kotlin distributed systems experience"
                ),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert uploaded.status_code == 200, uploaded.text
    assert uploaded.json()["cv"]["status"] == "ready"
    assert uploaded.json()["cv"]["analysis"]
    old_hash = uploaded.json()["cv"]["sha256"]

    public = client.get(f"/v1/profiles/{user_id}", headers=auth_headers)
    assert public.status_code == 200
    assert public.json()["headline"] == "Spatial systems architect"
    assert "cv" not in public.json()
    assert "permissions" not in public.json()

    answer = client.post(
        "/v1/profiles/search",
        headers=auth_headers,
        json={"question": "¿Quién sabe de arquitectura?"},
    )
    assert answer.status_code == 200, answer.text
    assert answer.json()["simulated"] is True
    assert answer.json()["profiles"][0]["user_id"] == user_id

    replacement = client.request(
        "POST",
        "/v1/me/profile/cv",
        headers=auth_headers,
        files={
            "file": (
                "design.docx",
                _docx_cv(
                    "Product design research accessibility and typography experience"
                ),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert replacement.status_code == 200, replacement.text
    assert replacement.json()["cv"]["sha256"] != old_hash
    with client.app.state.database.session_factory() as db:
        from app.social import UserProfile

        row = db.get(UserProfile, uuid.UUID(user_id))
        assert "Product design" in row.cv_text
        assert "Enterprise architecture" not in row.cv_text

    removed = client.request("DELETE", "/v1/me/profile/cv", headers=auth_headers)
    assert removed.status_code == 200
    assert removed.json()["cv"]["present"] is False
    assert removed.json()["cv"]["status"] == "empty"


def test_owner_uploads_group_profile_publication(client, auth_headers):
    output = io.BytesIO()
    Image.new("RGB", (48, 32), "green").save(output, format="PNG")
    response = client.post(
        "/v1/me/profile/publications",
        headers=auth_headers,
        files={"file": ("profile.png", output.getvalue(), "image/png")},
        data={
            "caption": "Nueva publicación",
            "workspace_id": client.post(
                "/v1/groups", headers=auth_headers, json={"name": "Profile group"}
            ).json()["id"],
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["caption"] == "Nueva publicación"
    assert payload["owned"] is True
    assert payload["audience"] == "work"

    owner_id = client.get("/v1/me/profile", headers=auth_headers).json()["user_id"]
    own_media = client.get(
        f"/v1/profiles/{owner_id}/media", headers=auth_headers
    ).json()
    assert any(item["id"] == payload["id"] for item in own_media["items"])

    with client.app.state.database.session_factory() as db:
        publication = db.get(Publication, uuid.UUID(payload["id"]))
        assert publication is not None
        asset = db.get(MediaAsset, publication.media_id)
        assert asset is not None
        assert asset.original_bytes == output.getvalue()

        other = User(
            email="profile-viewer@test.invalid",
            display_name="Profile viewer",
            password_hash=hash_password("password123456"),
        )
        db.add(other)
        db.commit()
        other_headers = {
            "Authorization": "Bearer "
            + create_access_token(other.id, client.app.state.settings)
        }
    public_media = client.get(
        f"/v1/profiles/{owner_id}/media", headers=other_headers
    ).json()
    assert all(item["id"] != payload["id"] for item in public_media["items"])

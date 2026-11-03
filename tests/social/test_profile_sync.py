"""Facebook refreshes on each login; outage is distinct from a withheld field."""

import time

import httpx
from app.social import FacebookIdentity, FacebookProfile


def test_each_facebook_login_refreshes_identity_and_available_details(
    client, monkeypatch
):
    settings = client.app.state.settings
    settings.facebook_app_id = "profile-sync-app"
    settings.facebook_app_secret = "synthetic-secret"
    settings.enqueue_processing = True
    monkeypatch.setattr(
        "app.tasks.import_facebook_media_task.delay", lambda *args: None
    )
    node = {
        "id": "synthetic-person",
        "name": "First Name",
        "birthday": "01/02/1990",
        "gender": "female",
        "hometown": {"name": "Lima"},
        "location": {"name": "Madrid"},
        "email": "synthetic@example.test",
    }
    unavailable = False
    reads = []
    inventory_reads = []

    async def get(self, url, **kwargs):
        if url.endswith("debug_token"):
            payload = {
                "data": {
                    "is_valid": True,
                    "app_id": settings.facebook_app_id,
                    "user_id": node["id"],
                    "expires_at": int(time.time()) + 3600,
                    "scopes": [
                        "public_profile",
                        "email",
                        "user_birthday",
                        "user_hometown",
                        "user_location",
                        "user_gender",
                    ],
                }
            }
        elif url.endswith("/me"):
            if kwargs["params"]["fields"] != "id,name":
                reads.append(kwargs["params"]["fields"])
                if unavailable:
                    return httpx.Response(
                        503,
                        json={"error": "offline"},
                        request=httpx.Request("GET", url),
                    )
            payload = node.copy()
        else:
            inventory_reads.append(url)
            payload = {"data": [], "summary": {"total_count": 0}}
        return httpx.Response(200, json=payload, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", get)

    def login():
        result = client.post(
            "/v1/auth/facebook", json={"access_token": "synthetic-token"}
        )
        assert result.status_code == 200, result.text
        headers = {"Authorization": "Bearer " + result.json()["access_token"]}
        return (
            result.json(),
            client.get("/v1/me/profile", headers=headers).json(),
            headers,
        )

    first, old, headers = login()
    assert first["profile_synced"] and old["location"] == "Madrid"
    node.update(
        name="Updated Name",
        birthday="03/04/1991",
        gender="other",
        hometown={"name": "Quito"},
        location={"name": "Bogotá"},
    )
    second, new, headers = login()
    assert second["profile_synced"] and len(reads) == 2
    assert new["user_id"] == old["user_id"]
    assert new["display_name"] == "Updated Name" and new["birthday"] == "03/04/1991"
    assert (
        new["hometown"] == "Quito"
        and new["location"] == "Bogotá"
        and new["gender"] == "other"
    )
    assert new["profile_source"] == "facebook" and not new["personal_details_editable"]
    synced = client.get("/v1/me/facebook-profile", headers=headers).json()["synced_at"]
    inventory_before_failure = len(inventory_reads)
    unavailable = True
    third, kept, headers = login()
    assert not third["profile_synced"]
    assert len(inventory_reads) > inventory_before_failure
    assert kept["location"] == "Bogotá" and kept["birthday"] == "03/04/1991"
    assert (
        client.get("/v1/me/facebook-profile", headers=headers).json()["synced_at"]
        == synced
    )
    unavailable = False
    del node["birthday"]
    del node["location"]
    fourth, limited, _ = login()
    assert fourth["profile_synced"] and len(reads) == 4
    assert limited["birthday"] is None and limited["location"] is None
    assert limited["hometown"] == "Quito"
    with client.app.state.database.session_factory() as db:
        assert (
            db.query(FacebookIdentity).count() == db.query(FacebookProfile).count() == 1
        )

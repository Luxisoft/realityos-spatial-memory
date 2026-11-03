from datetime import UTC, datetime, timedelta

from app.accounts.models import AccountChallenge


def signup(client, monkeypatch):
    sent = []
    monkeypatch.setattr(
        "app.accounts.service.send_mail", lambda *args: sent.append(args)
    )
    payload = {
        "username": "nurse.one",
        "email": "nurse@example.test",
        "display_name": "Nurse",
        "password": "SecurePassword123!",
    }
    r = client.post("/v1/auth/register", json=payload)
    assert r.status_code == 202, r.text
    return sent, payload


def test_registration_confirmation_reset_revokes_sessions(client, monkeypatch):
    sent, payload = signup(client, monkeypatch)
    assert (
        client.post(
            "/v1/auth/login",
            json={"email": payload["username"], "password": payload["password"]},
        ).status_code
        == 401
    )
    assert (
        client.post("/v1/auth/confirm-email", json={"token": sent[-1][-1]}).status_code
        == 200
    )
    assert (
        client.post("/v1/auth/confirm-email", json={"token": sent[-1][-1]}).status_code
        == 400
    )
    r = client.post(
        "/v1/auth/login",
        json={"email": payload["username"], "password": payload["password"]},
    )
    assert r.status_code == 200, r.text
    tokens = r.json()
    headers = {"Authorization": "Bearer " + tokens["access_token"]}
    assert client.get("/v1/auth/account-session", headers=headers).json()[
        "password_account"
    ]
    assert (
        client.post("/v1/auth/account-capture-profile", headers=headers).status_code
        == 200
    )
    assert (
        client.post(
            "/v1/auth/forgot-password", json={"email": payload["email"]}
        ).status_code
        == 202
    )
    assert (
        client.post(
            "/v1/auth/reset-password",
            json={"token": sent[-1][-1], "password": "AnotherSecure123!"},
        ).status_code
        == 200
    )
    assert client.get("/v1/auth/me", headers=headers).status_code == 401
    assert (
        client.post(
            "/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/v1/auth/reset-password",
            json={"token": sent[-1][-1], "password": "ThirdSecure123!"},
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/v1/auth/login",
            json={"email": payload["email"], "password": "AnotherSecure123!"},
        ).status_code
        == 200
    )


def test_expired_tokens_and_password_rules(client, monkeypatch):
    sent, payload = signup(client, monkeypatch)
    with client.app.state.database.session_factory() as db:
        for row in db.query(AccountChallenge):
            row.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        db.commit()
    assert (
        client.post("/v1/auth/confirm-email", json={"token": sent[-1][-1]}).status_code
        == 400
    )
    assert (
        client.post(
            "/v1/auth/register", json={**payload, "password": "short"}
        ).status_code
        == 422
    )
    assert client.post("/v1/auth/register", json=payload).status_code == 409


def test_failed_login_is_throttled_and_generic_recovery(client, monkeypatch):
    for _ in range(8):
        assert (
            client.post(
                "/v1/auth/login",
                json={"email": "missing@test.invalid", "password": "wrong"},
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/v1/auth/login",
            json={"email": "missing@test.invalid", "password": "wrong"},
        ).status_code
        == 429
    )
    sent = []
    monkeypatch.setattr(
        "app.accounts.service.send_mail", lambda *args: sent.append(args)
    )
    assert (
        client.post(
            "/v1/auth/forgot-password", json={"email": "missing@test.invalid"}
        ).status_code
        == 202
    )
    assert not sent


def test_admin_provisioning_is_disabled_by_default_and_not_email_verification(
    client, auth_headers
):
    ws = client.post(
        "/v1/workspaces", headers=auth_headers, json={"name": "Jury"}
    ).json()["id"]
    path = f"/v1/workspaces/{ws}/test-workers"
    payload = {"username": "jury.nurse", "display_name": "Jury Nurse"}
    assert client.post(path, headers=auth_headers, json=payload).status_code == 404
    client.app.state.settings.test_worker_provisioning_enabled = True
    response = client.post(path, headers=auth_headers, json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["email_verified"] is False
    login = client.post(
        "/v1/auth/login",
        json={"email": payload["username"], "password": response.json()["password"]},
    )
    assert login.status_code == 200
    headers = {"Authorization": "Bearer " + login.json()["access_token"]}
    assert (
        client.get("/v1/auth/account-session", headers=headers).json()[
            "password_account"
        ]
        is True
    )
    assert (
        client.post("/v1/auth/account-capture-profile", headers=headers).status_code
        == 200
    )

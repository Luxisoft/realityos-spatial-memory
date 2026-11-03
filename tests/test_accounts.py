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


def test_mail_failure_keeps_pending_account_and_preserves_previous_link(
    client, monkeypatch
):
    from app.accounts.models import PasswordAccount
    from app.models import User
    from fastapi import HTTPException
    from sqlalchemy import select
    from test_accounts import signup

    sent, payload = signup(client, monkeypatch)
    first = sent[-1][-1]

    def failed(*args):
        raise HTTPException(503, "Synthetic mail outage")

    monkeypatch.setattr("app.accounts.service.send_mail", failed)
    assert (
        client.post(
            "/v1/auth/resend-confirmation", json={"email": payload["email"]}
        ).status_code
        == 503
    )
    assert (
        client.post("/v1/auth/confirm-email", json={"token": first}).status_code == 200
    )
    pending = {**payload, "username": "pending.user", "email": "pending@example.test"}
    assert client.post("/v1/auth/register", json=pending).status_code == 503
    with client.app.state.database.session_factory() as db:
        user = db.scalar(select(User).where(User.email == pending["email"]))
        assert user and not user.is_active
        assert db.get(PasswordAccount, user.id).verified_at is None
    sent = []
    monkeypatch.setattr(
        "app.accounts.service.send_mail", lambda *args: sent.append(args)
    )
    assert (
        client.post(
            "/v1/auth/resend-confirmation", json={"email": pending["email"]}
        ).status_code
        == 202
    )
    assert (
        client.post("/v1/auth/confirm-email", json={"token": sent[-1][-1]}).status_code
        == 200
    )


import pytest


@pytest.mark.parametrize("port", [465, 587])
@pytest.mark.parametrize(
    "sender",
    [
        "realityos@example.test",
        "Animalia <realityos@example.test>",
        "RealityOS <realityos@example.test>",
    ],
)
def test_smtp_transport_confirmation_and_reset_links(client, monkeypatch, port, sender):
    from urllib.parse import parse_qs, urlsplit

    from app.accounts.models import AccountChallenge
    from pydantic import SecretStr

    settings = client.app.state.settings
    settings.smtp_host = "mail.example.test"
    settings.smtp_port = port
    settings.smtp_username = "transport-test"
    settings.smtp_password = SecretStr("synthetic-mail-password")
    settings.smtp_from = sender
    settings.auth_public_url = "https://example.test"
    deliveries = []
    calls = []

    class SMTP:
        def __init__(self, host, used_port, **kwargs):
            assert host == settings.smtp_host and used_port == port
            if port == 465:
                assert kwargs["context"].check_hostname

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def ehlo(self):
            calls.append("ehlo")

        def starttls(self, context):
            assert context.check_hostname
            calls.append("tls")

        def login(self, user, password):
            assert (user, password) == ("transport-test", "synthetic-mail-password")
            calls.append("login")

        def send_message(self, message):
            assert message["From"].addresses[0].display_name == "RealityOS"
            assert message["From"].addresses[0].addr_spec == "realityos@example.test"
            deliveries.append(message)

    monkeypatch.setattr("app.accounts.service.smtplib.SMTP_SSL", SMTP)
    monkeypatch.setattr("app.accounts.service.smtplib.SMTP", SMTP)
    payload = {
        "username": "smtp.test",
        "email": "recipient@example.test",
        "display_name": "Transport Test",
        "password": "SecurePassword123!",
    }
    assert client.post("/v1/auth/register", json=payload).status_code == 202

    def token_from_last():
        link = next(
            line
            for line in deliveries[-1]
            .get_body(preferencelist=("plain",))
            .get_content()
            .splitlines()
            if line.startswith("https:")
        )
        parsed = urlsplit(link)
        assert parse_qs(parsed.query) == {"lang": ["es"]}
        return parsed, parse_qs(parsed.fragment)["token"][0]

    parsed, token = token_from_last()
    assert parsed.path == "/v1/auth/verify"
    with client.app.state.database.session_factory() as db:
        row = db.query(AccountChallenge).one()
        assert row.digest != token and len(row.digest) == 64
    assert (
        client.post("/v1/auth/confirm-email", json={"token": token}).status_code == 200
    )
    assert (
        client.post(
            "/v1/auth/forgot-password", json={"email": payload["email"]}
        ).status_code
        == 202
    )
    parsed, token = token_from_last()
    assert parsed.path == "/v1/auth/reset"
    assert (
        client.post(
            "/v1/auth/reset-password",
            json={"token": token, "password": "NewSecurePassword123!"},
        ).status_code
        == 200
    )
    assert len(deliveries) == 2
    assert calls.count("tls") == (2 if port == 587 else 0)
    assert calls.count("login") == 2


@pytest.mark.parametrize(
    "lang,title", [("es", "Restablecer contraseña"), ("en", "Reset password")]
)
def test_action_page_language_security_and_confirmation(client, lang, title):
    response = client.get("/v1/auth/reset?lang=" + lang)
    assert response.status_code == 200
    assert title in response.text
    assert 'id="confirmation"' in response.text
    assert "#262729" in response.text and "#62A9F8" in response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "style-src 'nonce-" in response.headers["content-security-policy"]
    assert "history.replaceState" in response.text
    verify = client.get("/v1/auth/verify?lang=" + lang)
    assert 'id="password"' not in verify.text
    assert '<html lang="' + lang + '"' in verify.text


def test_mail_language_preference_and_fallback(client, monkeypatch):
    from app.models import User
    from sqlalchemy import select

    sent, payload = signup(client, monkeypatch)
    assert sent[-1][-2] == "es"
    with client.app.state.database.session_factory() as db:
        user = db.scalar(select(User).where(User.email == payload["email"]))
        user.preferred_language = "en"
        db.commit()
    for header, expected in [
        ({}, "en"),
        ({"Accept-Language": "es-CO,en;q=0.5"}, "es"),
        ({"Accept-Language": "fr"}, "en"),
    ]:
        assert (
            client.post(
                "/v1/auth/resend-confirmation",
                json={"email": payload["email"]},
                headers=header,
            ).status_code
            == 202
        )
        assert sent[-1][-2] == expected


def test_html_mail_has_matching_plain_action_and_escaped_link():
    from app.accounts.presentation import language, mail_content

    subject, plain, html = mail_content(
        "verify", "https://example.test/v1/auth/verify?lang=en#token=synthetic", "en"
    )
    assert subject == "RealityOS — Confirm email"
    assert "30 minutes" in plain and "30 minutes" in html
    assert "#262729" in html and "#62A9F8" in html
    assert "https://example.test/v1/auth/verify?lang=en#token=synthetic" in plain
    assert language("en;q=0,es;q=0.8") == "es"
    assert language("es;q=0.1,en;q=0.9") == "en"
    assert language("invalid", "en") == "en"
    assert language(None) == "es"

"""Account ownership, atomic address replacement, and duplicate registration."""

import pytest
from app.accounts.models import AccountChallenge, PasswordAccount
from app.models import User
from fastapi import HTTPException
from sqlalchemy import func, select


@pytest.fixture
def pending(client, monkeypatch):
    sent = []
    monkeypatch.setattr(
        "app.accounts.service.send_mail", lambda *args: sent.append(args)
    )
    payload = {
        "username": "pending.person",
        "email": "initial@example.test",
        "display_name": "Pending Person",
        "password": "InitialPassword123!",
    }
    assert client.post("/v1/auth/register", json=payload).status_code == 202
    with client.app.state.database.session_factory() as db:
        user_id = db.scalar(select(User.id).where(User.email == payload["email"]))
    return payload, sent, user_id


def correction(payload, **changes):
    return {
        "username": payload["username"],
        "password": payload["password"],
        "email": "corrected@example.test",
    } | changes


def test_email_replaces_initial_on_same_account_and_resends_to_new_address(
    client, pending
):
    payload, sent, user_id = pending
    old_token = sent[-1][-1]
    response = client.post(
        "/v1/auth/change-pending-email",
        json=correction(payload, email=" Corrected@Example.Test "),
    )
    assert response.status_code == 202
    assert sent[-1][1] == "corrected@example.test"
    assert (
        client.post("/v1/auth/confirm-email", json={"token": old_token}).status_code
        == 400
    )
    with client.app.state.database.session_factory() as db:
        user = db.get(User, user_id)
        assert user.email == "corrected@example.test"
        assert not user.is_active
        assert db.get(PasswordAccount, user_id).username == payload["username"]
        assert db.scalar(select(User.id).where(User.email == payload["email"])) is None
    assert (
        client.post(
            "/v1/auth/resend-confirmation", json={"email": payload["email"]}
        ).status_code
        == 202
    )
    assert len(sent) == 2
    assert (
        client.post(
            "/v1/auth/resend-confirmation", json={"email": "corrected@example.test"}
        ).status_code
        == 202
    )
    assert len(sent) == 3 and sent[-1][1] == "corrected@example.test"
    assert (
        client.post("/v1/auth/confirm-email", json={"token": sent[-1][-1]}).status_code
        == 200
    )
    assert (
        client.post(
            "/v1/auth/login",
            json={"email": "corrected@example.test", "password": payload["password"]},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/v1/auth/login",
            json={"email": payload["email"], "password": payload["password"]},
        ).status_code
        == 401
    )


@pytest.mark.parametrize(
    "changes", [{"password": "WrongPassword123!"}, {"username": "another.person"}]
)
def test_replacement_requires_the_pending_accounts_credentials(
    client, pending, changes
):
    payload, sent, user_id = pending
    response = client.post(
        "/v1/auth/change-pending-email", json=correction(payload, **changes)
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid account credentials."
    with client.app.state.database.session_factory() as db:
        assert db.get(User, user_id).email == payload["email"]
    assert len(sent) == 1


def test_replacement_cannot_take_another_accounts_address(client, pending):
    payload, sent, user_id = pending
    response = client.post(
        "/v1/auth/change-pending-email",
        json=correction(payload, email="admin@example.test"),
    )
    assert response.status_code == 409
    assert response.json()["detail"]["fields"] == ["email"]
    with client.app.state.database.session_factory() as db:
        assert db.get(User, user_id).email == payload["email"]
        assert (
            db.scalar(select(User.id).where(User.email == "admin@example.test"))
            != user_id
        )
    assert len(sent) == 1


@pytest.mark.parametrize("state", ["confirmed", "provisioned", "active"])
def test_replacement_is_limited_to_unconfirmed_registration(client, pending, state):
    payload, sent, user_id = pending
    if state == "confirmed":
        assert (
            client.post(
                "/v1/auth/confirm-email", json={"token": sent[-1][-1]}
            ).status_code
            == 200
        )
    else:
        with client.app.state.database.session_factory() as db:
            if state == "provisioned":
                db.get(PasswordAccount, user_id).provisioned_by = db.scalar(
                    select(User.id).where(User.email == "admin@example.test")
                )
            else:
                db.get(User, user_id).is_active = True
            db.commit()
    assert (
        client.post(
            "/v1/auth/change-pending-email", json=correction(payload)
        ).status_code
        == 409
    )
    with client.app.state.database.session_factory() as db:
        assert db.get(User, user_id).email == payload["email"]
    assert len(sent) == 1


def test_failed_mail_rolls_back_address_and_preserves_previous_confirmation(
    client, pending, monkeypatch
):
    payload, sent, user_id = pending
    token = sent[-1][-1]

    def offline(*args):
        raise HTTPException(503, "Email delivery failed. Please retry.")

    monkeypatch.setattr("app.accounts.service.send_mail", offline)
    assert (
        client.post(
            "/v1/auth/change-pending-email", json=correction(payload)
        ).status_code
        == 503
    )
    with client.app.state.database.session_factory() as db:
        assert db.get(User, user_id).email == payload["email"]
        assert (
            db.scalar(
                select(func.count())
                .select_from(AccountChallenge)
                .where(AccountChallenge.user_id == user_id)
            )
            == 1
        )
    assert (
        client.post("/v1/auth/confirm-email", json={"token": token}).status_code == 200
    )


def test_replacement_attempts_are_limited(client, pending):
    payload, sent, _ = pending
    for _ in range(8):
        assert (
            client.post(
                "/v1/auth/change-pending-email",
                json=correction(payload, password="WrongPassword123!"),
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/v1/auth/change-pending-email", json=correction(payload)
        ).status_code
        == 429
    )
    assert len(sent) == 1


@pytest.mark.parametrize("fields", [["email"], ["username"], ["email", "username"]])
def test_duplicate_data_is_identified_before_creating_or_sending(
    client, pending, fields
):
    payload, sent, _ = pending
    candidate = payload | {
        "username": "different.person",
        "email": "different@example.test",
    }
    for field in fields:
        candidate[field] = payload[field].upper()
    with client.app.state.database.session_factory() as db:
        initial_count = db.scalar(select(func.count()).select_from(User))
    result = client.post("/v1/auth/register", json=candidate)
    assert result.status_code == 409
    assert result.json()["detail"] == {
        "code": "registration_conflict",
        "fields": fields,
    }
    with client.app.state.database.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(User)) == initial_count
    assert len(sent) == 1

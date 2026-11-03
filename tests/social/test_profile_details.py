"""Owned email-account details and server-enforced Facebook field ownership."""

import importlib.util
from datetime import UTC, datetime
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from app.accounts.models import PasswordAccount
from app.models import User
from app.security import create_access_token, hash_password
from app.social import FacebookIdentity, UserProfile


@pytest.fixture
def email_owner(client, auth_headers):
    with client.app.state.database.session_factory() as db:
        user = db.scalar(sa.select(User).where(User.email == "admin@example.test"))
        db.add(
            PasswordAccount(
                user_id=user.id, username="email.owner", verified_at=datetime.now(UTC)
            )
        )
        db.commit()
        return user.id, auth_headers


def patch(client, headers, **fields):
    return client.request("PATCH", "/v1/me/profile", headers=headers, json=fields)


def test_email_details_save_read_clear_and_keep_unsupplied_fields(client, email_owner):
    user_id, headers = email_owner
    response = patch(
        client,
        headers,
        display_name="  Updated Name  ",
        birthday="2000-02-29",
        gender="  female  ",
        hometown=" Bogotá ",
        location=" Madrid ",
        biography="Keep this",
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["personal_details_editable"] and result["profile_source"] == "email"
    assert result["display_name"] == "Updated Name"
    assert result["birthday"] == "2000-02-29"
    assert result["gender"] == "female"
    assert result["location"] == "Madrid"
    assert result["hometown"] == "Bogotá"
    today = datetime.now(UTC).date()
    assert (
        result["age_min"]
        == result["age_max"]
        == today.year - 2000 - ((today.month, today.day) < (2, 29))
    )
    assert (
        patch(client, headers, location="Valencia").json()["biography"] == "Keep this"
    )
    public = client.get(f"/v1/profiles/{user_id}", headers=headers).json()
    assert public["birthday"] == "2000-02-29" and public["location"] == "Valencia"
    assert "personal_details_editable" not in public
    assert public["profile_source"] == "email"
    cleared = patch(
        client, headers, birthday=None, gender=None, hometown=" ", location=None
    )
    assert cleared.status_code == 200
    assert all(
        cleared.json()[key] is None
        for key in ("birthday", "gender", "hometown", "location", "age_min", "age_max")
    )
    assert cleared.json()["biography"] == "Keep this"


@pytest.mark.parametrize(
    "fields",
    [
        {"birthday": "2025-02-29"},
        {"birthday": "2999-01-01"},
        {"birthday": "1899-12-31"},
        {"birthday": 123456},
        {"birthday": "01/02/2000"},
        {"birthday": "20000101"},
        {"display_name": "  "},
        {"display_name": None},
        {"location": "x" * 161},
        {"gender": "x" * 33},
    ],
)
def test_invalid_details_do_not_partially_save(client, email_owner, fields):
    _user_id, headers = email_owner
    before = client.get("/v1/me/profile", headers=headers).json()
    assert (
        patch(
            client, headers, **({"biography": "must not persist"} | fields)
        ).status_code
        == 422
    )
    after = client.get("/v1/me/profile", headers=headers).json()
    assert after == before


def test_facebook_identity_blocks_manual_changes_even_without_synced_profile(
    client, email_owner
):
    user_id, headers = email_owner
    with client.app.state.database.session_factory() as db:
        db.add(FacebookIdentity(subject="synthetic:account", user_id=user_id))
        db.commit()
    own = client.get("/v1/me/profile", headers=headers).json()
    assert own["profile_source"] == "facebook" and not own["personal_details_editable"]
    public = client.get(f"/v1/profiles/{user_id}", headers=headers).json()
    assert public["profile_source"] == "facebook"
    assert public["facebook_link"] is None
    assert "personal_details_editable" not in public
    for field, value in {
        "display_name": "Forged",
        "birthday": None,
        "location": "Forged",
        "hometown": "Forged",
        "gender": "Forged",
    }.items():
        assert (
            patch(
                client, headers, **{field: value, "biography": "must not save"}
            ).status_code
            == 403
        )
    assert client.get("/v1/me/profile", headers=headers).json()["biography"] == ""
    assert (
        patch(
            client, headers, biography="Custom biography is still editable"
        ).status_code
        == 200
    )


def test_profile_edit_cannot_target_another_account(client, email_owner):
    _user_id, headers = email_owner
    with client.app.state.database.session_factory() as db:
        other = User(
            email="separate@example.test",
            display_name="Separate",
            password_hash=hash_password("SyntheticPassword123!"),
        )
        db.add(other)
        db.flush()
        db.add(
            PasswordAccount(
                user_id=other.id, username="separate", verified_at=datetime.now(UTC)
            )
        )
        other_id = other.id
        db.commit()
    assert (
        patch(client, headers, user_id=str(other_id), location="Owner City").status_code
        == 200
    )
    other_headers = {
        "Authorization": "Bearer "
        + create_access_token(other_id, client.app.state.settings)
    }
    assert (
        client.get("/v1/me/profile", headers=other_headers).json()["location"] is None
    )
    assert (
        client.get("/v1/me/profile", headers=headers).json()["location"] == "Owner City"
    )
    assert (
        client.request(
            "PATCH",
            f"/v1/profiles/{other_id}",
            headers=headers,
            json={"location": "Forged"},
        ).status_code
        == 405
    )
    assert patch(client, {}, location="Forged").status_code == 401


def test_viewed_profile_source_is_independent_from_the_viewer(client, email_owner):
    user_id, headers = email_owner
    with client.app.state.database.session_factory() as db:
        other = User(
            email="facebook@example.test",
            display_name="Facebook account",
            password_hash=hash_password("SyntheticPassword123!"),
        )
        db.add(other)
        db.flush()
        db.add(FacebookIdentity(subject="synthetic:viewer", user_id=other.id))
        other_id = other.id
        db.commit()
    other_headers = {
        "Authorization": "Bearer "
        + create_access_token(other_id, client.app.state.settings)
    }
    assert (
        client.get(f"/v1/profiles/{user_id}", headers=other_headers).json()[
            "profile_source"
        ]
        == "email"
    )
    assert (
        client.get(f"/v1/profiles/{other_id}", headers=headers).json()["profile_source"]
        == "facebook"
    )
    assert client.get(f"/v1/profiles/{other_id}").status_code == 401


def test_guest_cannot_opt_into_email_account_details(client):
    response = client.post(
        "/v1/auth/guest", json={"device_id": "synthetic-profile-guest"}
    )
    headers = {"Authorization": "Bearer " + response.json()["access_token"]}
    assert not client.get("/v1/me/profile", headers=headers).json()[
        "personal_details_editable"
    ]
    assert patch(client, headers, location="Forged").status_code == 403


@pytest.mark.parametrize("fresh", [False, True])
def test_profile_migration_preserves_existing_data_and_supports_fresh_metadata(fresh):
    path = (
        Path(__file__).parents[2]
        / "backend/alembic/versions/20261103_0034_profile_details.py"
    )
    spec = importlib.util.spec_from_file_location("profile_details_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    engine = sa.create_engine("sqlite://")
    with engine.begin() as connection:
        if fresh:
            UserProfile.__table__.create(connection)
        else:
            connection.exec_driver_sql(
                "CREATE TABLE user_profiles (user_id TEXT PRIMARY KEY, headline TEXT)"
            )
            connection.exec_driver_sql(
                "INSERT INTO user_profiles VALUES ('synthetic','Keep this')"
            )
        with Operations.context(MigrationContext.configure(connection)):
            module.upgrade()
            module.upgrade()
        columns = {
            c["name"] for c in sa.inspect(connection).get_columns("user_profiles")
        }
        assert {"birthday", "gender", "hometown", "location"} <= columns
        if not fresh:
            assert connection.exec_driver_sql(
                "SELECT headline, birthday FROM user_profiles"
            ).one() == ("Keep this", None)
    engine.dispose()

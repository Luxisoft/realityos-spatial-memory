"""SQL installation is atomic, PostgreSQL-backed and independent of runtime files."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from app.db import Base
from app.local.bootstrap import seed_evaluation
from app.local_models import LocalAccessAccount, LocalEvaluationState
from app.main import create_app
from app.models import MediaAsset, User, Workspace
from app.social_features.models import Publication
from conftest import APIClient
from sqlalchemy import select, text
from test_local_access import local_settings


def test_database_changes_are_visible_without_reading_seed_files(
    evaluation, monkeypatch
):
    original = evaluation.get("/v1/auth/local-accounts").json()["accounts"]
    with evaluation.app.state.database.session_factory() as db:
        user = db.scalar(
            select(User).join(LocalAccessAccount).order_by(LocalAccessAccount.position)
        )
        user.display_name = "Updated database account"
        workspace = db.get(Workspace, db.get(LocalAccessAccount, user.id).workspace_id)
        workspace.name = "Updated database group"
        db.commit()

    def no_fixture(*args, **kwargs):
        raise AssertionError("Runtime must not read initialization resources")

    monkeypatch.setattr(Path, "read_text", no_fixture)
    monkeypatch.setattr(Path, "read_bytes", no_fixture)
    listing = evaluation.get("/v1/auth/local-accounts").json()["accounts"]
    assert listing[0]["display_name"] == "Updated database account"
    assert listing[0]["workspace_name"] == "Updated database group"
    token = evaluation.post(
        "/v1/auth/local-select", json={"user_id": original[0]["id"]}
    ).json()["access_token"]
    response = evaluation.get(
        "/v1/gallery/page?limit=30", headers={"Authorization": "Bearer " + token}
    )
    assert response.status_code == 200 and len(response.json()["items"]) == 19
    with evaluation.app.state.database.session_factory() as db:
        assert (
            seed_evaluation(
                db, evaluation.app.state.settings, root=Path("/missing-local-fixtures")
            )["initialized"]
            is False
        )


def test_selector_eligibility_is_not_inferred_from_account_names(evaluation):
    with evaluation.app.state.database.session_factory() as db:
        access = db.scalar(
            select(LocalAccessAccount).order_by(LocalAccessAccount.position)
        )
        access.enabled = False
        user_id = str(access.user_id)
        db.commit()
    assert len(evaluation.get("/v1/auth/local-accounts").json()["accounts"]) == 8
    assert (
        evaluation.post("/v1/auth/local-select", json={"user_id": user_id}).status_code
        == 404
    )
    with evaluation.app.state.database.session_factory() as db:
        seed_evaluation(db, evaluation.app.state.settings)
        assert db.get(LocalAccessAccount, access.user_id).enabled is False


def test_missing_original_rolls_back_the_whole_installation(tmp_path, monkeypatch):
    from app.local import sql_data

    app = create_app(local_settings(tmp_path, local_evaluation_enabled=True))
    Base.metadata.create_all(app.state.database.engine)
    original_path = sql_data.fixture_file
    damaged = tmp_path / "damaged.png"
    damaged.write_bytes(b"invalid original")
    monkeypatch.setattr(
        sql_data,
        "fixture_file",
        lambda root, path: (
            damaged if "person-01" in path else original_path(root, path)
        ),
    )
    with app.state.database.session_factory() as db:
        with pytest.raises(ValueError, match="integrity"):
            seed_evaluation(db, app.state.settings)
        db.rollback()
        assert db.query(User).count() == 0
        assert db.query(MediaAsset).count() == 0
        assert db.query(LocalEvaluationState).count() == 0
        assert not db.execute(
            text("SELECT name FROM sqlite_temp_master WHERE type='table'")
        ).all()
    app.state.database.engine.dispose()


def test_postgres_initialization_and_concurrent_restart(postgres_url, tmp_path):
    settings = local_settings(
        tmp_path, database_url=postgres_url, local_evaluation_enabled=True
    )
    app = create_app(settings)
    Base.metadata.create_all(app.state.database.engine)

    def initialize():
        with app.state.database.session_factory() as db:
            result = seed_evaluation(db, settings)
            db.commit()
            return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: initialize(), range(2)))
    assert sorted(result["initialized"] for result in results) == [False, True]
    client = APIClient(app)
    assert len(client.get("/v1/auth/local-accounts").json()["accounts"]) == 9
    with app.state.database.session_factory() as db:
        assert db.query(Publication).count() == 41
        assert db.query(MediaAsset).count() == 57
        assert db.query(Workspace).count() == 3
    app.state.database.engine.dispose()

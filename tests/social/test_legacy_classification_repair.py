"""A real pre-SQL local catalog reaches the approved scoped gallery filters."""

import pytest
from app.db import Base, Database
from app.local import bootstrap
from app.local.upgrades import POLICE
from app.local_models import LocalEvaluationState
from app.main import create_app
from conftest import APIClient
from test_local_access import local_settings
from test_local_legacy_classification import RECEIPT, seed_legacy_history

from social.test_operational_taxonomy import (
    assert_approved_gallery_filters,
    authorization,
)


@pytest.mark.parametrize("dialect", ["sqlite", "postgresql"])
def test_legacy_catalog_repair_reaches_api_filters_and_preserves_scope(
    dialect, request, tmp_path, monkeypatch
):
    path = tmp_path / "legacy-gallery.sqlite"
    url = (
        request.getfixturevalue("postgres_url")
        if dialect == "postgresql"
        else f"sqlite:///{path}"
    )
    settings = local_settings(tmp_path, database_url=url, local_evaluation_enabled=True)
    app = create_app(settings)
    try:
        with Database(url) as database:
            Base.metadata.create_all(database.engine)
            with database.session() as db:
                seed_legacy_history(
                    db,
                    settings,
                    monkeypatch,
                    legacy_source_refs=True,
                    alternate_media=True,
                )
                assert db.get(LocalEvaluationState, RECEIPT) is None
            api = APIClient(app)
            _, headers = authorization(api, POLICE)
            previous = api.get(
                "/v1/gallery/filter-options",
                headers={**headers, "Accept-Language": "es"},
                params={"workspace_id": str(POLICE)},
            )
            assert previous.status_code == 200
            assert {term["name"] for term in previous.json()["tags"]} == {
                "Case information",
                "Observation video",
            }
            with database.session() as db:
                result = bootstrap.seed_evaluation(db, settings)
                assert result["updates"] == {RECEIPT: {"publications": 0}}
            assert_approved_gallery_filters(api)
            with database.session() as db:
                assert bootstrap.seed_evaluation(db, settings)["updates"] == {}
            assert_approved_gallery_filters(api)
    finally:
        app.state.database.engine.dispose()
        path.unlink(missing_ok=True)

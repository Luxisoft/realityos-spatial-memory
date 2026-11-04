"""Keep the public API aligned with its explicitly reviewed contract."""

import json
from pathlib import Path

from app.config import Settings
from app.main import create_app


def test_openapi_matches_reviewed_contract():
    expected = json.loads(
        (Path(__file__).parent / "contracts" / "openapi.json").read_text()
    )
    application = create_app(Settings(database_url="sqlite://", meta_mode="mock"))
    try:
        assert application.openapi() == expected
    finally:
        application.state.database.engine.dispose()

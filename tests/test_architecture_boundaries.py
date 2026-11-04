"""Architectural boundaries reject real regressions without banning JSON transport."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "architecture_rules",
    Path(__file__).resolve().parents[1] / "scripts/architecture_rules.py",
)
RULES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RULES)


@pytest.mark.parametrize(
    "module,source,message",
    [
        ("app.workspaces.service", "from app.http.common import save", "HTTP handlers"),
        ("app.workspaces.service", "from ..http.common import save", "HTTP handlers"),
        ("app.providers.live", "from app import meta", "provider contracts"),
        (
            "app.tasks",
            "from app.local.bootstrap import seed_evaluation",
            "data initializers",
        ),
        ("app.local.access", "from app.local import sql_data", "data initializers"),
        (
            "app.local.access",
            "from app.local.state import applied",
            "data initializers",
        ),
        ("app.accounts.service", "from app.local_catalog import accounts", "retired"),
        ("app.runtime.routers", "from scripts import seed_demo", "scripts"),
        ("app.processing.search", "import json as j\ndata = j.load(file)", "JSON file"),
        (
            "app.processing.search",
            "from json import load as read\ndata = read(file)",
            "JSON file",
        ),
        (
            "app.accounts.service",
            'file = root / "users.json"\ndata = file.read_text()',
            "JSON file",
        ),
        (
            "app.accounts.service",
            "import json\ndata = json.loads(path.read_text())",
            "file-backed",
        ),
        (
            "app.accounts.service",
            'import importlib\nimportlib.import_module("app.http.identity")',
            "HTTP handlers",
        ),
    ],
)
def test_forbidden_dependencies_and_catalog_reads(module, source, message):
    assert any(message in detail for _, detail in RULES.module_issues(module, source))


@pytest.mark.parametrize(
    "module,source",
    [
        ("app.http.queries", "from app.http.common import answer"),
        ("app.runtime.routers", "from app.http.local_access import router"),
        ("app.providers.live", "import json\nresult = json.loads(response.text)"),
        ("app.local.bootstrap", "from app.local.sql_data import apply_seed"),
        ("app.local.sql_data", 'data = (root / "database" / "001.sql").read_text()'),
        ("app.runtime.schema", 'data = (root / "schema.sql").read_text()'),
        ("app.faces", "from app.social import Publication"),
    ],
)
def test_transport_bootstrap_and_protected_compatibility_remain_valid(module, source):
    assert not RULES.module_issues(module, source)


def test_new_simulator_business_catalogs_are_rejected(tmp_path):
    simulator = tmp_path / "simulator"
    simulator.mkdir()
    (simulator / "new-catalog.json").write_text('{"groups": []}')
    assert "business records belong in SQL" in RULES.architecture_issues(tmp_path)[0]
    (simulator / "new-catalog.json").write_text(
        '{"files": [{"path": "a.jpg", "sha256": "hash", "license": "owned"}]}'
    )
    assert RULES.architecture_issues(tmp_path) == []

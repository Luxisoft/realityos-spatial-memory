"""Published local scenarios never contain credentials or an active remote target."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_retired_password_provisioner_cannot_create_accounts(client):
    spec = importlib.util.spec_from_file_location("retired", ROOT / "simulator/postman/provision.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(ValueError, match="Retired"):
        module.provision(None, None, None, None)


def test_local_scenario_identifiers_match_initialized_fixture():
    catalog = json.loads((ROOT / "simulator/local/catalog.json").read_text())
    jury = json.loads((ROOT / "simulator/postman/jury.json").read_text())
    assert jury["base_url"] == "http://localhost:8080"
    for scenario, group in zip(jury["scenarios"], catalog["groups"], strict=True):
        values = scenario["values"]
        assert not values["password"]
        assert values["user_id"] == group["users"][0]["id"]
        assert values["workspace_id"] == group["id"]
        assert values["record_id"] in group["records"].values()
        assert values["post_id"] in group["publications"].values()


def test_collection_has_one_enabled_local_destination():
    data = json.loads((ROOT / "docs/postman/RealityOS.postman_collection.json").read_text())
    assert [f["name"] for f in data["item"]] == ["Localhost requests", "Server requests"]
    assert "skipRequest" in str(data["item"][1]["event"])
    variables = {v["key"]: v["value"] for v in data["variable"]}
    assert variables["localhost_base_url"] == "http://localhost:8080"
    assert variables["localhost_auth_mode"] == "local-select"
    assert variables["server_base_url"] == ""
    assert all(not value for key, value in variables.items() if key.endswith(("_password", "_access_token", "_refresh_token")))

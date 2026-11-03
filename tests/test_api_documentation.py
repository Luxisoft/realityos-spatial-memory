"""Offline checks for the downloadable public API examples."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = Path(
    os.environ.get("REALITYOS_DOCS_CONTRACT", ROOT / "tests/contracts/openapi.json")
)


def collection():
    return json.loads(
        (ROOT / "docs/postman/RealityOS.postman_collection.json").read_text()
    )


def items():
    return [item for folder in collection()["item"][1:] for item in folder["item"]]


def test_reference_and_collection_are_reproducible():
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/build_api_docs.py"),
            "--check",
            "--contract",
            str(CONTRACT),
        ],
        check=True,
        cwd=ROOT,
    )


def test_all_contract_operations_have_one_reference_request():
    spec = json.loads(CONTRACT.read_text())
    expected = {
        f"{m.upper()} {path}"
        for path, methods in spec["paths"].items()
        for m in methods
        if m in {"get", "post", "put", "patch", "delete"}
    }
    names = [i["name"] for i in items()]
    assert len(names) == len(set(names))
    assert expected == {name for name in names if "/auth/local-" not in name}
    assert {"GET /v1/auth/local-session", "POST /v1/auth/local-login"} <= set(names)


def test_credentials_and_required_variables_are_not_published():
    referenced = set(re.findall(r"{{([^}]+)}}", json.dumps(collection())))
    for path in (ROOT / "docs/postman").glob("*.postman_environment.json"):
        values = {v["key"]: v["value"] for v in json.loads(path.read_text())["values"]}
        assert referenced <= values.keys()
        assert values["enable_write_requests"] == "false"
        for key, value in values.items():
            if key not in {"base_url", "enable_write_requests", "language"}:
                assert value == "", key
        assert not values["base_url"].endswith("/v1")


def test_transport_auth_and_uploads_match_their_realm():
    for item in items():
        request = item["request"]
        headers = {h["key"] for h in request["header"]}
        if "/v1/integrations/" in item["name"]:
            assert "X-RealityOS-Integration-Key" in headers
            assert request["auth"]["type"] == "noauth"
        if "/v1/device/" in item["name"] and "/device/display/" not in item["name"]:
            assert {"X-RealityOS-Device-ID", "X-RealityOS-Device-Key"} <= headers
        if request.get("body", {}).get("mode") == "formdata":
            assert "Content-Type" not in headers
            assert all(
                f.get("src", "") == ""
                for f in request["body"]["formdata"]
                if f["type"] == "file"
            )
    facebook = next(i for i in items() if i["name"] == "POST /v1/auth/facebook")
    assert "{{facebook_access_token}}" in facebook["request"]["body"]["raw"]


def test_quick_start_never_selects_a_workspace_or_enrolls_a_face():
    quick = collection()["item"][0]["item"]
    assert len(quick) == 5
    scripts = json.dumps([i.get("event") for i in quick])
    assert 'environment.set(\\"workspace_id' not in scripts
    assert "Choose workspace_id" in scripts
    assert not any("/faces/" in i["name"] for i in quick)

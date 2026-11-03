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


def items(target=None):
    targets = [target] if target else collection()["item"]
    return [
        item
        for root in targets
        for folder in root["item"][1:]
        for item in folder["item"]
    ]


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
    targets = collection()["item"]
    assert [t["name"] for t in targets] == ["Server requests", "Localhost requests"]
    for index, target in enumerate(targets):
        names = [i["name"] for i in items(target)]
        assert len(names) == len(set(names))
        assert expected == {name for name in names if "/auth/local-" not in name}
        local = {name for name in names if "/auth/local-" in name}
        assert local == (
            {"GET /v1/auth/local-session", "POST /v1/auth/local-login"}
            if index
            else set()
        )


def test_all_variables_are_declared_and_isolated_with_only_public_demo_credentials():
    c = collection()
    demo = json.loads((ROOT / "simulator/postman/demo.json").read_text())
    variables = {v["key"]: v["value"] for v in c["variable"]}
    assert len(variables) == len(c["variable"])
    assert set(re.findall(r"{{([^}]+)}}", json.dumps(c))) <= variables.keys()
    assert all(v["description"] for v in c["variable"])
    for target, prefix, filename, origin in zip(
        c["item"],
        ["server", "localhost"],
        ["public", "local"],
        ["https://realityos.luxisoft.com", "http://localhost:8080"],
        strict=True,
    ):
        keys = {k for k in variables if k.startswith(prefix + "_")}
        refs = set(re.findall(r"{{([^}]+)}}", json.dumps(target)))
        assert refs <= keys
        script_refs = set(
            re.findall(
                r'pm\.(?:variables|environment|collectionVariables)\.(?:get|set|has)\("([^"\n]+)"',
                "\n".join(
                    line
                    for folder in target["item"]
                    for item in folder["item"]
                    for e in item["event"]
                    for line in e["script"]["exec"]
                ),
            )
        )
        assert script_refs <= keys
        env = json.loads(
            (
                ROOT / f"docs/postman/RealityOS.{filename}.postman_environment.json"
            ).read_text()
        )
        values = {v["key"]: v["value"] for v in env["values"]}
        assert env["name"] == "RealityOS · " + target["name"]
        assert values == {k: variables[k] for k in keys}
        assert values[prefix + "_base_url"] == origin
        assert values[prefix + "_language"] == "en"
        assert values[prefix + "_enable_write_requests"] == "false"
        published = {
            "email",
            "username",
            "password",
            "display_name",
            "workspace_id",
            "user_id",
        }
        for key, value in values.items():
            name = key.removeprefix(prefix + "_")
            if name in published:
                assert value == demo[prefix][name]
            elif name not in {"base_url", "enable_write_requests", "language", "query"}:
                assert value == "", key
        secret_types = {v["key"]: v["type"] for v in env["values"]}
        assert secret_types[prefix + "_password"] == "secret"
        assert secret_types[prefix + "_access_token"] == "secret"


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
    for target, prefix in zip(
        collection()["item"], ["server", "localhost"], strict=True
    ):
        facebook = next(
            i for i in items(target) if i["name"] == "POST /v1/auth/facebook"
        )
        assert (
            "{{" + prefix + "_facebook_access_token}}"
            in facebook["request"]["body"]["raw"]
        )


def test_quick_start_uses_the_explicit_demo_workspace_without_enrolling_or_capturing():
    for target in collection()["item"]:
        assert target["item"][0]["name"] == "00 Quick start"
        quick = target["item"][0]["item"]
        assert [i["name"] for i in quick] == [
            "GET /health/live",
            "POST /v1/auth/login",
            "GET /v1/auth/me",
            "GET /v1/workspaces",
            "POST /v1/queries",
        ]
        scripts = "\n".join(
            line for i in quick for e in i["event"] for line in e["script"]["exec"]
        )
        assert not re.search(r'\.set\("[^"\n]*workspace_id"', scripts)
        assert "Choose workspace_id" in scripts


def test_auth_bodies_keep_existing_and_replacement_credentials_separate():
    for target, prefix in zip(
        collection()["item"], ["server", "localhost"], strict=True
    ):
        requests = {i["name"]: i["request"] for i in items(target)}
        change = json.loads(
            requests["POST /v1/auth/change-pending-email"]["body"]["raw"]
        )
        assert change == {
            "username": "{{" + prefix + "_username}}",
            "email": "{{" + prefix + "_new_email}}",
            "password": "{{" + prefix + "_password}}",
        }
        reset = json.loads(requests["POST /v1/auth/reset-password"]["body"]["raw"])
        assert reset["password"] == "{{" + prefix + "_new_password}}"

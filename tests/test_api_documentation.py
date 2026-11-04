"""Offline checks for the downloadable public API examples."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from postman_dataset import evaluation_dataset

CONTRACT = Path(
    os.environ.get("REALITYOS_DOCS_CONTRACT", ROOT / "tests/contracts/openapi.json")
)


def collection():
    return json.loads(
        (ROOT / "docs/postman/RealityOS.reference.postman_collection.json").read_text()
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
    targets = collection()["item"]
    assert [t["name"] for t in targets] == ["Server requests", "Localhost requests"]
    for target in targets:
        spec = json.loads(
            (
                ROOT
                / "tests/contracts"
                / (
                    "openapi.local.json"
                    if target["name"] == "Localhost requests"
                    else "openapi.json"
                )
            ).read_text()
        )
        expected = {
            f"{method.upper()} {path}"
            for path, methods in spec["paths"].items()
            for method in methods
            if method in {"get", "post", "put", "patch", "delete"}
        }
        names = [item["name"] for item in items(target)]
        assert len(names) == len(set(names))
        assert expected == set(names)


def test_primary_catalog_request_fields_match_current_contract():
    spec = json.loads(CONTRACT.read_text())
    public = json.loads(
        (ROOT / "docs/postman/RealityOS.postman_collection.json").read_text()
    )
    for target in public["item"]:
        spec = json.loads(
            (
                ROOT
                / "tests/contracts"
                / (
                    "openapi.local.json"
                    if target["name"] == "Localhost requests"
                    else "openapi.json"
                )
            ).read_text()
        )
        catalog = {
            item["name"]: item["request"]
            for folder in target["item"]
            if not folder["name"].startswith("00 ")
            for item in folder["item"]
        }
        for path, methods in spec["paths"].items():
            for method, operation in methods.items():
                if method not in {"get", "post", "put", "patch", "delete"}:
                    continue
                request = catalog[f"{method.upper()} {path}"]
                assert request["method"] == method.upper()
                actual_path = "/" + "/".join(request["url"]["path"])
                actual_path = re.sub(
                    r"{{(?:server|localhost)_([^}]+)}}", r"{\1}", actual_path
                )
                assert actual_path == path
                query = {q["key"]: q for q in request["url"].get("query", [])}
                for parameter in methods.get("parameters", []) + operation.get(
                    "parameters", []
                ):
                    if parameter["in"] == "query":
                        assert parameter["name"] in query
                        if parameter.get("required"):
                            assert not query[parameter["name"]].get("disabled")
                for mime, content in (
                    operation.get("requestBody", {}).get("content", {}).items()
                ):
                    schema = content.get("schema", {})
                    if "$ref" in schema:
                        schema = spec["components"]["schemas"][
                            schema["$ref"].split("/")[-1]
                        ]
                    body = request["body"]
                    if mime == "application/json":
                        assert body["mode"] == "raw"
                        assert (
                            set(schema.get("required", []))
                            <= json.loads(body["raw"]).keys()
                        )
                    elif mime == "multipart/form-data":
                        assert body["mode"] == "formdata"
                        enabled = {
                            f["key"] for f in body["formdata"] if not f.get("disabled")
                        }
                        assert set(schema.get("required", [])) <= enabled


def test_all_variables_are_declared_and_isolated_without_published_credentials():
    c = collection()
    demo = evaluation_dataset()["defaults"]
    variables = {v["key"]: v["value"] for v in c["variable"]}
    assert len(variables) == len(c["variable"])
    assert set(re.findall(r"{{([^}]+)}}", json.dumps(c))) <= variables.keys()
    assert all(v["description"] for v in c["variable"])
    for target, prefix, filename, origin in zip(
        c["item"],
        ["server", "localhost"],
        ["reference", "local"],
        ["", "http://localhost:8080"],
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
            elif name not in {
                "base_url",
                "enable_write_requests",
                "language",
                "query",
                "auth_mode",
            }:
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
        if prefix == "localhost":
            assert not any("facebook" in item["name"] for item in items(target))
            continue
        facebook = next(
            i for i in items(target) if i["name"] == "POST /v1/auth/facebook"
        )
        assert (
            "{{" + prefix + "_facebook_access_token}}"
            in facebook["request"]["body"]["raw"]
        )


def test_local_login_example_includes_current_local_response_fields():
    from app.http.local_access import LocalLoginResponse

    item = next(
        item
        for item in items(collection()["item"][1])
        if item["name"] == "POST /v1/auth/local-login"
    )
    response = json.loads(item["response"][0]["body"])
    parsed = LocalLoginResponse.model_validate(response)
    assert parsed.local_access is True
    assert "capture_profile" in response


def test_quick_start_uses_the_explicit_demo_workspace_without_enrolling_or_capturing():
    for target in collection()["item"]:
        assert target["item"][0]["name"] == "00 Quick start"
        quick = target["item"][0]["item"]
        assert [i["name"] for i in quick] == [
            "GET /health/live",
            "POST /v1/auth/local-select",
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
        if prefix == "localhost":
            assert "POST /v1/auth/change-pending-email" not in requests
            continue
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


def test_download_has_all_inputs_for_installed_local_scenarios():
    public = json.loads(
        (ROOT / "docs/postman/RealityOS.postman_collection.json").read_text()
    )
    fixture = evaluation_dataset()
    variables = {v["key"]: v["value"] for v in public["variable"]}
    environment = json.loads(
        (ROOT / "docs/postman/RealityOS.public.postman_environment.json").read_text()
    )
    assert {v["key"]: v["value"] for v in environment["values"]} == {
        key: value for key, value in variables.items() if not key.startswith("server_")
    }
    assert [folder["name"] for folder in public["item"]] == [
        "Localhost requests",
        "Server requests",
    ]
    scenarios = next(
        folder["item"]
        for folder in public["item"][0]["item"]
        if folder["name"] == "00 Local scenarios"
    )
    assert len(scenarios) == 3
    for target, scenario in zip(scenarios, fixture["scenarios"], strict=True):
        prefix = scenario["prefix"] + "_"
        assert set(scenario["values"]) == {
            "email",
            "username",
            "password",
            "display_name",
            "user_id",
            "workspace_id",
            "record_id",
            "post_id",
            "query",
            "record_question",
            "auth_mode",
        }
        assert target["name"] == scenario["name"]
        core = [
            item for item in target["item"] if not item["name"].startswith("Video ")
        ]
        expected_count = 13 if scenario["values"]["record_id"] else 10
        assert len(core) == expected_count
        assert len({item["name"] for item in core}) == expected_count
        assert variables[prefix + "base_url"] == "http://localhost:8080"
        for key, value in scenario["values"].items():
            assert variables[prefix + key] == value
            assert value or key in {"email", "password", "record_id", "record_question"}
        for key in ("access_token", "refresh_token", "session_identity"):
            assert variables[prefix + key] == ""
        for item in target["item"]:
            request = item["request"]
            if item["name"].startswith("Video "):
                assert request["method"] == "POST"
                assert request["url"]["path"] == ["v1", "queries"]
            assert (
                request["method"] == "GET"
                or item["name"]
                in {
                    "POST /v1/auth/local-select",
                    "POST /v1/auth/refresh",
                    "POST /v1/workspaces/{workspace_id}/records/search",
                    "POST /v1/queries",
                }
                or item["name"].startswith("Video ")
            )
            assert request.get("body", {}).get("mode") != "formdata"
            for ref in re.findall(r"{{([^}]+)}}", json.dumps(request)):
                assert ref.startswith(prefix)
                assert ref in variables
                assert variables[ref] or ref in {
                    prefix + "access_token",
                    prefix + "refresh_token",
                }
            assert not item["response"]
        assert not any(
            key.startswith(prefix) and key.endswith(("integration_key", "device_key"))
            for key in variables
        )


def test_primary_collection_preserves_both_catalogs_and_local_defaults():
    public = json.loads(
        (ROOT / "docs/postman/RealityOS.postman_collection.json").read_text()
    )
    reference = collection()
    values = {v["key"]: v["value"] for v in public["variable"]}
    for target in public["item"]:
        expected = next(t for t in reference["item"] if t["name"] == target["name"])
        assert [
            f for f in target["item"] if f["name"] != "00 Local scenarios"
        ] == expected["item"]
        refs = set(re.findall(r"{{([^}]+)}}", json.dumps(target)))
        assert refs <= values.keys()
        if target["name"] == "Localhost requests":
            assert all(
                key.startswith(("localhost_", "security_", "meta_social_", "memory_"))
                for key in refs
            )
        else:
            assert not any(key.startswith("localhost_") for key in refs)
    local_env = json.loads(
        (ROOT / "docs/postman/RealityOS.local.postman_environment.json").read_text()
    )
    assert {v["key"]: v["value"] for v in local_env["values"]} == {
        key: value for key, value in values.items() if key.startswith("localhost_")
    }
    fixture = evaluation_dataset()
    memory = next(s["values"] for s in fixture["scenarios"] if s["prefix"] == "memory")
    for key in ("email", "password", "workspace_id", "user_id"):
        assert values["localhost_" + key] == memory[key]
    assert values["server_base_url"] == ""
    assert values["localhost_base_url"] == "http://localhost:8080"
    assert values["localhost_password"] == values["server_password"] == ""

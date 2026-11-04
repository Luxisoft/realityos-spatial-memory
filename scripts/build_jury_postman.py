"""Generate the owner-approved public collection for existing server scenarios."""

import copy
import json

from build_video_postman import video_requests

REQUESTS = [
    "GET /v1/auth/me",
    "POST /v1/auth/local-select",
    "POST /v1/auth/refresh",
    "GET /v1/workspaces",
    "GET /v1/workspaces/{workspace_id}/records",
    "GET /v1/workspaces/{workspace_id}/records/{record_id}",
    "GET /v1/workspaces/{workspace_id}/records/{record_id}/revisions",
    "GET /v1/gallery/page",
    "GET /v1/gallery/{post_id}/media",
    "GET /v1/me/profile",
    "GET /v1/profiles/{user_id}",
    "POST /v1/workspaces/{workspace_id}/records/search",
    "POST /v1/queries",
]


def publish(folders, root, write, namespace, describe, check, reference):
    fixture = json.loads((root / "simulator/postman/jury.json").read_text())
    evaluation = json.loads(
        (root / "simulator/real-scenes/video-evaluation.json").read_text()
    )
    local_catalog = json.loads((root / "simulator/local/catalog.json").read_text())
    for video in evaluation["videos"]:
        group = next(
            g for g in local_catalog["groups"] if g["media_group"] == video["group"]
        )
        video["post_id"] = group["publications"][str(video["id"])]
    templates = {item["name"]: item for items in folders.values() for item in items}
    collection = {
        "info": {
            "name": "RealityOS · Live jury evaluation",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "description": "Import this collection, select No environment, open a scenario and click Send on any request. Existing server accounts, passwords, workspace IDs, record IDs, publication IDs and questions are included. Login and token renewal run automatically. All requests use the live RealityOS server and its existing stored data. The owner authorized public release of these three evaluation accounts on 2026-11-03. Their existing workspace roles are administrator. Session tokens and provider credentials are not published. Full API templates are available separately in RealityOS.reference.postman_collection.json.",
        },
        "item": [],
        "variable": [],
    }
    for scenario in fixture["scenarios"]:
        values = dict(
            scenario["values"],
            base_url=fixture["base_url"],
            language="en",
            access_token="",
            refresh_token="",
            session_identity="",
        )
        items = []
        for name in REQUESTS:
            if scenario.get("empty") and name not in {
                "GET /v1/auth/me",
                "POST /v1/auth/local-select",
                "POST /v1/auth/refresh",
                "GET /v1/workspaces",
                "GET /v1/workspaces/{workspace_id}/records",
                "GET /v1/gallery/page",
                "GET /v1/me/profile",
                "GET /v1/profiles/{user_id}",
            }:
                continue
            item = copy.deepcopy(templates[name])
            item["response"] = []
            request = item["request"]
            if name == "POST /v1/queries":
                body = json.loads(request["body"]["raw"])
                body["search_scope"] = "gallery"
                request["body"]["raw"] = json.dumps(body, indent=2)
            if name == "GET /v1/gallery/page":
                for query in request["url"]["query"]:
                    if query["key"] == "workspace_id":
                        query["disabled"] = False
                request["url"]["raw"] += "?workspace_id={{workspace_id}}"
            if name.endswith("/records/search"):
                request["body"]["raw"] = request["body"]["raw"].replace(
                    "{{query}}", "{{record_question}}"
                )
            tests = next(
                e["script"]["exec"] for e in item["event"] if e["listen"] == "test"
            )
            if name == "GET /v1/auth/me":
                tests.append(
                    'pm.test("Expected scenario user", () => pm.expect(pm.response.json().id).to.eql(pm.variables.get("user_id")));'
                )
            elif name in {"GET /v1/me/profile", "GET /v1/profiles/{user_id}"}:
                tests.append(
                    'pm.test("Expected scenario profile", () => pm.expect(pm.response.json().user_id).to.eql(pm.variables.get("user_id")));'
                )
            elif name == "GET /v1/workspaces/{workspace_id}/records/{record_id}":
                tests += [
                    'pm.test("Expected existing record", () => pm.expect(pm.response.json().id).to.eql(pm.variables.get("record_id")));',
                    'pm.test("Expected record workspace", () => pm.expect(pm.response.json().workspace_id).to.eql(pm.variables.get("workspace_id")));',
                ]
            elif name == "GET /v1/workspaces/{workspace_id}/records":
                tests += [
                    'pm.test("Empty workspace records", () => pm.expect(pm.response.json()).to.have.length(0));'
                    if scenario.get("empty")
                    else 'pm.test("Existing record is listed", () => pm.expect(pm.response.json().some(r => r.id === pm.variables.get("record_id"))).to.eql(true));',
                    'pm.test("Records stay in the selected workspace", () => pm.expect(pm.response.json().every(r => r.workspace_id === pm.variables.get("workspace_id"))).to.eql(true));',
                ]
            elif name == "GET /v1/gallery/page":
                tests += [
                    'pm.test("Empty workspace gallery", () => pm.expect(pm.response.json().items).to.have.length(0));'
                    if scenario.get("empty")
                    else 'pm.test("Existing publication is listed", () => pm.expect(pm.response.json().items.some(p => p.id === pm.variables.get("post_id"))).to.eql(true));',
                    'pm.test("Gallery stays in the selected workspace", () => pm.expect(pm.response.json().items.every(p => p.workspace_id === pm.variables.get("workspace_id"))).to.eql(true));',
                ]
            request["description"] += (
                "\n\nReady to send. All inputs use this scenario's existing account and stored resources. Authentication and renewal are automatic."
            )
            items.append(item)
        group = "nursing" if scenario["prefix"] == "hospital" else scenario["prefix"]
        items.extend(
            video_requests(
                templates["POST /v1/queries"],
                [v for v in evaluation["videos"] if v["group"] == group],
            )
        )
        collection["item"].append(
            {
                "name": scenario["name"],
                "description": scenario["workspace_name"]
                + ". Click Send on any request; no setup or manual login is needed.",
                "item": namespace(items, scenario["prefix"], values),
            }
        )
        collection["variable"].extend(
            {
                "key": scenario["prefix"] + "_" + key,
                "value": value,
                "type": "string",
                "description": "Preconfigured evaluation value. " + describe(key),
            }
            for key, value in sorted(values.items())
        )
    scenarios = collection
    collection = copy.deepcopy(reference)
    collection["info"].update(
        name="RealityOS API · Local evaluation",
        description="Start the four local Docker services, select No environment and open Localhost requests. Nine accounts and three scenarios are prepared locally. Authentication uses the local selector; no passwords or provider keys are published. Historical Server requests is disabled. AI requests use your Meta key from the private .env.local file; allow indexing to finish before running video checks.",
    )
    server, localhost = collection["item"]
    server["description"] = (
        "Disabled historical catalog. No server URL, account or password is supplied."
    )
    localhost["description"] = (
        "Primary destination: http://localhost:8080. Local selector, independent sessions, existing scenarios and normal processing."
    )
    localhost["item"].insert(
        1,
        {
            "name": "00 Local scenarios",
            "description": "Police and Memory fixtures, plus Meta Social Media with three accounts and no content. Indexing uses real Meta models.",
            "item": scenarios["item"],
        },
    )
    collection["item"] = [localhost, server]
    collection["variable"].extend(scenarios["variable"])
    write(
        "docs/postman/RealityOS.postman_collection.json",
        json.dumps(collection, indent=2, ensure_ascii=False) + "\n",
        check,
    )
    environment = {
        "name": "RealityOS · Local evaluation (optional)",
        "values": [
            dict(
                v,
                enabled=True,
                type="secret"
                if any(
                    p in v["key"]
                    for p in (
                        "password",
                        "token",
                        "access_key",
                        "secret_key",
                        "device_key",
                        "integration_key",
                    )
                )
                else "default",
            )
            for v in collection["variable"]
            if not v["key"].startswith("server_")
        ],
        "_postman_variable_scope": "environment",
    }
    write(
        "docs/postman/RealityOS.public.postman_environment.json",
        json.dumps(environment, indent=2, ensure_ascii=False) + "\n",
        check,
    )
    return collection

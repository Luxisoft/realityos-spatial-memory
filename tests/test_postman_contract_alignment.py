"""Validate every catalog template against the actual FastAPI request/response models."""

import io
import json
import re
from pathlib import Path

import pytest
from fastapi.routing import APIRoute
from starlette.datastructures import UploadFile

ROOT = Path(__file__).resolve().parents[1]


def substitute(raw):
    def value(match):
        key = match[1].split("_", 1)[1]
        if key.endswith("_id"):
            return "00000000-0000-4000-8000-000000000001"
        if key.endswith("email"):
            return "account@example.test"
        if key.endswith("password"):
            return "OwnPasswordExample123!"
        if key.endswith("token"):
            return "a" * 64
        if key == "language":
            return "en"
        return "example-value"

    return re.sub(r"{{([^}]+)}}", value, raw)


@pytest.fixture(params=["server", "localhost"])
def catalog(client, request):
    from app.http.local_access import router

    routes = {
        f"{method} {route.path}": route
        for route in client.app.routes
        if isinstance(route, APIRoute) and route.include_in_schema
        for method in route.methods
    }
    if request.param == "localhost":
        routes.update(
            {
                f"{method} /v1{route.path}": route
                for route in router.routes
                if isinstance(route, APIRoute)
                for method in route.methods
            }
        )
    collection = json.loads(
        (ROOT / "docs/postman/RealityOS.postman_collection.json").read_text()
    )
    target = collection["item"][0 if request.param == "server" else 1]
    items = {
        item["name"]: item
        for folder in target["item"]
        if not folder["name"].startswith("00 ")
        for item in folder["item"]
    }
    assert items.keys() == routes.keys()
    return [(item, routes[name]) for name, item in items.items()]


def dependencies(dependant):
    yield getattr(dependant.call, "__name__", "")
    for child in dependant.dependencies:
        yield from dependencies(child)


def test_catalog_auth_and_parameter_samples_match_runtime(catalog):
    for item, route in catalog:
        request = item["request"]
        if "get_current_user" in set(dependencies(route.dependant)):
            assert request["auth"]["type"] == "bearer", item["name"]
        headers = [header["key"].lower() for header in request["header"]]
        assert len(headers) == len(set(headers)), item["name"]
        samples = {q["key"]: q for q in request["url"].get("query", [])}
        assert samples.keys() == {field.alias for field in route.dependant.query_params}
        for field in route.dependant.query_params:
            sample = samples[field.alias]
            if field.required:
                assert not sample.get("disabled"), (item["name"], field.alias)
            _, errors = field.validate(
                substitute(sample["value"]), {}, loc=("query", field.alias)
            )
            assert not errors, (item["name"], errors)


def test_catalog_request_and_response_samples_match_runtime(catalog):
    for item, route in catalog:
        request = item["request"]
        body = request.get("body")
        if body:
            if body["mode"] == "raw":
                payload = json.loads(substitute(body["raw"]))
            else:
                assert body["mode"] == "formdata", item["name"]
                assert not any(
                    h["key"].lower() == "content-type" for h in request["header"]
                )
                payload = {
                    field["key"]: UploadFile(
                        io.BytesIO(b"sample"), filename="sample.png"
                    )
                    if field["type"] == "file"
                    else substitute(field["value"])
                    for field in body["formdata"]
                    if not field.get("disabled")
                }
            _, errors = route.body_field.validate(payload, {}, loc=("body",))
            assert not errors, (item["name"], errors)
        else:
            assert route.body_field is None or not route.body_field.required, item[
                "name"
            ]
        if route.response_field:
            assert item["response"], item["name"]
            for response in item["response"]:
                _, errors = route.response_field.validate(
                    json.loads(substitute(response["body"])), {}, loc=("response",)
                )
                assert not errors, (item["name"], errors)

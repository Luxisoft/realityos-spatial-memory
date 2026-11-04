"""Spanish API reference must not silently fall back to handler names in English."""

import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def generator(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("build_api_docs")


def test_every_documented_operation_has_reviewed_spanish_copy(generator):
    labels = json.loads((ROOT / "docs/postman/operation-labels.es.json").read_text())
    for filename in ("openapi.json", "openapi.local.json"):
        spec = json.loads((ROOT / "tests/contracts" / filename).read_text())
        for path, methods in spec["paths"].items():
            for method, operation in methods.items():
                if method not in generator.METHODS:
                    continue
                name = f"{method.upper()} {path}"
                summary = operation.get("summary", name)
                translated = generator.spanish_operation_label(name, summary, labels)
                assert translated.strip() and translated != summary, name


def test_generic_operation_summaries_use_route_specific_copy(generator):
    assert (
        generator.spanish_operation_label(
            "POST /storage",
            "Create",
            {"Create": "Crear", "POST /storage": "Crear conexión"},
        )
        == "Crear conexión"
    )


def test_missing_copy_blocks_document_generation(generator):
    with pytest.raises(ValueError, match="Missing Spanish operation label"):
        generator.spanish_operation_label("GET /new-operation", "New Operation", {})

"""Request language changes presentation, never authorization or original data."""

import ast
from pathlib import Path

import pytest
from app.error_text import SPANISH
from app.models import User
from app.providers.contracts import MetaProviderError
from app.security import create_access_token
from fastapi import HTTPException


@pytest.mark.parametrize(
    "header,expected",
    [
        (None, "Authentication required."),
        ("en-US", "Authentication required."),
        ("fr", "Authentication required."),
        ("es-CO,en;q=0.5", "Debes iniciar sesión."),
        ("es;q=0,en;q=0.5", "Authentication required."),
        ("en;q=NaN,es;q=0.8", "Debes iniciar sesión."),
        ("en;q=bad,es_MX;q=0.8", "Debes iniciar sesión."),
    ],
)
def test_authentication_negotiates_language_without_changing_status(
    client, header, expected
):
    response = client.get(
        "/v1/auth/me", headers={"Accept-Language": header} if header else {}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": expected}
    assert "Accept-Language" in response.headers["vary"]
    assert response.headers["content-language"] == (
        "es" if expected.startswith("Debes") else "en"
    )
    if header and expected.startswith("Debes"):
        assert response.headers["content-language"] == "es"
        assert "Accept-Language" in response.headers["vary"]


def test_validation_localizes_only_messages_and_retains_machine_fields(client):
    payload = {
        "username": "valid.name",
        "email": "invalid-mail",
        "display_name": "Invalid image.",
        "password": "short",
    }
    english = client.post("/v1/auth/register", json=payload)
    spanish = client.post(
        "/v1/auth/register", json=payload, headers={"Accept-Language": "es"}
    )
    assert english.status_code == spanish.status_code == 422
    errors = spanish.json()["detail"]
    assert {e["msg"] for e in errors} == {
        "El correo electrónico no es válido.",
        "El texto debe tener al menos 12 caracteres.",
    }
    assert [{k: v for k, v in e.items() if k != "msg"} for e in errors] == [
        {k: v for k, v in e.items() if k != "msg"} for e in english.json()["detail"]
    ]
    invalid_json = client.post(
        "/v1/auth/register",
        content=b"{",
        headers={"Content-Type": "application/json", "Accept-Language": "es"},
    )
    assert invalid_json.status_code == 422
    assert invalid_json.json()["detail"][0]["msg"] == "El contenido JSON no es válido."


def test_storage_validation_remains_redacted_in_spanish(client, auth_headers):
    response = client.post(
        "/v1/me/storage-connections",
        headers=auth_headers | {"Accept-Language": "es"},
        json={
            "name": "Storage",
            "endpoint": "https://storage.example.test",
            "bucket": "photos",
            "access_key": "sensitive-access-value",
        },
    )
    assert response.status_code == 422
    assert (
        response.json()["detail"][0]["msg"]
        == "Introduce tanto la clave de acceso como la clave secreta."
    )
    assert "sensitive-access-value" not in response.text
    assert all(set(e) == {"loc", "type", "msg"} for e in response.json()["detail"])


def test_group_permissions_and_structured_conflicts_remain_unchanged(
    client, auth_headers
):
    group = client.post(
        "/v1/workspaces", headers=auth_headers, json={"name": "Private group"}
    ).json()["id"]
    with client.app.state.database.session_factory() as db:
        outsider = User(
            email="outsider@example.test",
            display_name="Outside",
            password_hash="unused",
        )
        db.add(outsider)
        db.commit()
        token = create_access_token(outsider.id, client.app.state.settings)
    denied = client.get(
        f"/v1/workspaces/{group}/records",
        headers={"Authorization": "Bearer " + token, "Accept-Language": "es"},
    )
    assert denied.status_code == 403
    assert denied.json() == {"detail": "No tienes acceso a este grupo de trabajo."}
    assert (
        client.get(
            f"/v1/workspaces/{group}/records",
            headers=auth_headers | {"Accept-Language": "es"},
        ).status_code
        == 200
    )
    conflict = client.post(
        "/v1/auth/register",
        headers={"Accept-Language": "es"},
        json={
            "username": "new.name",
            "email": "admin@example.test",
            "display_name": "Name",
            "password": "LongEnoughPassword123!",
        },
    )
    assert conflict.status_code == 409
    assert conflict.json() == {
        "detail": {"code": "registration_conflict", "fields": ["email"]}
    }


@pytest.mark.parametrize("module", ["app.faces", "app.face_setup"])
def test_protected_module_exclusion_does_not_depend_on_path(client, module):
    def protected(value: int = 1):
        raise HTTPException(
            401, "Authentication required.", headers={"WWW-Authenticate": "Bearer"}
        )

    protected.__module__ = module
    client.app.add_api_route("/test-protected-alias", protected, methods=["GET"])
    for suffix in ("", "?value=invalid"):
        english = client.get("/test-protected-alias" + suffix)
        spanish = client.get(
            "/test-protected-alias" + suffix, headers={"Accept-Language": "es"}
        )
        assert spanish.status_code == english.status_code
        assert spanish.json() == english.json()
        assert "content-language" not in spanish.headers
    assert spanish.status_code == 422
    for path in ("/v1/faces/consent", "/v1/faces/setup"):
        response = client.get(path, headers={"Accept-Language": "es"})
        assert response.status_code == 401
        assert response.json() == {"detail": "Authentication required."}


@pytest.mark.parametrize("explicit_cause", [False, True])
def test_provider_errors_and_unknown_details_are_never_translated(
    client, explicit_cause
):
    def provider():
        try:
            raise MetaProviderError("Invalid image.")
        except MetaProviderError as error:
            if not explicit_cause:
                raise HTTPException(503, str(error), headers={"Retry-After": "30"})
            raise HTTPException(
                503, str(error), headers={"Retry-After": "30"}
            ) from error

    client.app.add_api_route("/test-provider-error", provider, methods=["GET"])
    response = client.get("/test-provider-error", headers={"Accept-Language": "es"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Invalid image."}
    assert response.headers["retry-after"] == "30"
    assert "content-language" not in response.headers


def test_face_group_display_errors_keep_original_copy_but_generic_media_is_localized(
    client, auth_headers
):
    for headers in (auth_headers, auth_headers | {"Accept-Language": "es"}):
        invalid_marks = client.post(
            "/v1/display/face-group-links",
            headers=headers,
            data={"marks": "invalid"},
            files={"probe": ("probe.png", b"invalid-image", "image/png")},
        )
        assert invalid_marks.status_code == 422
        assert invalid_marks.json() == {"detail": "Invalid marks."}
        assert "content-language" not in invalid_marks.headers
        unavailable = client.get(
            "/v1/display/face-group?token=invalid", headers=headers
        )
        assert unavailable.status_code == 404
        assert unavailable.json() == {"detail": "Display media unavailable."}
        assert "content-language" not in unavailable.headers
        missing = client.post("/v1/display/face-group-links", headers=headers, json={})
        assert missing.status_code == 422
        assert {error["msg"] for error in missing.json()["detail"]} == {
            "Field required"
        }
        assert "content-language" not in missing.headers
    generic = client.get(
        "/v1/display/media?token=invalid", headers={"Accept-Language": "es"}
    )
    assert generic.status_code == 404
    assert generic.json() == {
        "detail": "El contenido para la pantalla no está disponible."
    }
    assert generic.headers["content-language"] == "es"


def test_error_headers_are_preserved_and_unknown_copy_is_not_mislabeled(client):
    def known():
        raise HTTPException(
            401,
            "Invalid access token.",
            headers={
                "WWW-Authenticate": "Bearer",
                "Vary": "Origin",
                "Retry-After": "30",
            },
        )

    def unknown():
        raise HTTPException(
            502, "Unrecognized provider diagnostic", headers={"Retry-After": "30"}
        )

    client.app.add_api_route("/test-known-error", known, methods=["GET"])
    client.app.add_api_route("/test-unknown-error", unknown, methods=["GET"])
    for language in ("en", "es"):
        response = client.get(
            "/test-known-error", headers={"Accept-Language": language}
        )
        assert response.status_code == 401
        assert response.headers["content-language"] == language
        assert response.headers["www-authenticate"] == "Bearer"
        assert response.headers["retry-after"] == "30"
        assert response.headers["vary"] == "Origin, Accept-Language"
    response = client.get("/test-unknown-error", headers={"Accept-Language": "es"})
    assert response.status_code == 502
    assert response.json() == {"detail": "Unrecognized provider diagnostic"}
    assert "content-language" not in response.headers


def test_account_actions_and_generic_recovery_follow_selected_language(client):
    for action in ("verify", "reset"):
        response = client.get(
            f"/v1/auth/{action}?lang=es", headers={"Accept-Language": "en"}
        )
        assert response.headers["content-language"] == "es"
        assert "'Accept-Language':'es'" in response.text
        assert "r.status===429?words.limited" in response.text
        assert "r.status===400?words.invalid:words.rejected" in response.text
    for action, expected in (
        ("forgot-password", "recuperación"),
        ("resend-confirmation", "confirmación"),
    ):
        response = client.post(
            f"/v1/auth/{action}",
            json={"email": "unknown@example.test"},
            headers={"Accept-Language": "es"},
        )
        assert response.status_code == 202
        assert response.json() == {
            "status": f"Si la cuenta cumple los requisitos, se ha enviado un correo de {expected}."
        }


def test_internal_literal_http_errors_have_authored_copy():
    root = Path(__file__).resolve().parents[1] / "backend" / "app"
    missing = set()
    for path in root.rglob("*.py"):
        if (
            path.name in {"faces.py", "face_setup.py"}
            or "local" in path.relative_to(root).parts
        ):
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            if (
                not isinstance(node, ast.Call)
                or not isinstance(node.func, ast.Name)
                or node.func.id != "HTTPException"
            ):
                continue
            detail = next(
                (k.value for k in node.keywords if k.arg == "detail"),
                node.args[1] if len(node.args) > 1 else None,
            )
            if (
                isinstance(detail, ast.Constant)
                and isinstance(detail.value, str)
                and detail.value not in SPANISH
            ):
                missing.add(detail.value)
    assert not missing


def test_record_authorization_validation_is_localized_without_changing_fields():
    from app.error_handlers import validation_errors
    from app.workspaces.schemas import ImportedRecord
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as invalid:
        ImportedRecord(
            external_id="record-1",
            kind="object",
            title="Owner title",
            version=1,
            status="active",
            authorized=False,
            occurred_at="2026-11-04T10:00:00Z",
        )
    original = invalid.value.errors()
    translated = validation_errors(original, "es")
    assert (
        translated[0]["msg"]
        == "Los registros activos requieren autorización explícita."
    )
    assert translated[0]["input"] == original[0]["input"]
    assert translated[0]["type"] == original[0]["type"]

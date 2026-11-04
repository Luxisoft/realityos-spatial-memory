"""Localize HTTP presentation without changing errors, permissions or payload data."""

import re

from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.error_text import error_text
from app.languages import request_language

PROTECTED_ENDPOINT_MODULES = {"app.faces", "app.face_setup"}
PROTECTED_ENDPOINT_FUNCTIONS = {
    ("app.social_features.display_media", "face_group_link"),
    ("app.social_features.display_media", "face_group_media"),
}
VALIDATION_COPY = {
    "missing": "Este campo es obligatorio.",
    "extra_forbidden": "Este campo no está permitido.",
    "string_type": "El valor debe ser texto.",
    "string_unicode": "El texto contiene caracteres no válidos.",
    "string_pattern_mismatch": "El formato no es válido.",
    "string_too_short": "El texto debe tener al menos {min_length} caracteres.",
    "string_too_long": "El texto no debe superar {max_length} caracteres.",
    "int_type": "El valor debe ser un número entero.",
    "int_parsing": "El valor debe ser un número entero.",
    "int_from_float": "El valor debe ser un número entero.",
    "float_type": "El valor debe ser un número.",
    "float_parsing": "El valor debe ser un número.",
    "finite_number": "El número debe ser finito.",
    "bool_type": "El valor debe ser verdadero o falso.",
    "bool_parsing": "El valor debe ser verdadero o falso.",
    "list_type": "El valor debe ser una lista.",
    "dict_type": "El valor debe ser un objeto.",
    "model_type": "El valor debe ser un objeto válido.",
    "model_attributes_type": "El valor debe ser un objeto válido.",
    "json_invalid": "El contenido JSON no es válido.",
    "json_type": "Se requiere contenido JSON válido.",
    "uuid_type": "El identificador debe ser un UUID válido.",
    "uuid_parsing": "El identificador debe ser un UUID válido.",
    "uuid_version": "La versión del UUID no es válida.",
    "url_type": "La URL no es válida.",
    "url_parsing": "La URL no es válida.",
    "url_scheme": "El protocolo de la URL no está permitido.",
    "date_type": "La fecha no es válida.",
    "date_parsing": "La fecha no es válida.",
    "date_from_datetime_parsing": "La fecha no es válida.",
    "datetime_type": "La fecha y hora no son válidas.",
    "datetime_parsing": "La fecha y hora no son válidas.",
    "datetime_from_date_parsing": "La fecha y hora no son válidas.",
    "timezone_aware": "La fecha debe incluir una zona horaria.",
    "enum": "Selecciona uno de los valores permitidos.",
    "literal_error": "Selecciona uno de los valores permitidos.",
    "greater_than": "El valor debe ser mayor que {gt}.",
    "greater_than_equal": "El valor debe ser mayor o igual que {ge}.",
    "less_than": "El valor debe ser menor que {lt}.",
    "less_than_equal": "El valor debe ser menor o igual que {le}.",
    "multiple_of": "El valor debe ser múltiplo de {multiple_of}.",
    "too_short": "Se requieren al menos {min_length} elementos.",
    "too_long": "No se permiten más de {max_length} elementos.",
}


def protected_endpoint(request):
    endpoint = request.scope.get("endpoint")
    module = getattr(endpoint, "__module__", None)
    return (
        module in PROTECTED_ENDPOINT_MODULES
        or (module, getattr(endpoint, "__name__", None)) in PROTECTED_ENDPOINT_FUNCTIONS
    )


def validation_errors(errors, language):
    result = []
    for error in errors:
        if not isinstance(error, dict) or not isinstance(error.get("msg"), str):
            result.append(error)
            continue
        message = error["msg"]
        custom = message.removeprefix("Value error, ")
        translated = error_text(custom, language)
        if translated == custom:
            template = VALIDATION_COPY.get(error.get("type")) if language == "es" else None
            context = error.get("ctx", {})
            # Storage intentionally removes input/context containing credentials.
            # Read numeric limits only from recognized standard validator copy.
            if not context and error.get("type") in {"string_too_short", "string_too_long"}:
                match = re.fullmatch(
                    r"String should have (at least|at most) (\d+) characters?", message
                )
                if match:
                    key = "min_length" if match[1] == "at least" else "max_length"
                    context = {key: match[2]}
            try:
                translated = template.format(**context) if template else message
            except (KeyError, ValueError):
                translated = message
        result.append({**error, "msg": translated})
    return result


def language_headers(response, language):
    response.headers["Content-Language"] = language
    vary = response.headers.get("Vary", "")
    if "accept-language" not in {v.strip().lower() for v in vary.split(",")}:
        response.headers["Vary"] = ", ".join(filter(None, (vary, "Accept-Language")))
    return response


async def localized_http_error(request, exc):
    cause = exc.__cause__ or (None if exc.__suppress_context__ else exc.__context__)
    cause_module = type(cause).__module__
    forwarded_provider_error = cause_module.startswith(
        ("app.providers.", "httpx")
    ) and exc.detail == str(cause)
    if protected_endpoint(request) or forwarded_provider_error:
        return await http_exception_handler(request, exc)
    language = request_language(request.headers.get("accept-language"))
    detail = exc.detail
    has_localized_copy = False
    if isinstance(detail, str):
        has_localized_copy = error_text(detail, "es") != detail
        detail = error_text(detail, language)
    elif isinstance(detail, list):
        has_localized_copy = validation_errors(detail, "es") != detail
        detail = validation_errors(detail, language)
    response = await http_exception_handler(
        request, HTTPException(exc.status_code, detail, exc.headers)
    )
    return language_headers(response, language) if has_localized_copy else response


async def localized_validation_error(request, exc):
    if protected_endpoint(request):
        return await request_validation_exception_handler(request, exc)
    language = request_language(request.headers.get("accept-language"))
    errors = exc.errors()
    translated = validation_errors(errors, language)
    response = JSONResponse(status_code=422, content=jsonable_encoder({"detail": translated}))
    return (
        language_headers(response, language)
        if validation_errors(errors, "es") != errors
        else response
    )


def register_error_handlers(app):
    app.add_exception_handler(HTTPException, localized_http_error)
    app.add_exception_handler(RequestValidationError, localized_validation_error)

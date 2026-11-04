"""Localize only this gateway's messages; upstream responses remain untouched."""

import math

COPY = {
    "Invalid gateway token.": "El token del gateway no es válido.",
    "Gateway request exceeds the configured size limit.": "La solicitud al gateway supera el tamaño configurado.",
    "Meta upstream is unavailable.": "El servicio de Meta no está disponible.",
    "Not Found": "No se encontró el recurso.",
    "Method Not Allowed": "Método no permitido.",
}


def request_language(request):
    choices = []
    for item in request.headers.get("accept-language", "").split(","):
        tag, *parameters = item.strip().lower().replace("_", "-").split(";")
        quality = 1.0
        try:
            for parameter in parameters:
                name, _, value = parameter.strip().partition("=")
                if name == "q":
                    quality = float(value)
        except ValueError:
            continue
        base = tag.strip().split("-")[0]
        if base in {"es", "en"} and math.isfinite(quality) and 0 < quality <= 1:
            choices.append((quality, base))
    return max(choices, key=lambda value: value[0])[1] if choices else "en"


def message(request, text):
    return COPY.get(text, text) if request_language(request) == "es" else text

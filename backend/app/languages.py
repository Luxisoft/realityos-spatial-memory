"""Resolve supported request languages without translating application data."""

import math


def request_language(header: str | None, fallback: str = "en") -> str:
    choices = []
    for item in (header or "").split(","):
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
    return (
        max(choices, key=lambda value: value[0])[1]
        if choices
        else (fallback if fallback in {"es", "en"} else "en")
    )

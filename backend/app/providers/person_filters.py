"""Offline person-filter interpretation for record questions.

The live provider interprets free phrasing with the model; this deterministic
fallback keeps record search working during outages and in tests. It has no
application imports so providers and services can share it.
"""

from __future__ import annotations

import unicodedata

JUDICIAL_FILTERS = ("warrant", "missing", "proceedings", "no_proceedings", "clean")
PERSON_FILTERS = JUDICIAL_FILTERS + ("person", "none")

# Whole-word person markers ("a young woman", "las personas").
PERSON_LABEL_TOKENS = frozenset(
    {
        "persona",
        "personas",
        "person",
        "persons",
        "people",
        "face",
        "faces",
        "rostro",
        "rostros",
        "cara",
        "caras",
        "man",
        "men",
        "woman",
        "women",
        "hombre",
        "hombres",
        "mujer",
        "mujeres",
        "nino",
        "nina",
        "ninos",
        "boy",
        "girl",
        "child",
        "adult",
        "retrato",
        "portrait",
        "human",
        "humano",
        "humanos",
        "gentleman",
        "lady",
        "caballero",
        "dama",
    }
)

# Accent-stripped qualifier phrases, checked before positive judicial terms so
# that "sin ordenes de captura" never matches the warrant filter.
_CLEAN_PHRASES = (
    "sin orden",
    "sin antecedente",
    "no warrant",
    "no arrest",
    "no criminal",
)
_MISSING_PHRASES = (
    "desaparecid",
    "missing",
    "search order",
    "orden de busqueda",
    "orden busqueda",
)
_NO_PROCEEDINGS_PHRASES = ("sin proceso", "no proceeding", "without proceeding")
_PROCEEDINGS_PHRASES = ("proceso", "proceeding", "judicial")
_WARRANT_PHRASES = (
    "orden de captura",
    "ordenes de captura",
    "orden de arresto",
    "orden de detencion",
    "arrest warrant",
    "detention",
    "detencion",
    "warrant",
    "arresto",
    "arrest",
    "wanted",
    "fugitiv",
    "requerid",
)
_QUALIFIER_PHRASES = (
    _CLEAN_PHRASES,
    _MISSING_PHRASES,
    _NO_PROCEEDINGS_PHRASES,
    _PROCEEDINGS_PHRASES,
    _WARRANT_PHRASES,
)

# Words that never name a record on their own; what remains after removing
# them, person nouns and qualifier phrases decides generic-person questions.
_FILLER_WORDS = frozenset(
    {
        "find",
        "finds",
        "show",
        "shows",
        "search",
        "looking",
        "look",
        "list",
        "lista",
        "with",
        "con",
        "the",
        "all",
        "todas",
        "todos",
        "todo",
        "toda",
        "las",
        "los",
        "del",
        "una",
        "uno",
        "por",
        "favor",
        "please",
        "dime",
        "fotos",
        "photos",
        "videos",
        "imagenes",
        "images",
        "dame",
        "give",
        "necesito",
        "quiero",
        "ver",
        "muestrame",
        "muestren",
        "busca",
        "busco",
        "buscan",
        "buscar",
        "encuentra",
        "encontrar",
    }
)


def normalize(text: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFD", text.casefold())
        if unicodedata.category(char) != "Mn"
    )


def parse_qualifier(question: str) -> str | None:
    """Map a record question to one structured judicial filter, if any."""

    normalized = normalize(question)
    if any(phrase in normalized for phrase in _CLEAN_PHRASES):
        return "clean"
    if any(phrase in normalized for phrase in _MISSING_PHRASES):
        return "missing"
    if any(phrase in normalized for phrase in _NO_PROCEEDINGS_PHRASES):
        return "no_proceedings"
    if any(phrase in normalized for phrase in _PROCEEDINGS_PHRASES):
        return "proceedings"
    if any(phrase in normalized for phrase in _WARRANT_PHRASES):
        return "warrant"
    return None


def is_person_generic(question: str) -> bool:
    """True when the question names people in general, not a specific record."""

    normalized = normalize(question)
    words = [word for word in normalized.replace(",", " ").split() if len(word) > 2]
    if not any(word in PERSON_LABEL_TOKENS for word in words):
        return False
    for phrases in _QUALIFIER_PHRASES:
        for phrase in phrases:
            normalized = normalized.replace(phrase, " ")
    remainder = [
        word
        for word in normalized.replace(",", " ").split()
        if len(word) > 2 and word not in _FILLER_WORDS and word not in PERSON_LABEL_TOKENS
    ]
    return not remainder


def interpret(question: str) -> str:
    """Deterministic offline person-filter interpretation."""

    qualifier = parse_qualifier(question)
    if qualifier is not None:
        return qualifier
    if is_person_generic(question):
        return "person"
    return "none"

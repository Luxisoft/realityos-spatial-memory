"""Gallery-only semantic relations; never changes verified-object retrieval."""

from dataclasses import dataclass, field

from app.meta import MetaProviderError
from app.services import search_phrase

KINDS = ("exact", "family", "similar")
FILLER = {
    "busques",
    "busca",
    "buscar",
    "busquen",
    "buscarme",
    "buscame",
    "ayudes",
    "ayuda",
    "encontrar",
    "encuentres",
    "quisiera",
    "quiero",
    "muestres",
    "muestrame",
    "mostrar",
    "necesito",
    "favor",
    "hola",
    "please",
    "find",
    "show",
    "looking",
}
# Conservative offline bridge for the workshop vocabulary. Generic 'tool' is
# deliberately absent: a box around a toolbox does not locate a pair of pliers.
PLIERS = {
    "exact": ("alicate", "alicates", "pliers", "pinza", "pinzas"),
    "family": (
        "crimping tool",
        "crimping pliers",
        "wire strippers",
        "wire stripper",
        "wire cutter",
        "wire cutters",
        "cutting pliers",
        "needle nose pliers",
        "long nose pliers",
        "locking pliers",
        "tenazas",
        "pelacables",
        "crimpadora",
        "engarzadora",
    ),
    "similar": ("clamp", "metal clamp", "clamping tool", "abrazadera", "mordaza"),
}


def phrase(text):
    return " ".join(w for w in search_phrase(text).split() if w not in FILLER)


def contains(label, term):
    return bool(term) and f" {term} " in f" {label} "


@dataclass
class MatchTerms:
    labels: dict[str, str] = field(default_factory=dict)
    unavailable: bool = False


def classify_terms(question, vocabulary, client):
    """Use the entire authorized detection vocabulary, never caption-only tags."""
    import re

    from app.processing.search import normalize

    # A correction selects its last clause; preserve the full wording for Muse.
    selected = re.split(r"\b(?:mejor|instead|rather)\b", normalize(question))[-1]
    intent = phrase(selected)
    clear_hammer = (
        any(contains(intent, t) for t in ("martillo", "martillos", "hammer", "hammers"))
        and not re.search(r"\b(?:no|not|sin|without|nunca|never)\b", selected)
        and not any(contains(intent, t) for t in PLIERS["exact"])
    )
    output = MatchTerms()
    pliers = intent in PLIERS["exact"]
    # Do not generalize an explicit request for a specialized plier as exact.
    specialized = any(contains(intent, phrase(t)) for t in PLIERS["family"])
    for label in vocabulary:
        name = phrase(label)
        if pliers and not specialized:
            kind = next(
                (k for k in reversed(KINDS) if any(contains(name, phrase(t)) for t in PLIERS[k])),
                None,
            )
            # A specialized plier is family even if its label also contains 'pliers'.
            if any(contains(name, phrase(t)) for t in PLIERS["family"]):
                kind = "family"
        elif clear_hammer:
            kind = (
                "exact"
                if any(contains(name, t) for t in ("hammer", "hammers", "martillo", "martillos"))
                else None
            )
        else:
            kind = "exact" if contains(name, intent) else None
        if kind:
            output.labels[label] = kind
    if client is None or not vocabulary:
        return output
    try:
        interpreted = client.interpret_gallery_matches(question, vocabulary)
    except MetaProviderError:
        output.unavailable = True
        return output
    allowed = {label.casefold(): label for label in vocabulary}
    for kind in KINDS:
        for label in getattr(interpreted, kind):
            canonical = allowed.get(label.casefold())
            if canonical is not None and canonical not in output.labels:
                output.labels[canonical] = kind
    return output

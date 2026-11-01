from __future__ import annotations

import re
import uuid

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.meta import (
    MetaModelClient,
    MetaProviderError,
)
from app.models import (
    ObjectAlias,
    ObjectObservation,
    TrackedObject,
    VerificationStatus,
)


def normalize(value: str) -> str:
    return " ".join(re.sub(r"[^\wáéíóúñü]+", " ", value.casefold()).split())


_QUERY_STOP_WORDS = {
    "a",
    "al",
    "con",
    "cual",
    "cuál",
    "de",
    "del",
    "donde",
    "dónde",
    "el",
    "en",
    "esta",
    "está",
    "este",
    "la",
    "las",
    "lo",
    "los",
    "me",
    "mi",
    "por",
    "que",
    "qué",
    "se",
    "sobre",
    "un",
    "una",
    "and",
    "at",
    "find",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "locate",
    "my",
    "of",
    "please",
    "the",
    "this",
    "where",
    "with",
    "est",
    "où",
    "ou",
    "dans",
    "mon",
    "ma",
    "le",
    "les",
    "du",
    "des",
    "wo",
    "ist",
    "mein",
    "meine",
    "der",
    "die",
    "das",
    "hola",
    "oye",
    "mira",
    "necesito",
    "necesita",
    "necesitas",
    "favor",
    "ayuda",
    "ayúdame",
    "ayudame",
    "ayudes",
    "ayude",
    "buscar",
    "busco",
    "busca",
    "buscan",
    "buscando",
    "encontrar",
    "encuentro",
    "encuentra",
    "dime",
    "puedes",
    "podrías",
    "podrias",
    "quieres",
    "quiero",
    "saber",
    "tienes",
    "tiene",
    "estás",
    "estas",
    "estoy",
    "están",
    "estan",
    "cómo",
    "como",
    "gracias",
    "vale",
    "hello",
    "hey",
    "need",
    "needs",
    "help",
    "thanks",
    "thank",
    "looking",
    "look",
    "show",
    "tell",
    "want",
    "wants",
    "could",
    "would",
    "should",
    "that",
    "what",
    "which",
    "your",
    "you",
    "are",
    "there",
    "here",
    "see",
    "know",
    "have",
    "has",
    "got",
    "search",
    "searching",
    "bonjour",
    "salut",
    "aide",
    "aider",
    "cherche",
    "chercher",
    "trouve",
    "trouver",
    "peux",
    "veux",
    "voir",
    "savoir",
    "merci",
    "hallo",
    "bitte",
    "hilfe",
    "helfen",
    "suche",
    "suchen",
    "finde",
    "finden",
    "kannst",
    "willst",
    "sehen",
    "wissen",
    "danke",
    "ciao",
    "aiuto",
    "cerca",
    "cercare",
    "trova",
    "trovare",
    "puoi",
    "vuoi",
    "vedere",
    "sapere",
    "grazie",
}


def search_phrase(question: str) -> str:
    """Keep only meaningful terms before querying a workspace-local index."""

    return " ".join(
        word
        for word in normalize(question).split()
        if len(word) > 2 and word not in _QUERY_STOP_WORDS
    )


def _candidate_ids_statement(workspace_id: uuid.UUID, phrase: str, dialect_name: str):
    """Build a workspace-scoped candidate query for PostgreSQL or SQLite tests."""

    base = (
        select(TrackedObject.id)
        .outerjoin(ObjectAlias, ObjectAlias.object_id == TrackedObject.id)
        .where(TrackedObject.workspace_id == workspace_id)
    )
    if dialect_name == "postgresql":
        object_vector = func.to_tsvector("simple", TrackedObject.canonical_name)
        alias_vector = func.to_tsvector("simple", ObjectAlias.alias)
        tsquery = func.plainto_tsquery("simple", phrase)
        return base.where(
            or_(
                object_vector.op("@@")(tsquery),
                alias_vector.op("@@")(tsquery),
                func.similarity(TrackedObject.canonical_name, phrase) >= 0.24,
                func.similarity(ObjectAlias.alias, phrase) >= 0.24,
            )
        ).distinct()

    clauses = [TrackedObject.canonical_name.ilike(f"%{word}%") for word in phrase.split()]
    alias_clauses = [ObjectAlias.alias.ilike(f"%{word}%") for word in phrase.split()]
    return base.where(or_(and_(*clauses), and_(*alias_clauses))).distinct()


def object_candidates(
    db: Session,
    workspace_id: uuid.UUID,
    question: str,
    *,
    additional_terms: list[str] | None = None,
) -> list[TrackedObject]:
    phrases = list(
        dict.fromkeys(
            phrase
            for source in [question, *(additional_terms or [])]
            if (phrase := search_phrase(source))
        )
    )
    if not phrases:
        return []
    dialect_name = db.get_bind().dialect.name
    object_ids = list(
        dict.fromkeys(
            object_id
            for phrase in phrases
            for object_id in db.scalars(
                _candidate_ids_statement(workspace_id, phrase, dialect_name)
            ).unique()
        )
    )
    if not object_ids:
        return []
    return list(
        db.scalars(
            select(TrackedObject)
            .where(TrackedObject.id.in_(object_ids))
            .order_by(TrackedObject.canonical_name)
        )
    )


def workspace_terms(db: Session, workspace_id: uuid.UUID) -> list[str]:
    """Return workspace-local vocabulary only; this is never cross-tenant data."""

    canonical = list(
        db.scalars(
            select(TrackedObject.canonical_name)
            .where(TrackedObject.workspace_id == workspace_id)
            .order_by(TrackedObject.canonical_name)
        )
    )
    aliases = list(
        db.scalars(
            select(ObjectAlias.alias)
            .join(TrackedObject, TrackedObject.id == ObjectAlias.object_id)
            .where(TrackedObject.workspace_id == workspace_id)
            .order_by(ObjectAlias.alias)
        )
    )
    # The request stays bounded even in very large authorized workspaces while
    # preserving all canonical terms before optional aliases.
    return list(dict.fromkeys([*canonical, *aliases]))[:1000]


def exact_term_candidates(
    db: Session, workspace_id: uuid.UUID, question: str
) -> list[TrackedObject]:
    """Prefer an authorized human name/alias over broad lexical similarity."""

    requested = search_phrase(question)
    if not requested:
        return []
    tracked = list(
        db.scalars(
            select(TrackedObject)
            .where(TrackedObject.workspace_id == workspace_id)
            .order_by(TrackedObject.canonical_name)
        )
    )
    aliases_by_object: dict[uuid.UUID, list[str]] = {}
    for object_id, alias in db.execute(
        select(ObjectAlias.object_id, ObjectAlias.alias)
        .join(TrackedObject, TrackedObject.id == ObjectAlias.object_id)
        .where(TrackedObject.workspace_id == workspace_id)
    ):
        aliases_by_object.setdefault(object_id, []).append(alias)
    alias_matches = [
        item
        for item in tracked
        if any(search_phrase(alias) == requested for alias in aliases_by_object.get(item.id, []))
    ]
    if alias_matches:
        return alias_matches
    return [item for item in tracked if search_phrase(item.canonical_name) == requested]


def verified_candidates(
    db: Session, workspace_id: uuid.UUID, candidates: list[TrackedObject]
) -> list[TrackedObject]:
    """Keep exact-name collisions honest without hiding multiple verified items."""

    if not candidates:
        return []
    verified_ids = set(
        db.scalars(
            select(ObjectObservation.object_id)
            .where(
                ObjectObservation.workspace_id == workspace_id,
                ObjectObservation.object_id.in_([candidate.id for candidate in candidates]),
                ObjectObservation.verification_status == VerificationStatus.VERIFIED,
            )
            .distinct()
        )
    )
    return [candidate for candidate in candidates if candidate.id in verified_ids]


def multilingual_object_candidates(
    db: Session,
    workspace_id: uuid.UUID,
    question: str,
    client: MetaModelClient | None,
) -> tuple[list[TrackedObject], bool]:
    """Use the provider only to select existing terms; evidence remains local."""

    exact_candidates = exact_term_candidates(db, workspace_id, question)
    if exact_candidates:
        return exact_candidates, False

    interpreted_terms: list[str] = []
    simulated = False
    if client is not None:
        try:
            interpretation = client.interpret_query(question, workspace_terms(db, workspace_id))
            interpreted_terms = interpretation.terms
            simulated = interpretation.simulated
        except MetaProviderError:
            # Local trigram/FTS search is a safe degraded mode: it never invents
            # a match or makes an unavailable provider look successful.
            pass
    if interpreted_terms:
        return object_candidates(
            db, workspace_id, interpreted_terms[0], additional_terms=interpreted_terms[1:]
        ), simulated
    return object_candidates(db, workspace_id, question), simulated

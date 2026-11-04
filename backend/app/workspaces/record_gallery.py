"""Boxed publication matches for person-record questions.

Record questions ("people with active arrest warrants") filter structured
workspace data; the linked portrait publications supply the boxed thumbnails
from their already indexed gallery evidence. Person presence comes from
Meta/SAM detection labels, never from face embeddings or identity matching,
so this module stays outside the biometric arm.
"""

from __future__ import annotations

import unicodedata
import uuid
from urllib.parse import urlencode

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, defer

from app.models import MediaAsset, User
from app.social_features.evidence import usable_detection
from app.social_features.evidence_models import GalleryEvidence, GalleryIndexRun
from app.social_features.models import Publication
from app.social_features.publication_access import visible
from app.workspaces.models import Record, RecordMedia

GALLERY_LIMIT = 6

# Whole-word person markers in indexed detection labels ("a young woman").
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
    "arrest warrant",
    "warrant",
    "arresto",
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


def _normalize(text: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFD", text.casefold())
        if unicodedata.category(char) != "Mn"
    )


def parse_qualifier(question: str) -> str | None:
    """Map a record question to one structured judicial filter, if any."""

    normalized = _normalize(question)
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


def _record_data(record: Record) -> dict:
    return record.data if isinstance(record.data, dict) else {}


def qualifier_matches(record: Record, qualifier: str) -> bool:
    """Structured judicial predicates over person-record data."""

    data = _record_data(record)
    warrant = data.get("has_active_warrant") is True
    missing = data.get("has_active_search_order") is True or data.get("is_missing") is True
    proceedings = data.get("has_active_proceedings") is True
    if qualifier == "warrant":
        return warrant
    if qualifier == "missing":
        return missing
    if qualifier == "proceedings":
        return proceedings
    if qualifier == "no_proceedings":
        return not proceedings
    if qualifier == "clean":
        return not warrant and not missing and not proceedings
    return False


def _is_person_generic(question: str) -> bool:
    """True when the question names people in general, not a specific record."""

    normalized = _normalize(question)
    words = [word for word in normalized.replace(",", " ").split() if len(word) > 2]
    if not any(word in PERSON_LABEL_TOKENS for word in words):
        return False
    for phrases in (
        _CLEAN_PHRASES,
        _MISSING_PHRASES,
        _NO_PROCEEDINGS_PHRASES,
        _PROCEEDINGS_PHRASES,
        _WARRANT_PHRASES,
    ):
        for phrase in phrases:
            normalized = normalized.replace(phrase, " ")
    remainder = [
        word
        for word in normalized.replace(",", " ").split()
        if len(word) > 2 and word not in _FILLER_WORDS and word not in PERSON_LABEL_TOKENS
    ]
    return not remainder


def candidate_records(
    db: Session,
    workspace_id: uuid.UUID,
    question: str,
    retrieved: list[Record],
    limit: int = GALLERY_LIMIT,
) -> list[Record]:
    """Person records behind the gallery, in display order."""

    qualifier = parse_qualifier(question)
    if qualifier is not None:
        rows = db.scalars(
            select(Record)
            .where(
                Record.workspace_id == workspace_id,
                Record.status == "active",
                Record.kind == "person",
            )
            .order_by(Record.occurred_at.desc(), Record.id)
        )
        return [row for row in rows if qualifier_matches(row, qualifier)][:limit]
    persons = [
        row
        for row in retrieved
        if row.workspace_id == workspace_id and row.status == "active" and row.kind == "person"
    ]
    if persons:
        return persons[:limit]
    if _is_person_generic(question):
        return list(
            db.scalars(
                select(Record)
                .where(
                    Record.workspace_id == workspace_id,
                    Record.status == "active",
                    Record.kind == "person",
                )
                .order_by(Record.occurred_at.desc(), Record.id)
                .limit(limit)
            )
        )
    return []


def _current_evidence(db: Session, post: Publication) -> list[GalleryEvidence]:
    """Current indexed evidence rows, mirroring gallery search currency."""

    rows = list(
        db.scalars(
            select(GalleryEvidence)
            .options(defer(GalleryEvidence.image_bytes))
            .where(
                GalleryEvidence.post_id == post.id,
                GalleryEvidence.media_id == post.media_id,
            )
            .order_by(GalleryEvidence.version.desc(), GalleryEvidence.created_at.desc())
        )
    )
    if post.active_index_run_id:
        rows = [row for row in rows if row.index_run_id == post.active_index_run_id]
    else:
        rows = [
            row
            for row in rows
            if row.index_run_id is None and not (row.version < 2 and post.evidence_version >= 2)
        ]
    current = []
    for row in rows:
        if row.index_run_id is not None:
            run = db.get(GalleryIndexRun, row.index_run_id)
            if run is None or run.status != "ready":
                continue
        current.append(row)
    return current


def _is_person_label(label: object) -> bool:
    if not isinstance(label, str):
        return False
    words = _normalize(label).replace(",", " ").split()
    return any(word in PERSON_LABEL_TOKENS for word in words)


def _person_detections(post: Publication, evidence: GalleryEvidence) -> list[dict]:
    current = post.ai_detections or []
    matches = []
    for detection in evidence.detections:
        if not usable_detection(detection) or not _is_person_label(detection.get("label")):
            continue
        if (
            detection in current
            or {**detection, "frame_timestamp_ms": evidence.frame_timestamp_ms} in current
        ):
            matches.append(detection)
    return matches


def record_gallery(
    db: Session,
    user: User,
    workspace_id: uuid.UUID,
    question: str,
    retrieved: list[Record],
    limit: int = GALLERY_LIMIT,
) -> list[dict]:
    """Boxed publication thumbnails for the person records behind a question.

    Every item reuses the gallery match shape (thumbnail, boxed and full-size
    image URLs), so chat shows the framed person in both sizes. Items without
    an indexed person box are skipped instead of inventing an annotation.
    """

    from app.social_features.localizations import LANGUAGES, display_information, stored_rows

    items: list[dict] = []
    seen_posts: set[uuid.UUID] = set()
    for record in candidate_records(db, workspace_id, question, retrieved, limit):
        links = db.scalars(
            select(RecordMedia).where(
                RecordMedia.record_id == record.id,
                RecordMedia.publication_id.is_not(None),
            )
        )
        for link in links:
            if link.publication_id in seen_posts or len(items) >= limit:
                continue
            post = db.get(Publication, link.publication_id)
            if (
                post is None
                or post.workspace_id != workspace_id
                or post.hidden
                or post.media_id != link.media_id
            ):
                continue
            try:
                visible(post, user, db)
            except HTTPException:
                continue
            ranked = []
            for evidence in _current_evidence(db, post):
                matches = _person_detections(post, evidence)
                if matches:
                    ranked.append(
                        (
                            -evidence.version,
                            -max(item["confidence"] for item in matches),
                            evidence.frame_timestamp_ms or 0,
                            evidence,
                            matches,
                        )
                    )
            if not ranked:
                continue
            _, _, _, evidence, matches = min(ranked, key=lambda row: row[:3])
            asset = db.get(MediaAsset, post.media_id, options=[defer(MediaAsset.original_bytes)])
            if asset is None:
                continue
            seen_posts.add(post.id)
            labels = list(dict.fromkeys(item["label"] for item in matches))
            url = f"/v1/gallery/evidence/{evidence.id}?" + urlencode({"labels": ",".join(labels)})
            items.append(
                dict(
                    post_id=str(post.id),
                    media_id=str(asset.id),
                    evidence_id=str(evidence.id),
                    record_id=str(record.id),
                    caption=post.caption or "",
                    ai_caption=post.ai_caption or "",
                    thumbnail_url=url,
                    boxed_url=url,
                    media_url=f"/v1/gallery/{post.id}/media",
                    image_url=url + "&full_size=true",
                    mime_type=asset.mime_type,
                    frame_timestamp_ms=evidence.frame_timestamp_ms,
                    note_text=post.note_text or "",
                    note_source=post.note_source or "",
                    matched_labels=labels,
                    confidence=max(item["confidence"] for item in matches),
                    match_kind="exact",
                    localization_quality="sam" if evidence.version >= 2 else "approximate_box",
                    published_at=post.published_at.isoformat(),
                    simulated=any(item.get("simulated") for item in matches),
                )
            )
            break
    translations = stored_rows(db, [uuid.UUID(item["post_id"]) for item in items])
    for item in items:
        item["localized_information"] = {}
        for language in LANGUAGES:
            text = display_information(
                translations,
                uuid.UUID(item["post_id"]),
                uuid.UUID(item["post_id"]),
                language,
                item["caption"],
                item["note_text"],
                item["matched_labels"],
            )
            if text is not None:
                item["localized_information"][language] = text
    return items

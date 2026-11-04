"""Prepare bilingual text at write time; reads never call or enqueue a model."""

import hashlib

from sqlalchemy import select

from app.providers.contracts import MetaProviderError
from app.social_features.evidence_models import GalleryEvidence, PublicationTranslation

LANGUAGES = ("en", "es")


def text_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def publication_texts(db, post):
    labels = {d.get("label", "") for d in post.ai_detections or [] if isinstance(d, dict)}
    for detections in db.scalars(
        select(GalleryEvidence.detections).where(GalleryEvidence.post_id == post.id)
    ):
        labels.update(d.get("label", "") for d in detections if isinstance(d, dict))
    return {
        text
        for text in (post.caption or "", post.note_text or "", *labels)
        if isinstance(text, str) and text.strip()
    }


def stored_rows(db, post_ids):
    if not post_ids:
        return {}
    return {
        (row.post_id, row.language, row.text_hash): row
        for row in db.scalars(
            select(PublicationTranslation).where(PublicationTranslation.post_id.in_(post_ids))
        )
    }


def prepare_languages(client, texts):
    # Numeric keys keep model output compact. Persist only a complete pair.
    keys = {str(i): text for i, text in enumerate(sorted({text for text in texts if text.strip()}))}
    result = (
        client.prepare_gallery_languages(keys) if keys else {language: {} for language in LANGUAGES}
    )
    if (
        not isinstance(result, dict)
        or set(result) != set(LANGUAGES)
        or any(
            not isinstance(result[language], dict)
            or set(result[language]) != set(keys)
            or any(not isinstance(t, str) or not t.strip() for t in result[language].values())
            for language in LANGUAGES
        )
    ):
        raise MetaProviderError("Both publication languages must be ready before publishing.")
    return {
        language: {text_hash(text): result[language][key] for key, text in keys.items()}
        for language in LANGUAGES
    }


def persist(db, post_id, translated, simulated=False):
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    insert = pg_insert if db.get_bind().dialect.name == "postgresql" else sqlite_insert
    values = [
        dict(
            post_id=post_id,
            language=language,
            text_hash=digest,
            translated_text=value,
            simulated=simulated,
        )
        for language, texts in translated.items()
        for digest, value in texts.items()
    ]
    for start in range(0, len(values), 100):
        db.execute(
            insert(PublicationTranslation)
            .values(values[start : start + 100])
            .on_conflict_do_nothing()
        )
    db.flush()


def prepare_posts(db, posts, client, batch_size=48):
    """Administrative/indexing operation, including old labels kept in history."""
    existing = stored_rows(db, [post.id for post in posts])
    per_post = {post.id: publication_texts(db, post) for post in posts}
    missing = {
        text
        for post_id, texts in per_post.items()
        for text in texts
        if any((post_id, language, text_hash(text)) not in existing for language in LANGUAGES)
    }
    translations = {language: {} for language in LANGUAGES}
    missing = sorted(missing)
    for start in range(0, len(missing), batch_size):
        prepared = prepare_languages(client, missing[start : start + batch_size])
        for language in LANGUAGES:
            translations[language].update(prepared[language])
    simulated = client.__class__.__name__.startswith("Mock")
    for post_id, texts in per_post.items():
        digests = {text_hash(text) for text in texts}
        persist(
            db,
            post_id,
            {
                language: {
                    digest: translated for digest, translated in values.items() if digest in digests
                }
                for language, values in translations.items()
            },
            simulated,
        )
    return len(missing)


def display_information(rows, post_id, label_post_id, language, title, note, labels):
    if language not in LANGUAGES:
        return None
    requested = [(post_id, title), (post_id, note), *((label_post_id, label) for label in labels)]
    values, simulated = [], False
    for owner, text in requested:
        if not text.strip():
            values.append("")
            continue
        row = rows.get((owner, language, text_hash(text)))
        if row is None:
            return None
        values.append(row.translated_text)
        simulated |= row.simulated
    return dict(
        title=values[0], note_text=values[1], matched_labels=values[2:], simulated=simulated
    )

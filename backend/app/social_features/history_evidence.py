"""Refresh old chat resource snapshots from authorized immutable evidence."""

import uuid
from urllib.parse import parse_qs, urlencode, urlsplit

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import defer

from app.models import MediaAsset
from app.social_features.evidence import readable_post, term_matches, usable_detection
from app.social_features.evidence_models import GalleryEvidence
from app.social_features.localizations import LANGUAGES, display_information, stored_rows
from app.social_features.models import ChatMessage, Publication


def reference(item):
    evidence_id, post_id = None, None
    try:
        if item.get("evidence_id"):
            evidence_id = uuid.UUID(str(item["evidence_id"]))
    except ValueError:
        pass
    terms = [t for t in item.get("matched_labels", []) if isinstance(t, str)]
    for key in ("boxed_url", "image_url", "thumbnail_url", "media_url"):
        parsed = urlsplit(item.get(key) or "")
        parts = parsed.path.strip("/").split("/")
        try:
            if len(parts) == 4 and parts[:2] == ["v1", "gallery"]:
                if parts[2] == "evidence":
                    evidence_id = evidence_id or uuid.UUID(parts[3])
                elif parts[3] in ("boxed", "thumbnail", "media"):
                    post_id = post_id or uuid.UUID(parts[2])
        except ValueError:
            pass
        if not terms:
            terms = [
                t.strip()
                for value in parse_qs(parsed.query).get("labels", [])
                for t in value.split(",")
                if t.strip()
            ]
    return evidence_id, post_id, terms


def question_before(db, user, message_id):
    return (
        db.scalar(
            select(ChatMessage.text)
            .where(
                ChatMessage.user_id == user.id,
                ChatMessage.id < message_id,
                ChatMessage.role == "user",
            )
            .order_by(ChatMessage.id.desc())
            .limit(1)
        )
        or ""
    )


def history_matches(label, terms, question):
    from app.social_features.retrieval_terms import PLIERS, classify_terms, contains, phrase

    if terms:
        if term_matches(label, terms):
            return "exact"
        if any(phrase(term) == "clamp" for term in terms) and any(
            contains(phrase(label), name) for name in ("bench vise", "bench vice")
        ):
            return "similar"
        return None
    relation = classify_terms(question, [label], None).labels.get(label)
    if relation:
        return relation
    if phrase(question) in PLIERS["exact"] and any(
        contains(phrase(label), name)
        for name in ("tweezers", "scissors", "bench vise", "bench vice")
    ):
        return "similar"
    return None


def refresh_item(db, user, item, question=""):

    eid, pid, terms = reference(item)
    if not eid and not pid:
        return item  # Unknown historical attachment types remain unchanged.
    try:
        if eid:
            evidence = db.get(GalleryEvidence, eid, options=[defer(GalleryEvidence.image_bytes)])
            if evidence is None:
                return None
            post = readable_post(db, evidence.post_id, user)
            choices = [evidence]
        else:
            post = readable_post(db, pid, user)
            original = db.get(Publication, pid)
            media_id = (
                uuid.UUID(str(item["media_id"])) if item.get("media_id") else original.media_id
            )
            choices = list(
                db.scalars(
                    select(GalleryEvidence)
                    .options(defer(GalleryEvidence.image_bytes))
                    .where(
                        GalleryEvidence.post_id == pid,
                        GalleryEvidence.media_id == media_id,
                    )
                    .order_by(GalleryEvidence.version.desc(), GalleryEvidence.created_at.desc())
                )
            )
        ranked = []
        for candidate in choices:
            if candidate.index_run_id:
                from app.social_features.evidence_models import GalleryIndexRun

                if db.get(GalleryIndexRun, candidate.index_run_id).status != "ready":
                    continue
            detections = [
                d
                for d in candidate.detections
                if usable_detection(d) and history_matches(d["label"], terms, question)
            ]
            if detections:
                ranked.append(
                    (
                        candidate.version,
                        max(d["confidence"] for d in detections),
                        candidate,
                        detections,
                    )
                )
        if not ranked:
            # The old result did not retain a recoverable annotation. Preserve
            # and localize its information without fabricating a marked object.
            rows = stored_rows(db, {post.id})
            localized = {
                language: text
                for language in LANGUAGES
                if (
                    text := display_information(
                        rows,
                        post.id,
                        post.id,
                        language,
                        post.caption or "",
                        post.note_text or "",
                        [],
                    )
                )
                is not None
            }
            return {
                **item,
                "caption": post.caption or "",
                "note_text": post.note_text or "",
                "localized_information": localized,
                "legacy_information_only": True,
            }
        _, score, evidence, detections = max(ranked, key=lambda x: x[:2])
        asset = db.get(MediaAsset, evidence.media_id, options=[defer(MediaAsset.original_bytes)])
        labels = list(dict.fromkeys(d["label"] for d in detections))
        url = f"/v1/gallery/evidence/{evidence.id}?" + urlencode({"labels": ",".join(labels)})
        from app.social_features.retrieval_terms import KINDS, classify_terms

        relations = classify_terms(question, labels, None).labels
        kinds = list(relations.values())
        if not kinds and item.get("match_kind") in KINDS:
            kinds = [item["match_kind"]]
        if not kinds:
            kinds = [history_matches(d["label"], terms, question) for d in detections]
        kind = min((value for value in kinds if value in KINDS), key=KINDS.index, default=None)
        rows = stored_rows(db, {post.id, evidence.post_id})
        localized = {}
        for language in LANGUAGES:
            text = display_information(
                rows,
                post.id,
                evidence.post_id,
                language,
                post.caption or "",
                post.note_text or "",
                labels,
            )
            if text is not None:
                localized[language] = text
        return {
            **item,
            "post_id": str(post.id),
            "match_kind": kind,
            "evidence_id": str(evidence.id),
            "media_id": str(asset.id),
            "caption": post.caption or "",
            "note_text": post.note_text or "",
            "note_source": post.note_source or "",
            "matched_labels": labels,
            "confidence": score,
            "published_at": post.published_at.isoformat(),
            "mime_type": asset.mime_type,
            "frame_timestamp_ms": evidence.frame_timestamp_ms,
            "thumbnail_url": url,
            "boxed_url": url,
            "image_url": url + "&full_size=true",
            "localized_information": localized,
            "localization_quality": "sam" if evidence.version >= 2 else "approximate_box",
        }
    except (HTTPException, ValueError, AttributeError):
        return None


def refreshed_gallery(db, user, gallery, question=""):
    return [
        value
        for item in gallery or []
        if isinstance(item, dict)
        if (value := refresh_item(db, user, item, question)) is not None
    ]


def persist_refreshed_history(db, user, evidence_ids=None):
    changed = 0
    for row in db.scalars(
        select(ChatMessage).where(ChatMessage.user_id == user.id).order_by(ChatMessage.id)
    ):
        if not row.gallery:
            continue
        if evidence_ids is not None and not any(
            str(reference(item)[0]) in evidence_ids
            for item in row.gallery
            if isinstance(item, dict)
        ):
            continue
        # Keep unresolved original references in storage; read projections hide
        # unavailable media without destroying historical attachment records.
        question = question_before(db, user, row.id)
        gallery = [
            refresh_item(db, user, item, question) or item if isinstance(item, dict) else item
            for item in row.gallery
        ]
        if gallery != row.gallery:
            row.gallery = gallery
            changed += 1
    db.flush()
    return changed

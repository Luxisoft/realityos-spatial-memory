"""Owner-selected, idempotent publication copies with group-local interactions."""

from fastapi import HTTPException
from sqlalchemy import select

from app.social_features.evidence_models import GalleryEvidence, PublicationTranslation
from app.social_features.models import Publication
from app.social_features.uploads import check_destination


def import_publications(db, user, workspace_id, publication_ids):
    check_destination(db, user, "work", workspace_id)
    # Same-owner serialization prevents duplicate copies across simultaneous requests.
    db.refresh(user, with_for_update=True)
    from app.social_features.gallery import get_post

    originals = [get_post(key, user, db) for key in dict.fromkeys(publication_ids)]
    if any(post.owner_id != user.id for post in originals):
        raise HTTPException(403, "Only your own publications can be imported.")
    result = []
    for post in originals:
        root = post.shared_from_id or post.id
        copy = db.scalar(
            select(Publication).where(
                Publication.workspace_id == workspace_id,
                (Publication.id == root) | (Publication.shared_from_id == root),
            )
        )
        if copy:
            if copy.hidden:
                copy.hidden = False
            result.append({"source_id": str(post.id), "id": str(copy.id), "status": "existing"})
            continue
        copy = Publication(
            owner_id=user.id,
            media_id=post.media_id,
            audience="work",
            workspace_id=workspace_id,
            shared_from_id=root,
            source="workspace-share",
            source_ref=f"{root}:{workspace_id}",
            published_at=post.published_at,
        )
        for name in (
            "caption",
            "note_text",
            "note_source",
            "ai_labels",
            "ai_detections",
            "search_text",
            "ai_caption",
            "indexed_at",
            "evidence_version",
        ):
            setattr(copy, name, getattr(post, name))
        db.add(copy)
        db.flush()
        for evidence in db.scalars(
            select(GalleryEvidence).where(
                GalleryEvidence.post_id == post.id, GalleryEvidence.media_id == post.media_id
            )
        ):
            db.add(
                GalleryEvidence(
                    post_id=copy.id,
                    media_id=post.media_id,
                    image_bytes=evidence.image_bytes,
                    content_hash=evidence.content_hash,
                    frame_timestamp_ms=evidence.frame_timestamp_ms,
                    detections=evidence.detections,
                    version=evidence.version,
                )
            )
        for translation in db.scalars(
            select(PublicationTranslation).where(PublicationTranslation.post_id == post.id)
        ):
            db.add(
                PublicationTranslation(
                    post_id=copy.id,
                    language=translation.language,
                    text_hash=translation.text_hash,
                    translated_text=translation.translated_text,
                    simulated=translation.simulated,
                )
            )
        result.append({"source_id": str(post.id), "id": str(copy.id), "status": "imported"})
    db.flush()
    return {"items": result, "workspace_id": str(workspace_id)}

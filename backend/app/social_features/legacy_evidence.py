"""Explicit administrative repair of existing image boxes, without inference.

Version 1 is approximate localization. Query never invokes this operation and
SAM version 2 remains the only completed reindex version on Publication.
"""

import io

from PIL import Image
from sqlalchemy import select

from app.models import MediaAsset, MediaKind
from app.social_features.evidence import usable_detection
from app.social_features.evidence_models import GalleryEvidence
from app.social_features.models import Publication
from app.social_features.visual import normalize


def repair_image(db, post):
    db.refresh(post, with_for_update=True)
    if post.hidden or post.evidence_version >= 2:
        return False
    asset = db.get(MediaAsset, post.media_id)
    if asset is None or asset.kind != MediaKind.IMAGE:
        return False
    if db.scalar(
        select(GalleryEvidence.id).where(
            GalleryEvidence.post_id == post.id,
            GalleryEvidence.media_id == post.media_id,
            GalleryEvidence.version == 1,
        )
    ):
        return False
    # Old boxes were derived from original encoded pixels. Rotated EXIF images
    # require a fresh pass: never guess which coordinate space the model used.
    with Image.open(io.BytesIO(asset.original_bytes)) as image:
        if image.getexif().get(274, 1) not in (None, 1):
            return False
    detections = [
        d
        for d in post.ai_detections or []
        if usable_detection(d)
        and d.get("frame_index", 0) == 0
        and all(float(d["box"][k]) >= 0 for k in ("x", "y"))
        and float(d["box"]["x"]) + float(d["box"]["width"]) <= 1.000001
        and float(d["box"]["y"]) + float(d["box"]["height"]) <= 1.000001
    ]
    if not detections:
        return False
    image, _, _, digest, _ = normalize(asset.original_bytes)
    db.add(
        GalleryEvidence(
            post_id=post.id,
            media_id=post.media_id,
            image_bytes=image,
            content_hash=digest,
            detections=detections,
            version=1,
        )
    )
    db.flush()
    return True


def repair(database):
    counts = dict(repaired=0, skipped=0, invalid=0)
    with database.session_factory() as db:
        ids = list(
            db.scalars(
                select(Publication.id).where(
                    Publication.hidden.is_(False),
                    Publication.evidence_version < 2,
                )
            )
        )
    for key in ids:
        with database.session_factory() as db:
            try:
                changed = repair_image(db, db.get(Publication, key))
                counts["repaired" if changed else "skipped"] += 1
                db.commit()
            except (ValueError, OSError):
                db.rollback()
                counts["invalid"] += 1
    return counts

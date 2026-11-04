"""Resumable, serial gallery upgrade and reversible duplicate retirement."""

from __future__ import annotations

from sqlalchemy import select

from app.models import MediaAsset
from app.providers.contracts import MetaProviderError
from app.social_features.evidence_models import PublicationDuplicate, PublicationRevision
from app.social_features.models import Comment, Publication, Reaction, Report
from app.social_features.upload_service import duplicate, scope_lock


def retire(db, post, canonical):
    media_before = {post.id: post.media_id, canonical.id: canonical.media_id}
    # Lock and refresh the destinations after Meta finishes, before moving notes/activity.
    for row in sorted((post, canonical), key=lambda item: str(item.id)):
        db.refresh(row, with_for_update=True)
        if row.media_id != media_before[row.id]:
            raise ValueError("Publication media changed during duplicate review.")
    if post.hidden or canonical.hidden:
        raise ValueError("Publication visibility changed during duplicate review.")
    if post.owner_id != canonical.owner_id or post.workspace_id != canonical.workspace_id:
        raise ValueError("Cannot merge different publication scopes")
    previous = {"hidden": post.hidden, "comments": [], "reactions": [], "reports": []}
    for comment in db.scalars(select(Comment).where(Comment.post_id == post.id)):
        previous["comments"].append(str(comment.id))
        comment.post_id = canonical.id
    for reaction in db.scalars(select(Reaction).where(Reaction.post_id == post.id)):
        if db.get(Reaction, (canonical.id, reaction.user_id)) is None:
            previous["reactions"].append(str(reaction.user_id))
            reaction.post_id = canonical.id
    for report in db.scalars(select(Report).where(Report.post_id == post.id)):
        exists = db.scalar(
            select(Report).where(Report.post_id == canonical.id, Report.user_id == report.user_id)
        )
        if exists is None:
            previous["reports"].append(str(report.id))
            report.post_id = canonical.id
    db.add(
        PublicationRevision(
            post_id=canonical.id,
            previous={"note_text": canonical.note_text, "duplicate_post": str(post.id)},
        )
    )
    if post.note_text and post.note_text not in (canonical.note_text or ""):
        canonical.note_text = ((canonical.note_text or "") + "\n" + post.note_text).strip()[:4000]
    post.hidden = True
    db.add(PublicationDuplicate(post_id=post.id, canonical_id=canonical.id, previous=previous))
    old_asset = db.get(MediaAsset, post.media_id)
    new_asset = db.get(MediaAsset, canonical.media_id)
    identity = (new_asset.extra_metadata or {}).get("visual_identity", new_asset.sha256)
    for asset in (old_asset, new_asset):
        asset.extra_metadata = {**(asset.extra_metadata or {}), "visual_identity": identity}


def rebuild(database, client, limit=0):
    from app.gallery_index import index_publication
    from app.social_features.repair_inventory import inventory

    with database.session_factory() as db:
        selections = inventory(db)
    counts = dict(indexed=0, duplicates=0, failed=0, skipped=0)
    for selection in selections[: limit or len(selections)]:
        key = __import__("uuid").UUID(selection["post_id"])
        with database.session_factory() as db:
            post = db.get(Publication, key)
            if post.hidden:
                continue
            asset = db.get(MediaAsset, post.media_id)
            try:
                scope_lock(db, post.owner_id, post.workspace_id)
                if asset.mime_type.startswith("image/") and not selection["review_only"]:
                    match = duplicate(
                        db,
                        client,
                        asset.original_bytes,
                        post.owner_id,
                        post.workspace_id,
                        older_than=post,
                    )
                    if match:
                        retire(db, post, match)
                        from app.social_features.localizations import prepare_posts

                        prepare_posts(db, [match], client)
                        counts["duplicates"] += 1
                        db.commit()
                        continue
                    identity_match = duplicate(
                        db, client, asset.original_bytes, post.owner_id, None, None, older_than=post
                    )
                    if identity_match:
                        identity_asset = db.get(MediaAsset, identity_match.media_id)
                        asset.extra_metadata = {
                            **(asset.extra_metadata or {}),
                            "visual_identity": (identity_asset.extra_metadata or {}).get(
                                "visual_identity", identity_asset.sha256
                            ),
                        }
                result = index_publication(
                    db,
                    key,
                    client,
                    force=True,
                    deduplicate=False,
                    checkpoint=True,
                    recover_legacy=True,
                    review_only=selection["review_only"],
                )
                counts["failed" if result.index_error else "indexed"] += 1
                db.commit()
            except (MetaProviderError, ValueError, OSError) as error:
                db.rollback()
                post = db.get(Publication, key)
                post.index_error = str(error)[:1000]
                db.commit()
                counts["failed"] += 1
    return counts

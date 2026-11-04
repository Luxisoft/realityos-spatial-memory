"""Import group takes over 5 photo slots per directory profile.

For each profile, the group generator overwrote ``muse/<slug>/photo-{02,04,
06,08,10}.jpg`` with owner-plus-companions takes. This script swaps the
imported bytes: it deletes the 5 old photo assets (enrollments cascade),
resets their inventory rows, and re-imports through the production
``import_facebook_media`` path, which enrolls EVERY face found — owner and
companions alike — so cross-profile face search can be tested. Work
publications are rebuilt afterwards.

Dry-run by default; pass ``--apply`` to write. Run inside the ``api``
container with the refreshed ``muse/`` tree under ``--fixture-root``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _extra in (ROOT / "backend", ROOT / "scripts"):
    if _extra.is_dir() and str(_extra) not in sys.path:
        sys.path.append(str(_extra))

from sqlalchemy import select  # noqa: E402

import seed_social_directory as seed  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.db import Database  # noqa: E402
from app.models import MediaAsset, Workspace  # noqa: E402
from app.social import (  # noqa: E402
    Comment,
    FacebookMedia,
    Publication,
    Reaction,
    Report,
    import_facebook_media,
)
from generate_group_photos import GROUP_SLOTS  # noqa: E402


def refresh_profile(db, settings, workspace, row, index: int, *, apply: bool) -> dict:
    slug, _name, profession, region, _gender, tags = row
    user_id = seed.stable_uuid("user", slug)
    fb_ids = [f"directory-{slug}-photo-{slot + 1:02d}" for slot in GROUP_SLOTS]
    rows = [db.get(FacebookMedia, fb_id) for fb_id in fb_ids]
    if any(item is None or item.user_id != user_id for item in rows):
        raise RuntimeError(f"[{slug}] inventory rows are missing or reassigned.")
    asset_ids = [item.imported_media_id for item in rows if item.imported_media_id]
    work_pubs = list(
        db.scalars(
            select(Publication).where(
                Publication.owner_id == user_id,
                Publication.source == "simulator-work",

            )
        )
    )
    feed_pubs = list(
        db.scalars(
            select(Publication).where(
                Publication.owner_id == user_id,
                Publication.source_ref.in_(fb_ids),
            )
        )
    )
    counts = {
        "assets": len(asset_ids),
        "work_pubs": len(work_pubs),
        "feed_pubs": len(feed_pubs),
        "slots": len(rows),
    }
    if not apply:
        return counts
    for post in work_pubs:
        db.delete(post)
    for post in feed_pubs:
        for interaction in db.scalars(
            select(Comment).where(Comment.post_id == post.id)
        ):
            db.delete(interaction)
        for report in db.scalars(select(Report).where(Report.post_id == post.id)):
            db.delete(report)
        for reaction in db.scalars(
            select(Reaction).where(Reaction.post_id == post.id)
        ):
            db.delete(reaction)
        db.delete(post)
    db.flush()
    for asset_id in asset_ids:
        asset = db.get(MediaAsset, asset_id)
        if asset is not None:
            db.delete(asset)
    for slot, item in zip(GROUP_SLOTS, rows):
        item.imported_media_id = None
        item.caption = (
            seed.scene_caption(slug, f"photo-{slot + 1:02d}.jpg", profession, region, slot)
            + " · con amigos"
        )
    db.flush()
    result = import_facebook_media(db, settings, user_id, fetch_bytes=seed.local_fetch)
    counts["import"] = result
    touched = list(
        db.scalars(
            select(Publication).where(
                Publication.owner_id == user_id,
                Publication.source_ref.in_(fb_ids),
            )
        )
    )
    for post in touched:

        post.source = "simulator"
        post.search_text = f"{post.caption} {profession} {region} {tags}"
    photo_pub = next(
        (
            post
            for post in db.scalars(
                select(Publication)
                .where(
                    Publication.owner_id == user_id,
                    Publication.source == "simulator",
                )
                .order_by(Publication.published_at.desc())
            )
            if db.get(MediaAsset, post.media_id) is not None
            and db.get(MediaAsset, post.media_id).mime_type.startswith("image/")
        ),
        None,
    )
    if photo_pub is not None:
        db.add(
            Publication(
                owner_id=user_id,
                media_id=photo_pub.media_id,

                workspace_id=workspace.id,
                caption=photo_pub.caption,
                search_text=photo_pub.search_text,
                source="simulator-work",
                source_ref=f"work-{slug}-photo",
                published_at=photo_pub.published_at,
            )
        )
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--slugs", default="")
    parser.add_argument("--fixture-root", default=str(seed.FIXTURE_ROOT))
    args = parser.parse_args()

    fixture_root = Path(args.fixture_root)
    seed.FIXTURE_ROOT = fixture_root
    seed.SOURCE_ROOT = fixture_root / "source"
    seed.GENERATED_ROOT = fixture_root / "generated"
    seed.MUSE_ROOT = fixture_root / "muse"
    wanted = {slug.strip() for slug in args.slugs.split(",") if slug.strip()}

    settings = get_settings()
    database = Database(settings.database_url)
    with database.session_factory() as db:
        workspace = db.scalar(
            select(Workspace).where(Workspace.name == seed.DEMO_WORKSPACE)
        )
        workspace_id = workspace.id
    rows = [
        (index, row)
        for index, row in enumerate(seed.PROFILE_ROWS)
        if not wanted or row[0] in wanted
    ]
    for index, row in rows:
        with database.session_factory() as db:
            workspace = db.get(Workspace, workspace_id)
            counts = refresh_profile(db, settings, workspace, row, index, apply=args.apply)
            if args.apply:
                db.commit()
            else:
                db.rollback()
            print(f"{'refreshed' if args.apply else 'would refresh'} {row[0]}: {counts}")


if __name__ == "__main__":
    main()
"""Inspect or enqueue the resumable, serial gallery evidence upgrade."""

import argparse

from app.config import get_settings
from app.db import Database
from app.social_features.models import Publication
from sqlalchemy import func, select


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Enqueue Live analysis and duplicate retirement; default is read-only.",
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--pending-only",
        action="store_true",
        help="Repair only incomplete search files, serially with durable per-file tasks.",
    )
    parser.add_argument(
        "--repair-legacy-images",
        action="store_true",
        help="Materialize existing valid image boxes (approximate v1); no provider calls.",
    )
    args = parser.parse_args()
    db = Database(get_settings().database_url)
    if args.pending_only:
        from app.social_features.repair_inventory import pending_inventory

        with db.session_factory() as session:
            items = pending_inventory(session)
        items = items[: args.limit or len(items)]
        print(f"Pending search files: {len(items)}", flush=True)
        if args.apply and items:
            from app.tasks import repair_gallery_publication
            from celery import chain

            result = chain(
                *(
                    repair_gallery_publication.si(item["post_id"], item["media_id"])
                    for item in items
                )
            ).apply_async()
            print(f"Task: {result.id}", flush=True)
        return
    with db.session_factory() as session:
        from app.social_features.repair_inventory import inventory

        repairs = inventory(session)
        print(f"Selective repairs: {len(repairs)}", flush=True)
        pending = session.scalar(
            select(func.count())
            .select_from(Publication)
            .where(Publication.hidden.is_(False), Publication.evidence_version < 2)
        )
    print(f"Pending publications: {pending}", flush=True)
    if args.repair_legacy_images:
        if not args.apply:
            parser.error("--repair-legacy-images requires --apply")
        from app.social_features.legacy_evidence import repair

        print(repair(db), flush=True)
        return
    if args.apply:
        from app.tasks import rebuild_gallery_evidence

        task = rebuild_gallery_evidence.delay(max(0, args.limit))
        print(f"Task: {task.id}", flush=True)


if __name__ == "__main__":
    main()

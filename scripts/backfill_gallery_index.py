"""Enqueue AI indexing for gallery publications missing an index.

Usage (from repo root, backend venv active):
    .venv/bin/python -m app --help                 # not this; run as script:
    PYTHONPATH=backend .venv/bin/python scripts/backfill_gallery_index.py --dry-run
    PYTHONPATH=backend .venv/bin/python scripts/backfill_gallery_index.py --limit 50

Each image costs one Meta analysis call; each video up to three (sampled
frames). Indexing runs on the worker; this script only enqueues.
"""

from __future__ import annotations

import argparse

from app.config import get_settings
from app.db import Database
from app.gallery_index import queue_publication_index
from app.social import Publication
from sqlalchemy import select


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill gallery AI index queue.")
    parser.add_argument("--limit", type=int, default=0, help="Max publications (0 = all).")
    parser.add_argument("--dry-run", action="store_true", help="List candidates only.")
    parser.add_argument("--force", action="store_true", help="Re-index already indexed rows.")
    args = parser.parse_args()

    settings = get_settings()
    database = Database(settings.database_url)
    with database.session_factory() as db:
        statement = select(Publication.id).order_by(Publication.published_at.desc())
        if not args.force:
            statement = statement.where(Publication.indexed_at.is_(None))
        if args.limit > 0:
            statement = statement.limit(args.limit)
        ids = list(db.scalars(statement))
    print(f"candidates without index: {len(ids)}")
    if args.dry_run:
        return 0
    for publication_id in ids:
        queue_publication_index(publication_id, force=args.force)
    print(f"enqueued: {len(ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

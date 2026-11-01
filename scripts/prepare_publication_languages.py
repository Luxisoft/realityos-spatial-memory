"""Explicit, resumable bilingual preparation; viewing never starts this job."""

import argparse
import json

from app.config import get_settings
from app.db import Database
from app.meta import MetaProviderError, build_meta_client
from app.social_features.localizations import (
    LANGUAGES,
    persist,
    prepare_languages,
    publication_texts,
    stored_rows,
    text_hash,
)
from app.social_features.models import Publication
from sqlalchemy import case, select


def missing(database):
    with database.session_factory() as db:
        posts = list(
            db.scalars(
                select(Publication).order_by(
                    case((Publication.source == "workshop", 0), else_=1),
                    Publication.published_at.desc(),
                )
            )
        )
        existing = stored_rows(db, [p.id for p in posts])
        targets = {}
        for post in posts:
            # Capture only text snapshots. Originals, media and evidence stay intact.
            for text in sorted(publication_texts(db, post)):
                digest = text_hash(text)
                for language in LANGUAGES:
                    if (post.id, language, digest) not in existing:
                        item = targets.setdefault(
                            digest, {"text": text, "destinations": {}}
                        )
                        item["destinations"].setdefault(post.id, set()).add(language)
    return targets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--batch-size", type=int, default=48)
    args = parser.parse_args()
    database = Database(get_settings().database_url)
    targets = list(missing(database).values())
    print(json.dumps({"missing_unique_texts": len(targets)}), flush=True)
    if not args.apply:
        return
    client = build_meta_client(get_settings())
    size = min(64, max(1, args.batch_size))
    completed, failed = 0, 0
    for start in range(0, len(targets), size):
        chunk = targets[start : start + size]
        try:
            translated = prepare_languages(client, [item["text"] for item in chunk])
            per_post = {}
            for item in chunk:
                digest = text_hash(item["text"])
                for post_id, languages in item["destinations"].items():
                    for language in languages:
                        per_post.setdefault(post_id, {}).setdefault(language, {})[
                            digest
                        ] = translated[language][digest]
            with database.session_factory() as db:
                for post_id, values in per_post.items():
                    persist(db, post_id, values, get_settings().meta_mode == "mock")
                db.commit()
            completed += len(chunk)
        except MetaProviderError as error:
            failed += len(chunk)
            print(json.dumps({"batch_error": str(error)[:300]}), flush=True)
        print(
            json.dumps(
                {
                    "prepared_unique_texts": completed,
                    "failed_unique_texts": failed,
                    "total": len(targets),
                }
            ),
            flush=True,
        )
    remaining = len(missing(database))
    print(json.dumps({"remaining_unique_texts": remaining}), flush=True)
    if remaining:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

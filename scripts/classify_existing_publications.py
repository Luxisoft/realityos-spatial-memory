"""Apply reviewed, hash-bound publication classifications; dry-run by default.

Run inside the server runtime after the classification migration. This never
creates groups, imports media, changes evidence, or calls an inference provider.
"""

import argparse
import hashlib
import json
import os
import uuid
from pathlib import Path

from app.config import get_settings
from app.db import Database
from app.models import MediaAsset, MediaAssetChunk
from app.social_features import evidence_models  # noqa: F401 -- register upload/evidence foreign keys
from app.social_features.classification import (
    add_term,
    classification_json,
    set_classification,
)
from app.social_features.models import Publication, PublicationTag, PublicationTerm
from app.social_features.publication_visibility import publication_content
from sqlalchemy import delete, select


def media_hash(db, asset):
    digest = hashlib.sha256()
    if asset.original_bytes:
        digest.update(asset.original_bytes)
    else:
        for chunk in db.scalars(
            select(MediaAssetChunk)
            .where(MediaAssetChunk.asset_id == asset.id)
            .order_by(MediaAssetChunk.chunk_index)
        ):
            digest.update(chunk.content)
    return digest.hexdigest()


def reviewed_posts(db, manifest):
    rows = []
    seen = set()
    for item in manifest["items"]:
        key = uuid.UUID(item["post_id"])
        if key in seen:
            raise ValueError(f"Repeated publication: {key}")
        seen.add(key)
        post = db.scalar(
            select(Publication).where(
                Publication.id == key,
                Publication.hidden.is_(False),
                publication_content(),
            )
        )
        if post is None or str(post.workspace_id) != item["workspace_id"]:
            raise ValueError(f"Publication unavailable or destination changed: {key}")
        asset = db.get(MediaAsset, post.media_id)
        if media_hash(db, asset) != item["media_sha256"]:
            raise ValueError(f"Original changed since visual review: {key}")
        if not item["category"].strip() or not item["tags"]:
            raise ValueError(f"Incomplete reviewed classification: {key}")
        rows.append((post, item))
    return rows


def save_journal(path, journal):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as output:
        json.dump(journal, output, ensure_ascii=False, indent=2)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())


def apply_review(db, manifest, journal_path):
    rows = reviewed_posts(db, manifest)
    journal = {"version": 1, "publications": [], "created_terms": []}
    for post, item in rows:
        db.refresh(post, with_for_update=True)
        if (
            str(post.workspace_id) != item["workspace_id"]
            or media_hash(db, db.get(MediaAsset, post.media_id)) != item["media_sha256"]
        ):
            raise ValueError(f"Publication changed during review: {post.id}")
        previous = classification_json(db, post)
        terms = []
        for kind, name in [
            ("category", item["category"]),
            *[("tag", tag) for tag in item["tags"]],
        ]:
            name = " ".join(name.split())
            term = db.scalar(
                select(PublicationTerm).where(
                    PublicationTerm.workspace_id == post.workspace_id,
                    PublicationTerm.kind == kind,
                    PublicationTerm.name_key == name.casefold(),
                )
            )
            if term is None:
                term = add_term(db, post.workspace_id, kind, name)
                journal["created_terms"].append(str(term.id))
            elif not term.active:
                raise ValueError(f"Reviewed catalog value was archived: {name}")
            terms.append(term)
        if post.category_id == terms[0].id and {t["id"] for t in previous["tags"]} == {
            str(t.id) for t in terms[1:]
        }:
            continue
        set_classification(db, post, terms[0].id, [t.id for t in terms[1:]])
        journal["publications"].append(
            {
                "post_id": str(post.id),
                "previous": previous,
                "assigned": classification_json(db, post),
            }
        )
    if journal["publications"] or journal["created_terms"]:
        save_journal(journal_path, journal)
        db.commit()
    return {
        "reviewed": len(rows),
        "classified": len(journal["publications"]),
        "created_terms": len(journal["created_terms"]),
        "journal": str(journal_path),
    }


def rollback_review(db, journal, apply=False):
    posts = {}
    for change in journal["publications"]:
        post = db.scalar(
            select(Publication)
            .where(Publication.id == uuid.UUID(change["post_id"]))
            .with_for_update()
        )
        if post is None or classification_json(db, post) != change["assigned"]:
            raise ValueError(
                f"Publication changed after classification: {change['post_id']}"
            )
        posts[change["post_id"]] = post
    if apply:
        for change in journal["publications"]:
            post = posts[change["post_id"]]
            previous = change["previous"]
            post.category_id = (
                uuid.UUID(previous["category"]["id"]) if previous["category"] else None
            )
            db.execute(delete(PublicationTag).where(PublicationTag.post_id == post.id))
            db.add_all(
                PublicationTag(post_id=post.id, term_id=uuid.UUID(tag["id"]))
                for tag in previous["tags"]
            )
        # Leave catalog IDs intact: later publications or queued uploads may refer to them.
        db.commit()
    return {"rollback_publications": len(journal["publications"]), "applied": apply}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("simulator/real-scenes/publication-classification.json"),
    )
    parser.add_argument(
        "--journal",
        type=Path,
        default=Path(".runtime/publication-classification-journal.json"),
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--rollback", action="store_true")
    args = parser.parse_args()
    database = Database(get_settings().database_url)
    try:
        with database.session_factory() as db:
            if args.rollback:
                result = rollback_review(
                    db, json.loads(args.journal.read_text()), args.apply
                )
            else:
                manifest = json.loads(args.manifest.read_text())
                if args.apply:
                    result = apply_review(db, manifest, args.journal)
                else:
                    rows = reviewed_posts(db, manifest)
                    result = {
                        "reviewed": len(rows),
                        "groups": len({p.workspace_id for p, _ in rows}),
                        "applied": False,
                    }
            print(json.dumps(result))
    finally:
        database.engine.dispose()


if __name__ == "__main__":
    main()

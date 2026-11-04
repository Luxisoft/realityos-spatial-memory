import hashlib
import json
import runpy
from pathlib import Path

import pytest
from app.models import MediaAsset, MediaKind, User, Workspace
from app.social_features.classification import classification_json
from app.social_features.models import Publication
from sqlalchemy import select

SCRIPT = runpy.run_path(
    str(
        Path(__file__).resolve().parents[1]
        / "scripts/classify_existing_publications.py"
    )
)


def existing_publication(db):
    owner = db.scalar(select(User))
    group = Workspace(name="Existing work group", created_by_id=owner.id)
    db.add(group)
    db.flush()
    raw = b"original media retained by the classification operation"
    asset = MediaAsset(
        workspace_id=group.id,
        kind=MediaKind.IMAGE,
        mime_type="image/jpeg",
        original_bytes=raw,
        byte_size=len(raw),
        sha256=hashlib.sha256(raw).hexdigest(),
    )
    db.add(asset)
    db.flush()
    post = Publication(
        owner_id=owner.id,
        workspace_id=group.id,
        media_id=asset.id,
        caption="Original caption",
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    manifest = {
        "items": [
            {
                "post_id": str(post.id),
                "workspace_id": str(group.id),
                "media_sha256": asset.sha256,
                "category": "Equipment",
                "tags": ["Radio"],
            }
        ]
    }
    return post, asset, manifest


def test_review_is_idempotent_and_rollback_preserves_media(client, tmp_path):
    with client.app.state.database.session_factory() as db:
        post, asset, manifest = existing_publication(db)
        before = (post.media_id, post.caption, post.published_at, asset.original_bytes)
        journal = tmp_path / "review.json"
        result = SCRIPT["apply_review"](db, manifest, journal)
        assert result["classified"] == 1
        assert classification_json(db, post)["category"]["name"] == "Equipment"
        repeated = SCRIPT["apply_review"](db, manifest, journal)
        assert repeated["classified"] == repeated["created_terms"] == 0
        assert (
            post.media_id,
            post.caption,
            post.published_at,
            asset.original_bytes,
        ) == before
        SCRIPT["rollback_review"](db, json.loads(journal.read_text()), apply=True)
        assert classification_json(db, post) == {"category": None, "tags": []}
        assert (
            post.media_id,
            post.caption,
            post.published_at,
            asset.original_bytes,
        ) == before


def test_changed_original_or_group_cannot_receive_reviewed_classification(
    client, tmp_path
):
    with client.app.state.database.session_factory() as db:
        post, asset, manifest = existing_publication(db)
        asset.original_bytes = b"a newer original"
        db.commit()
        with pytest.raises(ValueError, match="Original changed"):
            SCRIPT["apply_review"](db, manifest, tmp_path / "never-written.json")
        assert classification_json(db, post) == {"category": None, "tags": []}
        assert not (tmp_path / "never-written.json").exists()

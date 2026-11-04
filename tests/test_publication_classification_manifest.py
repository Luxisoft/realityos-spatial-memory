"""Reviewed classification belongs to the same persisted publications and groups."""

from app.models import MediaAsset, Workspace
from app.social_features.models import Publication, PublicationTag, PublicationTerm
from sqlalchemy import select


def test_every_prepared_publication_has_scoped_classification(evaluation):
    with evaluation.app.state.database.session_factory() as db:
        publications = list(db.scalars(select(Publication)))
        assert len(publications) == 25
        assert {p.workspace_id for p in publications} == set(
            db.scalars(select(Workspace.id))
        )
        for post in publications:
            original = db.get(MediaAsset, post.media_id)
            category = db.get(PublicationTerm, post.category_id)
            assert original.original_bytes and len(original.sha256) == 64
            assert (
                category.kind == "category"
                and category.workspace_id == post.workspace_id
            )
            tags = list(
                db.scalars(
                    select(PublicationTerm)
                    .join(PublicationTag)
                    .where(PublicationTag.post_id == post.id)
                )
            )
            assert 1 <= len(tags) <= 20
            assert len(tags) == len({tag.name_key for tag in tags})
            assert all(
                tag.kind == "tag" and tag.workspace_id == post.workspace_id
                for tag in tags
            )
            assert all(tag.name.strip() and len(tag.name) <= 80 for tag in tags)

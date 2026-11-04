"""Local gallery additions keep group isolation and preserve user edits."""

import uuid
from pathlib import Path

import pytest
from app.security import create_access_token
from app.social_features.models import Publication
from app.workspaces.models import RecordMedia
from local_support import catalog


@pytest.mark.parametrize("evaluation", ["baseline"], indirect=True)
def test_existing_installation_uses_shared_catalog_without_duplicate_media(
    evaluation, monkeypatch
):
    from app.models import MediaAsset
    from app.social_features.models import PublicationTag
    from sqlalchemy import delete, select, update

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from app.local.upgrades import upgrade_local_data
    from app.local_models import LocalEvaluationState

    def seed_local_publications(db, settings):
        result = upgrade_local_data(db, settings).get("local-group-publications-v1")
        return {"initialized": result is not None, **(result or {})}

    groups = [
        g
        for g in catalog(evaluation)["groups"]
        if g["slug"] in {"security", "meta-social"}
    ]
    ids = [uuid.UUID(value) for g in groups for value in g["publications"].values()]
    with evaluation.app.state.database.session_factory() as db:
        db.delete(db.get(LocalEvaluationState, "local-group-publications-v1"))
        originals = {
            p.id: p.media_id
            for p in db.scalars(select(Publication).where(Publication.id.in_(ids)))
        }
        ids = list(originals)
        media_count = db.query(MediaAsset).count()
        db.execute(
            update(RecordMedia)
            .where(RecordMedia.publication_id.in_(ids))
            .values(publication_id=None)
        )
        db.execute(delete(PublicationTag).where(PublicationTag.post_id.in_(ids)))
        db.execute(delete(Publication).where(Publication.id.in_(ids)))
        db.commit()
        assert seed_local_publications(db, evaluation.app.state.settings) == {
            "initialized": True,
            "publications": 13,
        }
        db.commit()
        assert db.query(MediaAsset).count() == media_count
        assert {
            p.id: p.media_id
            for p in db.scalars(select(Publication).where(Publication.id.in_(ids)))
        } == originals
        assert (
            seed_local_publications(db, evaluation.app.state.settings)["initialized"]
            is False
        )


def test_publication_seed_gallery_scope_and_restart(evaluation, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from app.local.upgrades import upgrade_local_data

    def seed_local_publications(db, settings):
        result = upgrade_local_data(db, settings).get("local-group-publications-v1")
        return {"initialized": result is not None, **(result or {})}

    with evaluation.app.state.database.session_factory() as db:
        result = seed_local_publications(db, evaluation.app.state.settings)
        db.commit()
        assert result == {"initialized": False}
        assert (
            db.query(RecordMedia)
            .filter(RecordMedia.publication_id.is_not(None))
            .count()
            == 16
        )
    social = next(
        g for g in catalog(evaluation)["groups"] if g["name"] == "Meta Social Media"
    )
    police = next(g for g in catalog(evaluation)["groups"] if "Police" in g["name"])

    def auth(group):
        return {
            "Authorization": "Bearer "
            + create_access_token(
                uuid.UUID(group["users"][0]["id"]), evaluation.app.state.settings
            )
        }

    for group, image_count in ((social, 3), (police, 16)):
        response = evaluation.get(
            "/v1/gallery/page",
            params={"workspace_id": group["id"], "limit": 30},
            headers=auth(group),
        )
        assert response.status_code == 200, response.text
        posts = response.json()["items"]
        assert len(posts) == image_count + 3
        images = [p for p in posts if p["mime_type"].startswith("image/")]
        videos = [p for p in posts if p["mime_type"].startswith("video/")]
        assert len(images) == image_count and len(videos) == 3
        assert all(
            p["note_text"] and p["display_text"]["note_text"]["es"] for p in images
        )
        for post in posts:
            assert (
                evaluation.get(
                    "/v1/" + post["media_url"], headers=auth(group)
                ).status_code
                == 200
            )
        outsider = auth(police if group == social else social)
        assert evaluation.get(
            "/v1/" + posts[0]["media_url"], headers=outsider
        ).status_code in (403, 404)
        with evaluation.app.state.database.session_factory() as db:
            first = db.get(Publication, uuid.UUID(posts[0]["id"]))
            first.caption = "Edited by owner"
            removed_id = uuid.UUID(posts[1]["id"])
            # Hide instead of deleting a case-linked publication.
            db.get(Publication, removed_id).hidden = True
            db.commit()
            assert (
                seed_local_publications(db, evaluation.app.state.settings)[
                    "initialized"
                ]
                is False
            )
            assert first.caption == "Edited by owner"
            assert db.get(Publication, removed_id).hidden
        with (
            evaluation.app.state.database.session_factory() as db,
            pytest.raises(ValueError, match="local"),
        ):
            seed_local_publications(
                db,
                evaluation.app.state.settings.model_copy(
                    update={"environment": "production"}
                ),
            )

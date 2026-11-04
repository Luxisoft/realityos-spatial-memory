"""Local gallery additions keep group isolation and preserve user edits."""

import uuid
from pathlib import Path

import pytest
from app.local_catalog import catalog
from app.security import create_access_token
from app.social_features.models import Publication
from app.workspaces.models import RecordMedia
from test_local_evaluation import evaluation as evaluation  # noqa: PLC0414


def test_publication_seed_gallery_scope_and_restart(evaluation, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from seed_local_publications import seed_local_publications

    with evaluation.app.state.database.session_factory() as db:
        result = seed_local_publications(db, evaluation.app.state.settings)
        db.commit()
        assert result == {"initialized": True, "publications": 13}
        assert (
            db.query(RecordMedia)
            .filter(RecordMedia.publication_id.is_not(None))
            .count()
            == 10
        )
    social = next(g for g in catalog()["groups"] if g["name"] == "Meta Social Media")
    police = next(g for g in catalog()["groups"] if "Police" in g["name"])

    def auth(group):
        return {
            "Authorization": "Bearer "
            + create_access_token(
                uuid.UUID(group["users"][0]["id"]), evaluation.app.state.settings
            )
        }

    for group, count in ((social, 3), (police, 10)):
        response = evaluation.get(
            "/v1/gallery/page",
            params={"workspace_id": group["id"]},
            headers=auth(group),
        )
        assert response.status_code == 200, response.text
        posts = response.json()["items"]
        assert len(posts) == count
        assert all(
            p["note_text"] and p["display_text"]["note_text"]["es"] for p in posts
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

import json

# The shared pytest fixture is injected by name.
# ruff: noqa: F811
import uuid

from app.local_catalog import FIXTURES, catalog
from app.local_display import RECEIPT, install_display_text
from app.local_models import LocalEvaluationState
from app.social_features.classification import term_json
from app.social_features.models import Publication, PublicationTerm, UserProfile
from app.stored_display import display_text
from app.workspaces.models import Record, RecordRevision
from sqlalchemy import select
from test_local_evaluation import evaluation  # noqa: F401


def test_all_prepared_display_fields_have_both_languages(evaluation):
    fixture = json.loads(
        (FIXTURES / "local/display-text.json").read_text(encoding="utf-8")
    )
    with evaluation.app.state.database.session_factory() as db:
        assert db.get(LocalEvaluationState, RECEIPT)
        for group in fixture["groups"]:
            for collection, model in (
                ("records", Record),
                ("publications", Publication),
                ("profiles", UserProfile),
            ):
                for item in group[collection]:
                    row = db.get(model, uuid.UUID(item["id"]))
                    assert display_text(row) == item["fields"]
                    assert all(
                        set(pair) == {"source", "en", "es"}
                        for pair in row.display_text.values()
                    )
            terms = db.scalars(
                select(PublicationTerm).where(
                    PublicationTerm.workspace_id == uuid.UUID(group["id"])
                )
            ).all()
            assert len(terms) == len(group["terms"])
            assert all(
                set(term_json(term)["display_text"]["name"]) == {"source", "en", "es"}
                for term in terms
            )


def test_authored_copy_is_membership_scoped_and_does_not_rewrite_history(evaluation):
    group, other = catalog()["groups"][2], catalog()["groups"][1]
    response = evaluation.post(
        "/v1/auth/local-select", json={"user_id": group["users"][0]["id"]}
    )
    headers = {"Authorization": "Bearer " + response.json()["access_token"]}
    path = f"/v1/groups/{group['id']}/publication-catalog"
    body = evaluation.get(path, headers=headers).json()
    assert body["tags"][0]["display_text"]["name"]["en"]
    assert evaluation.get(path).status_code == 401
    assert evaluation.get(
        f"/v1/groups/{other['id']}/publication-catalog", headers=headers
    ).status_code in (403, 404)
    records = evaluation.get(
        f"/v1/workspaces/{group['id']}/records", headers=headers
    ).json()
    assert all(r["display_text"]["title"]["en"] for r in records)
    english = evaluation.get(
        f"/v1/workspaces/{group['id']}/records?q=folder", headers=headers
    ).json()
    spanish = evaluation.get(
        f"/v1/workspaces/{group['id']}/records?q=carpeta", headers=headers
    ).json()
    assert english and {r["id"] for r in english} == {r["id"] for r in spanish}
    with evaluation.app.state.database.session_factory() as db:
        record = db.scalar(select(Record))
        revision = db.scalar(
            select(RecordRevision).where(RecordRevision.record_id == record.id)
        )
        assert revision.snapshot["title"] == record.title
        assert revision.snapshot["display_text"] == {}


def test_copy_preserves_edits_deletions_and_never_masks_later_edits(evaluation):
    with evaluation.app.state.database.session_factory() as db:
        record = db.scalar(select(Record))
        record.title = "My updated title"
        assert "title" not in display_text(record)
        term = db.scalar(select(PublicationTerm))
        term.name = "My updated tag"
        assert term_json(term)["display_text"] == {}
        profile = db.scalar(select(UserProfile))
        user_id = profile.user_id
        db.delete(profile)
        db.delete(db.get(LocalEvaluationState, RECEIPT))
        db.flush()
        install_display_text(db, evaluation.app.state.settings)
        assert record.title == "My updated title"
        assert term.name == "My updated tag"
        assert db.get(UserProfile, user_id) is None
        db.commit()
        install_display_text(db, evaluation.app.state.settings)
        assert db.get(UserProfile, user_id) is None

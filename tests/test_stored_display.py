# The shared pytest fixture is injected by name.

from app.local.upgrades import upgrade_local_data
from local_support import catalog

RECEIPT = "bilingual-copy-v1"
from app.local_models import LocalEvaluationState
from app.social_features.classification import term_json
from app.social_features.models import Publication, PublicationTerm, UserProfile
from app.stored_display import display_text
from app.workspaces.models import Record, RecordRevision
from sqlalchemy import select


def test_all_prepared_display_fields_have_both_languages(evaluation):
    with evaluation.app.state.database.session_factory() as db:
        assert db.get(LocalEvaluationState, RECEIPT)
        for model, expected in (
            (Record, 16),
            (Publication, 25),
            (UserProfile, 6),
            (PublicationTerm, 10),
        ):
            rows = list(db.scalars(select(model)))
            assert len(rows) == expected
            for row in rows:
                assert row.display_text
                assert display_text(row) == row.display_text
                for field, pair in row.display_text.items():
                    assert set(pair) == {"source", "en", "es"}
                    assert pair["source"] == getattr(row, field)
                    assert pair["en"] and pair["es"]


def test_authored_copy_is_membership_scoped_and_does_not_rewrite_history(evaluation):
    group, other = catalog(evaluation)["groups"]
    with evaluation.app.state.database.session_factory() as db:
        record = db.scalar(
            select(Record).where(Record.external_id == "security-person-01")
        )
        record.display_text = {
            **record.display_text,
            "title": {
                "source": record.title,
                "en": f"Record for {record.title}",
                "es": f"Expediente de {record.title}",
            },
        }
        db.commit()
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
        f"/v1/workspaces/{group['id']}/records?q=Record%20for", headers=headers
    ).json()
    spanish = evaluation.get(
        f"/v1/workspaces/{group['id']}/records?q=Expediente%20de", headers=headers
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
        upgrade_local_data(db, evaluation.app.state.settings)
        assert record.title == "My updated title"
        assert term.name == "My updated tag"
        assert db.get(UserProfile, user_id) is None
        db.commit()
        upgrade_local_data(db, evaluation.app.state.settings)
        assert db.get(UserProfile, user_id) is None

import hashlib
import uuid
from pathlib import Path

import pytest
from app.local_models import LocalEvaluationState
from app.models import MediaAsset, User, WorkspaceMember
from app.social_features.models import Publication, UserProfile
from app.workspaces.models import Record, RecordMedia
from local_support import catalog
from sqlalchemy import select


def test_police_people_portraits_and_access(evaluation):
    group, _, other = catalog(evaluation)["groups"]

    def login(user):
        token = evaluation.post(
            "/v1/auth/local-select", json={"user_id": user["id"]}
        ).json()["access_token"]
        return {"Authorization": "Bearer " + token}

    headers = login(group["users"][0])
    other_headers = login(other["users"][0])
    base = f"/v1/workspaces/{group['id']}"
    rows = evaluation.get(base + "/records", headers=headers).json()
    assert len(rows) == 16 and all(
        r["kind"] == "person" and r["simulated"] for r in rows
    )
    assert sum(r["data"]["has_active_warrant"] for r in rows) == 5
    assert sum(r["data"]["has_active_proceedings"] for r in rows) == 2
    assert all(
        not r["data"]["has_active_proceedings"] or r["data"]["has_active_warrant"]
        for r in rows
    )
    missing = [r for r in rows if r["data"].get("has_active_search_order")]
    assert len(missing) == 4
    assert all(row["data"]["is_missing"] for row in missing)
    assert all(not row["data"]["has_active_warrant"] for row in missing)
    assert all(not row["data"]["has_active_proceedings"] for row in missing)
    assert all(not r["biometric_authorized"] for r in rows)
    hashes = set()
    for row in rows:
        detail = evaluation.get(base + "/records/" + row["id"], headers=headers).json()
        assert len(detail["media"]) == 1
        link = detail["media"][0]
        path = base + "/record-media/" + link["id"]
        response = evaluation.get(path, headers=headers)
        assert response.status_code == 200
        hashes.add(hashlib.sha256(response.content).hexdigest())
        assert evaluation.get(path, headers=other_headers).status_code in {403, 404}
        assert evaluation.get(path).status_code == 401
        if row["data"]["has_active_warrant"]:
            assert row["data"]["issuing_judge"] and row["data"]["warrant_reference"]
        else:
            assert row["data"]["warrant_reference"] is None
            assert not row["data"]["has_active_proceedings"]
    assert len(hashes) == 16
    with evaluation.app.state.database.session_factory() as db:
        assert (
            db.query(Publication).filter_by(workspace_id=uuid.UUID(group["id"])).count()
            == 19
        )


@pytest.mark.parametrize("evaluation", ["baseline"], indirect=True)
def test_police_replacement_is_atomic_and_preserves_accounts(evaluation, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from app.local.upgrades import POLICE as WORKSPACE
    from app.local.upgrades import upgrade_local_data

    RECEIPT = "police-people-v1"

    def refresh_local_police(db, settings):
        return upgrade_local_data(db, settings).get(RECEIPT)

    settings = evaluation.app.state.settings
    with evaluation.app.state.database.session_factory() as db:
        # Model a previously initialized dataset that still needs replacement.
        db.delete(db.get(LocalEvaluationState, RECEIPT))
        members = list(
            db.scalars(
                select(WorkspaceMember).where(WorkspaceMember.workspace_id == WORKSPACE)
            )
        )
        member_ids = {m.id for m in members}
        profiles = {
            m.user_id: db.get(UserProfile, m.user_id).avatar_media_id for m in members
        }
        accounts = {m.user_id: db.get(User, m.user_id).password_hash for m in members}
        portrait = db.scalar(
            select(RecordMedia).join(Record).where(Record.workspace_id == WORKSPACE)
        )
        stale = Publication(
            id=uuid.uuid4(),
            workspace_id=WORKSPACE,
            owner_id=members[0].user_id,
            media_id=portrait.media_id,
            caption="Old content",
        )
        stale_id = stale.id
        db.add(stale)
        db.commit()
        report = refresh_local_police(db, settings)
        assert report["removed"]["publications"] == 11
        assert report["created"] == {"records": 10, "attachments": 10}
        db.commit()
        db.expire_all()
        assert db.get(Publication, stale_id) is None
        assert {
            m.id
            for m in db.scalars(
                select(WorkspaceMember).where(WorkspaceMember.workspace_id == WORKSPACE)
            )
        } == member_ids
        for user_id, avatar in profiles.items():
            assert db.get(UserProfile, user_id).avatar_media_id == avatar
            assert db.get(MediaAsset, avatar).original_bytes
            assert db.get(User, user_id).password_hash == accounts[user_id]
        record = db.scalar(select(Record).where(Record.workspace_id == WORKSPACE))
        record.title = "Owner edit"
        db.commit()
        assert refresh_local_police(db, settings) is None
        assert record.title == "Owner edit"
        with pytest.raises(ValueError):
            refresh_local_police(
                db, settings.model_copy(update={"environment": "production"})
            )

import uuid

import pytest
from app.meta import MetaProviderError
from app.models import User
from app.providers.mock import MockMetaModelClient
from app.social_features.evidence_models import PublicationTranslation
from app.social_features.history_evidence import persist_refreshed_history
from app.social_features.models import ChatMessage, Publication
from sqlalchemy import delete, func, select

from .test_evidence_information import URL, payload, prepare

PREPARE = URL + "/prepare"


def save_old_history(client, pid, eid, legacy=False):
    with client.app.state.database.session_factory() as db:
        post = db.get(Publication, pid)
        gallery = (
            {
                "thumbnail_url": f"/v1/gallery/{pid}/thumbnail",
                "media_url": f"/v1/gallery/{pid}/media",
                "caption": "Workshop",
                "boxed_url": f"/v1/gallery/{pid}/boxed?labels=crimping%20tool",
            }
            if legacy
            else {
                "thumbnail_url": f"/v1/gallery/evidence/{eid}?labels=crimping%20tool",
                "evidence_id": eid,
                "matched_labels": ["crimping tool"],
                "caption": "Workshop",
            }
        )
        row = ChatMessage(
            user_id=post.owner_id,
            role="ai",
            text="Encontré una foto",
            gallery=[gallery],
        )
        db.add(row)
        db.commit()
        return row.id


def test_history_refreshes_modern_and_legacy_cards_from_saved_translations(
    client, auth_headers, monkeypatch
):
    pid, eid = prepare(client)
    modern = save_old_history(client, pid, eid)
    old = save_old_history(client, pid, eid, legacy=True)

    def forbidden(*args):
        raise AssertionError("History GET must not infer")

    monkeypatch.setattr(MockMetaModelClient, "prepare_gallery_languages", forbidden)
    response = client.get("/v1/chat/history", headers=auth_headers).json()
    rows = {row["id"]: row for row in response["messages"]}
    for key in (modern, old):
        item = rows[key]["gallery"][0]
        assert item["evidence_id"] == eid
        assert "full_size=true" in item["image_url"]
        assert item["localized_information"]["es"]["title"] == "Taller"
        assert item["localized_information"]["es"]["matched_labels"] == ["crimpadora"]


@pytest.mark.parametrize("legacy", [False, True])
def test_missing_history_language_is_generated_saved_and_returned_in_one_action(
    client, auth_headers, monkeypatch, legacy
):
    pid, eid = prepare(client)
    mid = save_old_history(client, pid, eid, legacy=legacy)
    with client.app.state.database.session_factory() as db:
        db.execute(
            delete(PublicationTranslation).where(
                PublicationTranslation.post_id == pid,
                PublicationTranslation.language == "es",
            )
        )
        db.commit()
    assert (
        client.post(URL, headers=auth_headers, json=payload(eid)).json()["status"]
        == "pending"
    )
    calls = []
    original = MockMetaModelClient.prepare_gallery_languages

    def generate(self, texts):
        calls.append(True)
        return original(self, texts)

    monkeypatch.setattr(MockMetaModelClient, "prepare_gallery_languages", generate)
    repaired = client.post(PREPARE, headers=auth_headers, json=payload(eid))
    assert repaired.status_code == 200, repaired.text
    assert repaired.json()["status"] == "ready"
    assert repaired.json()["items"][0]["note_text"] == "Guardar en el estante 2"
    assert calls == [True]
    again = client.post(PREPARE, headers=auth_headers, json=payload(eid)).json()
    assert again["status"] == "ready" and calls == [True]
    with client.app.state.database.session_factory() as db:
        saved = db.get(ChatMessage, mid).gallery[0]
        assert saved["localized_information"]["es"]["title"] == "Taller"
        assert (
            db.scalar(
                select(func.count())
                .select_from(PublicationTranslation)
                .where(PublicationTranslation.language == "es")
            )
            == 3
        )


def test_recovery_authorizes_whole_batch_before_generation(
    client, auth_headers, monkeypatch
):
    _, eid = prepare(client)
    calls = []
    monkeypatch.setattr(
        MockMetaModelClient,
        "prepare_gallery_languages",
        lambda *args: calls.append(True),
    )
    request = payload(eid)
    request["items"].append({"evidence_id": str(uuid.uuid4()), "labels": ["private"]})
    assert client.post(PREPARE, headers=auth_headers, json=request).status_code == 404
    assert not calls
    assert client.post(PREPARE, json=payload(eid)).status_code == 401


def test_failed_recovery_never_persists_partial_languages(
    client, auth_headers, monkeypatch
):
    pid, eid = prepare(client)
    with client.app.state.database.session_factory() as db:
        db.execute(
            delete(PublicationTranslation).where(PublicationTranslation.post_id == pid)
        )
        db.commit()

    def unavailable(*args):
        raise MetaProviderError("Unavailable")

    monkeypatch.setattr(MockMetaModelClient, "prepare_gallery_languages", unavailable)
    response = client.post(PREPARE, headers=auth_headers, json=payload(eid)).json()
    assert response["status"] == "unavailable" and not response["items"]
    with client.app.state.database.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(PublicationTranslation)) == 0


def test_repair_snapshots_persist_and_do_not_expose_hidden_resources(
    client, auth_headers
):
    pid, eid = prepare(client)
    mid = save_old_history(client, pid, eid, legacy=True)
    with client.app.state.database.session_factory() as db:
        post = db.get(Publication, pid)
        owner = db.get(User, post.owner_id)
        assert persist_refreshed_history(db, owner) == 1
        assert persist_refreshed_history(db, owner) == 0
        db.commit()
        assert (
            db.get(ChatMessage, mid).gallery[0]["localized_information"]["es"]["title"]
            == "Taller"
        )
        post.hidden = True
        db.commit()
        assert persist_refreshed_history(db, owner) == 0
        assert db.get(ChatMessage, mid).gallery
    row = client.get("/v1/chat/history", headers=auth_headers).json()["messages"][0]
    assert not row["gallery"]


def test_recovery_rechecks_permission_after_inference_before_saving(
    client, auth_headers, monkeypatch
):
    from app.models import Role, Workspace, WorkspaceMember
    from app.security import create_access_token

    pid, eid = prepare(client)
    with client.app.state.database.session_factory() as db:
        viewer = User(
            email="history-locale-member@test.invalid",
            display_name="Member",
            password_hash="unused",
        )
        db.add(viewer)
        db.flush()
        workspace = db.scalar(select(Workspace))
        membership = WorkspaceMember(
            workspace_id=workspace.id, user_id=viewer.id, role=Role.QUERY
        )
        db.add(membership)
        post = db.get(Publication, pid)

        post.workspace_id = workspace.id
        db.execute(
            delete(PublicationTranslation).where(PublicationTranslation.post_id == pid)
        )
        db.flush()
        mid = membership.id
        headers = {
            "Authorization": "Bearer "
            + create_access_token(viewer.id, client.app.state.settings)
        }
        db.commit()
    original = MockMetaModelClient.prepare_gallery_languages

    def revoke(self, texts):
        with client.app.state.database.session_factory() as db:
            db.delete(db.get(WorkspaceMember, mid))
            db.commit()
        return original(self, texts)

    monkeypatch.setattr(MockMetaModelClient, "prepare_gallery_languages", revoke)
    response = client.post(PREPARE, headers=headers, json=payload(eid))
    assert response.status_code == 403
    with client.app.state.database.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(PublicationTranslation)) == 0


def test_pre_box_history_recovers_only_objects_supported_by_stored_boxes(
    client, auth_headers
):
    pid, eid = prepare(client)
    with client.app.state.database.session_factory() as db:
        post = db.get(Publication, pid)
        db.add(
            ChatMessage(
                user_id=post.owner_id,
                role="user",
                text="Hola, necesito que me ayudes a buscar un alicate",
            )
        )
        db.flush()
        db.add(
            ChatMessage(
                user_id=post.owner_id,
                role="ai",
                text="Encontré una foto",
                gallery=[
                    {
                        "thumbnail_url": f"/v1/gallery/{pid}/thumbnail",
                        "media_url": f"/v1/gallery/{pid}/media",
                        "caption": "Workshop",
                    }
                ],
            )
        )
        db.commit()
    card = client.get("/v1/chat/history", headers=auth_headers).json()["messages"][0][
        "gallery"
    ][0]
    assert card["evidence_id"] == eid
    assert card["match_kind"] == "family"
    assert card["localized_information"]["es"]["matched_labels"] == ["crimpadora"]


def test_similar_legacy_match_remains_stable_after_saving_exact_stored_labels(client):
    from app.social_features.localizations import prepare_posts

    from .test_search_recovery import legacy, setup

    with client.app.state.database.session_factory() as db:
        user, workspace = setup(db)
        post = legacy(db, user, workspace, label="bench vise")
        from app.social_features.legacy_evidence import repair_image

        assert repair_image(db, post)
        prepare_posts(db, [post], MockMetaModelClient())
        message = ChatMessage(
            user_id=user.id,
            role="ai",
            text="Resultado",
            gallery=[
                {
                    "thumbnail_url": f"/v1/gallery/{post.id}/thumbnail",
                    "boxed_url": f"/v1/gallery/{post.id}/boxed?labels=clamp",
                }
            ],
        )
        db.add(message)
        db.flush()
        assert persist_refreshed_history(db, user) == 1
        assert message.gallery[0]["match_kind"] == "similar"
        assert persist_refreshed_history(db, user) == 0
        assert message.gallery[0]["match_kind"] == "similar"

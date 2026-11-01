import uuid

from app.meta import MetaProviderError
from app.models import User
from app.providers.mock import MockMetaModelClient
from app.social_features.evidence import search_evidence
from app.social_features.evidence_models import PublicationTranslation
from app.social_features.localizations import prepare_posts, stored_rows, text_hash
from app.social_features.models import Publication
from sqlalchemy import func, select

from .test_evidence_uploads import upload
from .test_search_recovery import legacy, setup


def test_publish_persists_both_languages_before_becoming_visible(
    client, auth_headers, monkeypatch
):
    response = upload(
        client,
        auth_headers,
        caption="Workshop",
        note_text="Keep on shelf 2",
        note_source="text",
    )
    assert response.status_code == 202
    result = response.json()
    assert result["status"] == "published"
    with client.app.state.database.session_factory() as db:
        post = db.get(Publication, uuid.UUID(result["result_id"]))
        rows = stored_rows(db, [post.id])
        assert rows[(post.id, "es", text_hash("Workshop"))].translated_text == "Taller"
        assert (
            rows[(post.id, "es", text_hash("Keep on shelf 2"))].translated_text
            == "Guardar en el estante 2"
        )
        assert (
            rows[(post.id, "en", text_hash("Workshop"))].translated_text == "Workshop"
        )

    def forbidden(*args, **kwargs):
        raise AssertionError("No translation while reading")

    monkeypatch.setattr(MockMetaModelClient, "prepare_gallery_languages", forbidden)
    with client.app.state.database.session_factory() as db:
        owner = db.get(User, post.owner_id)
        matches = search_evidence(db, owner, "yellow drill", None).matches
        assert matches[0]["localized_information"]["es"]["matched_labels"] == [
            "taladro amarillo"
        ]
        eid = matches[0]["evidence_id"]
    request = {
        "language": "es",
        "items": [{"evidence_id": str(eid), "labels": ["yellow drill"]}],
    }
    info = client.post(
        "/v1/gallery/evidence/information", headers=auth_headers, json=request
    ).json()
    assert (
        info["status"] == "ready"
        and info["items"][0]["note_text"] == "Guardar en el estante 2"
    )


def test_translation_failure_does_not_publish_image(client, auth_headers, monkeypatch):
    def unavailable(*args, **kwargs):
        raise MetaProviderError("Languages unavailable")

    monkeypatch.setattr(MockMetaModelClient, "prepare_gallery_languages", unavailable)
    result = upload(client, auth_headers).json()
    assert result["status"] == "failed"
    assert not client.get("/v1/gallery", headers=auth_headers).json()
    with client.app.state.database.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(PublicationTranslation)) == 0


def test_incomplete_language_pair_is_not_published(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        MockMetaModelClient, "prepare_gallery_languages", lambda *args: {"en": {}}
    )
    assert upload(client, auth_headers).json()["status"] == "failed"
    assert not client.get("/v1/gallery", headers=auth_headers).json()


def test_preparation_is_resumable_and_keeps_old_texts_for_history(client):
    with client.app.state.database.session_factory() as db:
        owner, workspace = setup(db)
        post = legacy(
            db, owner, workspace, caption="Workshop", note_text="Keep on shelf 2"
        )
        model = MockMetaModelClient()
        assert prepare_posts(db, [post], model) == 3
        assert prepare_posts(db, [post], model) == 0
        post.note_text = "Guardar en el estante 2"
        assert prepare_posts(db, [post], model) == 1
        rows = stored_rows(db, [post.id])
        assert (post.id, "es", text_hash("Keep on shelf 2")) in rows
        assert (
            rows[(post.id, "en", text_hash(post.note_text))].translated_text
            == "Keep on shelf 2"
        )


def test_duplicate_replacement_stores_new_note_languages(client, auth_headers):
    first = upload(
        client, auth_headers, note_text="Keep on shelf 2", note_source="text"
    ).json()
    replacement = upload(client, auth_headers, caption="Workshop").json()
    result = client.post(
        f"/v1/me/publication-uploads/{replacement['id']}/confirm", headers=auth_headers
    ).json()
    assert result["result_id"] == first["result_id"]
    with client.app.state.database.session_factory() as db:
        pid = uuid.UUID(first["result_id"])
        rows = stored_rows(db, [pid])
        assert rows[(pid, "es", text_hash("Workshop"))].translated_text == "Taller"
        assert (pid, "es", text_hash("Keep on shelf 2")) in rows


def test_live_prepares_complete_pair_in_one_request(monkeypatch):
    import json
    from types import SimpleNamespace

    from app.config import Settings
    from app.providers.live import LiveMetaModelClient

    model = LiveMetaModelClient(
        Settings(
            meta_mode="live",
            meta_connection_mode="gateway",
            meta_gateway_base_url="https://example.invalid/v1",
            meta_gateway_token="fixture",
        )
    )
    calls = []

    def request(method, route, **kwargs):
        calls.append(kwargs["json"])
        return SimpleNamespace(json=dict)

    monkeypatch.setattr(model, "_request", request)
    monkeypatch.setattr(
        model,
        "_output_text",
        lambda _: json.dumps({"en": {"0": "pliers"}, "es": {"0": "alicates"}}),
    )
    assert model.prepare_gallery_languages({"0": "pliers"})["es"]["0"] == "alicates"
    assert len(calls) == 1 and calls[0]["store"] is False
    monkeypatch.setattr(
        model, "_output_text", lambda _: '{"en":{"0":"pliers"},"es":{}}'
    )
    import pytest

    with pytest.raises(MetaProviderError):
        model.prepare_gallery_languages({"0": "pliers"})


def test_failed_index_translation_preserves_previous_evidence(client):
    from app.gallery_index import index_publication
    from app.social_features.evidence_models import GalleryEvidence
    from app.social_features.legacy_evidence import repair_image

    class FailedLanguages(MockMetaModelClient):
        def prepare_gallery_languages(self, texts):
            raise MetaProviderError("Languages unavailable")

    with client.app.state.database.session_factory() as db:
        owner, workspace = setup(db)
        post = legacy(db, owner, workspace)
        assert repair_image(db, post)
        old = db.scalar(select(GalleryEvidence.id))
        result = index_publication(
            db, post.id, FailedLanguages(), force=True, deduplicate=False
        )
        assert result.index_error and result.evidence_version == 0
        assert result.ai_detections[0]["label"] == "crimping tool"
        assert db.get(GalleryEvidence, old) is not None
        assert result.active_index_run_id is None
        assert (
            search_evidence(db, owner, "alicate", None).matches[0]["evidence_id"] == old
        )
        staged = list(
            db.scalars(
                select(GalleryEvidence).where(GalleryEvidence.index_run_id.is_not(None))
            )
        )
        assert staged  # Retained for retry, but never selected by Query.


def test_failed_note_translation_does_not_partially_retire_duplicate(
    client, monkeypatch
):
    from app.gallery_index import index_publication
    from app.social_features.evidence_models import PublicationDuplicate

    class FailedLanguages(MockMetaModelClient):
        def prepare_gallery_languages(self, texts):
            raise MetaProviderError("Languages unavailable")

    with client.app.state.database.session_factory() as db:
        owner, workspace = setup(db)
        original = legacy(db, owner, workspace, note_text="Original note")
        duplicate = legacy(db, owner, workspace, color="blue", note_text="Another note")
        monkeypatch.setattr(
            "app.social_features.upload_service.duplicate",
            lambda *args, **kwargs: original,
        )
        result = index_publication(db, duplicate.id, FailedLanguages(), force=True)
        assert result.index_error and not duplicate.hidden
        assert original.note_text == "Original note"
        assert db.get(PublicationDuplicate, duplicate.id) is None

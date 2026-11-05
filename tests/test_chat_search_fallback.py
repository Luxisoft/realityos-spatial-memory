"""Chat search honors the user's request with boxed evidence, even during outages.

Regression coverage for the finder-chat report: an image plus "Find people..."
must not fail with "Could not analyze the image", and person questions scoped
to the work group (for example people with an active arrest warrant) must
return the linked group photos/videos with the found person framed, in both
the thumbnail and the large viewer. Free phrasing is interpreted by the model;
deterministic keywords only back it up during outages and in tests.
"""

from __future__ import annotations

import hashlib
import io
import uuid
from datetime import UTC, datetime

from app.meta import MetaProviderError
from app.models import MediaAsset, MediaKind, User
from app.schemas import GalleryMatch
from app.social_features.evidence_models import GalleryEvidence
from app.social_features.models import Publication
from app.workspaces.models import Connection, Record, RecordMedia
from PIL import Image


def _png_bytes(color=(241, 198, 36)) -> bytes:
    image = Image.new("RGB", (80, 60), color=color)
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _workspace(client, headers) -> str:
    response = client.post(
        "/v1/workspaces",
        headers=headers,
        json={
            "name": f"Security group {uuid.uuid4().hex[:8]}",
            "description": "Person search",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _person_case(db, owner_id, workspace_id, *, name, warrant, portrait_color, label="person"):
    """One person record with a linked portrait publication and person evidence."""
    raw = _png_bytes(portrait_color)
    asset = MediaAsset(
        workspace_id=workspace_id,
        kind=MediaKind.IMAGE,
        mime_type="image/png",
        original_bytes=raw,
        sha256=hashlib.sha256(raw).hexdigest(),
        byte_size=len(raw),
        width=80,
        height=60,
    )
    db.add(asset)
    db.flush()
    detection = {
        "label": label,
        "box": {"x": 0.1, "y": 0.1, "width": 0.8, "height": 0.8},
        "confidence": 0.94,
        "localization_confidence": 0.9,
        "model": "mock-sam-3.1",
        "simulated": True,
    }
    post = Publication(
        owner_id=owner_id,
        workspace_id=workspace_id,
        media_id=asset.id,
        caption=name,
        note_text=f"Arrest warrant: {'Active' if warrant else 'No warrants registered'}",
        search_text=f"{name} person",
        ai_labels=[label],
        ai_detections=[{**detection, "frame_timestamp_ms": None}],
        evidence_version=2,
        face_count=1,
    )
    db.add(post)
    db.flush()
    evidence = GalleryEvidence(
        post_id=post.id,
        media_id=asset.id,
        image_bytes=raw,
        content_hash=hashlib.sha256(raw).hexdigest(),
        detections=[detection],
        version=2,
        index_run_id=None,
    )
    db.add(evidence)
    connection = db.query(Connection).filter_by(workspace_id=workspace_id).first()
    if connection is None:
        connection = Connection(
            workspace_id=workspace_id,
            created_by_id=owner_id,
            name="Cases",
            token_hash=hashlib.sha256(uuid.uuid4().bytes).hexdigest(),
            source_url=None,
        )
        db.add(connection)
        db.flush()
    now = datetime.now(UTC)
    record = Record(
        workspace_id=workspace_id,
        connection_id=connection.id,
        external_id=f"person-{uuid.uuid4().hex[:8]}",
        kind="person",
        title=name,
        data={
            "full_name": name,
            "has_active_warrant": warrant,
            "warrant_reference": "PR-OC-2026-011" if warrant else None,
            "has_active_proceedings": False,
            "is_missing": False,
            "has_active_search_order": False,
        },
        status="active",
        occurred_at=now,
        updated_at=now,
        simulated=True,
        biometric_authorized=False,
    )
    db.add(record)
    db.flush()
    db.add(
        RecordMedia(
            record_id=record.id,
            external_id="portrait",
            media_id=asset.id,
            publication_id=post.id,
        )
    )
    db.commit()
    return record, post, evidence


def _provider_outage(monkeypatch):
    def _raise(settings):
        raise MetaProviderError(
            "MODEL_API_KEY is required for a direct Meta connection."
        )

    monkeypatch.setattr("app.http.queries.build_meta_client", _raise)


def test_search_classify_returns_faces_when_object_analysis_fails(
    client, auth_headers, monkeypatch
):
    _provider_outage(monkeypatch)
    workspace_id = _workspace(client, auth_headers)
    response = client.request(
        "POST",
        "/v1/search/classify",
        headers=auth_headers,
        data={"workspace_id": workspace_id},
        files={"image": ("probe.png", _png_bytes(), "image/png")},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["faces"] >= 1
    assert payload["object_labels"] == []
    assert payload["simulated"] is True


def test_search_route_falls_back_to_keywords_when_provider_fails(
    client, auth_headers, monkeypatch
):
    _provider_outage(monkeypatch)
    person = client.post(
        "/v1/search/route",
        headers=auth_headers,
        json={"text": "Find people with arrest warrants"},
    )
    assert person.status_code == 200, person.text
    assert person.json()["target"] == "person"
    assert person.json()["simulated"] is True
    objects = client.post(
        "/v1/search/route", headers=auth_headers, json={"text": "martillo"}
    )
    assert objects.json()["target"] == "object"


def test_image_query_falls_back_to_text_when_provider_fails(
    client, auth_headers, monkeypatch
):
    _provider_outage(monkeypatch)
    workspace_id = _workspace(client, auth_headers)
    response = client.request(
        "POST",
        "/v1/queries/image",
        headers=auth_headers,
        data={"workspace_id": workspace_id, "question": "martillo"},
        files={"image": ("probe.png", _png_bytes(), "image/png")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["found"] is False
    blank = client.request(
        "POST",
        "/v1/queries/image",
        headers=auth_headers,
        data={"workspace_id": workspace_id, "question": "  "},
        files={"image": ("probe.png", _png_bytes(), "image/png")},
    )
    assert blank.status_code == 503, blank.text


def test_records_search_returns_boxed_warrant_portraits(client, auth_headers):
    workspace_id = _workspace(client, auth_headers)
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter_by(email="admin@example.test").one()
        wanted, _, _ = _person_case(
            db,
            owner.id,
            uuid.UUID(workspace_id),
            name="Bruno Escobar",
            warrant=True,
            portrait_color=(200, 40, 40),
        )
        _person_case(
            db,
            owner.id,
            uuid.UUID(workspace_id),
            name="Samuel Ortega",
            warrant=False,
            portrait_color=(40, 120, 200),
        )
    response = client.post(
        f"/v1/workspaces/{workspace_id}/records/search",
        headers=auth_headers,
        json={"question": "Find people with arrest warrants", "language": "en"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert [record["title"] for record in payload["records"]] == ["Bruno Escobar"]
    gallery = payload["gallery_matches"]
    assert len(gallery) == 1
    item = GalleryMatch.model_validate(gallery[0]).model_dump(mode="json")
    assert item["caption"] == "Bruno Escobar"
    assert item["matched_labels"] == ["person"]
    assert "/v1/gallery/evidence/" in item["thumbnail_url"]
    assert item["boxed_url"] == item["thumbnail_url"]
    assert item["image_url"].endswith("&full_size=true")
    assert gallery[0]["record_id"] == str(wanted.id)
    thumbnail = client.get(item["thumbnail_url"], headers=auth_headers)
    assert thumbnail.status_code == 200
    assert thumbnail.headers["content-type"] == "image/jpeg"
    large = client.get(item["image_url"], headers=auth_headers)
    assert large.status_code == 200
    with (
        Image.open(io.BytesIO(thumbnail.content)) as small,
        Image.open(io.BytesIO(large.content)) as big,
    ):
        assert big.size[0] >= small.size[0]


def test_records_search_person_gallery_skips_hidden_and_foreign_posts(
    client, auth_headers
):
    workspace_id = _workspace(client, auth_headers)
    other_id = _workspace(client, auth_headers)
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter_by(email="admin@example.test").one()
        _, hidden_post, _ = _person_case(
            db,
            owner.id,
            uuid.UUID(workspace_id),
            name="Hidden Case",
            warrant=True,
            portrait_color=(10, 10, 10),
        )
        hidden_post.hidden = True
        _person_case(
            db,
            owner.id,
            uuid.UUID(other_id),
            name="Foreign Case",
            warrant=True,
            portrait_color=(10, 200, 10),
        )
        db.commit()
    response = client.post(
        f"/v1/workspaces/{workspace_id}/records/search",
        headers=auth_headers,
        json={"question": "personas con orden de captura", "language": "es"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["gallery_matches"] == []


def test_records_search_generic_person_question_lists_group_portraits(
    client, auth_headers
):
    workspace_id = _workspace(client, auth_headers)
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter_by(email="admin@example.test").one()
        _person_case(
            db,
            owner.id,
            uuid.UUID(workspace_id),
            name="Bruno Escobar",
            warrant=True,
            portrait_color=(200, 40, 40),
        )
    response = client.post(
        f"/v1/workspaces/{workspace_id}/records/search",
        headers=auth_headers,
        json={"question": "Find people", "language": "en"},
    )
    assert response.status_code == 200, response.text
    gallery = response.json()["gallery_matches"]
    assert [item["caption"] for item in gallery] == ["Bruno Escobar"]


def test_records_search_gallery_needs_workspace_membership(client, auth_headers):
    from app.security import hash_password

    workspace_id = _workspace(client, auth_headers)
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter_by(email="admin@example.test").one()
        db.add(
            User(
                email="outsider@example.test",
                display_name="Outsider",
                password_hash=hash_password("OutsiderPass123!"),
            )
        )
        _person_case(
            db,
            owner.id,
            uuid.UUID(workspace_id),
            name="Bruno Escobar",
            warrant=True,
            portrait_color=(200, 40, 40),
        )
        db.commit()
    login = client.post(
        "/v1/auth/login",
        json={"email": "outsider@example.test", "password": "OutsiderPass123!"},
    )
    assert login.status_code == 200, login.text
    outsider_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    denied = client.post(
        f"/v1/workspaces/{workspace_id}/records/search",
        headers=outsider_headers,
        json={"question": "Find people with arrest warrants", "language": "en"},
    )
    assert denied.status_code == 403, denied.text


def test_records_search_offline_filter_covers_varied_warrant_phrasings(
    client, auth_headers
):
    from app.providers.person_filters import interpret

    assert interpret("muéstrame los requeridos por la justicia") == "warrant"
    assert interpret("wanted people") == "warrant"
    assert interpret("fugitives in the group") == "warrant"
    assert interpret("people under arrest") == "warrant"
    assert interpret("personas desaparecidas del grupo") == "missing"
    assert interpret("people with no criminal history") == "clean"
    assert interpret("maintenance cabinet Delta") == "none"
    workspace_id = _workspace(client, auth_headers)
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter_by(email="admin@example.test").one()
        _person_case(
            db,
            owner.id,
            uuid.UUID(workspace_id),
            name="Bruno Escobar",
            warrant=True,
            portrait_color=(200, 40, 40),
        )
    response = client.post(
        f"/v1/workspaces/{workspace_id}/records/search",
        headers=auth_headers,
        json={"question": "muéstrame los requeridos por la justicia", "language": "es"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert [record["title"] for record in payload["records"]] == ["Bruno Escobar"]
    assert [item["caption"] for item in payload["gallery_matches"]] == ["Bruno Escobar"]


def test_records_search_non_person_question_returns_no_gallery(client, auth_headers):
    workspace_id = _workspace(client, auth_headers)
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter_by(email="admin@example.test").one()
        _person_case(
            db,
            owner.id,
            uuid.UUID(workspace_id),
            name="Bruno Escobar",
            warrant=True,
            portrait_color=(200, 40, 40),
        )
    response = client.post(
        f"/v1/workspaces/{workspace_id}/records/search",
        headers=auth_headers,
        json={"question": "maintenance cabinet Delta", "language": "en"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["gallery_matches"] == []


def test_records_search_outage_still_returns_indexed_gallery(
    client, auth_headers, monkeypatch
):
    def _raise(settings):
        raise MetaProviderError(
            "MODEL_API_KEY is required for a direct Meta connection."
        )

    monkeypatch.setattr("app.workspaces.search.build_meta_client", _raise)
    workspace_id = _workspace(client, auth_headers)
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter_by(email="admin@example.test").one()
        _person_case(
            db,
            owner.id,
            uuid.UUID(workspace_id),
            name="Bruno Escobar",
            warrant=True,
            portrait_color=(200, 40, 40),
        )
    response = client.post(
        f"/v1/workspaces/{workspace_id}/records/search",
        headers=auth_headers,
        json={"question": "Find people with arrest warrants", "language": "en"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert [record["title"] for record in payload["records"]] == ["Bruno Escobar"]
    assert [item["caption"] for item in payload["gallery_matches"]] == ["Bruno Escobar"]


def test_live_person_filter_parses_model_output(monkeypatch):
    import httpx
    from app.config import Settings
    from app.meta import LiveMetaModelClient

    settings = Settings(
        _env_file=None,
        meta_mode="live",
        meta_connection_mode="direct",
        model_api_key="direct-test-key",
        meta_gateway_fallback_enabled=False,
        meta_api_base_url="https://meta.test/v1",
        meta_max_retries=0,
    )

    def fake_request(method, url, **kwargs):
        return httpx.Response(
            200,
            request=httpx.Request(method, str(url)),
            json={"output_text": '{"filter": "missing"}'},
        )

    monkeypatch.setattr(httpx, "request", fake_request)
    result = LiveMetaModelClient(settings).interpret_person_filter(
        "¿A quiénes estamos buscando?"
    )
    assert result.filter == "missing"
    assert result.simulated is False


def test_live_person_filter_falls_back_to_keywords_on_invalid_output(monkeypatch):
    import httpx
    from app.config import Settings
    from app.meta import LiveMetaModelClient

    settings = Settings(
        _env_file=None,
        meta_mode="live",
        meta_connection_mode="direct",
        model_api_key="direct-test-key",
        meta_gateway_fallback_enabled=False,
        meta_api_base_url="https://meta.test/v1",
        meta_max_retries=0,
    )

    def fake_request(method, url, **kwargs):
        return httpx.Response(
            200,
            request=httpx.Request(method, str(url)),
            json={"output_text": "not json"},
        )

    monkeypatch.setattr(httpx, "request", fake_request)
    result = LiveMetaModelClient(settings).interpret_person_filter("wanted people")
    assert result.filter == "warrant"
    assert result.simulated is True
def test_records_search_gallery_skips_comma_labels_instead_of_404_urls(
    client, auth_headers
):
    """Comma labels cannot round-trip the evidence endpoint, so they are skipped."""
    workspace_id = _workspace(client, auth_headers)
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter_by(email="admin@example.test").one()
        _person_case(
            db,
            owner.id,
            uuid.UUID(workspace_id),
            name="Bruno Escobar",
            warrant=True,
            portrait_color=(200, 40, 40),
        )
        _person_case(
            db,
            owner.id,
            uuid.UUID(workspace_id),
            name="Esteban Pardo",
            warrant=True,
            portrait_color=(40, 200, 40),
            label="older man with receding gray hair, blue eyes and gray mustache",
        )
    response = client.post(
        f"/v1/workspaces/{workspace_id}/records/search",
        headers=auth_headers,
        json={"question": "Find people with arrest warrants", "language": "en"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert [record["title"] for record in payload["records"]] == [
        "Esteban Pardo",
        "Bruno Escobar",
    ]
    gallery = payload["gallery_matches"]
    assert [item["caption"] for item in gallery] == ["Bruno Escobar"]
    for item in gallery:
        fetched = client.get(item["thumbnail_url"], headers=auth_headers)
        assert fetched.status_code == 200, item["thumbnail_url"]

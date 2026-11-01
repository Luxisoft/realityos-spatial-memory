"""Regressions for gallery retrieval during the versioned evidence upgrade."""

import io

import pytest
from app.meta import MetaProviderError
from app.models import MediaAsset, MediaKind, Role, User, Workspace, WorkspaceMember
from app.schemas import GalleryInterpretation
from app.security import create_access_token
from app.services import media_sha256
from app.social_features.evidence import search_evidence
from app.social_features.evidence_models import GalleryEvidence
from app.social_features.legacy_evidence import repair_image
from app.social_features.models import Publication
from app.social_features.retrieval_terms import classify_terms, phrase
from PIL import Image
from sqlalchemy import func, select

QUESTIONS = (
    "Hola, necesito que por favor me busques un alicate.",
    "Hola, necesito que por favor me ayudes a buscar un alicate.",
)
BOX = {"x": 0.54, "y": 0.742, "width": 0.185, "height": 0.258}


def setup(db):
    user = db.scalar(select(User).where(User.email == "admin@example.test"))
    workspace = Workspace(name="Workshop", created_by_id=user.id)
    db.add(workspace)
    db.flush()
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=Role.ADMIN))
    db.flush()
    return user, workspace


def legacy(db, user, workspace, label="crimping tool", color="red", **changes):
    out = io.BytesIO()
    Image.new("RGB", (1200, 800), color).save(out, "JPEG")
    raw = out.getvalue()
    asset = MediaAsset(
        workspace_id=workspace.id,
        kind=MediaKind.IMAGE,
        mime_type="image/jpeg",
        original_bytes=raw,
        sha256=media_sha256(raw),
        byte_size=len(raw),
    )
    db.add(asset)
    db.flush()
    post = Publication(
        owner_id=user.id,
        media_id=asset.id,
        audience="home",
        source="workshop",
        ai_labels=[label],
        ai_detections=[
            {"label": label, "box": BOX, "confidence": 0.97, "frame_index": 0}
        ],
        **changes,
    )
    db.add(post)
    db.flush()
    return post


@pytest.mark.parametrize("question", QUESTIONS)
def test_polite_requests_recover_family_and_full_size_annotation(
    client, auth_headers, question
):
    with client.app.state.database.session_factory() as db:
        user, workspace = setup(db)
        post = legacy(db, user, workspace)
        asset = db.get(MediaAsset, post.media_id)
        original = asset.original_bytes
        assert repair_image(db, post)
        assert not repair_image(db, post)  # Idempotent, leaves v2 pending.
        result = search_evidence(db, user, question, None)
        assert result.status == "partial" and result.pending_count == 1
        assert len(result.matches) == 1
        match = result.matches[0]
        assert match["match_kind"] == "family"
        assert match["matched_labels"] == ["crimping tool"]
        assert match["localization_quality"] == "approximate_box"
        assert post.evidence_version == 0
        assert not db.new and not db.dirty  # Query made no writes.
        assert asset.original_bytes == original
        db.commit()
    thumb = client.get(match["thumbnail_url"], headers=auth_headers)
    large = client.get(match["image_url"], headers=auth_headers)
    assert thumb.status_code == large.status_code == 200
    assert Image.open(io.BytesIO(large.content)).size == (1200, 800)
    assert Image.open(io.BytesIO(thumb.content)).width <= 360
    pixel = Image.open(io.BytesIO(large.content)).getpixel((650, 594))
    assert pixel[1] > 100  # Yellow annotation on the red source, at the stored box.


def test_semantic_ranking_dedup_and_sam_preferred(client):
    with client.app.state.database.session_factory() as db:
        user, workspace = setup(db)
        posts = [
            legacy(db, user, workspace, label, color)
            for label, color in (
                ("metal clamp", "red"),
                ("crimping tool", "green"),
                ("pliers", "blue"),
                ("hammer", "yellow"),
                ("pliers", "blue"),
            )
        ]
        for post in posts:
            assert repair_image(db, post)
        exact = posts[2]
        old = db.scalar(
            select(GalleryEvidence).where(GalleryEvidence.post_id == exact.id)
        )
        sam = GalleryEvidence(
            post_id=exact.id,
            media_id=exact.media_id,
            image_bytes=old.image_bytes,
            content_hash=old.content_hash,
            detections=old.detections,
            version=2,
        )
        db.add(sam)
        exact.evidence_version = 2
        db.flush()
        result = search_evidence(db, user, QUESTIONS[0], None)
        assert [r["match_kind"] for r in result.matches] == [
            "exact",
            "family",
            "similar",
        ]
        assert result.matches[0]["evidence_id"] == sam.id
        assert result.matches[0]["localization_quality"] == "sam"
        assert "hammer" not in str(result.matches)


def test_complete_vocabulary_scoped_and_no_cutoff(client):
    class Interpreter:
        def interpret_gallery_matches(self, question, vocabulary):
            assert "crimping tool" in vocabulary and len(vocabulary) > 1000
            assert "secret-private-tool" not in vocabulary
            return GalleryInterpretation(family=["crimping tool", "invented"])

    with client.app.state.database.session_factory() as db:
        user, workspace = setup(db)
        post = legacy(db, user, workspace)
        post.ai_detections = [
            {"label": f"ui label {i}", "box": BOX, "confidence": 0.9}
            for i in range(1100)
        ] + post.ai_detections
        db.flush()
        assert repair_image(db, post)
        other = User(
            email="other@test.invalid", display_name="Other", password_hash="unused"
        )
        db.add(other)
        db.flush()
        private = legacy(db, other, workspace, "secret-private-tool", "green")
        assert repair_image(db, private)
        result = search_evidence(db, user, QUESTIONS[0], Interpreter())
        assert len(result.matches) == 1 and result.matches[0]["post_id"] == post.id
        # Previously omitted tags remain available to the older gallery interpreter too.
        from app.gallery_index import _known_tags

        post.ai_labels = [f"tag {i}" for i in range(1100)] + ["crimping tool"]
        assert "crimping tool" in _known_tags(db, user)


@pytest.mark.parametrize(
    "invalid",
    [
        {"confidence": 0.4},
        {"box": {"x": 0, "y": 0, "width": 0, "height": 1}},
        {"confidence": float("nan")},
        {"label": ""},
    ],
)
def test_repair_never_makes_invalid_or_unmarked_objects_searchable(client, invalid):
    with client.app.state.database.session_factory() as db:
        user, workspace = setup(db)
        post = legacy(db, user, workspace)
        post.ai_detections = [{**post.ai_detections[0], **invalid}]
        db.flush()
        assert not repair_image(db, post)
        assert not search_evidence(db, user, "alicate", None).matches
        assert db.scalar(select(func.count()).select_from(GalleryEvidence)) == 0


def test_orientation_and_replaced_media_never_use_stale_boxes(client):
    with client.app.state.database.session_factory() as db:
        user, workspace = setup(db)
        post = legacy(db, user, workspace)
        asset = db.get(MediaAsset, post.media_id)
        exif = Image.Exif()
        exif[274] = 6
        raw = io.BytesIO()
        Image.new("RGB", (1200, 800), "red").save(raw, "JPEG", exif=exif)
        asset.original_bytes = raw.getvalue()
        assert not repair_image(db, post)
        other = legacy(db, user, workspace, color="blue")
        assert repair_image(db, other)
        # The same post points to different media: old evidence remains history-only.
        other.media_id = post.media_id
        db.flush()
        assert not search_evidence(db, user, "alicate", None).matches


def test_search_status_distinguishes_pending_outage_and_no_match(
    client, auth_headers, monkeypatch
):
    with client.app.state.database.session_factory() as db:
        user, workspace = setup(db)
        post = legacy(db, user, workspace)
        wid, pid = str(workspace.id), post.id
        db.commit()
    request = {"workspace_id": wid, "question": QUESTIONS[0], "language": "es"}
    pending = client.post("/v1/queries", headers=auth_headers, json=request).json()
    assert pending["gallery_search_status"] == "indexing"
    assert "indexando" in pending["message"] and not pending["gallery_matches"]
    with client.app.state.database.session_factory() as db:
        post = db.get(Publication, pid)
        post.evidence_version = 2
        db.commit()
    missing = client.post("/v1/queries", headers=auth_headers, json=request).json()
    assert missing["gallery_search_status"] == "no_match"

    def failure(*args, **kwargs):
        raise RuntimeError("search storage unavailable")

    monkeypatch.setattr("app.social_features.evidence.search_evidence", failure)
    failed = client.post("/v1/queries", headers=auth_headers, json=request).json()
    assert failed["gallery_search_status"] == "unavailable"
    assert "No pude completar" in failed["message"]


def test_provider_failure_uses_safe_family_bridge_and_reports_incomplete():
    class Failed:
        def interpret_gallery_matches(self, *args):
            raise MetaProviderError("Unavailable")

    result = classify_terms(
        QUESTIONS[0],
        ["pliers", "crimping tool", "clamp", "toolbox", "hammer"],
        Failed(),
    )
    assert result.unavailable
    assert result.labels == {
        "pliers": "exact",
        "crimping tool": "family",
        "clamp": "similar",
    }
    assert phrase(QUESTIONS[0]) == phrase(QUESTIONS[1]) == "alicate"


def test_recovered_evidence_remains_private_and_membership_scoped(client, auth_headers):
    with client.app.state.database.session_factory() as db:
        user, workspace = setup(db)
        post = legacy(db, user, workspace)
        post.audience = "work"
        post.workspace_id = workspace.id
        db.flush()
        assert repair_image(db, post)
        evidence = db.scalar(select(GalleryEvidence))
        eid = evidence.id
        outsider = User(
            email="outsider@test.invalid", display_name="Other", password_hash="unused"
        )
        db.add(outsider)
        db.flush()
        assert not search_evidence(db, outsider, "alicate", None).matches
        headers = {
            "Authorization": "Bearer "
            + create_access_token(outsider.id, client.app.state.settings)
        }
        db.commit()
    assert (
        client.get(
            f"/v1/gallery/evidence/{eid}?labels=crimping%20tool", headers=headers
        ).status_code
        == 403
    )
    assert (
        client.get(
            f"/v1/gallery/evidence/{eid}?labels=crimping%20tool", headers=auth_headers
        ).status_code
        == 200
    )


def test_live_relations_allowlist_and_invalid_provider_reply(monkeypatch):
    import json
    from types import SimpleNamespace

    from app.config import Settings
    from app.providers.live import LiveMetaModelClient

    model = LiveMetaModelClient(
        Settings(
            meta_mode="live",
            meta_gateway_base_url="https://example.invalid/v1",
            meta_gateway_token="fixture",
        )
    )
    requests = []

    def request(*args, **kwargs):
        requests.append(kwargs["json"]["input"])
        return SimpleNamespace(json=dict)

    monkeypatch.setattr(model, "_request", request)
    monkeypatch.setattr(
        model,
        "_output_text",
        lambda payload: json.dumps(
            {
                "exact": ["PLIERS", "not-authorized"],
                "family": ["crimping tool"],
                "similar": ["clamp"],
            }
        ),
    )
    interpreted = model.interpret_gallery_matches(
        QUESTIONS[0], ["pliers", "crimping tool", "clamp"]
    )
    assert interpreted.exact == ["pliers"] and interpreted.family == ["crimping tool"]
    assert QUESTIONS[0] in requests[0]
    monkeypatch.setattr(model, "_output_text", lambda payload: '{"terms":[]}')
    with pytest.raises(MetaProviderError):
        model.interpret_gallery_matches("alicate", ["pliers"])


def test_api_keeps_recovered_results_during_provider_outage(
    client, auth_headers, monkeypatch
):
    with client.app.state.database.session_factory() as db:
        user, workspace = setup(db)
        post = legacy(db, user, workspace)
        assert repair_image(db, post)
        wid = str(workspace.id)
        db.commit()

    def unavailable(*args, **kwargs):
        raise MetaProviderError("Unavailable")

    monkeypatch.setattr(
        "app.providers.mock.MockMetaModelClient.interpret_gallery_matches", unavailable
    )
    response = client.post(
        "/v1/queries",
        headers=auth_headers,
        json={"workspace_id": wid, "question": QUESTIONS[0], "language": "es"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["gallery_matches"][0]["match_kind"] == "family"
    assert body["gallery_matches"][0]["matched_labels"] == ["crimping tool"]
    assert body["gallery_search_status"] == "partial"
    assert body["gallery_search_reason"] == "semantic_unavailable"
    assert "parciales" in body["message"]

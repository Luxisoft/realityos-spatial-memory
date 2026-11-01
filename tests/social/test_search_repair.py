"""SAM limit, atomic replacement, selective recovery and honest query status."""

import contextlib

import httpx
import pytest
from app.config import Settings
from app.gallery_index import index_publication
from app.meta import MetaProviderError
from app.providers.live import LiveMetaModelClient
from app.providers.mock import MockMetaModelClient
from app.schemas import ImageAnalysis
from app.social_features.evidence import search_evidence
from app.social_features.evidence_models import GalleryEvidence, GalleryIndexRun
from app.social_features.legacy_evidence import repair_image
from app.social_features.retrieval_terms import classify_terms
from sqlalchemy import select

from .test_search_recovery import legacy, setup


def live():
    return LiveMetaModelClient(
        Settings(
            meta_mode="live",
            meta_connection_mode="gateway",
            meta_gateway_base_url="https://fixture.invalid/v1",
            meta_gateway_token="fixture",
            meta_max_retries=2,
        )
    )


@pytest.mark.parametrize(
    "count,groups",
    [
        (0, []),
        (1, [1]),
        (16, [16]),
        (17, [16, 1]),
        (28, [16, 12]),
        (32, [16, 16]),
        (40, [16, 16, 8]),
    ],
)
def test_sam_batches_keep_every_object_and_original_order(monkeypatch, count, groups):
    client = live()
    calls = []

    def batch(image, width, height, items):
        calls.append(len(items))
        return [f"mask-{item}" for item in items]

    monkeypatch.setattr(client, "_segment_gallery_batch", batch)
    assert client.segment_gallery(b"image", 100, 100, list(range(count))) == [
        f"mask-{i}" for i in range(count)
    ]
    assert calls == groups


@pytest.mark.parametrize("stream", [False, True])
def test_http_400_preserves_reason_and_is_not_retried(monkeypatch, stream):
    client = live()
    calls = []
    response = httpx.Response(
        400,
        json={
            "error": {
                "message": "invalid prompt: 28 objects exceed this model's limit of 16"
            }
        },
        request=httpx.Request("POST", "https://fixture.invalid/v1/responses"),
    )

    def request(*args, **kwargs):
        calls.append(1)
        return response

    @contextlib.contextmanager
    def events(*args, **kwargs):
        yield request()

    monkeypatch.setattr(httpx, "request", request)
    monkeypatch.setattr(httpx, "stream", events)
    with pytest.raises(MetaProviderError, match="limit of 16") as error:
        if stream:
            client._stream_events({"model": "sam-3.1"})
        else:
            client._request("POST", "responses", json={"model": "muse-spark-1.3"})
    assert error.value.status_code == 400 and not error.value.retryable
    assert calls == [1]


def test_failed_analysis_keeps_previous_search_and_resumes_completed_frame(client):
    class Broken(MockMetaModelClient):
        def segment_gallery(self, *args):
            raise MetaProviderError(
                "group 2 failed",
                phase="sam_localization",
                status_code=503,
                retryable=True,
            )

    with client.app.state.database.session_factory() as db:
        owner, workspace = setup(db)
        post = legacy(db, owner, workspace, label="hammer")
        repair_image(db, post)
        original = post.ai_detections.copy()
        index_publication(db, post.id, Broken(), force=True, deduplicate=False)
        assert post.ai_detections == original
        run = db.scalar(select(GalleryIndexRun))
        assert run.status == "failed" and run.error["stage"] == "sam_localization"
        assert search_evidence(db, owner, "martillo", None).matches
        assert post.active_index_run_id is None


def test_missing_previous_object_is_reconfirmed_not_silently_dropped(client):
    class Missing(MockMetaModelClient):
        def analyze_image(self, *args, **kwargs):
            return ImageAnalysis(model="mock", simulated=True, detections=[])

    with client.app.state.database.session_factory() as db:
        owner, workspace = setup(db)
        post = legacy(db, owner, workspace, label="hammer")
        repair_image(db, post)
        old = db.scalar(select(GalleryEvidence.id))
        index_publication(db, post.id, Missing(), force=True, deduplicate=False)
        assert post.active_index_run_id is not None and post.index_error is None
        matches = search_evidence(
            db, owner, "mejor quiero un martillo, un martillo", None
        ).matches
        assert matches and matches[0]["matched_labels"] == ["hammer"]
        assert matches[0]["evidence_id"] != old
        assert db.get(GalleryEvidence, old) is not None
        run = db.get(GalleryIndexRun, post.active_index_run_id)
        assert "confirmed" in run.progress["reviews"].values()


@pytest.mark.parametrize(
    "verdict,confidence,activated",
    [("rejected", 0.95, True), ("uncertain", 0.5, False), ("rejected", 0.5, False)],
)
def test_only_explicit_confident_rejection_can_remove_previous_object(
    client, verdict, confidence, activated
):
    class Missing(MockMetaModelClient):
        def analyze_image(self, *args, **kwargs):
            return ImageAnalysis(model="mock", simulated=True, detections=[])

        def review_gallery_objects(self, image, candidates):
            return [
                {
                    "id": c["id"],
                    "verdict": verdict,
                    "confidence": confidence,
                    "box": None,
                }
                for c in candidates
            ]

    with client.app.state.database.session_factory() as db:
        owner, workspace = setup(db)
        post = legacy(db, owner, workspace, label="hammer")
        repair_image(db, post)
        index_publication(db, post.id, Missing(), force=True, deduplicate=False)
        assert bool(post.active_index_run_id) == activated
        run = db.scalar(select(GalleryIndexRun))
        assert run.status == ("ready" if activated else "needs_review")
        assert bool(search_evidence(db, owner, "hammer", None).matches) == (
            not activated
        )


def test_old_discarded_hammer_is_only_recovered_after_explicit_repair(client):
    class Missing(MockMetaModelClient):
        def analyze_image(self, *args, **kwargs):
            return ImageAnalysis(model="mock", simulated=True, detections=[])

    with client.app.state.database.session_factory() as db:
        owner, workspace = setup(db)
        post = legacy(db, owner, workspace, label="hammer")
        repair_image(db, post)
        post.evidence_version = 2
        post.ai_detections = []
        assert not search_evidence(db, owner, "hammer", None).matches
        index_publication(
            db, post.id, Missing(), force=True, deduplicate=False, recover_legacy=True
        )
        assert search_evidence(db, owner, "hammer", None).matches


def test_unrelated_failed_file_reports_partial_instead_of_service_outage(client):
    with client.app.state.database.session_factory() as db:
        owner, workspace = setup(db)
        legacy(db, owner, workspace, label="pliers", index_error="old HTTP 400")
        result = search_evidence(db, owner, "hammer", None)
        assert (
            result.status == "partial"
            and result.failed_count == 1
            and result.pending_count == 0
        )
        assert result.reason == "incomplete_index" and not result.matches


def test_semantics_receives_original_question_and_local_hammer_alias_is_safe():
    question = "Aunque sabes qué, mejor quiero un martillo, un martillo. Ayúdeme a buscar un martillo, por favor."

    class Failed:
        def interpret_gallery_matches(self, text, vocabulary):
            assert text == question
            raise MetaProviderError("Unavailable")

    result = classify_terms(question, ["claw hammer", "toolbox", "pliers"], Failed())
    assert result.labels == {"claw hammer": "exact"}


def test_video_retry_resumes_completed_frames_without_exposing_staged_results(
    client, auth_headers, monkeypatch
):
    from app.models import MediaAsset, MediaKind

    from .test_search_recovery import legacy

    with client.app.state.database.session_factory() as db:
        owner, workspace = setup(db)
        post = legacy(db, owner, workspace, label="unused")
        asset = db.get(MediaAsset, post.media_id)
        asset.kind = MediaKind.VIDEO
        post.ai_detections = []
        first = asset.original_bytes
        second = first + b"different-frame"
        monkeypatch.setattr(
            "app.social_features.evidence_index.frames",
            lambda *args: iter([(first, 0), (second, 2000)]),
        )
        calls = []

        class Interrupt(MockMetaModelClient):
            broken = True

            def analyze_image(self, image, *args, **kwargs):
                # Ground normalizes both fixture encodings; count calls by stage sequence.
                calls.append(1)
                if len(calls) == 2 and self.broken:
                    raise MetaProviderError(
                        "TLS EOF", phase="detection", retryable=True
                    )
                return super().analyze_image(image, *args, **kwargs)

        model = Interrupt()
        index_publication(
            db, post.id, model, force=True, deduplicate=False, checkpoint=True
        )
        run = db.scalar(select(GalleryIndexRun))
        assert run.progress["completed_frames"] == [0]
        staged = db.scalar(
            select(GalleryEvidence).where(GalleryEvidence.index_run_id == run.id)
        )
        assert not search_evidence(db, owner, "yellow drill", None).matches
        staged_id = staged.id
        assert (
            client.get(
                f"/v1/gallery/evidence/{staged_id}?labels=yellow%20drill",
                headers=auth_headers,
            ).status_code
            == 404
        )
        model.broken = False
        index_publication(
            db, post.id, model, force=True, deduplicate=False, checkpoint=True
        )
        assert len(calls) == 3  # The completed first frame was not analyzed twice.
        assert post.active_index_run_id == run.id and run.status == "ready"
        assert run.progress["completed_frames"] == [0, 2000]
        assert (
            client.get(
                f"/v1/gallery/evidence/{staged_id}?labels=yellow%20drill",
                headers=auth_headers,
            ).status_code
            == 200
        )


def test_review_only_repair_does_not_repeat_full_scene_analysis(client):
    class ReviewOnly(MockMetaModelClient):
        def analyze_image(self, *args, **kwargs):
            pytest.fail("An already indexed image only needs omitted-object review")

    with client.app.state.database.session_factory() as db:
        owner, workspace = setup(db)
        post = legacy(db, owner, workspace, label="hammer")
        repair_image(db, post)
        post.ai_detections = []
        post.evidence_version = 2
        index_publication(
            db,
            post.id,
            ReviewOnly(),
            force=True,
            deduplicate=False,
            recover_legacy=True,
            review_only=True,
        )
        assert post.active_index_run_id is not None
        assert search_evidence(db, owner, "martillo", None).matches


def test_plural_hammer_omission_is_prioritized_for_repair(client):
    from app.social_features.repair_inventory import inventory

    with client.app.state.database.session_factory() as db:
        owner, workspace = setup(db)
        post = legacy(db, owner, workspace, label="hammers")
        repair_image(db, post)
        post.evidence_version = 2
        post.ai_detections = []
        selection = inventory(db)[0]
        assert selection["post_id"] == str(post.id) and selection["priority"] == 0


def test_confirmed_discarded_object_recovers_even_if_other_discarded_label_is_uncertain(
    client,
):
    class ReviewOnly(MockMetaModelClient):
        def review_gallery_objects(self, image, candidates):
            return [
                {
                    "id": c["id"],
                    "verdict": "confirmed" if c["label"] == "hammer" else "uncertain",
                    "confidence": 0.95 if c["label"] == "hammer" else 0.4,
                    "box": c["box"],
                }
                for c in candidates
            ]

    with client.app.state.database.session_factory() as db:
        owner, workspace = setup(db)
        post = legacy(db, owner, workspace, label="hammer")
        post.ai_detections = [
            *post.ai_detections,
            {**post.ai_detections[0], "label": "unknown tool"},
        ]
        db.flush()
        repair_image(db, post)
        post.ai_detections = []
        post.evidence_version = 2
        index_publication(
            db,
            post.id,
            ReviewOnly(),
            force=True,
            deduplicate=False,
            recover_legacy=True,
            review_only=True,
        )
        assert post.active_index_run_id is not None
        result = search_evidence(db, owner, "martillo", None)
        assert result.matches and result.matches[0]["matched_labels"] == ["hammer"]
        assert result.status == "partial" and result.failed_count == 1, db.get(
            GalleryIndexRun, post.active_index_run_id
        ).progress


def test_small_object_crop_review_maps_box_to_original_coordinates(monkeypatch):
    import io

    from app.providers import gallery_review
    from PIL import Image

    image = io.BytesIO()
    Image.new("RGB", (1000, 800)).save(image, "JPEG")
    calls = []

    def review(client, raw, candidates):
        calls.append(Image.open(io.BytesIO(raw)).size)
        return [
            {
                "id": "object",
                "verdict": "uncertain" if len(calls) == 1 else "confirmed",
                "confidence": 0.4 if len(calls) == 1 else 0.97,
                "box": {"x": 0.25, "y": 0.25, "width": 0.5, "height": 0.5},
            }
        ]

    monkeypatch.setattr(gallery_review, "review_batch", review)
    result = gallery_review.review_objects(
        None,
        image.getvalue(),
        [
            {
                "id": "object",
                "label": "hammer",
                "box": {"x": 0.4, "y": 0.3, "width": 0.2, "height": 0.2},
            }
        ],
    )[0]
    assert len(calls) == 2 and calls[1][0] < 1000
    assert result["verdict"] == "confirmed" and "_crop" in result
    assert result["box"]["x"] == pytest.approx(0.4, abs=0.002)
    assert result["box"]["y"] == pytest.approx(0.3, abs=0.002)
    assert result["box"]["width"] == pytest.approx(0.2, abs=0.002)


@pytest.mark.parametrize(
    "question",
    [
        "No quiero un martillo, busco alicates",
        "Do not find a hammer",
        "Quiero un martillo y alicates",
    ],
)
def test_local_alias_bridge_does_not_override_negation_or_ambiguous_objects(question):
    assert not classify_terms(question, ["hammer"], None).labels


def test_small_confirmed_object_uses_detail_for_segmentation(client):
    class Small(MockMetaModelClient):
        def __init__(self):
            self.sizes = []

        def review_gallery_objects(self, image, candidates):
            return [
                {
                    "id": c["id"],
                    "verdict": "confirmed",
                    "confidence": 0.97,
                    "box": {"x": 0.5, "y": 0.3, "width": 0.03, "height": 0.1},
                }
                for c in candidates
            ]

        def segment_gallery(self, image, width, height, items):
            self.sizes.append((width, height))
            return super().segment_gallery(image, width, height, items)

    with client.app.state.database.session_factory() as db:
        owner, workspace = setup(db)
        post = legacy(db, owner, workspace, label="hammer")
        repair_image(db, post)
        post.ai_detections = []
        post.evidence_version = 2
        model = Small()
        index_publication(
            db,
            post.id,
            model,
            force=True,
            deduplicate=False,
            recover_legacy=True,
            review_only=True,
        )
        assert post.active_index_run_id is not None
        assert model.sizes[0][0] < 1200 and model.sizes[0][1] < 800
        evidence = db.scalar(
            select(GalleryEvidence).where(
                GalleryEvidence.index_run_id == post.active_index_run_id
            )
        )
        assert evidence.detections[0]["box"]["x"] == pytest.approx(0.5, abs=0.002)
        assert evidence.detections[0]["box"]["y"] == pytest.approx(0.3, abs=0.002)

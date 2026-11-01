"""Recover real pending work without hiding uncertainty or repeating completed frames."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from app.gallery_index import index_publication
from app.models import MediaAsset
from app.providers.contracts import MetaProviderError
from app.providers.live import LiveMetaModelClient
from app.providers.mock import MockMetaModelClient
from app.schemas import ImageAnalysis
from app.social_features.evidence import search_evidence
from app.social_features.evidence_models import GalleryEvidence, GalleryIndexRun
from app.social_features.index_runs import configuration
from app.social_features.legacy_evidence import repair_image
from app.social_features.repair_inventory import pending_inventory
from meta_sam_parser import SegmentationBoxRecord, SegmentationMaskRecord
from sqlalchemy import select

from .test_search_recovery import BOX, legacy, setup


def parser(monkeypatch, module, records):
    def parse(*args):
        def final():
            future = asyncio.get_running_loop().create_future()
            future.set_result(SimpleNamespace(records=records))
            return future

        return SimpleNamespace(final_result=final)

    monkeypatch.setattr(module, "parse_responses_stream", parse)
    monkeypatch.setattr(module, "decode_mask_to_raster", lambda mask: b"\x01" * 100)


def records(ident, box, confidence):
    return [
        SegmentationBoxRecord(
            order=0,
            object_id=ident,
            left=box[0],
            top=box[1],
            right=box[2],
            bottom=box[3],
            confidence=confidence,
        ),
        SegmentationMaskRecord(
            order=1,
            object_id=ident,
            identity=None,
            revision=0,
            mask=SimpleNamespace(width=100, height=100),
            bounds=None,
            confidence=confidence,
        ),
    ]


def test_single_segmentation_parser_runs_inside_event_loop(monkeypatch):
    from app.providers import live

    parser(monkeypatch, live, records("1", (10, 10, 30, 30), 0.95))
    result = LiveMetaModelClient._sam_result_from_events([], 100, 100)
    assert result and result.confidence == 0.95 and any(result.mask)


@pytest.mark.parametrize(
    "confidence,matching,accepted",
    [(0.95, True, True), (0.6, True, False), (0.99, False, False)],
)
def test_concept_localization_keeps_threshold_and_same_instance(
    monkeypatch, confidence, matching, accepted
):
    from app.providers import gallery_localization as module

    data = records("0", (10, 10, 29, 29) if matching else (70, 70, 89, 89), confidence)
    parser(monkeypatch, module, data)
    requests = []
    client = SimpleNamespace(
        _data_url=lambda *args: "data:image/jpeg;base64,fixture",
        _stream_events=lambda body: requests.append(body) or [],
    )
    result = module.segment_confirmed_concept(
        client,
        b"image",
        100,
        100,
        "ceramic mug",
        {"x": 0.1, "y": 0.1, "width": 0.2, "height": 0.2},
    )
    assert bool(result) == accepted
    assert requests[0]["input"][0]["content"][0]["text"] == "ceramic mug"
    assert requests[0]["metadata"]["include_confidence"] == "true"


@pytest.mark.parametrize("confidence,accepted", [(0.95, True), (0.5, False)])
def test_weak_box_gets_independent_concept_mask_without_lowering_threshold(
    client, confidence, accepted
):
    class WeakBox(MockMetaModelClient):
        calls = 0

        def analyze_image(self, *args, **kwargs):
            return ImageAnalysis(model="mock", simulated=True, detections=[])

        def segment_gallery(self, image, width, height, items):
            return [
                replace(value, confidence=0.3)
                for value in super().segment_gallery(image, width, height, items)
            ]

        def segment_gallery_concept(self, image, width, height, label, expected_box):
            self.calls += 1
            assert label == "hammer" and width <= 1200 and height <= 800
            return replace(
                self.segment(
                    image,
                    "image/jpeg",
                    label,
                    width=width,
                    height=height,
                    bounding_box=expected_box,
                ),
                confidence=confidence,
            )

    with client.app.state.database.session_factory() as db:
        owner, workspace = setup(db)
        post = legacy(db, owner, workspace, label="hammer")
        repair_image(db, post)
        before = list(post.ai_detections)
        model = WeakBox()
        index_publication(db, post.id, model, force=True, deduplicate=False)
        run = db.scalar(select(GalleryIndexRun))
        assert model.calls == 1
        assert (run.status == "ready") == accepted
        assert run.progress["review_details"]
        assert (
            next(iter(run.progress["review_details"].values()))["localization_method"]
            == "concept"
        )
        if accepted:
            result = search_evidence(db, owner, "hammer", None)
            assert (
                result.status == "ready"
                and result.matches[0]["localization_quality"] == "sam"
            )
            b = result.matches[0]
            assert b["confidence"] >= 0.65
        else:
            assert post.ai_detections == before
            assert post.index_error and post.active_index_run_id is None


def test_confident_rejection_is_not_overwritten_by_ambiguous_crop(monkeypatch):
    from app.providers import gallery_review

    from .test_evidence_uploads import photo

    calls = []

    def review(*args):
        calls.append(1)
        return [{"id": "old", "verdict": "rejected", "confidence": 0.96, "box": None}]

    monkeypatch.setattr(gallery_review, "review_batch", review)
    result = gallery_review.review_objects(
        None, photo(), [{"id": "old", "label": "absent tool", "box": BOX}]
    )
    assert len(calls) == 1 and result[0]["verdict"] == "rejected"


def test_expired_task_resumes_staged_frame_and_persists_heartbeat(client, monkeypatch):
    from app import tasks

    monkeypatch.setattr(tasks, "settings", client.app.state.settings)
    with client.app.state.database.session_factory() as db:
        owner, workspace = setup(db)
        post = legacy(db, owner, workspace, label="hammer", index_error="interrupted")
        asset = db.get(MediaAsset, post.media_id)
        run = GalleryIndexRun(
            post_id=post.id,
            media_id=asset.id,
            source_hash=asset.sha256,
            status="running",
            stage="detection",
            lease="old-worker",
            attempt=1,
            lease_until=datetime.now(UTC) - timedelta(minutes=1),
            updated_at=datetime(2000, 1, 1, tzinfo=UTC),
            progress={
                "configuration": configuration(),
                "completed_frames": [-1],
                "frames_complete": True,
                "prior": [],
            },
        )
        db.add(run)
        db.flush()
        db.add(
            GalleryEvidence(
                post_id=post.id,
                media_id=asset.id,
                image_bytes=asset.original_bytes,
                content_hash="fixture",
                detections=post.ai_detections,
                version=2,
                index_run_id=run.id,
            )
        )
        pid, mid, rid = str(post.id), str(asset.id), run.id
        db.commit()

    class Resume(MockMetaModelClient):
        def analyze_image(self, *args, **kwargs):
            pytest.fail("Completed frame must not be analyzed again")

    monkeypatch.setattr(tasks, "build_meta_client", lambda settings: Resume())
    result = tasks.repair_gallery_publication.run(pid, mid)
    assert result["status"] == "ready"
    assert (
        tasks.repair_gallery_publication.acks_late
        and tasks.repair_gallery_publication.reject_on_worker_lost
    )
    assert tasks.repair_gallery_publication.max_retries is None
    with client.app.state.database.session_factory() as db:
        run = db.get(GalleryIndexRun, rid)
        assert run.status == "ready" and run.attempt == 2
        assert run.updated_at.year > 2000
        assert db.get(type(post), post.id).active_index_run_id == rid
        assert pending_inventory(db) == []
    # Late delivery after completion is a no-op, rather than another billable analysis.
    monkeypatch.setattr(
        tasks, "build_meta_client", lambda settings: pytest.fail("Already complete")
    )
    assert tasks.repair_gallery_publication.run(pid, mid)["status"] == "ready"
    assert (
        tasks.repair_gallery_publication.run(pid, str(__import__("uuid").uuid4()))[
            "status"
        ]
        == "skipped"
    )


def test_incomplete_review_stream_is_not_silently_retried_as_new_request(client):
    from app.schemas import MetaDetection
    from app.social_features.review_localization import localize

    from .test_evidence_uploads import photo

    class Incomplete(MockMetaModelClient):
        def segment_gallery(self, *args):
            return []

        def segment_gallery_concept(self, *args):
            pytest.fail("An incomplete accepted stream must stay explicit")

    with pytest.raises(MetaProviderError, match="Incomplete reviewed localization"):
        localize(
            Incomplete(),
            photo(),
            128,
            96,
            MetaDetection(label="hammer", confidence=0.95, bounding_box=BOX),
        )


def test_resumed_review_clears_warning_for_already_verified_staged_object(client):
    class AlreadyVerified(MockMetaModelClient):
        def analyze_image(self, *args, **kwargs):
            pytest.fail("Completed pixels must not be analyzed again")

        def review_gallery_objects(self, *args, **kwargs):
            pytest.fail("The staged object already has verified localization")

    with client.app.state.database.session_factory() as db:
        owner, workspace = setup(db)
        post = legacy(db, owner, workspace, label="hammer", index_error="interrupted")
        asset = db.get(MediaAsset, post.media_id)
        run = GalleryIndexRun(
            post_id=post.id,
            media_id=asset.id,
            source_hash=asset.sha256,
            status="needs_review",
            stage="review",
            attempt=1,
            lease="interrupted-review",
            progress={
                "configuration": configuration(),
                "frames_complete": True,
                "prior": [
                    {
                        "id": "old-hammer",
                        "active": True,
                        "timestamp": None,
                        "detection": post.ai_detections[0],
                    }
                ],
                "reviews": {"old-hammer": "uncertain"},
                "review_pending": 1,
            },
        )
        db.add(run)
        db.flush()
        db.add(
            GalleryEvidence(
                post_id=post.id,
                media_id=asset.id,
                image_bytes=asset.original_bytes,
                content_hash="fixture",
                detections=post.ai_detections,
                version=2,
                index_run_id=run.id,
            )
        )
        db.flush()
        index_publication(db, post.id, AlreadyVerified(), force=True, deduplicate=False)
        assert run.status == "ready"
        assert run.progress["reviews"]["old-hammer"] == "retained"
        assert run.progress["review_pending"] == 0
        assert pending_inventory(db) == []
        assert search_evidence(db, owner, "hammer", None).status == "ready"


def test_provider_failures_keep_separate_bounded_retry_budget(client, monkeypatch):
    from app import tasks
    from celery.exceptions import Retry

    class Transient(MockMetaModelClient):
        def analyze_image(self, *args, **kwargs):
            raise MetaProviderError(
                "Temporary analysis failure", phase="detection", retryable=True
            )

    retries = []

    def retry(**kwargs):
        retries.append(kwargs)
        raise Retry()

    monkeypatch.setattr(tasks, "settings", client.app.state.settings)
    monkeypatch.setattr(tasks, "build_meta_client", lambda settings: Transient())
    monkeypatch.setattr(tasks.repair_gallery_publication, "retry", retry)
    with client.app.state.database.session_factory() as db:
        owner, workspace = setup(db)
        post = legacy(db, owner, workspace, label="hammer", index_error="interrupted")
        pid, mid = str(post.id), str(post.media_id)
        db.commit()
    with pytest.raises(Retry):
        tasks.repair_gallery_publication.run(pid, mid)
    assert retries == [{"countdown": 20, "kwargs": {"provider_attempt": 1}}]
    result = tasks.repair_gallery_publication.run(pid, mid, provider_attempt=2)
    assert result["status"] == "failed" and len(retries) == 1

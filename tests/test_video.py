from __future__ import annotations

import shutil
import subprocess
import uuid
from pathlib import Path

import pytest
from app.meta import MetaProviderError, MockMetaModelClient
from app.models import (
    MediaAsset,
    MediaAssetChunk,
    MediaKind,
    ObjectObservation,
    ObjectTrack,
    ObjectTrackFrame,
    ProcessingJob,
)
from app.services import process_job
from app.video import VideoInfo, video_segments
from sqlalchemy import select

pytestmark = pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="ffmpeg and ffprobe are required for video processing tests",
)


def sample_mp4(tmp_path: Path) -> bytes:
    output = tmp_path / "electronics-bench.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=yellow:s=64x48:d=1",
            "-c:v",
            "mpeg4",
            "-y",
            str(output),
        ],
        check=True,
    )
    return output.read_bytes()


def test_video_capture_is_bytea_backed_and_extracts_bounded_frames(client, auth_headers, tmp_path):
    workspace = client.post(
        "/v1/workspaces",
        headers=auth_headers,
        json={"name": "Video workspace"},
    ).json()
    zone = client.post(
        f"/v1/workspaces/{workspace['id']}/zones",
        headers=auth_headers,
        json={"name": "Banco electrónico", "kind": "workbench"},
    ).json()
    session = client.post(
        "/v1/sessions",
        headers=auth_headers,
        json={
            "workspace_id": workspace["id"],
            "zone_id": zone["id"],
            "consent_confirmed": True,
        },
    ).json()
    video = sample_mp4(tmp_path)
    capture = client.post(
        "/v1/captures",
        headers=auth_headers,
        data={"session_id": session["id"]},
        files={"file": ("electronics-bench.mp4", video, "video/mp4")},
    )
    assert capture.status_code == 201, capture.text
    assert capture.json()["kind"] == "video"
    assert capture.json()["width"] == 64
    assert client.get(f"/v1/media/{capture.json()['id']}", headers=auth_headers).content == video

    job_response = client.post(f"/v1/captures/{capture.json()['id']}/process", headers=auth_headers)
    assert job_response.status_code == 200, job_response.text
    with client.app.state.database.session_factory() as db:
        process_job(
            db,
            uuid.UUID(job_response.json()["id"]),
            MockMetaModelClient(),
            video_segment_seconds=120,
            video_frames_per_segment=2,
        )
        db.commit()
        job = db.get(ProcessingJob, uuid.UUID(job_response.json()["id"]))
        frames = list(
            db.scalars(
                select(MediaAsset).where(
                    MediaAsset.parent_asset_id == uuid.UUID(capture.json()["id"]),
                    MediaAsset.kind == MediaKind.IMAGE,
                )
            )
        )
    assert job is not None
    assert job.status.value == "completed"
    assert job.error_message is None
    assert 1 <= len(frames) <= 2
    assert job.result_metadata["source_kind"] == "video"
    assert job.result_metadata["frames_extracted"] == len(frames)
    assert all(frame.extra_metadata["parent_video_id"] == capture.json()["id"] for frame in frames)


def test_long_video_is_partitioned_without_changing_source_evidence():
    segments = video_segments(
        VideoInfo(duration_seconds=818.333, width=1280, height=720), segment_seconds=120
    )
    assert [(segment.index, segment.start_seconds, round(segment.duration_seconds, 3)) for segment in segments] == [
        (0, 0.0, 120.0),
        (1, 120.0, 120.0),
        (2, 240.0, 120.0),
        (3, 360.0, 120.0),
        (4, 480.0, 120.0),
        (5, 600.0, 120.0),
        (6, 720.0, 98.333),
    ]


def test_video_over_inline_threshold_is_stored_as_postgres_bytea_chunks(
    client, auth_headers, tmp_path
):
    settings = client.app.state.settings
    original_threshold = settings.video_inline_bytes
    settings.video_inline_bytes = 1
    try:
        workspace = client.post(
            "/v1/workspaces",
            headers=auth_headers,
            json={"name": "Chunked video workspace"},
        ).json()
        session = client.post(
            "/v1/sessions",
            headers=auth_headers,
            json={"workspace_id": workspace["id"], "consent_confirmed": True},
        ).json()
        video = sample_mp4(tmp_path)
        capture = client.post(
            "/v1/captures",
            headers=auth_headers,
            data={"session_id": session["id"]},
            files={"file": ("chunked.mp4", video, "video/mp4")},
        )
        assert capture.status_code == 201, capture.text
        capture_id = uuid.UUID(capture.json()["id"])
        with client.app.state.database.session_factory() as db:
            asset = db.get(MediaAsset, capture_id)
            chunks = list(
                db.scalars(
                    select(MediaAssetChunk)
                    .where(MediaAssetChunk.asset_id == capture_id)
                    .order_by(MediaAssetChunk.chunk_index)
                )
            )
        assert asset is not None
        assert asset.original_bytes == b""
        assert asset.extra_metadata["storage"] == "chunked_postgres_bytea"
        assert b"".join(chunk.content for chunk in chunks) == video
        fetched = client.get(f"/v1/media/{capture_id}", headers=auth_headers)
        assert fetched.status_code == 200
        assert fetched.content == video
    finally:
        settings.video_inline_bytes = original_threshold


def test_failed_video_pipeline_keeps_only_the_original_for_safe_retry(
    client, auth_headers, tmp_path
):
    class FailingMeta(MockMetaModelClient):
        def analyze_image(self, image: bytes, mime_type: str, context: str = ""):
            raise MetaProviderError("fixture provider outage")

    workspace = client.post(
        "/v1/workspaces", headers=auth_headers, json={"name": "Atomic video workspace"}
    ).json()
    session = client.post(
        "/v1/sessions",
        headers=auth_headers,
        json={"workspace_id": workspace["id"], "consent_confirmed": True},
    ).json()
    capture = client.post(
        "/v1/captures",
        headers=auth_headers,
        data={"session_id": session["id"]},
        files={"file": ("atomic.mp4", sample_mp4(tmp_path), "video/mp4")},
    ).json()
    job = client.post(f"/v1/captures/{capture['id']}/process", headers=auth_headers).json()

    with client.app.state.database.session_factory() as db:
        process_job(
            db,
            uuid.UUID(job["id"]),
            FailingMeta(),
            video_segment_seconds=120,
            video_frames_per_segment=2,
        )
        db.commit()
        persisted = db.get(ProcessingJob, uuid.UUID(job["id"]))
        frames = list(
            db.scalars(
                select(MediaAsset).where(MediaAsset.parent_asset_id == uuid.UUID(capture["id"]))
            )
        )
        observations = list(
            db.scalars(
                select(ObjectObservation).where(ObjectObservation.workspace_id == uuid.UUID(workspace["id"]))
            )
        )

    assert persisted is not None
    assert persisted.status.value == "failed"
    assert frames == []
    assert observations == []


def test_detailed_video_profile_persists_simulated_masks_for_each_clip_frame(
    client, auth_headers, tmp_path
):
    workspace = client.post(
        "/v1/workspaces", headers=auth_headers, json={"name": "Detailed tracking workspace"}
    ).json()
    session = client.post(
        "/v1/sessions",
        headers=auth_headers,
        json={"workspace_id": workspace["id"], "consent_confirmed": True},
    ).json()
    capture = client.post(
        "/v1/captures",
        headers=auth_headers,
        data={"session_id": session["id"]},
        files={"file": ("yellow-drill-video.mp4", sample_mp4(tmp_path), "video/mp4")},
    ).json()
    queued = client.post(
        f"/v1/captures/{capture['id']}/process",
        headers=auth_headers,
        json={"profile": "detailed", "priority_terms": ["yellow drill"]},
    )
    assert queued.status_code == 200, queued.text
    with client.app.state.database.session_factory() as db:
        process_job(
            db,
            uuid.UUID(queued.json()["id"]),
            MockMetaModelClient(),
            video_segment_seconds=120,
            video_frames_per_segment=2,
        )
        db.commit()
        job = db.get(ProcessingJob, uuid.UUID(queued.json()["id"]))
        tracks = list(db.scalars(select(ObjectTrack)))
        track_frames = list(db.scalars(select(ObjectTrackFrame)))
    assert job is not None
    assert job.status.value == "completed"
    assert job.result_metadata["profile"] == "detailed"
    assert job.result_metadata["detailed_tracking"]["status"] == "completed"
    assert len(tracks) == 1
    assert track_frames
    assert all(frame.mask_rle and frame.mask_rle.startswith(b"RLE1") for frame in track_frames)
    listed = client.get(f"/v1/objects/{tracks[0].object_id}/tracks", headers=auth_headers)
    assert listed.status_code == 200, listed.text
    assert listed.json()[0]["status"] == "completed"
    trajectory = client.get(f"/v1/tracks/{tracks[0].id}/frames?limit=100", headers=auth_headers)
    assert trajectory.status_code == 200, trajectory.text
    assert len(trajectory.json()) == len(track_frames)
    assert all(item["visible"] for item in trajectory.json())

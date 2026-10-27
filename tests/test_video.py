from __future__ import annotations

import shutil
import subprocess
import uuid
from pathlib import Path

import pytest
from app.meta import MockMetaModelClient
from app.models import MediaAsset, MediaKind, ProcessingJob
from app.services import process_job
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
            max_video_frames=2,
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
    assert 1 <= len(frames) <= 2
    assert job.result_metadata["source_kind"] == "video"
    assert job.result_metadata["frames_extracted"] == len(frames)
    assert all(frame.extra_metadata["parent_video_id"] == capture.json()["id"] for frame in frames)

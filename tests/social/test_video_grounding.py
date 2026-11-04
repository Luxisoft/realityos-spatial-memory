"""Video grounding stays within detection limits.

Full-resolution frames made model analysis exceed the detection timeout, so
video publications kept failing with "Meta connection failed". Frames are now
bounded before upload, and connection failures name their real cause.
"""

from __future__ import annotations

import io
import shutil
import subprocess
from pathlib import Path

import pytest
from app.models import MediaAsset, MediaAssetChunk, MediaKind
from app.providers.contracts import MetaProviderError
from app.providers.mock import MockMetaModelClient
from app.social_features.evidence_index import frames, stage_evidence
from app.social_features.evidence_models import GalleryIndexRun
from app.social_features.index_runs import configuration
from PIL import Image

from .test_search_recovery import legacy, setup

needs_ffmpeg = pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="ffmpeg and ffprobe are required for video grounding tests",
)


def sample_hd_mp4(tmp_path: Path) -> bytes:
    output = tmp_path / "park-hd.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=1920x1080:rate=2:duration=3",
            "-c:v",
            "mpeg4",
            "-y",
            str(output),
        ],
        check=True,
    )
    return output.read_bytes()


@needs_ffmpeg
def test_video_frames_are_bounded_before_upload(client, tmp_path):
    with client.app.state.database.session_factory() as db:
        _, workspace = setup(db)
        raw = sample_hd_mp4(tmp_path)
        asset = MediaAsset(
            workspace_id=workspace.id,
            kind=MediaKind.VIDEO,
            mime_type="video/mp4",
            original_bytes=raw if len(raw) <= 1024 * 1024 else None,
            sha256="fixture",
            byte_size=len(raw),
        )
        db.add(asset)
        db.flush()
        if asset.original_bytes is None:
            db.add(
                MediaAssetChunk(
                    asset_id=asset.id, chunk_index=0, content=raw, byte_size=len(raw)
                )
            )
            db.flush()
        extracted = list(frames(db, asset))
        assert extracted, "expected at least one extracted frame"
        for frame_bytes, timestamp in extracted:
            with Image.open(io.BytesIO(frame_bytes)) as frame:
                assert max(frame.size) <= 1280
            assert timestamp is not None and timestamp >= 0


def test_stage_evidence_still_fails_when_every_frame_fails(client, monkeypatch):
    from app.social_features import evidence_index

    with client.app.state.database.session_factory() as db:
        user, workspace = setup(db)
        post = legacy(db, user, workspace)
        asset = db.get(MediaAsset, post.media_id)
        asset.kind = MediaKind.VIDEO
        db.flush()

        out = io.BytesIO()
        Image.new("RGB", (64, 48), "green").save(out, "JPEG")
        monkeypatch.setattr(
            evidence_index, "frames", lambda db, asset: [(out.getvalue(), 0)]
        )

        class Broken(MockMetaModelClient):
            def analyze_image(self, image, mime_type, context="", **kwargs):
                raise MetaProviderError("Meta connection failed (ReadTimeout).")

        run = GalleryIndexRun(
            post_id=post.id,
            media_id=asset.id,
            source_hash=asset.sha256,
            status="running",
            stage="detection",
            lease="test",
            attempt=1,
            progress={"configuration": configuration(), "completed_frames": []},
        )
        db.add(run)
        db.flush()
        with pytest.raises(MetaProviderError, match="ReadTimeout"):
            stage_evidence(db, post, Broken(), run, lambda: None)


def test_connection_failure_names_its_cause(monkeypatch):
    from types import SimpleNamespace

    import httpx
    from app.providers.transport import request_json

    def fake_request(method, url, **kwargs):
        raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr(httpx, "request", fake_request)
    client = SimpleNamespace(
        routes=[
            SimpleNamespace(
                name="direct",
                base_url="https://meta.test/v1",
                request_headers=lambda extra: {},
            )
        ],
        settings=SimpleNamespace(meta_max_retries=0, meta_timeout_seconds=5),
        _safe_error=lambda response: "error",
    )
    with pytest.raises(MetaProviderError, match=r"ReadTimeout"):
        request_json(client, "POST", "responses", json={"model": "m"})


def test_grounding_uses_its_own_timeout_ceiling(monkeypatch):
    from app.social_features import visual

    seen = {}

    class Recorder(MockMetaModelClient):
        def analyze_image(self, image, mime_type, context="", **kwargs):
            seen.update(kwargs)
            return super().analyze_image(image, mime_type, context)

    out = io.BytesIO()
    Image.new("RGB", (64, 48), "green").save(out, "JPEG")
    monkeypatch.delenv("META_GROUNDING_TIMEOUT_SECONDS", raising=False)
    visual.ground(Recorder(), out.getvalue())
    assert seen["timeout"] == visual.DEFAULT_GROUNDING_TIMEOUT_SECONDS
    assert seen["timeout"] > 30
    monkeypatch.setenv("META_GROUNDING_TIMEOUT_SECONDS", "45")
    visual.ground(Recorder(), out.getvalue())
    assert seen["timeout"] == 45.0
    monkeypatch.setenv("META_GROUNDING_TIMEOUT_SECONDS", "not-a-number")
    visual.ground(Recorder(), out.getvalue())
    assert seen["timeout"] == visual.DEFAULT_GROUNDING_TIMEOUT_SECONDS


def test_request_json_honors_timeout_override(monkeypatch):
    from types import SimpleNamespace

    import httpx
    from app.providers.transport import request_json

    seen = {}

    def fake_request(method, url, **kwargs):
        seen.update(kwargs)
        return httpx.Response(
            200, request=httpx.Request(method, str(url)), json={"ok": True}
        )

    monkeypatch.setattr(httpx, "request", fake_request)
    client = SimpleNamespace(
        routes=[
            SimpleNamespace(
                name="direct",
                base_url="https://meta.test/v1",
                request_headers=lambda extra: {},
            )
        ],
        settings=SimpleNamespace(meta_max_retries=0, meta_timeout_seconds=5),
        _safe_error=lambda response: "error",
    )
    request_json(client, "POST", "responses", json={"model": "m"})
    assert seen["timeout"] == 5
    request_json(client, "POST", "responses", json={"model": "m"}, timeout=300.0)
    assert seen["timeout"] == 300.0

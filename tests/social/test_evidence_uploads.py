import io
import uuid

import pytest
from app.models import MediaAsset, User
from app.security import create_access_token
from app.social_features.evidence_models import GalleryEvidence, PublicationRevision
from app.social_features.models import Comment, Publication
from app.social_features.visual import valid_box
from PIL import Image
from sqlalchemy import select


def photo(color="red", size=(128, 96)):
    out = io.BytesIO()
    Image.new("RGB", size, color).save(out, "JPEG")
    return out.getvalue()


def upload(client, headers, key=None, raw=None, **fields):
    return client.post(
        "/v1/me/publication-uploads",
        headers=headers,
        data={"request_key": key or str(uuid.uuid4()), **fields},
        files={"file": ("photo.jpg", raw or photo(), "image/jpeg")},
    )


def test_duplicate_requires_confirmation_preserves_post_and_original(
    client, auth_headers
):
    first = upload(client, auth_headers).json()
    assert first["status"] == "published"
    second = upload(
        client, auth_headers, note_text="Nueva nota", note_source="text"
    ).json()
    assert second["status"] == "duplicate"
    assert second["duplicate_id"] == first["result_id"]
    assert len(client.get("/v1/gallery", headers=auth_headers).json()) == 1
    with client.app.state.database.session_factory() as db:
        post = db.get(Publication, uuid.UUID(first["result_id"]))
        old = post.media_id
        db.add(
            Comment(post_id=post.id, user_id=post.owner_id, text="Conservar comentario")
        )
        db.commit()
    confirmed = client.post(
        f"/v1/me/publication-uploads/{second['id']}/confirm", headers=auth_headers
    ).json()
    assert confirmed["result_id"] == first["result_id"]
    # Confirming twice is idempotent.
    assert (
        client.post(
            f"/v1/me/publication-uploads/{second['id']}/confirm", headers=auth_headers
        ).status_code
        == 200
    )
    with client.app.state.database.session_factory() as db:
        post = db.get(Publication, uuid.UUID(first["result_id"]))
        assert post.media_id != old and post.note_text == "Nueva nota"
        assert db.get(MediaAsset, old).original_bytes == photo()
        assert db.scalar(select(Comment)).text == "Conservar comentario"
        assert db.scalar(select(PublicationRevision)).previous["media_id"] == str(old)


def test_cancel_and_idempotency_do_not_create_duplicate_posts(client, auth_headers):
    key = str(uuid.uuid4())
    first = upload(client, auth_headers, key=key).json()
    assert upload(client, auth_headers, key=key).json()["id"] == first["id"]
    assert upload(client, auth_headers, key=key, raw=photo("blue")).status_code == 409
    second = upload(client, auth_headers).json()
    assert (
        client.post(
            f"/v1/me/publication-uploads/{second['id']}/cancel", headers=auth_headers
        ).json()["status"]
        == "cancelled"
    )
    assert (
        client.post(
            f"/v1/me/publication-uploads/{second['id']}/confirm", headers=auth_headers
        ).status_code
        == 409
    )
    assert len(client.get("/v1/gallery", headers=auth_headers).json()) == 1


def test_upload_and_evidence_are_owner_scoped(client, auth_headers):
    first = upload(client, auth_headers).json()
    with client.app.state.database.session_factory() as db:
        user = User(
            email="evidence-other@test.invalid",
            display_name="Other",
            password_hash="unused",
        )
        db.add(user)
        db.flush()
        other = {
            "Authorization": "Bearer "
            + create_access_token(user.id, client.app.state.settings)
        }
        evidence = db.scalar(select(GalleryEvidence))
        eid = evidence.id
        db.commit()
    for path in (
        f"/v1/me/publication-uploads/{first['id']}",
        f"/v1/me/publication-uploads/{first['id']}/preview",
        f"/v1/gallery/evidence/{eid}?labels=yellow%20drill",
    ):
        assert client.get(path, headers=other).status_code == 404
        assert client.get(path).status_code == 401
    assert (
        client.get(
            f"/v1/gallery/evidence/{eid}?labels=not-present", headers=auth_headers
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/v1/gallery/evidence/{eid}?labels=yellow%20drill&full_size=true",
            headers=auth_headers,
        ).status_code
        == 200
    )
    assert (
        upload(
            client, auth_headers, audience="work", workspace_id=str(uuid.uuid4())
        ).status_code
        == 403
    )


def test_meta_failure_never_publishes_and_can_retry(client, auth_headers, monkeypatch):
    from app.meta import MetaProviderError
    from app.providers.mock import MockMetaModelClient

    original = MockMetaModelClient.compare_gallery_images

    def fail(*args):
        raise MetaProviderError("Unavailable")

    monkeypatch.setattr(MockMetaModelClient, "compare_gallery_images", fail)
    response = upload(client, auth_headers).json()
    assert response["status"] == "failed"
    assert client.get("/v1/gallery", headers=auth_headers).json() == []
    monkeypatch.setattr(MockMetaModelClient, "compare_gallery_images", original)
    assert (
        client.post(
            f"/v1/me/publication-uploads/{response['id']}/retry", headers=auth_headers
        ).json()["status"]
        == "published"
    )


@pytest.mark.parametrize(
    "box",
    [
        None,
        {},
        {"x": 0, "y": 0, "width": 0, "height": 1},
        {"x": float("nan"), "y": 0, "width": 1, "height": 1},
        {"x": 2, "y": 2, "width": 1, "height": 1},
    ],
)
def test_invalid_boxes_are_not_search_evidence(box):
    assert valid_box(box) is None


def test_search_requires_localization_and_deduplicates_content(client, auth_headers):
    from app.meta import build_meta_client
    from app.social_features.evidence import gallery_results

    upload(client, auth_headers)
    upload(client, auth_headers, audience="public")  # Different destination is allowed.
    with client.app.state.database.session_factory() as db:
        user = db.scalar(select(User))
        model = build_meta_client(client.app.state.settings)
        result = gallery_results(db, user, "yellow drill", model)
        assert len(result) == 1 and result[0]["image_url"].endswith("full_size=true")
        assert gallery_results(db, user, "hammer", model) == []


def test_retirement_preserves_references_and_different_destinations(
    client, auth_headers
):
    from app.social_features.evidence_models import PublicationDuplicate
    from app.social_features.maintenance import retire

    first = upload(client, auth_headers).json()
    with client.app.state.database.session_factory() as db:
        canonical = db.get(Publication, uuid.UUID(first["result_id"]))
        copy = Publication(
            owner_id=canonical.owner_id,
            media_id=canonical.media_id,
            audience="home",
            note_text="Otra nota",
        )
        db.add(copy)
        db.flush()
        comment = Comment(post_id=copy.id, user_id=copy.owner_id, text="No perder")
        db.add(comment)
        db.flush()
        retire(db, copy, canonical)
        db.commit()
        assert copy.hidden and comment.post_id == canonical.id
        assert db.get(PublicationDuplicate, copy.id).canonical_id == canonical.id
        assert "Otra nota" in canonical.note_text
        another = Publication(
            owner_id=canonical.owner_id, media_id=canonical.media_id, audience="public"
        )
        db.add(another)
        db.flush()
        with pytest.raises(ValueError):
            retire(db, another, canonical)


def test_video_sampling_records_real_pts_and_renders_matching_frame(
    client, auth_headers, tmp_path
):
    import shutil
    import subprocess

    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg required")
    from app.meta import MockMetaModelClient
    from app.models import MediaKind, Role, Workspace, WorkspaceMember
    from app.social_features.evidence_index import frames, index_evidence

    target = tmp_path / "sample.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=red:s=160x120:d=6:r=5",
            "-c:v",
            "mpeg4",
            str(target),
        ],
        check=True,
    )
    with client.app.state.database.session_factory() as db:
        owner = db.scalar(select(User))
        space = Workspace(name="video", created_by_id=owner.id)
        db.add(space)
        db.flush()
        db.add(
            WorkspaceMember(workspace_id=space.id, user_id=owner.id, role=Role.ADMIN)
        )
        db.flush()
        raw = target.read_bytes()
        asset = MediaAsset(
            workspace_id=space.id,
            kind=MediaKind.VIDEO,
            mime_type="video/mp4",
            original_bytes=raw,
            byte_size=len(raw),
            sha256="v" * 64,
        )
        db.add(asset)
        db.flush()
        post = Publication(owner_id=owner.id, media_id=asset.id, audience="home")
        db.add(post)
        db.flush()
        sampled = list(frames(db, asset))
        assert [t for _, t in sampled] == [0, 2000, 4000]
        indexed = index_evidence(db, post, MockMetaModelClient())
        db.flush()
        evidence = indexed[1]
        assert evidence.frame_timestamp_ms == 2000
        eid = evidence.id
        db.commit()
    image = client.get(
        f"/v1/gallery/evidence/{eid}?labels=yellow%20drill&full_size=true",
        headers=auth_headers,
    )
    assert image.status_code == 200
    assert Image.open(io.BytesIO(image.content)).size == (160, 120)


def test_batched_sam_parses_inside_running_loop_and_matches_string_ids(monkeypatch):
    import asyncio
    from types import SimpleNamespace

    from app.config import Settings
    from app.providers.live import LiveMetaModelClient
    from app.schemas import MetaDetection
    from meta_sam_parser import SegmentationBoxRecord, SegmentationMaskRecord

    client = LiveMetaModelClient(
        Settings(
            meta_mode="live",
            meta_connection_mode="gateway",
            meta_gateway_base_url="https://example.invalid/v1",
            meta_gateway_token="test-token",
        )
    )
    monkeypatch.setattr(client, "_stream_events", lambda body: [])
    box = SegmentationBoxRecord(
        order=0, object_id="1", left=1, top=1, right=4, bottom=4
    )
    mask = SegmentationMaskRecord(
        order=1,
        object_id="1",
        identity=None,
        revision=0,
        mask=SimpleNamespace(width=8, height=8),
        bounds=None,
    )

    def parse(*args):
        def final():
            future = asyncio.get_running_loop().create_future()
            future.set_result(SimpleNamespace(records=[box, mask]))
            return future

        return SimpleNamespace(final_result=final)

    monkeypatch.setattr("app.providers.live.parse_responses_stream", parse)
    monkeypatch.setattr(
        "app.providers.live.decode_mask_to_raster", lambda mask: b"\x01" * 64
    )
    result = client.segment_gallery(
        b"fixture",
        8,
        8,
        [
            MetaDetection(
                label="tool",
                confidence=0.9,
                bounding_box={"x": 0.1, "y": 0.1, "width": 0.4, "height": 0.4},
            )
        ],
    )
    assert result[0] is not None
    assert result[0].bounding_box["x"] == 0.125


def test_live_empty_comparison_accepts_bare_null_only_without_candidates(monkeypatch):
    from types import SimpleNamespace

    from app.config import Settings
    from app.meta import MetaProviderError
    from app.providers.live import LiveMetaModelClient

    client = LiveMetaModelClient(
        Settings(
            meta_mode="live",
            meta_connection_mode="gateway",
            meta_gateway_base_url="https://example.invalid/v1",
            meta_gateway_token="test-token",
        )
    )
    monkeypatch.setattr(
        client, "_request", lambda *args, **kwargs: SimpleNamespace(json=dict)
    )
    monkeypatch.setattr(client, "_output_text", lambda payload: "null")
    assert client.compare_gallery_images(b"image", []) is None
    with pytest.raises(MetaProviderError):
        client.compare_gallery_images(b"image", [("id", b"image")])


def test_concurrent_replacements_require_reanalysis_of_stale_candidate(
    client, auth_headers
):
    original = upload(client, auth_headers).json()
    a = upload(client, auth_headers).json()
    b = upload(client, auth_headers).json()
    base = "/v1/me/publication-uploads/"
    assert (
        client.post(base + a["id"] + "/confirm", headers=auth_headers).status_code
        == 200
    )
    assert (
        client.post(base + b["id"] + "/confirm", headers=auth_headers).status_code
        == 409
    )
    assert (
        client.post(base + b["id"] + "/retry", headers=auth_headers).json()["status"]
        == "duplicate"
    )
    assert (
        client.post(base + b["id"] + "/confirm", headers=auth_headers).json()[
            "result_id"
        ]
        == original["result_id"]
    )
    assert len(client.get("/v1/gallery", headers=auth_headers).json()) == 1


def test_deleting_group_cancels_private_upload_candidates(
    client, auth_headers, monkeypatch
):
    from app.meta import MetaProviderError
    from app.providers.mock import MockMetaModelClient

    def fail(*args):
        raise MetaProviderError("Unavailable")

    monkeypatch.setattr(MockMetaModelClient, "compare_gallery_images", fail)
    group = client.post(
        "/v1/groups", headers=auth_headers, json={"name": "Temporary group"}
    ).json()["id"]
    candidate = upload(client, auth_headers, audience="work", workspace_id=group).json()
    assert candidate["status"] == "failed"
    assert (
        client.request(
            "DELETE", f"/v1/groups/{group}", headers=auth_headers
        ).status_code
        == 200
    )
    status = client.get(
        f"/v1/me/publication-uploads/{candidate['id']}", headers=auth_headers
    ).json()
    assert status["status"] == "cancelled"


def test_membership_revoked_during_analysis_prevents_publication(
    client, auth_headers, monkeypatch
):
    from app.models import WorkspaceMember
    from app.providers.mock import MockMetaModelClient
    from sqlalchemy import delete

    original = MockMetaModelClient.segment_gallery
    group = client.post(
        "/v1/groups", headers=auth_headers, json={"name": "Revoked during review"}
    ).json()["id"]

    def segment(self, *args):
        with client.app.state.database.session_factory() as db:
            db.execute(
                delete(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == uuid.UUID(group)
                )
            )
            db.commit()
        return original(self, *args)

    monkeypatch.setattr(MockMetaModelClient, "segment_gallery", segment)
    response = upload(client, auth_headers, audience="work", workspace_id=group).json()
    assert response["status"] == "failed"
    with client.app.state.database.session_factory() as db:
        assert db.scalar(select(Publication)) is None


def test_prepare_queues_without_waiting_for_owner_analysis_lock(
    client, auth_headers, monkeypatch
):
    from app import tasks

    calls = []
    client.app.state.settings.enqueue_processing = True
    monkeypatch.setattr(
        tasks.process_publication_upload, "delay", lambda key: calls.append(key)
    )

    def blocked(*args, **kwargs):
        raise AssertionError("Upload preparation must not wait for worker locks")

    monkeypatch.setattr("app.social_features.upload_service.scope_lock", blocked)
    result = upload(client, auth_headers)
    assert result.status_code == 202 and result.json()["status"] == "pending"
    assert calls == [result.json()["id"]]
    assert client.get("/v1/gallery", headers=auth_headers).json() == []


def test_assistant_image_results_use_the_same_strict_evidence_filter(
    client, auth_headers
):
    upload(client, auth_headers, audience="public")
    result = client.post(
        "/v1/assistant",
        headers=auth_headers,
        json={"text": "yellow drill", "audience": "public"},
    ).json()
    assert len(result["posts"]) == 1
    assert "/gallery/evidence/" in result["posts"][0]["thumbnail_url"]
    assert "full_size=true" in result["posts"][0]["media_url"]
    result = client.post(
        "/v1/assistant",
        headers=auth_headers,
        json={"text": "hammer", "audience": "public"},
    ).json()
    assert result["posts"] == []


def test_retirement_rechecks_visibility_after_external_analysis(client, auth_headers):
    from app.social_features.maintenance import retire
    from sqlalchemy import update

    original = upload(client, auth_headers, audience="public").json()
    with client.app.state.database.session_factory() as db:
        canonical = db.get(Publication, uuid.UUID(original["result_id"]))
        copy = Publication(
            owner_id=canonical.owner_id,
            media_id=canonical.media_id,
            audience="public",
            note_text="Private after change",
        )
        db.add(copy)
        db.flush()
        db.execute(
            update(Publication)
            .where(Publication.id == copy.id)
            .values(audience="home")
            .execution_options(synchronize_session=False)
        )
        with pytest.raises(ValueError):
            retire(db, copy, canonical)
        assert not copy.hidden and "Private after change" not in (
            canonical.note_text or ""
        )


def test_resized_recompressed_copy_prompts_replacement_but_distinct_photo_publishes(
    client, auth_headers
):
    from PIL import ImageDraw

    image = Image.new("RGB", (320, 240), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((30, 30, 200, 180), fill="red")
    draw.ellipse((180, 100, 300, 220), fill="blue")
    original = io.BytesIO()
    image.save(original, "JPEG", quality=95)
    smaller = io.BytesIO()
    image.resize((160, 120)).save(smaller, "JPEG", quality=65)
    first = upload(client, auth_headers, raw=original.getvalue()).json()
    copy = upload(client, auth_headers, raw=smaller.getvalue()).json()
    assert copy["status"] == "duplicate" and copy["duplicate_id"] == first["result_id"]
    different = upload(client, auth_headers, raw=photo("blue")).json()
    assert (
        different["status"] == "published"
        and different["result_id"] != first["result_id"]
    )

"""Video renewal preserves existing evidence and requires measured acceptance."""

import hashlib
import importlib.util
import json
import shutil
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.accounts.models import PasswordAccount
from app.models import MediaAsset, MediaKind, Role, User, Workspace, WorkspaceMember
from app.social_features.evidence_models import PublicationUpload
from app.social_features.models import Publication
from app.storage.models import StorageConnection, StorageImport, StorageSync
from sqlalchemy import func, select


@pytest.fixture
def renewal():
    path = Path(__file__).resolve().parents[1] / "scripts/renew_evaluation_videos.py"
    spec = importlib.util.spec_from_file_location("video_renewal", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare_fixture(db, root, module):
    base = root / "simulator/real-scenes"
    (base / "assets").mkdir(parents=True)
    old, new, cases = [], [], []
    for number, (group, (name, folder, usernames)) in enumerate(module.GROUPS.items()):
        users = []
        for username in usernames:
            user = User(
                email=username + "@fixture.test",
                display_name=username,
                password_hash="fixture",
            )
            db.add(user)
            db.flush()
            db.add(PasswordAccount(user_id=user.id, username=username))
            users.append(user)
        workspace = Workspace(name=name, created_by_id=users[0].id)
        db.add(workspace)
        db.flush()
        for username, user in zip(usernames, users):
            db.add(
                WorkspaceMember(
                    workspace_id=workspace.id, user_id=user.id, role=Role.ADMIN
                )
            )
            connection = StorageConnection(
                owner_id=user.id,
                workspace_id=workspace.id,
                provider="s3",
                name="Fixture",
                endpoint="https://storage.example",
                bucket="fixtures",
                region="auto",
                secret="test",
                prefix=f"demo/v2/{folder}/{username}/",
            )
            db.add(connection)
            db.flush()
            db.add(
                StorageSync(
                    connection_id=connection.id,
                    prefix=connection.prefix,
                    workspace_id=workspace.id,
                    audience="work",
                    enabled=True,
                    interval_minutes=15,
                    next_run=datetime.now(UTC),
                )
            )
        for index in range(20):
            identifier = number * 100 + index
            raw = f"fixture-{identifier}".encode()
            kind = "image" if index < 12 else "video"
            suffix = "jpg" if kind == "image" else "mp4"
            path = f"simulator/real-scenes/assets/{identifier}.{suffix}"
            (root / path).write_bytes(raw)
            item = {
                "group": group,
                "id": identifier,
                "kind": kind,
                "path": path,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "duration": 2,
                "complete_recording": True,
                "width": 1280,
                "height": 720,
                "license": "fixture",
                "source": "fixture://video",
                "author": "Fixture",
                "label": "Fixture",
            }
            if index >= 16:
                new.append(item)
                cases.append(
                    {
                        "id": identifier,
                        "group": group,
                        "owner": usernames[(index - 16) % 3],
                        "sha256": item["sha256"],
                        "footage_reviewed": True,
                        "queries": [
                            {"es": "llaves", "en": "keys", "visible_ms": [0, 1000]},
                            {"es": "gafas", "en": "glasses", "visible_ms": [0, 2000]},
                        ],
                    }
                )
                continue
            old.append(item)
            asset = MediaAsset(
                workspace_id=workspace.id,
                kind=MediaKind.IMAGE if kind == "image" else MediaKind.VIDEO,
                mime_type="image/jpeg" if kind == "image" else "video/mp4",
                original_bytes=raw,
                byte_size=len(raw),
                sha256=item["sha256"],
            )
            db.add(asset)
            db.flush()
            db.add(
                Publication(
                    owner_id=users[index % 3].id,
                    workspace_id=workspace.id,
                    media_id=asset.id,
                    audience="work",
                    source=module.SOURCE,
                    source_ref=f"licensed-v2:{group}:{identifier}",
                )
            )
    for name, data in (
        ("video-previous-manifest.json", {"items": old}),
        ("video-candidate-manifest.json", {"items": new}),
        ("video-evaluation.json", {"release": module.RELEASE, "videos": cases}),
    ):
        (base / name).write_text(json.dumps(data))
    db.commit()


def test_stage_is_repeatable_and_keeps_previous_publications(client, tmp_path, renewal):
    with client.app.state.database.session_factory() as db:
        prepare_fixture(db, tmp_path, renewal)
        journal = renewal.inventory(db, tmp_path)
        before = db.scalar(select(func.count()).select_from(Workspace))
        renewal.stage(db, tmp_path, journal)
        db.commit()
        renewal.stage(db, tmp_path, journal)
        db.commit()
        assert db.scalar(select(func.count()).select_from(Publication)) == 60
        assert db.scalar(select(func.count()).select_from(Workspace)) == before
        assert all(
            not db.get(Publication, uuid.UUID(r["id"])).hidden
            for r in journal["previous"]
        )
        assert all(
            not db.get(Publication, uuid.UUID(r["id"])).ai_detections
            for r in journal["created"]
        )


def test_activation_and_rollback_preserve_photos_and_use_separate_sync_folders(
    client, tmp_path, renewal
):
    with client.app.state.database.session_factory() as db:
        prepare_fixture(db, tmp_path, renewal)
        journal = renewal.inventory(db, tmp_path)
        renewal.stage(db, tmp_path, journal)
        db.commit()
        photo_ids = [
            r["id"] for r in journal["previous"] if r["item"]["kind"] == "image"
        ]
        old_video_ids = [
            r["id"] for r in journal["previous"] if r["item"]["kind"] == "video"
        ]
        renewal.activate(db, journal)
        db.commit()
        assert all(not db.get(Publication, uuid.UUID(i)).hidden for i in photo_ids)
        assert all(db.get(Publication, uuid.UUID(i)).hidden for i in old_video_ids)
        active = list(
            db.scalars(select(StorageSync).where(StorageSync.enabled.is_(True)))
        )
        assert len(active) == 9 and all(
            r.prefix.endswith(renewal.RELEASE + "/") for r in active
        )
        journal["sources_verified"] = True
        renewal.rollback(db, journal)
        db.commit()
        assert all(
            not db.get(Publication, uuid.UUID(r["id"])).hidden
            for r in journal["previous"]
        )
        assert all(
            db.get(Publication, uuid.UUID(r["id"])).hidden for r in journal["created"]
        )
        active = list(
            db.scalars(select(StorageSync).where(StorageSync.enabled.is_(True)))
        )
        assert len(active) == 9 and all(
            r.prefix.endswith(renewal.PREVIOUS + "/") for r in active
        )


def test_missing_membership_or_modified_source_blocks_staging(
    client, tmp_path, renewal
):
    with client.app.state.database.session_factory() as db:
        prepare_fixture(db, tmp_path, renewal)
        member = db.scalar(select(WorkspaceMember))
        db.delete(member)
        db.flush()
        with pytest.raises(ValueError, match="Existing membership"):
            renewal.inventory(db, tmp_path)
        db.rollback()
        source = tmp_path / "simulator/real-scenes/assets/16.mp4"
        source.write_bytes(b"unreviewed replacement")
        with pytest.raises(ValueError, match="bytes changed"):
            renewal.inventory(db, tmp_path)


def test_legacy_connection_setup_cannot_enable_recursive_root_scans(
    client, tmp_path, renewal
):
    path = Path(__file__).resolve().parents[1] / "scripts/connect_demo_buckets.py"
    spec = importlib.util.spec_from_file_location("legacy_buckets", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with client.app.state.database.session_factory() as db:
        prepare_fixture(db, tmp_path, renewal)
        journal = renewal.inventory(db, tmp_path)
        renewal.stage(db, tmp_path, journal)
        renewal.activate(db, journal)
        db.commit()
        with pytest.raises(ValueError, match="Versioned evaluation sources"):
            module.prepare(
                db, client.app.state.settings, {"endpoint": "https://storage.example"}
            )
        assert all(
            rule.prefix.endswith(renewal.RELEASE + "/")
            for rule in db.scalars(
                select(StorageSync).where(StorageSync.enabled.is_(True))
            )
        )


def test_full_sync_reuses_verified_uploads_and_does_not_revive_retired_videos(
    client, tmp_path, renewal, monkeypatch
):
    from app.storage import service

    monkeypatch.setattr(
        "app.social_features.video_uploads.validate_video", lambda *args: None
    )
    with client.app.state.database.session_factory() as db:
        prepare_fixture(db, tmp_path, renewal)
        journal = renewal.inventory(db, tmp_path)
        renewal.stage(db, tmp_path, journal)
        db.commit()
        connection_row = journal["connections"][0]
        connection = renewal.checked_connection(db, connection_row)
        sources = {}
        for row in journal["created"]:
            if row["owner"] == connection_row["owner"]:
                renewal.bind_source(db, connection, row, renewal.RELEASE)
                sources[
                    connection.prefix
                    + renewal.RELEASE
                    + "/"
                    + Path(row["item"]["path"]).name
                ] = (tmp_path / row["item"]["path"]).read_bytes()
        renewal.activate(db, journal)
        db.commit()

        class Bucket:
            generation = 0

            def __init__(self, *args):
                pass

            def objects(self, prefix, cursor, recursive=True):
                assert prefix.endswith(renewal.RELEASE + "/") and cursor is None
                return {
                    "items": [
                        {
                            "key": key,
                            "etag": str(self.generation),
                            "size": len(raw),
                            "modified_at": None,
                        }
                        for key, raw in sources.items()
                    ],
                    "next_cursor": None,
                }

            def download(self, key):
                raw = sources[key]
                return (
                    raw,
                    "video/mp4",
                    {"key": key, "sha256": hashlib.sha256(raw).hexdigest()},
                )

        monkeypatch.setattr(service, "BucketClient", Bucket)
        rule = db.scalar(
            select(StorageSync).where(
                StorageSync.connection_id == connection.id,
                StorageSync.enabled.is_(True),
            )
        )
        for generation in (1, 2):
            Bucket.generation = generation
            service.sync_page(db, rule, client.app.state.settings)
        imports = list(db.scalars(select(StorageImport)))
        assert len(imports) == 2 and all(run.status == "completed" for run in imports)
        assert db.scalar(select(func.count()).select_from(PublicationUpload)) == len(
            sources
        )
        assert db.scalar(select(func.count()).select_from(Publication)) == 60
        assert all(
            db.get(Publication, uuid.UUID(r["id"])).hidden
            for r in journal["previous"]
            if r["item"]["kind"] == "video"
        )


def test_incomplete_or_mismatched_acceptance_cannot_retire_old_videos(
    client, tmp_path, renewal
):
    with client.app.state.database.session_factory() as db:
        prepare_fixture(db, tmp_path, renewal)
        journal = renewal.inventory(db, tmp_path)
        with pytest.raises(ValueError, match="does not match"):
            renewal.require_acceptance(db, journal, {"passed": True})
        receipt = {
            "release": renewal.RELEASE,
            "sources": {r["id"]: r["item"]["sha256"] for r in journal["created"]},
            "passed": True,
            "positive": [],
        }
        with pytest.raises(ValueError, match="Complete live and visual"):
            renewal.require_acceptance(db, journal, receipt)
        assert all(
            not db.get(Publication, uuid.UUID(r["id"])).hidden
            for r in journal["previous"]
        )


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        ({}, True),
        ({"post_id": "another-video"}, False),
        ({"frame_timestamp_ms": 5000}, False),
        ({"simulated": True}, False),
        ({"localization_quality": "approximate_box"}, False),
    ],
)
def test_acceptance_checks_gallery_evidence_independently_of_register_found(
    change, expected
):
    path = Path(__file__).resolve().parents[1] / "scripts/verify_evaluation_videos.py"
    spec = importlib.util.spec_from_file_location("video_verification", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    match = {
        "post_id": "reviewed-video",
        "frame_timestamp_ms": 2000,
        "evidence_id": "real-frame",
        "mime_type": "video/mp4",
        "localization_quality": "sam",
        "simulated": False,
        "boxed_url": "/evidence",
        "matched_labels": ["keys"],
        **change,
    }
    reply = {"found": False, "response_language": "es", "gallery_matches": [match]}
    assert (
        module.check_match(reply, "reviewed-video", [1000, 3000], "es")[0] is expected
    )


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg required")
@pytest.mark.parametrize("size", ["1280x720", "320x180"])
def test_preparation_keeps_full_actions_and_rejects_upscaled_sources(
    tmp_path, monkeypatch, size
):
    path = Path(__file__).resolve().parents[1] / "scripts/prepare_evaluation_videos.py"
    monkeypatch.syspath_prepend(str(path.parent))
    spec = importlib.util.spec_from_file_location("scene_preparation", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cache = tmp_path / "sources"
    cache.mkdir()
    base = tmp_path / "simulator/real-scenes"
    (base / "assets").mkdir(parents=True)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "BASE", base)
    monkeypatch.setattr(module, "CACHE", cache)
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"testsrc2=size={size}:rate=2:duration=17",
            "-c:v",
            "libx264",
            "-threads",
            "1",
            str(cache / "101.mp4"),
        ],
        check=True,
    )
    item = {
        "id": 101,
        "group": "memory",
        "kind": "video",
        "source": "fixture://recording",
    }
    if size == "320x180":
        with pytest.raises(RuntimeError, match="native HD"):
            module.prepare(item)
    else:
        result = module.prepare(item)
        assert result["duration"] == pytest.approx(17, abs=0.15)
        assert result["fps"] == 2 and result["complete_recording"]
        assert (result["width"], result["height"]) == (1280, 720)


def test_rate_limited_login_preserves_receipt_and_uses_only_selected_account(
    tmp_path, monkeypatch
):
    import httpx

    path = Path(__file__).resolve().parents[1] / "scripts/verify_evaluation_videos.py"
    spec = importlib.util.spec_from_file_location("rate_limited_verification", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    (tmp_path / "simulator/real-scenes").mkdir(parents=True)
    (tmp_path / "simulator/postman").mkdir()
    (tmp_path / "simulator/real-scenes/video-evaluation.json").write_text(
        '{"videos":[]}'
    )
    accounts = [
        {"prefix": group, "values": {"username": group, "password": "fixture"}}
        for group in ("security", "hospital", "memory")
    ]
    (tmp_path / "simulator/postman/jury.json").write_text(
        json.dumps({"base_url": "https://fixture.test", "scenarios": accounts})
    )
    journal = tmp_path / "journal.json"
    journal.write_text(json.dumps({"release": "evaluation-v3", "created": []}))
    output = tmp_path / "receipt.json"
    previous = '{"sources":{},"positive":[],"preserve":"previous measurements"}'
    output.write_text(previous)
    calls = []

    class RateLimited:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def post(self, url, json):
            calls.append(json["email"])
            return httpx.Response(
                429, request=httpx.Request("POST", "https://fixture.test" + url)
            )

    monkeypatch.setattr(module.httpx, "Client", lambda **kwargs: RateLimited())
    monkeypatch.setattr(
        "sys.argv",
        [
            str(path),
            "--journal",
            str(journal),
            "--output",
            str(output),
            "--resume",
            "--group",
            "memory",
        ],
    )
    with pytest.raises(httpx.HTTPStatusError):
        module.main()
    assert calls == ["memory"]
    assert output.read_text() == previous


def test_verify_sync_cli_keeps_active_release(client, tmp_path, renewal, monkeypatch):
    journal_path = tmp_path / "journal.json"
    journal = {"release": renewal.RELEASE, "phase": "active"}
    journal_path.write_text(json.dumps(journal))
    calls = []

    def verify(db, current, settings):
        calls.append(current["phase"])
        return {"passed": True, "cycles": [1, 2]}

    def unexpected_rollback(*args):
        pytest.fail("Synchronization verification must never roll back the release")

    monkeypatch.setattr(renewal, "verify_sync", verify)
    monkeypatch.setattr(renewal, "rollback", unexpected_rollback)
    monkeypatch.setattr(renewal, "Database", lambda _: client.app.state.database)
    monkeypatch.setattr(
        "sys.argv",
        ["renew", "--phase", "verify-sync", "--journal", str(journal_path)],
    )
    renewal.main()
    assert calls == ["active"]
    assert json.loads(journal_path.read_text()) == journal
    assert json.loads((tmp_path / "synchronization.json").read_text())["passed"]

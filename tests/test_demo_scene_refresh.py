"""Demo renewal must reuse groups and keep scheduled imports idempotent."""

import hashlib
import importlib.util
import json
from pathlib import Path

from app.accounts.models import PasswordAccount
from app.models import Role, User, Workspace, WorkspaceMember
from app.social_features.evidence_models import PublicationUpload
from app.social_features.models import Publication
from app.storage.models import StorageConnection
from app.storage.provenance_models import StorageObject
from sqlalchemy import func, select


def test_refresh_requires_current_groups_and_reuses_source_uploads(client, tmp_path):
    import pytest

    path = Path(__file__).resolve().parents[1] / "scripts/refresh_demo_gallery.py"
    spec = importlib.util.spec_from_file_location("scene_refresh", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert set(module.SCENARIOS) == {"security", "nursing", "memory"}
    fixture_dir = tmp_path / "simulator/real-scenes"
    fixture_dir.mkdir(parents=True)
    items = []
    for group in module.SCENARIOS:
        for index in range(16):
            raw = f"fixture {group} {index}".encode()
            name = f"{group}-{index}.jpg"
            (fixture_dir / name).write_bytes(raw)
            items.append(
                {
                    "group": group,
                    "id": index,
                    "path": f"simulator/real-scenes/{name}",
                    "kind": "image" if index < 12 else "video",
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "width": 1280,
                    "height": 720,
                    "license": "test fixture",
                    "source": "fixture://test",
                    "label": name,
                }
            )
    (fixture_dir / "manifest.json").write_text(json.dumps({"items": items}))
    with client.app.state.database.session_factory() as db:
        before = db.scalar(select(func.count()).select_from(Workspace))
        with pytest.raises(ValueError, match="Existing workspace is required"):
            module.prepare(db, tmp_path, True)
        assert db.scalar(select(func.count()).select_from(Workspace)) == before
        for group, (name, names) in module.SCENARIOS.items():
            users = []
            for username in names:
                user = User(
                    email=username + "@demo.test",
                    display_name=username,
                    password_hash="test",
                )
                db.add(user)
                db.flush()
                db.add(PasswordAccount(user_id=user.id, username=username))
                users.append(user)
            workspace = Workspace(name=name, created_by_id=users[0].id)
            db.add(workspace)
            db.flush()
            for user in users:
                db.add(
                    WorkspaceMember(
                        workspace_id=workspace.id, user_id=user.id, role=Role.REGISTER
                    )
                )
            if group == "security":
                db.add(
                    StorageConnection(
                        owner_id=users[0].id,
                        workspace_id=workspace.id,
                        name="Fixture source",
                        provider="s3",
                        endpoint="https://storage.example",
                        bucket="demo",
                        region="auto",
                        prefix="demo/v2/police/alex-rivera/",
                        secret="test-encrypted",
                    )
                )
        db.commit()
        counts = (
            db.scalar(select(func.count()).select_from(Workspace)),
            db.scalar(select(func.count()).select_from(WorkspaceMember)),
        )
        first = module.prepare(db, tmp_path, True)
        db.commit()
        second = module.prepare(db, tmp_path, True)
        assert len(first["created"]) == 48 and not second["created"]
        assert db.scalar(select(func.count()).select_from(Publication)) == 48
        assert db.scalar(select(func.count()).select_from(StorageObject)) == 6
        assert db.scalar(select(func.count()).select_from(PublicationUpload)) == 6
        assert counts == (
            db.scalar(select(func.count()).select_from(Workspace)),
            db.scalar(select(func.count()).select_from(WorkspaceMember)),
        )

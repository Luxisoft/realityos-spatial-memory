"""A purge must preserve shared personal media and must remain a dry run by default."""

import importlib.util
from pathlib import Path

from app.models import MediaAsset, MediaKind, User, Workspace
from app.social_features.models import Publication

spec = importlib.util.spec_from_file_location(
    "workspace_purge", Path(__file__).parents[1] / "scripts/purge_workspaces.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_purge_preserves_personal_publication_and_dry_run(client):
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).first()
        old = Workspace(name="Old team", created_by_id=owner.id)
        db.add(old)
        db.flush()
        shared = MediaAsset(
            workspace_id=old.id,
            kind=MediaKind.IMAGE,
            mime_type="image/png",
            original_bytes=b"keep",
            sha256="a" * 64,
            byte_size=4,
        )
        exclusive = MediaAsset(
            workspace_id=old.id,
            kind=MediaKind.IMAGE,
            mime_type="image/png",
            original_bytes=b"drop",
            sha256="b" * 64,
            byte_size=4,
        )
        db.add_all([shared, exclusive])
        db.flush()
        personal = Publication(owner_id=owner.id, media_id=shared.id, audience="home")
        db.add(personal)
        db.commit()
        old_id, shared_id, exclusive_id, personal_id = (
            old.id,
            shared.id,
            exclusive.id,
            personal.id,
        )
        report = module.purge(db, [old_id])
        assert report["applied"] is False
        assert db.get(Workspace, old_id) is not None
        assert db.get(MediaAsset, shared_id).workspace_id == old_id
        report = module.purge(db, [old_id], apply=True)
        db.expire_all()
        assert report["applied"] is True
        assert db.get(Workspace, old_id) is None
        assert db.get(MediaAsset, exclusive_id) is None
        assert db.get(MediaAsset, shared_id).original_bytes == b"keep"
        assert db.get(MediaAsset, shared_id).workspace_id != old_id
        assert db.get(Publication, personal_id) is not None

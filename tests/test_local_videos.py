"""Group videos use ordinary BYTEA publications and one transactional SQL revision."""

import hashlib
import uuid
from pathlib import Path

import pytest
from app.db import Base, Database
from app.local.bootstrap import install_data_updates
from app.local.sql_data import apply_seed
from app.local.state import require_local
from app.local_models import LocalEvaluationState
from app.models import MediaAsset, MediaKind, User, Workspace, WorkspaceMember
from app.security import create_access_token
from app.social_features.models import (
    Publication,
    PublicationTag,
    PublicationTerm,
    UserProfile,
)
from app.workspaces.purge import purge
from sqlalchemy import delete, select, update
from test_local_access import local_settings

REQUESTED = {
    "security": {"25757454", "29401365", "30614848"},
    "meta-social": {"33802407", "12557513", "3699519"},
}


def video_posts(db):
    return list(
        db.scalars(select(Publication).where(Publication.source_ref.like("%:pexels-%")))
    )


def test_requested_videos_are_scoped_publications_with_original_bytes(evaluation):
    accounts = evaluation.get("/v1/auth/local-accounts").json()["accounts"]
    settings = evaluation.app.state.settings
    with evaluation.app.state.database.session_factory() as db:
        posts = video_posts(db)
        assert len(posts) == 6
        for slug, expected in REQUESTED.items():
            scoped = [p for p in posts if p.source_ref.startswith(slug + ":")]
            assert {p.source_ref.split("pexels-")[1] for p in scoped} == expected
            workspace_id = scoped[0].workspace_id
            member = next(a for a in accounts if a["workspace_id"] == str(workspace_id))
            outsider = next(
                a for a in accounts if a["workspace_id"] != str(workspace_id)
            )

            def auth(account):
                return {
                    "Authorization": "Bearer "
                    + create_access_token(uuid.UUID(account["id"]), settings)
                }

            response = evaluation.get(
                "/v1/gallery/page",
                params={"workspace_id": str(workspace_id), "limit": 30},
                headers=auth(member),
            )
            assert response.status_code == 200
            gallery = {p["id"]: p for p in response.json()["items"]}
            for post in scoped:
                asset = db.get(MediaAsset, post.media_id)
                assert asset.kind == MediaKind.VIDEO and asset.mime_type == "video/mp4"
                assert asset.byte_size == len(asset.original_bytes)
                assert hashlib.sha256(asset.original_bytes).hexdigest() == asset.sha256
                assert asset.extra_metadata["source_url"].startswith(
                    "https://www.pexels.com/"
                )
                assert (
                    asset.extra_metadata["license_url"]
                    == "https://www.pexels.com/license/"
                )
                assert asset.extra_metadata["duration_seconds"] > 0
                assert not post.ai_detections and post.face_count == 0
                assert post.note_source == "text"
                assert post.display_text["caption"]["source"] == post.caption
                assert (
                    gallery[str(post.id)]["display_text"]["caption"]["es"]
                    == post.display_text["caption"]["es"]
                )
                path = "/v1/" + gallery[str(post.id)]["media_url"]
                playback = evaluation.get(
                    path, headers={**auth(member), "Range": "bytes=0-127"}
                )
                assert playback.status_code == 206
                assert playback.content == asset.original_bytes[:128]
                assert (
                    playback.headers["content-range"]
                    == f"bytes 0-127/{asset.byte_size}"
                )
                assert evaluation.get(path, headers=auth(outsider)).status_code in {
                    403,
                    404,
                }


@pytest.mark.parametrize(
    "change", ["removed_member", "inactive_owner", "removed_group"]
)
def test_video_update_is_atomic_and_preserves_membership_edits_and_deletions(
    postgres_url, tmp_path, monkeypatch, change
):
    from app.local import bootstrap, sql_data

    # Exercise this historical revision independently of later record additions.
    monkeypatch.setattr(
        bootstrap, "DATA_UPDATES", (("group-videos-v1", "004-group-videos.sql"),)
    )

    settings = local_settings(
        tmp_path, database_url=postgres_url, local_evaluation_enabled=True
    )
    with Database(postgres_url) as database:
        Base.metadata.create_all(database.engine)
        with database.session() as db:
            require_local(db, settings)
            apply_seed(db, settings, "001-scenarios.sql")
            original_count = db.query(Publication).count()
            media_count = db.query(MediaAsset).count()
            first = db.scalar(
                select(Publication).where(Publication.source_ref.like("memory:%"))
            )
            first.caption = "Edited before the new video revision"
            identifier = first.id

        original_file = sql_data.fixture_file
        with database.session() as db:
            with monkeypatch.context() as broken:
                broken.setattr(
                    sql_data, "fixture_file", lambda *args: tmp_path / "missing.mp4"
                )
                with pytest.raises(FileNotFoundError):
                    install_data_updates(db, settings)
            assert db.query(Publication).count() == original_count
            assert db.query(MediaAsset).count() == media_count
            assert db.get(LocalEvaluationState, "group-videos-v1") is None
            assert sql_data.fixture_file is original_file
            police = db.scalar(
                select(Publication.workspace_id).where(
                    Publication.source_ref.like("security:%")
                )
            )
            removed_member = db.scalar(
                select(WorkspaceMember)
                .where(WorkspaceMember.workspace_id == police)
                .order_by(WorkspaceMember.user_id)
            )
            removed_user = removed_member.user_id
            if change == "removed_member":
                db.delete(removed_member)
            elif change == "inactive_owner":
                db.get(User, removed_user).is_active = False
            else:
                # Simulate a completed removal without deleting the access
                # accounts or their identity profiles alongside the group.
                db.execute(
                    update(UserProfile)
                    .where(
                        UserProfile.avatar_media_id.in_(
                            select(MediaAsset.id).where(
                                MediaAsset.workspace_id == police
                            )
                        )
                    )
                    .values(avatar_media_id=None)
                )
                purge(db, [police], apply=True, commit=False, strict_scope=True)
            social = db.scalar(
                select(Publication.workspace_id).where(
                    Publication.source_ref.like("meta-social:%")
                )
            )
            existing_category = PublicationTerm(
                workspace_id=social,
                kind="category",
                name="Outdoor life",
                name_key="outdoor life",
                active=False,
                display_text={
                    "name": {"source": "Outdoor life", "es": "Texto del propietario"}
                },
            )
            db.add(existing_category)
            db.flush()
            expected = 3 if change == "removed_group" else 5
            assert install_data_updates(db, settings) == {
                "group-videos-v1": {"publications": expected}
            }
            assert not any(p.owner_id == removed_user for p in video_posts(db))
            assert all(
                p.category_id == existing_category.id
                for p in video_posts(db)
                if p.workspace_id == social
            )
            assert existing_category.active is False
            assert (
                existing_category.display_text["name"]["es"] == "Texto del propietario"
            )
            if change == "removed_group":
                assert db.get(Workspace, police) is None

        with database.session() as db:
            posts = video_posts(db)
            edited, removed = posts[:2]
            edited.caption = "Edited after installation"
            edited.hidden = True
            edited_id, removed_id = edited.id, removed.id
            # Ordinary gallery publications have no record or biometric linkage.
            db.execute(
                delete(PublicationTag).where(PublicationTag.post_id == removed_id)
            )
            db.delete(removed)
            db.execute(
                delete(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == edited.workspace_id,
                    WorkspaceMember.user_id == edited.owner_id,
                )
            )
        with database.session() as db:
            assert install_data_updates(db, settings, root=Path("/no-fixtures")) == {}
            assert db.get(Publication, removed_id) is None
            assert db.get(Publication, edited_id).hidden
            assert db.get(Publication, edited_id).caption == "Edited after installation"
            assert (
                db.get(Publication, identifier).caption
                == "Edited before the new video revision"
            )

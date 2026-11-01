"""Replace synthetic directory media with the Muse-anchored photo set.

For the 20 profiles in ``PROFILE_ROWS``: deletes only rows derived from the
synthetic directory (``facebook_media`` inventory, imported assets and frames,
derived publications) and re-seeds through the production import path
(10 photos, 0 videos). Avatars, users, consents and source portraits are kept.
Directory users outside ``PROFILE_ROWS`` are deleted entirely (10 dropped
profiles). The original workshop video plus 15 same-shop takes are published
in the "Mechanic Workshop" group (5 members, day/night shifts).

Dry-run by default; pass ``--apply`` to write. Run inside the ``api``
container with ``simulator/social-directory/muse/`` and ``workshop/`` copied
next to the seed tree (``--fixture-root``).
"""

from __future__ import annotations

import argparse
import io
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
for _extra in (ROOT / "backend", ROOT / "scripts"):
    if _extra.is_dir() and str(_extra) not in sys.path:
        sys.path.append(str(_extra))

from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.orm import defer  # noqa: E402

import seed_social_directory as seed  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.db import Database  # noqa: E402
from app.models import (  # noqa: E402
    AuditEvent,
    CaptureSession,
    CaptureStatus,
    Device,
    DeviceAssignment,
    MediaAsset,
    MediaKind,
    ObjectFact,
    ObjectObservation,
    QueryHistory,
    Role,
    User,
    Workspace,
    WorkspaceMember,
)
from app.social import (  # noqa: E402
    Comment,
    FacebookIdentity,
    FacebookMedia,
    FacebookProfile,
    Publication,
    Reaction,
    Report,
)

WORKSHOP_SOURCE = "workshop"
WORKSHOP_REF = "electronics-workshop-original"
WORKSHOP_JOSE = "__jose__"
# (directory slug or __jose__, role, shift, workshop role)
WORKSHOP_ROSTER = (
    (WORKSHOP_JOSE, "ADMIN", "day", "owner / lead mechanic"),
    ("diego-mendoza", "QUERY", "day", "electronics & diagnostics"),
    ("martin-quintero", "QUERY", "day", "fabrication & welding"),
    ("kwame-mensah", "QUERY", "night", "parts & inventory"),
    ("omar-benali", "QUERY", "night", "electrical systems"),
)


def directory_users(db):
    return list(
        db.scalars(
            select(User)
            .where(User.email.like("%@directory.realityos.invalid"))
            .order_by(User.email)
        )
    )


def collect_profile_rows(db, user):
    fb_ids = set(
        db.scalars(
            select(FacebookMedia.fb_id).where(
                FacebookMedia.user_id == user.id,
                FacebookMedia.fb_id.like("directory-%"),
            )
        )
    )
    home = db.scalar(select(Workspace).where(Workspace.name == f"home:{user.id}"))
    assets: list[MediaAsset] = []
    if home is not None:
        candidates = db.scalars(
            select(MediaAsset)
            .options(defer(MediaAsset.original_bytes))
            .where(MediaAsset.workspace_id == home.id)
        )
        for asset in candidates:
            meta = asset.extra_metadata or {}
            if meta.get("origin") == "facebook-import" and not meta.get(
                "face_profile_picture"
            ):
                assets.append(asset)
    asset_ids = {asset.id for asset in assets}
    publications: dict[UUID, Publication] = {}
    if asset_ids:
        for post in db.scalars(
            select(Publication).where(Publication.media_id.in_(asset_ids))
        ):
            publications[post.id] = post
    if fb_ids:
        for post in db.scalars(
            select(Publication).where(
                Publication.owner_id == user.id,
                Publication.source_ref.in_(fb_ids),
            )
        ):
            publications[post.id] = post
    for post in db.scalars(
        select(Publication).where(
            Publication.owner_id == user.id,
            Publication.source == "simulator-work",
        )
    ):
        publications[post.id] = post
    return fb_ids, assets, list(publications.values())


def purge_profile(db, user, fb_ids, assets, publications, *, apply: bool) -> dict:
    post_ids = [post.id for post in publications]
    asset_ids = [asset.id for asset in assets]
    counts = {
        "facebook_media": len(fb_ids),
        "assets": len(asset_ids),
        "publications": len(post_ids),
    }
    if not apply:
        return counts
    if post_ids:
        db.execute(delete(Comment).where(Comment.post_id.in_(post_ids)))
        db.execute(delete(Report).where(Report.post_id.in_(post_ids)))
        db.execute(delete(Reaction).where(Reaction.post_id.in_(post_ids)))
        db.execute(delete(Publication).where(Publication.id.in_(post_ids)))
    if asset_ids:
        # Face enrollments and BYTEA chunks cascade from media_assets.
        db.execute(delete(MediaAsset).where(MediaAsset.id.in_(asset_ids)))
    if fb_ids:
        db.execute(delete(FacebookMedia).where(FacebookMedia.fb_id.in_(fb_ids)))
    profile = db.get(FacebookProfile, user.id)
    if profile is not None:
        profile.photos_count = seed.PHOTOS_PER_PROFILE
        profile.videos_count = 0
        profile.imported_photos = 0
        profile.imported_videos = 0
        profile.skipped_media = 0
        profile.import_error = None
        profile.import_status = "pending"
    return counts


def delete_directory_user(db, user, *, apply: bool) -> dict:
    """Delete a dropped directory profile and everything it owns."""

    from sqlalchemy import update

    fb_ids, assets, publications = collect_profile_rows(db, user)
    owned_posts = list(
        db.scalars(select(Publication).where(Publication.owner_id == user.id))
    )
    post_ids = {post.id for post in publications} | {post.id for post in owned_posts}
    home = db.scalar(select(Workspace).where(Workspace.name == f"home:{user.id}"))
    home_assets = []
    if home is not None:
        home_assets = list(
            db.scalars(
                select(MediaAsset)
                .options(defer(MediaAsset.original_bytes))
                .where(MediaAsset.workspace_id == home.id)
            )
        )
    counts = {
        "facebook_media": len(fb_ids),
        "assets": len(home_assets),
        "publications": len(post_ids),
        "workspaces": len(
            list(db.scalars(select(Workspace).where(Workspace.created_by_id == user.id)))
        ),
    }
    if not apply:
        return counts
    if post_ids:
        post_id_list = list(post_ids)
        db.execute(delete(Comment).where(Comment.post_id.in_(post_id_list)))
        db.execute(delete(Report).where(Report.post_id.in_(post_id_list)))
        db.execute(delete(Reaction).where(Reaction.post_id.in_(post_id_list)))
        db.execute(delete(Publication).where(Publication.id.in_(post_id_list)))
    db.execute(delete(Comment).where(Comment.user_id == user.id))
    db.execute(delete(Report).where(Report.user_id == user.id))
    db.execute(delete(Reaction).where(Reaction.user_id == user.id))
    if fb_ids:
        db.execute(delete(FacebookMedia).where(FacebookMedia.fb_id.in_(fb_ids)))
    if home_assets:
        db.execute(
            delete(MediaAsset).where(
                MediaAsset.id.in_([asset.id for asset in home_assets])
            )
        )
    db.execute(delete(CaptureSession).where(CaptureSession.created_by_id == user.id))
    db.execute(delete(Workspace).where(Workspace.created_by_id == user.id))
    db.execute(delete(Device).where(Device.created_by_id == user.id))
    db.execute(delete(DeviceAssignment).where(DeviceAssignment.attested_by_id == user.id))
    db.execute(delete(QueryHistory).where(QueryHistory.user_id == user.id))
    db.execute(delete(FacebookIdentity).where(FacebookIdentity.user_id == user.id))
    db.execute(update(AuditEvent).where(AuditEvent.actor_id == user.id).values(actor_id=None))
    db.execute(
        update(ObjectObservation)
        .where(ObjectObservation.created_by_id == user.id)
        .values(created_by_id=None)
    )
    db.execute(
        update(ObjectObservation)
        .where(ObjectObservation.verified_by_id == user.id)
        .values(verified_by_id=None)
    )
    db.execute(
        update(ObjectFact).where(ObjectFact.verified_by_id == user.id).values(verified_by_id=None)
    )
    # Profiles, consents, enrollments, verifications, friends, posts, members
    # and tokens cascade from the user row.
    db.execute(delete(User).where(User.id == user.id))
    return counts


def resolve_roster(db) -> list[tuple[User, Role, str, str]]:
    jose = db.scalar(select(User).where(User.display_name == "Jose Marin"))
    if jose is None:
        raise RuntimeError("Owner user 'Jose Marin' not found.")
    roster = []
    for slug, role_name, shift, workshop_role in WORKSHOP_ROSTER:
        if slug == WORKSHOP_JOSE:
            roster.append((jose, Role[role_name], shift, workshop_role))
            continue
        member = db.scalar(
            select(User).where(User.email == f"{slug}@directory.realityos.invalid")
        )
        if member is None:
            raise RuntimeError(f"Workshop member not found: {slug}")
        roster.append((member, Role[role_name], shift, workshop_role))
    return roster


def ensure_workshop_publication(db, *, group_name: str, filename: str, apply: bool) -> dict:
    videos = db.scalars(
        select(MediaAsset)
        .options(defer(MediaAsset.original_bytes))
        .where(
            MediaAsset.kind == MediaKind.VIDEO,
            MediaAsset.parent_asset_id.is_(None),
        )
    )
    asset = next(
        (
            video
            for video in videos
            if (video.extra_metadata or {}).get("filename") == filename
        ),
        None,
    )
    if asset is None:
        raise RuntimeError(f"Workshop video not found: {filename}")
    roster = resolve_roster(db)
    owner = roster[0][0]
    description = (
        "Neighborhood mechanic workshop demo. Day shift (3): "
        + ", ".join(f"{user.display_name} ({role})" for user, _, s, role in roster if s == "day")
        + ". Night shift (2): "
        + ", ".join(f"{user.display_name} ({role})" for user, _, s, role in roster if s == "night")
        + ". Members share tools and bays across shifts."
    )
    group = db.scalar(select(Workspace).where(Workspace.name == group_name))
    if group is None:
        if not apply:
            return {
                "asset_id": str(asset.id),
                "group": group_name,
                "created": True,
                "members": len(roster),
            }
        group = Workspace(name=group_name, description=description, created_by_id=owner.id)
        db.add(group)
        db.flush()
    elif apply and group.description != description:
        group.description = description
    existing = db.scalar(
        select(Publication).where(
            Publication.owner_id == owner.id,
            Publication.source == WORKSHOP_SOURCE,
            Publication.source_ref == WORKSHOP_REF,
        )
    )
    if not apply:
        members = sum(
            1
            for user, _, _, _ in roster
            if db.scalar(
                select(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == group.id,
                    WorkspaceMember.user_id == user.id,
                )
            )
            is not None
        )
        return {
            "asset_id": str(asset.id),
            "group": group_name,
            "members": f"{members}/{len(roster)}",
            "publication": str(existing.id) if existing else None,
        }
    for user, role, _shift, _workshop_role in roster:
        member = db.scalar(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == group.id,
                WorkspaceMember.user_id == user.id,
            )
        )
        if member is None:
            db.add(WorkspaceMember(workspace_id=group.id, user_id=user.id, role=role))
        elif member.role != role:
            member.role = role
    caption = "Mechanic Workshop · original shop video, full walkthrough"
    if existing is None:
        db.add(
            Publication(
                owner_id=owner.id,
                media_id=asset.id,
                audience="work",
                workspace_id=group.id,
                caption=caption,
                search_text=(
                    f"{caption} mechanic workshop repair tools lifts "
                    "diagnostics day shift"
                ),
                source=WORKSHOP_SOURCE,
                source_ref=WORKSHOP_REF,
                published_at=asset.created_at or datetime.now(UTC),
            )
        )
    else:
        existing.media_id = asset.id
        existing.audience = "work"
        existing.workspace_id = group.id
        existing.caption = caption
        existing.search_text = (
            f"{caption} mechanic workshop repair tools lifts "
            "diagnostics day shift"
        )
    # The chunking script stored representative frames as IMAGE rows; the
    # thumbnail endpoint reads FRAME rows. Retag the first frame so gallery
    # thumbnails never assemble the 546 MB original.
    children = list(
        db.scalars(
            select(MediaAsset)
            .options(defer(MediaAsset.original_bytes))
            .where(MediaAsset.parent_asset_id == asset.id)
        )
    )
    if not any(child.kind == MediaKind.FRAME for child in children) and children:
        children.sort(key=lambda row: (row.extra_metadata or {}).get("frame_index", 0))
        children[0].kind = MediaKind.FRAME
    return {"asset_id": str(asset.id), "group": group_name, "group_id": str(group.id)}


def publish_workshop_photos(db, fixture_root: Path, group_id, *, apply: bool) -> dict:
    """Publish same-shop takes as work posts owned across day/night shifts."""

    import hashlib
    import json

    from PIL import Image as PilImage

    manifest_path = fixture_root / "workshop" / "manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(
            f"Missing workshop manifest: {manifest_path}. "
            "Run scripts/generate_workshop_photos.py first."
        )
    scenes = json.loads(manifest_path.read_text()).get("scenes", {})
    done = {
        key: entry for key, entry in scenes.items() if entry.get("status") == "done"
    }
    if len(done) != 15:
        raise RuntimeError(f"Workshop set is incomplete: {len(done)}/15 takes ready.")
    roster = {WORKSHOP_JOSE: None}
    counts = {"assets": 0, "publications": 0}
    sessions: dict[str, CaptureSession] = {}
    for key in sorted(done):
        entry = done[key]
        owner_slug = entry["owner"]
        if owner_slug not in roster:
            member = db.scalar(
                select(User).where(
                    User.email == f"{owner_slug}@directory.realityos.invalid"
                )
            )
            if member is None:
                raise RuntimeError(f"Workshop member not found: {owner_slug}")
            roster[owner_slug] = member
        elif roster[owner_slug] is None and owner_slug == WORKSHOP_JOSE:
            jose = db.scalar(select(User).where(User.display_name == "Jose Marin"))
            if jose is None:
                raise RuntimeError("Owner user 'Jose Marin' not found.")
            roster[owner_slug] = jose
        owner = roster[owner_slug]
        raw = (fixture_root / "workshop" / f"{key}.jpg").read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != entry["sha256"]:
            raise RuntimeError(f"Workshop take changed on disk: {key}.jpg")
        ref = f"workshop-{key}"
        existing = db.scalar(
            select(Publication).where(
                Publication.owner_id == owner.id,
                Publication.source == WORKSHOP_SOURCE,
                Publication.source_ref == ref,
            )
        )
        if existing is not None:
            continue
        counts["publications"] += 1
        if not apply:
            continue
        if owner_slug not in sessions:
            session = CaptureSession(
                workspace_id=group_id,
                created_by_id=owner.id,
                origin="workshop-upload",
                status=CaptureStatus.CLOSED,
                consent_confirmed=True,
                closed_at=datetime.now(UTC),
            )
            db.add(session)
            db.flush()
            sessions[owner_slug] = session
        with PilImage.open(io.BytesIO(raw)) as picture:
            width, height = picture.size
        asset = MediaAsset(
            workspace_id=group_id,
            capture_session_id=sessions[owner_slug].id,
            kind=MediaKind.IMAGE,
            mime_type="image/jpeg",
            original_bytes=raw,
            sha256=digest,
            byte_size=len(raw),
            width=width,
            height=height,
            extra_metadata={
                "origin": "workshop-upload",
                "shift": entry["shift"],
                "take": entry["take"],
                "tools": entry["tools"],
            },
        )
        db.add(asset)
        db.flush()
        counts["assets"] += 1
        try:
            published_at = datetime.fromisoformat(entry["generated_at"])
        except (KeyError, ValueError):
            published_at = datetime.now(UTC)
        db.add(
            Publication(
                owner_id=owner.id,
                media_id=asset.id,
                audience="work",
                workspace_id=group_id,
                caption=entry["caption"],
                search_text=(
                    f"{entry['caption']} {entry['tools']} {entry['shift']} shift "
                    "mechanic workshop"
                ),
                source=WORKSHOP_SOURCE,
                source_ref=ref,
                published_at=published_at,
            )
        )
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write to the database.")
    parser.add_argument("--slugs", default="", help="Comma-separated subset to replace.")
    parser.add_argument("--fixture-root", default=str(seed.FIXTURE_ROOT))
    parser.add_argument("--group-name", default="Mechanic Workshop")
    parser.add_argument("--workshop-filename", default="electronics-workshop-source.mp4")
    parser.add_argument("--skip-workshop", action="store_true")
    args = parser.parse_args()

    fixture_root = Path(args.fixture_root)
    seed.FIXTURE_ROOT = fixture_root
    seed.SOURCE_ROOT = fixture_root / "source"
    seed.GENERATED_ROOT = fixture_root / "generated"
    seed.MUSE_ROOT = fixture_root / "muse"
    # Re-seeding imports avatar bytes through local_fetch; avatars stay put.
    wanted = {slug.strip() for slug in args.slugs.split(",") if slug.strip()}

    settings = get_settings()
    database = Database(settings.database_url)
    with database.session_factory() as db:
        users = {
            user.email.split("@")[0]: user
            for user in directory_users(db)
            if not wanted or user.email.split("@")[0] in wanted
        }
        rows = [
            (index, row)
            for index, row in enumerate(seed.PROFILE_ROWS)
            if row[0] in users
        ]
        dropped = sorted(
            slug for slug in users if slug not in {row[0] for _, row in rows}
        )
        print(f"profiles in scope: {len(rows)} apply={args.apply}")
        totals = {"facebook_media": 0, "assets": 0, "publications": 0}
        for _index, row in rows:
            slug = row[0]
            user = users[slug]
            fb_ids, assets, publications = collect_profile_rows(db, user)
            counts = purge_profile(db, user, fb_ids, assets, publications, apply=args.apply)
            for key in totals:
                totals[key] += counts[key]
            print(f"purge {slug}: {counts}")
        for slug in dropped:
            counts = delete_directory_user(db, users[slug], apply=args.apply)
            print(f"delete {slug}: {counts}")
        if not args.skip_workshop:
            workshop = ensure_workshop_publication(
                db,
                group_name=args.group_name,
                filename=args.workshop_filename,
                apply=args.apply,
            )
            print(f"workshop: {workshop}")
            photos = publish_workshop_photos(
                db,
                fixture_root,
                workshop.get("group_id"),
                apply=args.apply,
            )
            print(f"workshop photos: {photos}")
        if args.apply:
            db.commit()
        else:
            db.rollback()
        print(f"totals: {totals}")
        if not args.apply:
            return
    # Re-seed through the production import path, one transaction per profile.
    with database.session_factory() as db:
        workspace = db.scalar(
            select(Workspace).where(Workspace.name == seed.DEMO_WORKSPACE)
        )
        workspace_id = workspace.id
    for index, row in rows:
        with database.session_factory() as db:
            workspace = db.get(Workspace, workspace_id)
            seed.seed_profile(db, settings, workspace, row, index)
            db.commit()
            print(f"seeded {row[0]}")


if __name__ == "__main__":
    main()
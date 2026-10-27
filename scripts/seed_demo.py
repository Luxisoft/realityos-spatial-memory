"""Load a legal, synthetic RealityOS workshop demonstration into PostgreSQL."""

from __future__ import annotations

import hashlib
import io
import os
from datetime import UTC, datetime

from app.config import get_settings
from app.db import Database
from app.meta import MockMetaModelClient
from app.models import (
    CaptureSession,
    CaptureStatus,
    MediaAsset,
    MediaKind,
    Role,
    User,
    Workspace,
    WorkspaceMember,
    Zone,
)
from app.security import hash_password
from app.services import create_processing_job, process_job
from PIL import Image, ImageDraw
from sqlalchemy import select


def synthetic_asset(name: str, location: str, color: str) -> bytes:
    image = Image.new("RGB", (960, 640), "#27312f")
    draw = ImageDraw.Draw(image)
    draw.rectangle((90, 130, 870, 520), fill="#554941")
    draw.rounded_rectangle((240, 215, 680, 380), radius=24, fill=color)
    draw.rectangle((620, 265, 810, 325), fill="#314044")
    draw.rectangle((330, 355, 470, 485), fill="#202725")
    draw.text((110, 75), f"Taller RealityOS · {location}", fill="#f1f0ea")
    draw.text((110, 105), name.title(), fill="#f1f0ea")
    result = io.BytesIO()
    image.save(result, format="PNG")
    return result.getvalue()


def synthetic_drill() -> bytes:
    return synthetic_asset("yellow drill", "Storage A · Shelf 3 · Level 2", "#f0bf24")


def main() -> None:
    settings = get_settings()
    database = Database(settings.database_url)
    email = os.getenv("SEED_ADMIN_EMAIL", "admin@realityos.local").casefold()
    password = os.getenv("SEED_ADMIN_PASSWORD", "ChangeMeNow123!")
    with database.session_factory() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(
                email=email,
                display_name="RealityOS Demo Admin",
                password_hash=hash_password(password),
            )
            db.add(user)
            db.flush()
        workspace = db.scalar(
            select(Workspace).where(Workspace.name == "RealityOS Workshop")
        )
        if workspace is None:
            workspace = Workspace(
                name="RealityOS Workshop",
                description="Synthetic workshop demo",
                created_by_id=user.id,
            )
            db.add(workspace)
            db.flush()
            db.add(
                WorkspaceMember(
                    workspace_id=workspace.id, user_id=user.id, role=Role.ADMIN
                )
            )
        zones: dict[str, Zone] = {}
        zone_specs = [
            ("Storage A", "zone", None),
            ("Shelf 1", "shelf", "Storage A"),
            ("Shelf 2", "shelf", "Storage A"),
            ("Shelf 3", "shelf", "Storage A"),
            ("Level 2", "level", "Shelf 3"),
            ("Workbench", "zone", None),
        ]
        for name, kind, parent_name in zone_specs:
            parent = zones.get(parent_name) if parent_name else None
            zone = db.scalar(
                select(Zone).where(
                    Zone.workspace_id == workspace.id,
                    Zone.name == name,
                    Zone.parent_id == (parent.id if parent else None),
                )
            )
            if zone is None and parent:
                zone = db.scalar(
                    select(Zone).where(
                        Zone.workspace_id == workspace.id,
                        Zone.name == name,
                        Zone.parent_id.is_(None),
                    )
                )
                if zone:
                    zone.parent_id = parent.id
            if zone is None:
                zone = Zone(
                    workspace_id=workspace.id,
                    parent_id=parent.id if parent else None,
                    name=name,
                    kind=kind,
                )
                db.add(zone)
                db.flush()
            zones[name] = zone
        demo_objects = [
            ("yellow drill", "Level 2", "#f0bf24"),
            ("hammer", "Workbench", "#b2b6bc"),
            ("adjustable wrench", "Shelf 1", "#8b9aa8"),
            ("screwdriver", "Shelf 2", "#d94343"),
            ("toolbox", "Storage A", "#2f495b"),
            ("battery charger", "Shelf 1", "#4c8d65"),
        ]
        assets: list[MediaAsset] = []
        for object_name, zone_name, color in demo_objects:
            raw = synthetic_drill() if object_name == "yellow drill" else synthetic_asset(
                object_name, zone_name, color
            )
            digest = hashlib.sha256(raw).hexdigest()
            asset = db.scalar(
                select(MediaAsset).where(
                    MediaAsset.workspace_id == workspace.id,
                    MediaAsset.sha256 == digest,
                )
            )
            if asset is None:
                session = CaptureSession(
                    workspace_id=workspace.id,
                    zone_id=zones[zone_name].id,
                    created_by_id=user.id,
                    status=CaptureStatus.CLOSED,
                    closed_at=datetime.now(UTC),
                    consent_confirmed=True,
                )
                db.add(session)
                db.flush()
                asset = MediaAsset(
                    workspace_id=workspace.id,
                    capture_session_id=session.id,
                    kind=MediaKind.IMAGE,
                    mime_type="image/png",
                    original_bytes=raw,
                    sha256=digest,
                    byte_size=len(raw),
                    width=960,
                    height=640,
                    captured_at=datetime.now(UTC),
                    extra_metadata={
                        "filename": f"{object_name.replace(' ', '_')}.png",
                        "synthetic": True,
                    },
                )
                db.add(asset)
                db.flush()
            assets.append(asset)
            job = create_processing_job(db, asset, provider="mock")
            process_job(db, job.id, MockMetaModelClient())
        db.commit()
        print(f"Seed ready: workspace={workspace.id} assets={len(assets)}")


if __name__ == "__main__":
    main()

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


def synthetic_drill() -> bytes:
    image = Image.new("RGB", (960, 640), "#27312f")
    draw = ImageDraw.Draw(image)
    draw.rectangle((90, 130, 870, 520), fill="#554941")
    draw.rectangle((240, 215, 680, 380), fill="#f0bf24")
    draw.rectangle((620, 265, 810, 325), fill="#314044")
    draw.rectangle((330, 355, 470, 485), fill="#202725")
    draw.text((110, 95), "Taller RealityOS · Bodega A", fill="#f1f0ea")
    result = io.BytesIO()
    image.save(result, format="PNG")
    return result.getvalue()


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
            select(Workspace).where(Workspace.name == "Taller RealityOS")
        )
        if workspace is None:
            workspace = Workspace(
                name="Taller RealityOS",
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
            ("Bodega A", "zone"),
            ("Estantería 1", "shelf"),
            ("Estantería 2", "shelf"),
            ("Estantería 3", "shelf"),
            ("Mesa de trabajo", "zone"),
        ]
        for name, kind in zone_specs:
            zone = db.scalar(
                select(Zone).where(Zone.workspace_id == workspace.id, Zone.name == name)
            )
            if zone is None:
                zone = Zone(workspace_id=workspace.id, name=name, kind=kind)
                db.add(zone)
                db.flush()
            zones[name] = zone
        raw = synthetic_drill()
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
                zone_id=zones["Estantería 3"].id,
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
                extra_metadata={"filename": "taladro_amarillo.png", "synthetic": True},
            )
            db.add(asset)
            db.flush()
        job = create_processing_job(db, asset, provider="mock")
        process_job(db, job.id, MockMetaModelClient())
        db.commit()
        print(f"Seed ready: workspace={workspace.id} media={asset.id} job={job.id}")


if __name__ == "__main__":
    main()

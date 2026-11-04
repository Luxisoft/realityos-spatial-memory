"""Provision the owner-authorized synthetic Meta directory in local evaluation only.

No OAuth, Graph requests, remote data, extra workspaces or publications. The
receipt preserves edits, removals and consent revocations across restarts.
"""

import hashlib
import io
import json
import secrets
import uuid
from datetime import UTC, date, datetime

from app.faces import BiometricConsent, build_face_engine, ingest_media_assets
from app.local_catalog import FIXTURES, local_id
from app.local_models import LocalEvaluationState
from app.local_runtime import validate_local_settings
from app.local_seed import add_media, fixture_file, read_json
from app.models import AuditEvent, Role, User, Workspace, WorkspaceMember
from app.security import hash_password
from app.social_features.models import (
    FacebookIdentity,
    FacebookMedia,
    FacebookProfile,
    UserProfile,
)
from PIL import Image
from sqlalchemy import text

RECEIPT = "meta-social-profiles-v1"
WORKSPACE = uuid.UUID("3ea760d8-8394-5ddd-b1d7-ad27bd996b17")
MANIFEST = "local/social-profiles/manifest.json"


def preflight_social(root=FIXTURES):
    manifest = read_json(root / MANIFEST)
    profiles = manifest["profiles"]
    if (
        manifest["revision"] != RECEIPT
        or manifest["workspace_id"] != str(WORKSPACE)
        or manifest.get("simulated") is not True
        or len(profiles) != 10
        or len({p["slug"] for p in profiles}) != 10
    ):
        raise ValueError("Unexpected local social manifest.")
    hashes = set()
    for profile in profiles:
        if len(profile["references"]) != 3:
            raise ValueError("Each social profile requires exactly three references.")
        for entry in [profile["avatar"], *profile["references"]]:
            raw = fixture_file(root, entry["path"]).read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if digest != entry["sha256"] or digest in hashes:
                raise ValueError(
                    "Social fixture integrity or distinct-photo check failed."
                )
            hashes.add(digest)
    return manifest


def seed_local_social(db, settings, root=FIXTURES, *, engine=None):
    validate_local_settings(settings)
    if not (
        settings.environment == "local"
        and settings.local_login_enabled
        and settings.local_evaluation_enabled
    ):
        raise ValueError("Social initialization is restricted to local evaluation.")
    if db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(7265616)"))
    previous = db.get(LocalEvaluationState, RECEIPT)
    if previous:
        return {"initialized": False, **previous.counts}
    if not db.get(LocalEvaluationState, "evaluation-v1"):
        raise ValueError("Initialize the three local scenarios first.")
    workspace = db.get(Workspace, WORKSPACE)
    if workspace is None:
        return {"initialized": False, "reason": "workspace-removed"}
    if workspace.name != "Meta Social Media":
        raise ValueError("Unexpected social workspace; initialization aborted.")
    manifest = preflight_social(root)
    engine = engine or build_face_engine(settings)
    counts = {"profiles": 0, "avatars": 0, "references": 0, "enrollments": 0}
    # The caller owns the transaction. Any invalid image rolls back the whole set.
    for entry in manifest["profiles"]:
        slug = entry["slug"]
        user_id = local_id("social-user", slug)
        if db.get(User, user_id) is not None:
            raise ValueError(
                "Existing social identity without receipt; refusing overwrite."
            )
        user = User(
            id=user_id,
            email=f"{slug}@local-meta.invalid",
            display_name=entry["name"],
            password_hash=hash_password(secrets.token_urlsafe(48)),
        )
        db.add(user)
        db.flush()
        db.add(
            WorkspaceMember(workspace_id=WORKSPACE, user_id=user_id, role=Role.QUERY)
        )
        db.add(FacebookIdentity(subject=f"local-meta:{slug}", user_id=user_id))
        # This is explicitly synthetic fixture consent, not a real person's action.
        db.add(
            BiometricConsent(
                user_id=user_id, notice_version=settings.biometric_notice_version
            )
        )
        db.add(
            AuditEvent(
                workspace_id=WORKSPACE,
                actor_id=None,
                entity_type="user",
                entity_id=user_id,
                event_type="local.social.fixture.created",
                payload={
                    "simulated": True,
                    "revision": RECEIPT,
                    "consent_basis": manifest["consent_basis"],
                    "oauth_performed": False,
                },
            )
        )
        provenance = {
            "simulated": True,
            "fixture_revision": RECEIPT,
            "owner_id": str(user_id),
        }
        avatar = add_media(
            db,
            WORKSPACE,
            fixture_file(root, entry["avatar"]["path"]),
            f"social:{slug}:avatar",
            {**provenance, "origin": "account-avatar"},
        )
        db.add(
            UserProfile(
                user_id=user_id,
                avatar_media_id=avatar.id,
                headline=entry["headline"]["en"],
                biography=entry["biography"]["en"],
                birthday=date.fromisoformat(entry["birthday"]),
                gender=entry["gender"],
                hometown=entry["location"],
                location=entry["location"],
                website=f"https://example.invalid/{slug}",
                display_text={
                    key: {**entry[key], "source": entry[key]["en"]}
                    for key in ("headline", "biography")
                },
            )
        )
        db.add(
            FacebookProfile(
                user_id=user_id,
                email=user.email,
                birthday=entry["birthday"],
                gender=entry["gender"],
                hometown=entry["location"],
                location=entry["location"],
                picture_url=f"/v1/profiles/{user_id}/avatar",
                photos_count=3,
                videos_count=0,
                friends_count=0,
                likes_count=0,
                granted_scopes=["public_profile", "email", "user_photos"],
                import_status="done",
                imported_photos=3,
                imported_videos=0,
                picture_imported=True,
                synced_at=datetime.now(UTC),
                sync_diagnostics={
                    "simulated": True,
                    "origin": "local-fixture",
                    "oauth_performed": False,
                    "revision": RECEIPT,
                },
            )
        )
        references = []
        for index, photo in enumerate(entry["references"], 1):
            asset = add_media(
                db,
                WORKSPACE,
                fixture_file(root, photo["path"]),
                f"social:{slug}:reference:{index}",
                {
                    **provenance,
                    "origin": "facebook-import",
                    "purpose": "biometric-reference",
                },
            )
            with Image.open(io.BytesIO(asset.original_bytes)) as image:
                asset.width, asset.height = image.size
            db.add(
                FacebookMedia(
                    fb_id=f"local-meta:{slug}:photo:{index}",
                    user_id=user_id,
                    kind="photo",
                    source_url="fixture://" + photo["path"],
                    imported_media_id=asset.id,
                    width=asset.width,
                    height=asset.height,
                )
            )
            references.append(asset)
        db.flush()
        enrolled = ingest_media_assets(db, user, references, "facebook-photo", engine)
        if len(enrolled) != 3 or any(
            face.quality < settings.face_min_quality
            or face.bounding_box.get("width", 0) * face.bounding_box.get("height", 0)
            < settings.face_min_box_area
            for face in enrolled
        ):
            raise ValueError(f"Three usable reference faces required for {slug}.")
        counts["profiles"] += 1
        counts["avatars"] += 1
        counts["references"] += len(references)
        counts["enrollments"] += len(enrolled)
    db.add(
        LocalEvaluationState(
            name=RECEIPT,
            manifest_hash=hashlib.sha256(
                json.dumps(manifest, sort_keys=True).encode()
            ).hexdigest(),
            counts=counts,
        )
    )
    db.flush()
    return {"initialized": True, **counts}

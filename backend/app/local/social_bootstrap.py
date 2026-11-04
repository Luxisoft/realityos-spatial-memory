"""Import the existing synthetic local directory, preserving its consent workflow."""

import uuid

from sqlalchemy import select

from app.local.sql_data import FIXTURES, apply_seed, seed_digest
from app.local.state import receipt, require_local
from app.local_models import LocalEvaluationState
from app.models import MediaAsset, User, Workspace
from app.social_features.models import FacebookMedia, FacebookProfile

RECEIPT = "meta-social-profiles-v1"
WORKSPACE = uuid.UUID("3ea760d8-8394-5ddd-b1d7-ad27bd996b17")


def seed_local_social(db, settings, root=FIXTURES, *, engine=None):
    require_local(db, settings)
    previous = db.get(LocalEvaluationState, RECEIPT)
    if previous:
        return {"initialized": False, **previous.counts}
    if db.get(LocalEvaluationState, "evaluation-v1") is None:
        raise ValueError("Initialize the three local scenarios first.")
    workspace = db.get(Workspace, WORKSPACE)
    if workspace is None:
        return {"initialized": False, "reason": "workspace-removed"}
    if workspace.name != "Meta Social Media":
        raise ValueError("Unexpected social workspace; initialization aborted.")
    from app.faces import build_face_engine, ingest_media_assets

    engine = engine or build_face_engine(settings)
    filename = "002-social-profiles.sql"
    # Data, private references and the existing enrollment workflow are one
    # transaction. Failure never leaves a partially installed local identity.
    with db.begin_nested():
        apply_seed(db, settings, filename, root)
        users = list(
            db.scalars(
                select(User)
                .join(FacebookProfile)
                .where(FacebookProfile.sync_diagnostics["revision"].as_string() == RECEIPT)
            )
        )
        if len(users) != 10:
            raise ValueError("The local directory requires exactly ten synthetic profiles.")
        hashes = set()
        enrolled_count = 0
        for user in users:
            references = list(
                db.scalars(
                    select(MediaAsset)
                    .join(FacebookMedia, FacebookMedia.imported_media_id == MediaAsset.id)
                    .where(
                        FacebookMedia.user_id == user.id,
                        MediaAsset.workspace_id == WORKSPACE,
                        MediaAsset.extra_metadata["fixture_revision"].as_string() == RECEIPT,
                        MediaAsset.extra_metadata["purpose"].as_string() == "biometric-reference",
                    )
                )
            )
            reference_hashes = {asset.sha256 for asset in references}
            if len(references) != 3 or len(reference_hashes) != 3 or reference_hashes & hashes:
                raise ValueError("Each local profile requires three distinct private references.")
            hashes.update(reference_hashes)
            enrolled = ingest_media_assets(db, user, references, "facebook-photo", engine)
            if len(enrolled) != 3 or any(
                face.quality < settings.face_min_quality
                or face.bounding_box.get("width", 0) * face.bounding_box.get("height", 0)
                < settings.face_min_box_area
                for face in enrolled
            ):
                raise ValueError("Three usable reference faces required for each local profile.")
            enrolled_count += len(enrolled)
        counts = {
            "profiles": 10,
            "avatars": 10,
            "references": len(hashes),
            "enrollments": enrolled_count,
        }
        receipt(db, RECEIPT, seed_digest(root, filename), counts)
    return {"initialized": True, **counts}

"""Install local synthetic profile revisions through the existing consent workflow."""

import uuid

from sqlalchemy import select

from app.local.sql_data import FIXTURES, apply_seed, seed_digest
from app.local.state import receipt, require_local
from app.local_models import LocalEvaluationState
from app.models import MediaAsset, User, Workspace
from app.social_features.models import FacebookMedia, FacebookProfile

RECEIPT = "meta-social-profiles-v1"
WORKSPACE = uuid.UUID("3ea760d8-8394-5ddd-b1d7-ad27bd996b17")
SOCIAL_REVISIONS = (
    (RECEIPT, "002-social-profiles.sql", 10),
    ("meta-social-profiles-v2", "006-social-profiles.sql", 3),
)
COUNT_FIELDS = ("profiles", "avatars", "references", "enrollments")


def _totals(states):
    return {
        field: sum(state.counts.get(field, 0) for state in states.values() if state)
        for field in COUNT_FIELDS
    }


def _install_revision(db, settings, root, name, filename, expected, engine, hashes):
    from app.faces import ingest_media_assets

    apply_seed(db, settings, filename, root)
    users = list(
        db.scalars(
            select(User)
            .join(FacebookProfile)
            .where(FacebookProfile.sync_diagnostics["revision"].as_string() == name)
        )
    )
    if len(users) != expected:
        raise ValueError("The local profile revision does not contain its expected profiles.")
    enrolled_count = 0
    for user in users:
        references = list(
            db.scalars(
                select(MediaAsset)
                .join(FacebookMedia, FacebookMedia.imported_media_id == MediaAsset.id)
                .where(
                    FacebookMedia.user_id == user.id,
                    MediaAsset.workspace_id == WORKSPACE,
                    MediaAsset.extra_metadata["fixture_revision"].as_string() == name,
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
        "profiles": len(users),
        "avatars": len(users),
        "references": len(users) * 3,
        "enrollments": enrolled_count,
    }
    receipt(db, name, seed_digest(root, filename), counts)
    return db.get(LocalEvaluationState, name)


def seed_local_social(db, settings, root=FIXTURES, *, engine=None):
    require_local(db, settings)
    states = {name: db.get(LocalEvaluationState, name) for name, _, _ in SOCIAL_REVISIONS}
    pending = [revision for revision in SOCIAL_REVISIONS if not states[revision[0]]]
    if not pending:
        return {"initialized": False, **_totals(states)}
    if db.get(LocalEvaluationState, "evaluation-v1") is None:
        raise ValueError("Initialize the local scenarios first.")
    workspace = db.get(Workspace, WORKSPACE)
    if workspace is None:
        return {"initialized": False, "reason": "workspace-removed"}
    if not states.get(RECEIPT) and workspace.name != "Meta Social Media":
        raise ValueError("Unexpected social workspace; initialization aborted.")
    from app.faces import build_face_engine

    engine = engine or build_face_engine(settings)
    hashes = set(
        db.scalars(
            select(MediaAsset.sha256).where(
                MediaAsset.workspace_id == WORKSPACE,
                MediaAsset.extra_metadata["purpose"].as_string() == "biometric-reference",
            )
        )
    )
    # All pending revisions and their enrollment results are atomic. Existing
    # receipts prevent replacement of edited profiles or revoked consent.
    with db.begin_nested():
        for name, filename, expected in pending:
            states[name] = _install_revision(
                db, settings, root, name, filename, expected, engine, hashes
            )
    return {"initialized": True, **_totals(states)}

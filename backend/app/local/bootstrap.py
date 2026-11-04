"""One transactional SQL initialization for local installations; no runtime catalog."""

from sqlalchemy import func, select, text

from app.local.retirement import retire_memory
from app.local.sql_data import FIXTURES, apply_seed, seed_digest, statements
from app.local.state import receipt, require_local
from app.local_models import LocalEvaluationState
from app.models import User, Workspace
from app.social_features.models import Publication
from app.workspaces.models import Record, RecordMedia

RECEIPT = "evaluation-v1"
ACCESS_RECEIPT = "local-access-v1"
DATA_UPDATES = (
    ("group-videos-v1", "004-group-videos.sql"),
    ("police-records-v2", "005-police-records.sql"),
    ("shared-publication-classification-v1", "008-shared-publication-classification.sql"),
    ("use-case-publication-classification-v1", "010-use-case-classification.sql"),
    ("legacy-publication-classification-repair-v1", "011-legacy-classification-repair.sql"),
)


def install_data_updates(db, settings, root=FIXTURES):
    """Apply explicit SQL revisions once, preserving later edits and deletions."""
    require_local(db, settings)
    installed = {}
    for name, filename in DATA_UPDATES:
        if db.get(LocalEvaluationState, name):
            continue
        with db.begin_nested():
            before = db.scalar(select(func.count()).select_from(Publication))
            apply_seed(db, settings, filename, root)
            counts = {
                "publications": db.scalar(select(func.count()).select_from(Publication)) - before
            }
            receipt(db, name, seed_digest(root, filename), counts)
            installed[name] = counts
    return installed


def install_local_access(db, settings, root=FIXTURES):
    require_local(db, settings)
    if db.get(LocalEvaluationState, ACCESS_RECEIPT):
        return
    filename = "003-local-access.sql"
    for sql in statements(root / "database" / filename):
        db.execute(text(sql))
    receipt(db, ACCESS_RECEIPT, seed_digest(root, filename), {})


def seed_evaluation(db, settings, root=FIXTURES):
    require_local(db, settings)
    previous = db.get(LocalEvaluationState, RECEIPT)
    if previous:
        from app.local.upgrades import upgrade_local_data

        retired = retire_memory(db, settings, root)
        upgrade_local_data(db, settings, root)
        install_local_access(db, settings, root)
        updates = install_data_updates(db, settings, root)
        if retired is not None:
            previous.counts = {**previous.counts, **evaluation_counts(db)}
        return {"initialized": False, **previous.counts, "updates": updates}
    if db.scalar(select(User.id).limit(1)) is not None:
        raise ValueError(
            "Use an empty isolated local database; existing accounts were not changed."
        )
    filename = "001-scenarios.sql"
    apply_seed(db, settings, filename, root)
    updates = install_data_updates(db, settings, root)
    counts = evaluation_counts(db)
    digest = seed_digest(root, filename)
    receipt(db, RECEIPT, digest, counts)
    receipt(db, "bilingual-copy-v1", digest, {})
    receipt(db, "police-people-v1", digest, {"records": 10, "attachments": 10})
    receipt(db, "local-group-publications-v1", digest, {"publications": 13})
    receipt(db, "replace-hospital-meta-social-v1", digest, {})
    retire_memory(db, settings, root)
    install_local_access(db, settings, root)
    return {"initialized": True, **counts, "updates": updates}


def evaluation_counts(db):
    return {
        name: db.scalar(select(func.count()).select_from(model))
        for name, model in (
            ("groups", Workspace),
            ("users", User),
            ("records", Record),
            ("attachments", RecordMedia),
            ("publications", Publication),
        )
    }


def enqueue_initial_media(db):
    """Resume task dispatch using durable receipts; ordinary jobs remain idempotent."""
    from app.tasks import index_gallery_media

    previous = db.get(LocalEvaluationState, RECEIPT)
    if previous is None:
        raise ValueError("Initialize the local dataset before indexing.")
    dispatched = set(previous.counts.get("dispatched", []))
    for post in db.scalars(select(Publication).where(Publication.source == "local-evaluation")):
        if str(post.id) in dispatched:
            continue
        if post.indexed_at is None:
            index_gallery_media.delay(str(post.id))
        dispatched.add(str(post.id))
        previous.counts = {**previous.counts, "dispatched": sorted(dispatched)}
        db.commit()
    return {"dispatched": len(dispatched)}

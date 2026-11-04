"""One group publication model; retire the former personal/public destinations.

The owner explicitly requested deletion of unassigned publications. Downgrade
restores the previous schema only; deleted data requires the release snapshot.
"""

import hashlib
import json
import uuid

import sqlalchemy as sa

from alembic import op

revision = "20261103_0038"
down_revision = "20261103_0037"
branch_labels = None
depends_on = None


def clean_legacy(bind):
    metadata = sa.MetaData()
    metadata.reflect(bind=bind)
    posts = metadata.tables["publications"]
    spaces = metadata.tables["workspaces"]
    rows = list(bind.execute(sa.select(posts)).mappings())
    private_spaces = set(bind.scalars(sa.select(spaces.c.id).where(spaces.c.name.like("home:%"))))
    removed = {
        row["id"]
        for row in rows
        if row["audience"] != "work"
        or row["workspace_id"] is None
        or row["workspace_id"] in private_spaces
    }
    media_ids = {row["media_id"] for row in rows if row["id"] in removed}
    # Preserve group copies, their IDs and their independent interactions.
    families = {}
    for row in rows:
        if row["id"] not in removed and row["shared_from_id"] in removed:
            families.setdefault(row["shared_from_id"], []).append(row)
    for family in families.values():
        family.sort(key=lambda row: (row["published_at"], str(row["id"])))
        bind.execute(
            posts.update()
            .where(posts.c.id.in_([row["id"] for row in family]))
            .values(shared_from_id=None)
        )
        for row in family[1:]:
            bind.execute(
                posts.update().where(posts.c.id == row["id"]).values(shared_from_id=family[0]["id"])
            )
    if removed:
        bind.execute(
            posts.update()
            .where(posts.c.id.in_(removed))
            .values(active_index_run_id=None, shared_from_id=None)
        )
        uploads = metadata.tables["publication_uploads"]
        for column in ("result_id", "duplicate_id"):
            bind.execute(
                uploads.update().where(uploads.c[column].in_(removed)).values({column: None})
            )
        records = metadata.tables["workspace_record_media"]
        bind.execute(
            records.update()
            .where(records.c.publication_id.in_(removed))
            .values(publication_id=None)
        )
        aliases = metadata.tables["publication_duplicates"]
        bind.execute(
            aliases.delete().where(
                sa.or_(aliases.c.post_id.in_(removed), aliases.c.canonical_id.in_(removed))
            )
        )
        # Evidence references index runs, so remove it first.
        for name in (
            "publication_tags",
            "publication_likes",
            "publication_comments",
            "publication_reports",
            "publication_revisions",
            "publication_translations",
            "gallery_evidence",
            "gallery_index_runs",
        ):
            table = metadata.tables[name]
            bind.execute(table.delete().where(table.c.post_id.in_(removed)))
        bind.execute(posts.delete().where(posts.c.id.in_(removed)))
    for name in ("publication_uploads", "storage_imports", "storage_syncs"):
        table = metadata.tables[name]
        invalid = sa.or_(
            table.c.audience != "work",
            table.c.workspace_id.is_(None),
            table.c.workspace_id.in_(private_spaces),
        )
        if name == "storage_syncs":
            bind.execute(table.update().where(invalid).values(enabled=False))
        else:
            values = {"status": "cancelled"}
            if name == "publication_uploads":
                values["error"] = (
                    "The former publication destination was removed. Choose a work group for a new upload."
                )
            bind.execute(table.update().where(invalid).values(**values))
    imports = metadata.tables["storage_imports"]
    for row in bind.execute(sa.select(imports)).mappings():
        payload = {
            "request_key": row["request_key"],
            "keys": [item["key"] for item in row["items"]],
        }
        classifications = {
            item["key"]: item["classification"]
            for item in row["items"]
            if item.get("classification")
        }
        if classifications:
            payload["classifications"] = classifications
        payload["workspace_id"] = (
            str(uuid.UUID(str(row["workspace_id"]))) if row["workspace_id"] else None
        )
        digest = hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        ).hexdigest()
        bind.execute(imports.update().where(imports.c.id == row["id"]).values(payload_hash=digest))
    assets = metadata.tables["media_assets"]
    # Only garbage-collect media from the deleted publications, plus their
    # descendants. Any FK, private purpose or biometric use protects the bytes.
    candidates = set(media_ids)
    while candidates:
        children = set(
            bind.scalars(sa.select(assets.c.id).where(assets.c.parent_asset_id.in_(candidates)))
        )
        if children.issubset(candidates):
            break
        candidates |= children
    references = [
        (table, foreign.parent)
        for table in metadata.tables.values()
        for foreign in table.foreign_keys
        if foreign.column.table.name == "media_assets" and table.name != "media_asset_chunks"
    ]
    deleted_media = 0
    while candidates:
        progress = False
        for key in list(candidates):
            row = bind.execute(sa.select(assets).where(assets.c.id == key)).mappings().first()
            if row is None:
                candidates.remove(key)
                continue
            extra = row["metadata"] or {}
            if (
                extra.get("origin") == "facebook-import"
                or extra.get("purpose") == "biometric-reference"
                or extra.get("face_profile")
            ):
                candidates.remove(key)
                continue
            if any(
                bind.scalar(sa.select(sa.func.count()).select_from(table).where(column == key))
                for table, column in references
            ):
                continue
            chunks = metadata.tables.get("media_asset_chunks")
            if chunks is not None:
                bind.execute(chunks.delete().where(chunks.c.asset_id == key))
            bind.execute(assets.delete().where(assets.c.id == key))
            candidates.remove(key)
            deleted_media += 1
            progress = True
        if not progress:
            break
    return {
        "publications_removed": len(removed),
        "media_removed": deleted_media,
        "group_copies_preserved": sum(map(len, families.values())),
    }


def upgrade():
    bind = op.get_bind()
    clean_legacy(bind)
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("publications")}
    for name in ("ix_publications_audience", "ix_publication_feed"):
        if name in indexes:
            op.drop_index(name, table_name="publications")
    for name in ("publications", "publication_uploads", "storage_imports", "storage_syncs"):
        with op.batch_alter_table(name) as batch:
            batch.drop_column("audience")
            if name == "publications":
                batch.alter_column("workspace_id", existing_type=sa.Uuid(), nullable=False)
    op.create_index("ix_publication_feed", "publications", ["workspace_id", "published_at", "id"])


def downgrade():
    op.drop_index("ix_publication_feed", table_name="publications")
    for name in ("publications", "publication_uploads", "storage_imports", "storage_syncs"):
        with op.batch_alter_table(name) as batch:
            batch.add_column(
                sa.Column("audience", sa.String(16), nullable=False, server_default="work")
            )
            if name == "publications":
                batch.alter_column("workspace_id", existing_type=sa.Uuid(), nullable=True)
    op.create_index("ix_publication_feed", "publications", ["audience", "published_at", "id"])
    op.create_index("ix_publications_audience", "publications", ["audience"])

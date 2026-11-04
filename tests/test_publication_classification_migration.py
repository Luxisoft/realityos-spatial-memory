import importlib.util
import uuid
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_classification_migration_preserves_posts_and_requires_pending_review(tmp_path):
    path = (
        Path(__file__).resolve().parents[1]
        / "backend/alembic/versions/20261103_0037_publication_classification.py"
    )
    spec = importlib.util.spec_from_file_location("classification_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'classification.db'}")
    metadata = sa.MetaData()
    sa.Table("workspaces", metadata, sa.Column("id", sa.Uuid(), primary_key=True))
    posts = sa.Table(
        "publications",
        metadata,
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("caption", sa.Text()),
    )
    uploads = sa.Table(
        "publication_uploads",
        metadata,
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("status", sa.String(24)),
        sa.Column("original_bytes", sa.LargeBinary()),
    )
    metadata.create_all(engine)
    states = ("pending", "failed", "duplicate", "published", "cancelled")
    keys = {status: uuid.uuid4() for status in states}
    post_id = uuid.uuid4()
    with engine.begin() as db:
        db.execute(posts.insert().values(id=post_id, caption="Existing caption"))
        db.execute(
            uploads.insert(),
            [
                {
                    "id": keys[status],
                    "status": status,
                    "original_bytes": b"retain original",
                }
                for status in states
            ],
        )
        with Operations.context(MigrationContext.configure(db)):
            module.upgrade()
        assert (
            db.scalar(sa.select(posts.c.caption).where(posts.c.id == post_id))
            == "Existing caption"
        )
        for status, key in keys.items():
            expected = (
                "awaiting_classification"
                if status in {"pending", "failed", "duplicate"}
                else status
            )
            assert (
                db.scalar(sa.select(uploads.c.status).where(uploads.c.id == key))
                == expected
            )
        assert set(db.scalars(sa.select(uploads.c.original_bytes))) == {
            b"retain original"
        }
        assert "category_id" in {
            field["name"] for field in sa.inspect(db).get_columns("publications")
        }
        assert db.scalar(sa.text("SELECT COUNT(*) FROM publication_terms")) == 0
        assert db.scalar(sa.text("SELECT COUNT(*) FROM publication_tags")) == 0
        assert db.scalar(
            sa.text("SELECT COUNT(*) FROM publication_uploads WHERE tag_ids = '[]'")
        ) == len(states)
        with Operations.context(MigrationContext.configure(db)):
            module.downgrade()
        assert "publication_terms" not in sa.inspect(db).get_table_names()
        assert db.scalar(sa.select(posts.c.caption)) == "Existing caption"
        assert (
            db.scalar(
                sa.select(uploads.c.status).where(uploads.c.id == keys["pending"])
            )
            == "awaiting_classification"
        )

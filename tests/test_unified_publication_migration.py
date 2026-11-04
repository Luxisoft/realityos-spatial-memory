"""Real SQL migration preserves group copies and private account media."""

import hashlib
import importlib.util
import uuid
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from app.db import Base
from app.models import MediaKind
from app.storage.schemas import ImportInput


def migration():
    path = (
        Path(__file__).resolve().parents[1]
        / "backend/alembic/versions/20261103_0038_unified_group_publications.py"
    )
    spec = importlib.util.spec_from_file_location(
        "unified_publications_migration", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cleanup_and_schema_upgrade_preserve_group_copies_and_private_bytes(tmp_path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'migration.db'}")
    metadata = sa.MetaData()
    for table in Base.metadata.tables.values():
        table.to_metadata(metadata)
    posts = metadata.tables["publications"]
    posts.c.workspace_id.nullable = True
    for name in (
        "publications",
        "publication_uploads",
        "storage_imports",
        "storage_syncs",
    ):
        metadata.tables[name].append_column(
            sa.Column("audience", sa.String(16), nullable=False, default="work")
        )
    metadata.create_all(engine)
    owner, group, other_group, private = (uuid.uuid4() for _ in range(4))
    shared_media, unused_media, private_media = (uuid.uuid4() for _ in range(3))
    original, copy, second_copy, obsolete, biometric_projection = (
        uuid.uuid4() for _ in range(5)
    )
    with engine.begin() as db:
        db.execute(
            metadata.tables["users"]
            .insert()
            .values(
                id=owner,
                email="migration@example.test",
                display_name="Owner",
                password_hash="unused",
            )
        )
        for key, name in (
            (group, "Care team"),
            (other_group, "Follow-up team"),
            (private, f"home:{owner}"),
        ):
            db.execute(
                metadata.tables["workspaces"]
                .insert()
                .values(id=key, name=name, created_by_id=owner)
            )
        for key, extra in (
            (shared_media, {}),
            (unused_media, {}),
            (private_media, {"purpose": "biometric-reference"}),
        ):
            db.execute(
                metadata.tables["media_assets"]
                .insert()
                .values(
                    id=key,
                    workspace_id=private,
                    kind=MediaKind.IMAGE,
                    mime_type="image/png",
                    original_bytes=b"private original",
                    sha256=str(key).replace("-", "") * 2,
                    byte_size=16,
                    metadata=extra,
                )
            )
        for key, media, space, audience, root in (
            (original, shared_media, None, "home", None),
            (copy, shared_media, group, "work", original),
            (second_copy, shared_media, other_group, "work", original),
            (obsolete, unused_media, private, "public", None),
            (biometric_projection, private_media, None, "home", None),
        ):
            db.execute(
                posts.insert().values(
                    id=key,
                    owner_id=owner,
                    media_id=media,
                    workspace_id=space,
                    audience=audience,
                    shared_from_id=root,
                )
            )
        db.execute(
            metadata.tables["publication_comments"]
            .insert()
            .values(
                id=uuid.uuid4(),
                post_id=copy,
                user_id=owner,
                text="Keep this group discussion",
            )
        )
        db.execute(
            metadata.tables["publication_comments"]
            .insert()
            .values(id=uuid.uuid4(), post_id=obsolete, user_id=owner, text="Obsolete")
        )
        connection = uuid.uuid4()
        db.execute(
            metadata.tables["storage_connections"]
            .insert()
            .values(
                id=connection,
                owner_id=owner,
                name="Private source",
                provider="s3",
                endpoint="https://storage.example.test",
                bucket="media",
                secret="encrypted",
                workspace_id=group,
            )
        )
        imports = metadata.tables["storage_imports"]
        expected_hashes = {}
        for classified in (False, True):
            key = uuid.uuid4()
            classifications = (
                {
                    "photo.png": {
                        "category_id": str(uuid.uuid4()),
                        "tag_ids": [str(uuid.uuid4())],
                    }
                }
                if classified
                else {}
            )
            payload = ImportInput(
                request_key=str(key),
                keys=["photo.png"],
                workspace_id=group,
                classifications=classifications,
            )
            expected_hashes[key] = hashlib.sha256(
                payload.model_dump_json(
                    exclude=set() if classified else {"classifications"}
                ).encode()
            ).hexdigest()
            db.execute(
                imports.insert().values(
                    id=key,
                    connection_id=connection,
                    request_key=str(key),
                    payload_hash="old-audience-hash",
                    workspace_id=group,
                    audience="work",
                    status="completed",
                    items=[
                        {
                            "key": "photo.png",
                            **(
                                {"classification": classifications["photo.png"]}
                                if classified
                                else {}
                            ),
                        }
                    ],
                )
            )
        result = migration().clean_legacy(db)
        assert (
            dict(db.execute(sa.select(imports.c.id, imports.c.payload_hash)).all())
            == expected_hashes
        )
        assert result == {
            "publications_removed": 3,
            "media_removed": 1,
            "group_copies_preserved": 2,
        }
        assert set(db.scalars(sa.select(posts.c.id))) == {copy, second_copy}
        surviving = list(db.execute(sa.select(posts)).mappings())
        root = next(row["id"] for row in surviving if row["shared_from_id"] is None)
        assert (
            next(row for row in surviving if row["id"] != root)["shared_from_id"]
            == root
        )
        assert set(db.scalars(sa.select(metadata.tables["media_assets"].c.id))) == {
            shared_media,
            private_media,
        }
        assert list(
            db.scalars(sa.select(metadata.tables["publication_comments"].c.text))
        ) == ["Keep this group discussion"]
        assert migration().clean_legacy(db)["publications_removed"] == 0
        with Operations.context(MigrationContext.configure(db)):
            migration().upgrade()
        fields = {
            field["name"]: field for field in sa.inspect(db).get_columns("publications")
        }
        assert "audience" not in fields
        assert not fields["workspace_id"]["nullable"]
        for name in ("publication_uploads", "storage_imports", "storage_syncs"):
            assert "audience" not in {
                field["name"] for field in sa.inspect(db).get_columns(name)
            }
        with Operations.context(MigrationContext.configure(db)):
            migration().downgrade()
        assert db.scalar(sa.text("SELECT COUNT(*) FROM publications")) == 2

"""Workspace copies, source revisions and private account enrollment."""

import sqlalchemy as sa

from alembic import op

revision = "20261103_0036"
down_revision = "20261103_0035"
branch_labels = None
depends_on = None


def add(table, column):
    if column.name not in {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}:
        if op.get_bind().dialect.name == "sqlite":
            with op.batch_alter_table(table) as batch:
                batch.add_column(column)
        else:
            op.add_column(table, column)


def upgrade():
    add(
        "publications",
        sa.Column(
            "shared_from_id",
            sa.Uuid(),
            sa.ForeignKey("publications.id", name="fk_publications_shared_from"),
        ),
    )
    indexes = {item["name"] for item in sa.inspect(op.get_bind()).get_indexes("publications")}
    if "ix_publications_shared_from_id" not in indexes:
        op.create_index("ix_publications_shared_from_id", "publications", ["shared_from_id"])
    names = {
        item["name"] for item in sa.inspect(op.get_bind()).get_unique_constraints("publications")
    }
    if "uq_publication_group_copy" not in names:
        with op.batch_alter_table("publications") as batch:
            batch.create_unique_constraint(
                "uq_publication_group_copy", ["shared_from_id", "workspace_id"]
            )
    add(
        "storage_connections",
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
    )
    add(
        "storage_connections",
        sa.Column(
            "workspace_id",
            sa.Uuid(),
            sa.ForeignKey("workspaces.id", name="fk_storage_connection_workspace"),
        ),
    )
    add("storage_imports", sa.Column("revision", sa.Integer(), nullable=False, server_default="1"))
    add("storage_syncs", sa.Column("seen_keys", sa.JSON(), nullable=False, server_default="[]"))
    from app.face_setup import BiometricSetup
    from app.social_features.evidence_models import PublicationUpload  # noqa: F401
    from app.storage.provenance_models import StorageObject

    StorageObject.__table__.create(op.get_bind(), checkfirst=True)
    BiometricSetup.__table__.create(op.get_bind(), checkfirst=True)
    # Record visibility before quarantine so downgrade is data-aware.
    journal = sa.Table(
        "biometric_publication_quarantine",
        sa.MetaData(),
        sa.Column("post_id", sa.Uuid(), primary_key=True),
        sa.Column("previous_hidden", sa.Boolean()),
    )
    journal.create(op.get_bind(), checkfirst=True)
    from app.models import MediaAsset
    from app.social_features.models import Publication
    from app.social_features.publication_visibility import private_media_predicate

    posts = Publication.__table__
    targets = sa.select(posts.c.id, posts.c.hidden).where(
        sa.or_(
            posts.c.source.in_(["facebook", "simulator"]),
            posts.c.media_id.in_(sa.select(MediaAsset.id).where(private_media_predicate())),
        )
    )
    for post_id, hidden in op.get_bind().execute(targets):
        op.get_bind().execute(journal.insert().values(post_id=post_id, previous_hidden=hidden))
        op.get_bind().execute(posts.update().where(posts.c.id == post_id).values(hidden=True))


def downgrade():
    bind = op.get_bind()
    journal = sa.Table("biometric_publication_quarantine", sa.MetaData(), autoload_with=bind)
    posts = sa.table("publications", sa.column("id", sa.Uuid()), sa.column("hidden", sa.Boolean()))
    for post_id, hidden in bind.execute(sa.select(journal)):
        bind.execute(posts.update().where(posts.c.id == post_id).values(hidden=hidden))
    journal.drop(bind)
    op.drop_table("biometric_setups")
    op.drop_table("storage_objects")
    indexes = {item["name"] for item in sa.inspect(bind).get_indexes("publications")}
    if "ix_publications_shared_from_id" in indexes:
        op.drop_index("ix_publications_shared_from_id", "publications")
    with op.batch_alter_table("publications") as batch:
        batch.drop_constraint("uq_publication_group_copy", type_="unique")
        batch.drop_column("shared_from_id")
    for table, column in [
        ("storage_syncs", "seen_keys"),
        ("storage_imports", "revision"),
        ("storage_connections", "workspace_id"),
        ("storage_connections", "revision"),
    ]:
        with op.batch_alter_table(table) as batch:
            batch.drop_column(column)

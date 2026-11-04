"""Group catalogs, manual classification and pending import review."""

import sqlalchemy as sa

from alembic import op

revision = "20261103_0037"
down_revision = "20261103_0036"
branch_labels = None
depends_on = None


def upgrade():
    from app.social_features.models import PublicationTag, PublicationTerm

    PublicationTerm.__table__.create(op.get_bind(), checkfirst=True)
    for table in ("publications", "publication_uploads"):
        columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}
        if "category_id" not in columns:
            with op.batch_alter_table(table) as batch:
                batch.add_column(
                    sa.Column(
                        "category_id",
                        sa.Uuid(),
                        sa.ForeignKey(
                            "publication_terms.id", name=f"fk_{table}_category", ondelete="SET NULL"
                        ),
                    )
                )
        if table == "publication_uploads" and "tag_ids" not in columns:
            op.add_column(
                table, sa.Column("tag_ids", sa.JSON(), nullable=False, server_default="[]")
            )
    indexes = {i["name"] for i in sa.inspect(op.get_bind()).get_indexes("publications")}
    if "ix_publications_category_id" not in indexes:
        op.create_index("ix_publications_category_id", "publications", ["category_id"])
    PublicationTag.__table__.create(op.get_bind(), checkfirst=True)
    # In-flight, unclassified candidates must not publish when the new worker starts.
    op.execute(
        "UPDATE publication_uploads SET status='awaiting_classification' "
        "WHERE category_id IS NULL AND status IN ('pending','failed','duplicate')"
    )


def downgrade():
    # Explicit review candidates remain pending for review; never silently publish on rollback.
    op.drop_table("publication_tags")
    op.drop_index("ix_publications_category_id", "publications")
    for table in ("publications", "publication_uploads"):
        with op.batch_alter_table(table) as batch:
            if table == "publication_uploads":
                batch.drop_column("tag_ids")
            batch.drop_column("category_id")
    op.drop_table("publication_terms")

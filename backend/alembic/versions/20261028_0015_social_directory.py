"""Chronological social directory media and Facebook sync diagnostics."""

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision = "20261028_0015"
down_revision = "20261028_0014"
branch_labels = None
depends_on = None


def _columns(bind, table: str) -> set[str]:
    return {column["name"] for column in inspect(bind).get_columns(table)}


def upgrade():
    bind = op.get_bind()
    publication_columns = _columns(bind, "publications")
    if "search_text" not in publication_columns:
        op.add_column(
            "publications",
            sa.Column("search_text", sa.Text(), nullable=False, server_default=""),
        )
    if "source" not in publication_columns:
        op.add_column(
            "publications",
            sa.Column("source", sa.String(length=32), nullable=False, server_default="local"),
        )
    if "source_ref" not in publication_columns:
        op.add_column("publications", sa.Column("source_ref", sa.String(length=160)))
    if "published_at" not in publication_columns:
        op.add_column(
            "publications",
            sa.Column(
                "published_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        op.execute("UPDATE publications SET published_at = created_at")
    indexes = {index["name"] for index in inspect(bind).get_indexes("publications")}
    if "ix_publication_feed" not in indexes:
        op.create_index(
            "ix_publication_feed", "publications", ["audience", "published_at", "id"]
        )
    constraints = {
        constraint["name"]
        for constraint in inspect(bind).get_unique_constraints("publications")
    }
    if "uq_publication_source" not in constraints:
        op.create_unique_constraint(
            "uq_publication_source", "publications", ["owner_id", "source", "source_ref"]
        )

    profile_columns = _columns(bind, "facebook_profiles")
    if "sync_diagnostics" not in profile_columns:
        op.add_column(
            "facebook_profiles",
            sa.Column("sync_diagnostics", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        )
    user_profile_columns = _columns(bind, "user_profiles")
    if "avatar_media_id" not in user_profile_columns:
        op.add_column("user_profiles", sa.Column("avatar_media_id", sa.Uuid()))
        op.create_foreign_key(
            "fk_user_profiles_avatar_media_id",
            "user_profiles",
            "media_assets",
            ["avatar_media_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade():
    bind = op.get_bind()
    if "avatar_media_id" in _columns(bind, "user_profiles"):
        op.drop_constraint("fk_user_profiles_avatar_media_id", "user_profiles", type_="foreignkey")
        op.drop_column("user_profiles", "avatar_media_id")
    if "sync_diagnostics" in _columns(bind, "facebook_profiles"):
        op.drop_column("facebook_profiles", "sync_diagnostics")
    indexes = {index["name"] for index in inspect(bind).get_indexes("publications")}
    if "ix_publication_feed" in indexes:
        op.drop_index("ix_publication_feed", table_name="publications")
    constraints = {
        constraint["name"]
        for constraint in inspect(bind).get_unique_constraints("publications")
    }
    if "uq_publication_source" in constraints:
        op.drop_constraint("uq_publication_source", "publications", type_="unique")
    for column in ("published_at", "source_ref", "source", "search_text"):
        if column in _columns(bind, "publications"):
            op.drop_column("publications", column)

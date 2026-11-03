"""Password accounts and workspace import records; no biometric schema changes."""

import sqlalchemy as sa

from alembic import op

revision = "20261102_0031"
down_revision = "20261101_0030"
branch_labels = None
depends_on = None


def upgrade():
    # Freeze this revision's table definitions rather than importing mutable ORM.
    op.create_table(
        "password_accounts",
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("provisioned_by", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_before", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "account_challenges",
        sa.Column("digest", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("purpose", sa.String(16), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "account_attempts",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("window", sa.Integer(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
    )
    op.create_table(
        "workspace_connections",
        *identity(),
        sa.Column(
            "workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id"), nullable=False, index=True
        ),
        sa.Column("created_by_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("token_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("source_url", sa.String(2048)),
        sa.Column("secret_encrypted", sa.Text()),
    )
    op.create_table(
        "workspace_import_runs",
        *identity(),
        sa.Column(
            "connection_id",
            sa.Uuid(),
            sa.ForeignKey("workspace_connections.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("request_key", sa.String(128), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.UniqueConstraint("connection_id", "request_key"),
    )
    op.create_table(
        "workspace_records",
        *identity(),
        sa.Column(
            "workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id"), nullable=False, index=True
        ),
        sa.Column(
            "connection_id",
            sa.Uuid(),
            sa.ForeignKey("workspace_connections.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("external_id", sa.String(160), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False, index=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("related_ids", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("simulated", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("connection_id", "external_id"),
    )
    op.create_table(
        "workspace_record_revisions",
        *identity(),
        sa.Column(
            "record_id",
            sa.Uuid(),
            sa.ForeignKey("workspace_records.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.UniqueConstraint("record_id", "version"),
    )
    op.create_table(
        "workspace_record_notes",
        *identity(),
        sa.Column(
            "record_id",
            sa.Uuid(),
            sa.ForeignKey("workspace_records.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "workspace_record_media",
        *identity(),
        sa.Column(
            "record_id",
            sa.Uuid(),
            sa.ForeignKey("workspace_records.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("external_id", sa.String(160), nullable=False),
        sa.Column("media_id", sa.Uuid(), sa.ForeignKey("media_assets.id"), nullable=False),
        sa.Column("publication_id", sa.Uuid(), sa.ForeignKey("publications.id")),
        sa.UniqueConstraint("record_id", "external_id"),
    )


def identity():
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def downgrade():
    for table in (
        "workspace_record_media",
        "workspace_record_notes",
        "workspace_record_revisions",
        "workspace_records",
        "workspace_import_runs",
        "workspace_connections",
        "account_attempts",
        "account_challenges",
        "password_accounts",
    ):
        op.drop_table(table)

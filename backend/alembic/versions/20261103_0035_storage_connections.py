"""Private bucket connections, resumable imports and synchronization rules."""

from alembic import op
from app.storage.models import StorageConnection, StorageImport, StorageSync

revision = "20261103_0035"
down_revision = "20261103_0034"
branch_labels = None
depends_on = None


def upgrade():
    for model in (StorageConnection, StorageImport, StorageSync):
        model.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    for model in (StorageSync, StorageImport, StorageConnection):
        model.__table__.drop(op.get_bind(), checkfirst=True)

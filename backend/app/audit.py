"""Append audit events to the caller-owned database transaction."""

import uuid

from sqlalchemy.orm import Session

from app.models import AuditEvent


def _audit(
    db: Session,
    event_type: str,
    entity_type: str,
    actor_id: uuid.UUID | None,
    entity_id: uuid.UUID | None = None,
    workspace_id: uuid.UUID | None = None,
    device_id: uuid.UUID | None = None,
) -> None:
    db.add(
        AuditEvent(
            workspace_id=workspace_id,
            actor_id=actor_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            device_id=device_id,
        )
    )

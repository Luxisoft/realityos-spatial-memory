from app.models import (
    Device,
    DeviceStatus,
    FactProvenance,
    ObjectActivityEvent,
    ObjectFact,
)
from sqlalchemy.dialects import postgresql


def _postgres_value(column, value):
    processor = column.type.bind_processor(postgresql.dialect())
    assert processor is not None
    return processor(value)


def test_lowercase_postgres_enums_persist_their_wire_values():
    """Guard manually-created PostgreSQL enum labels from name/value drift."""

    assert _postgres_value(Device.__table__.c.status, DeviceStatus.ACTIVE) == "active"
    assert (
        _postgres_value(ObjectFact.__table__.c.provenance, FactProvenance.VISIBLE_TEXT)
        == "visible_text"
    )
    assert _postgres_value(ObjectActivityEvent.__table__.c.provenance, FactProvenance.TEMPORAL) == "temporal"

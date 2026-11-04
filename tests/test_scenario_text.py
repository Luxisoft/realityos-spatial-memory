"""Prepared descriptions are natural; internal simulation and immutable history remain."""

from app.models import Workspace
from app.social_features.models import Publication, UserProfile
from app.workspaces.models import Record, RecordRevision
from sqlalchemy import select


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def test_prepared_display_avoids_retired_demo_labels(evaluation):
    with evaluation.app.state.database.session_factory() as db:
        values = []
        for model, fields in (
            (Workspace, ("name", "description")),
            (Publication, ("caption", "note_text")),
            (Record, ("title",)),
            (UserProfile, ("headline", "biography")),
        ):
            for row in db.scalars(select(model)):
                values.extend(getattr(row, field) for field in fields)
                values.extend(
                    pair[language]
                    for pair in row.display_text.values()
                    for language in ("en", "es")
                )
        assert not any(
            marker in value.casefold()
            for value in strings(values)
            for marker in (
                "[demo]",
                "[simulado]",
                "fictional scenario",
                "synthetic acceptance",
            )
        )
        assert all(record.simulated for record in db.scalars(select(Record)))
        for revision, record in db.execute(
            select(RecordRevision, Record).join(
                Record, Record.id == RecordRevision.record_id
            )
        ):
            assert revision.snapshot["simulated"] is True
            if record.external_id in {
                f"security-person-{number}" for number in range(11, 17)
            }:
                copy = revision.snapshot["display_text"]
                assert copy["title"]["source"] == revision.snapshot["title"]
                for field, pair in copy.items():
                    assert pair["source"] == revision.snapshot[field]
                    assert pair["en"] and pair["es"]
            else:
                assert revision.snapshot["display_text"] == {}

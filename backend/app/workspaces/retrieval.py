"""Bounded retrieval over matching records, local notes and same-source relationships."""

import json
import re

from sqlalchemy import Text, and_, case, cast, or_, select

from app.workspaces.models import Record, RecordNote

STOP_WORDS = set(
    "the and with for where what when was were this that de del los las una uno unos unas que con por para donde cuando como cual cuales visto ultima ultimo".split()
)


def pattern(term):
    return "%" + term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def retrieve(db, workspace_id, question, record_id=None):
    terms = list(
        dict.fromkeys(
            t for t in re.findall(r"\w+", question.casefold()) if len(t) > 2 and t not in STOP_WORDS
        )
    )[:24]
    visible = select(Record).where(Record.workspace_id == workspace_id, Record.status == "active")
    if record_id:
        anchors = list(db.scalars(visible.where(Record.id == record_id)))
    elif terms:
        conditions = []
        for term in terms:
            value = pattern(term)
            note_match = (
                select(RecordNote.id)
                .where(RecordNote.record_id == Record.id, RecordNote.text.ilike(value, escape="\\"))
                .exists()
            )
            conditions.append(
                or_(
                    Record.title.ilike(value, escape="\\"),
                    Record.external_id.ilike(value, escape="\\"),
                    cast(Record.data, Text).ilike(value, escape="\\"),
                    note_match,
                )
            )
        score = sum(case((condition, 1), else_=0) for condition in conditions)
        # Filter and rank in SQL before applying the bound: old matching evidence
        # must not disappear behind 500 newer unrelated records.
        anchors = list(
            db.scalars(
                visible.where(or_(*conditions))
                .order_by(score.desc(), Record.occurred_at.desc(), Record.id)
                .limit(9)
            )
        )
    else:
        anchors = []
    # The shared provider accepts eight contexts. Reserve room for linked
    # history instead of allowing it to silently discard every related record.
    truncated = len(anchors) > 4
    anchors = anchors[:4]
    if not anchors:
        return [], False
    relationships = [
        and_(
            Record.connection_id == row.connection_id,
            or_(
                Record.external_id.in_(row.related_ids),
                cast(Record.related_ids, Text).contains(
                    json.dumps(row.external_id), autoescape=True
                ),
            ),
        )
        for row in anchors
    ]
    related = list(
        db.scalars(
            visible.where(or_(*relationships), Record.id.not_in([r.id for r in anchors]))
            .order_by(Record.occurred_at.desc(), Record.id)
            .limit(9)
        )
    )
    related_limit = 8 - len(anchors)
    truncated |= len(related) > related_limit
    result = []
    for row in [*anchors, *related[:related_limit]]:
        notes_query = select(RecordNote).where(RecordNote.record_id == row.id)
        if terms:
            notes_query = notes_query.order_by(
                case(
                    (or_(*(RecordNote.text.ilike(pattern(t), escape="\\") for t in terms)), 1),
                    else_=0,
                ).desc()
            )
        notes = list(
            db.scalars(notes_query.order_by(RecordNote.occurred_at.desc(), RecordNote.id).limit(21))
        )
        truncated |= len(notes) > 20
        result.append((row, notes[:20]))
    return result, truncated

from __future__ import annotations

import uuid

from app.services import _candidate_ids_statement, search_phrase
from sqlalchemy.dialects import postgresql


def test_search_phrase_removes_spanish_question_words():
    assert search_phrase("¿Dónde está el taladro amarillo?") == "taladro amarillo"


def test_postgresql_candidates_use_fts_and_trigrams():
    statement = _candidate_ids_statement(
        uuid.uuid4(), "taladro amarillo", dialect_name="postgresql"
    )
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert "to_tsvector" in sql
    assert "plainto_tsquery" in sql
    assert "similarity" in sql

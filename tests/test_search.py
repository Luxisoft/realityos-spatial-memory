from __future__ import annotations

import uuid

from app.services import _candidate_ids_statement, search_phrase
from sqlalchemy.dialects import postgresql


def test_search_phrase_removes_spanish_question_words():
    assert search_phrase("¿Dónde está el taladro amarillo?") == "taladro amarillo"


def test_gallery_templates_speak_natural_plurals():
    from app.query_lang import normalize_language, qtext

    for language in ("en", "es", "pt", "fr", "de", "it"):
        one = qtext(language, "found_in_publications_one", count=1)
        other = qtext(language, "found_in_publications_other", count=6)
        assert "(" not in one and ")" not in one
        assert "(" not in other and ")" not in other
        assert normalize_language(language) == language


def test_search_phrase_strips_request_filler():
    assert (
        search_phrase("Hola, necesito que por favor me ayudes a buscar un alicate.")
        == "alicate"
    )


def test_postgresql_candidates_use_fts_and_trigrams():
    statement = _candidate_ids_statement(
        uuid.uuid4(), "taladro amarillo", dialect_name="postgresql"
    )
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert "to_tsvector" in sql
    assert "plainto_tsquery" in sql
    assert "similarity" in sql

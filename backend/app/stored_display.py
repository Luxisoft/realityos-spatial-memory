"""Read authored bilingual fields. No translation, inference or provider calls."""


def display_text(row):
    """Do not display an old wording after the owner edits its source field."""
    return {
        field: values
        for field, values in (row.display_text or {}).items()
        if values.get("source") == getattr(row, field, None)
    }

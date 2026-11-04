"""Text notes and recorded transcript merging shared across publications and chat."""

from fastapi import HTTPException


def merge_transcript_chunks(chunks: list[str]) -> str:
    """Join consecutive voice chunks, dropping words repeated at boundaries."""

    def tokens(text: str) -> list[str]:
        return [word for word in text.split() if word]

    def key(word: str) -> str:
        return word.casefold().strip(".,:?¿¡!\"'()")

    words: list[str] = []
    for chunk in chunks:
        parts = tokens(chunk)
        if not parts:
            continue
        if not words:
            words = parts
            continue
        overlap = 0
        for size in range(min(6, len(words), len(parts)), 0, -1):
            if [key(word) for word in words[-size:]] == [key(word) for word in parts[:size]]:
                overlap = size
                break
        words += parts[overlap:]
    return " ".join(words)


def _checked_note(note_text: str, note_source: str) -> tuple[str, str]:
    if note_source not in ("", "voice", "text"):
        raise HTTPException(422, "note_source must be voice or text.")
    note = note_text.strip()
    return note, note_source if note else ""

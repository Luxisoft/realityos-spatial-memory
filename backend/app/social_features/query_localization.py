"""Localize generated spatial prose without changing stored evidence or names."""

import logging

from app.query_lang import qtext

logger = logging.getLogger(__name__)


def spatial_detail(client, text: str | None, language: str) -> str:
    if not text:
        return qtext(language, "unknown_detail")
    try:
        value = client.translate_gallery_texts({"detail": text}, language)
        if (
            set(value) != {"detail"}
            or not isinstance(value["detail"], str)
            or not value["detail"].strip()
        ):
            raise ValueError("Incomplete spatial translation")
        return value["detail"].strip().rstrip(". ")
    except Exception:
        # Raw model prose may belong to a different language. The structured
        # observation remains available; never invent a translated location.
        logger.warning("spatial detail translation unavailable language=%s", language)
        return qtext(language, "unknown_detail")

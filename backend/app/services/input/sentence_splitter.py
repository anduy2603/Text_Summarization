from __future__ import annotations

import re

from app.core.logger import get_logger

_logger = get_logger(__name__)


def split_sentences(text: str) -> list[str]:
    if not text or not text.strip():
        return []
    try:
        from underthesea import sent_tokenize

        sents = sent_tokenize(text)
        if sents:
            return [s.strip() for s in sents if s.strip()]
    except Exception as exc:
        _logger.warning(
            "underthesea sent_tokenize failed, using regex fallback: %s",
            exc,
        )
    parts = re.split(r"(?<=[.!?…])\s+|\n{2,}", text)
    return [p.strip() for p in parts if p.strip()]

from __future__ import annotations

import re

_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?…])\s+|\n{2,}")


def split_sentences(text: str) -> list[str]:
    """
    Regex-only sentence splitting for Phase 0/1 reproducibility.
    This avoids environment-dependent drift caused by optional tokenizers.
    """
    if not text or not text.strip():
        return []
    parts = _SENTENCE_BOUNDARY_RE.split(text)
    return [part.strip() for part in parts if part.strip()]

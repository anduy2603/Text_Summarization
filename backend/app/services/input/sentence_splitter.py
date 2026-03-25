from __future__ import annotations

import re


def split_sentences(text: str) -> list[str]:
    if not text or not text.strip():
        return []
    try:
        from underthesea import sent_tokenize

        sents = sent_tokenize(text)
        if sents:
            return [s.strip() for s in sents if s.strip()]
    except Exception:
        pass
    parts = re.split(r"(?<=[.!?…])\s+|\n{2,}", text)
    return [p.strip() for p in parts if p.strip()]

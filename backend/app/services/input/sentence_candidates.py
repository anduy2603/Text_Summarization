from __future__ import annotations

import re
import unicodedata

from app.services.input.document_line_filters import (
    _CAPTION_ONLY_RE,
    _METADATA_ONLY_RE,
    _NOISE_LINE_RE,
)

_MIN_SENTENCE_CHARS = 20
_MAX_SENTENCE_CHARS = 900
_MIN_SENTENCE_WORDS = 4

# Inline photo/caption phrasing inside sentences (PDF/DOCX news).
_CAPTION_INLINE_RE = re.compile(
    r"(?:"
    r"bắt\s*tay|trong\s+lễ\s+ký\s+kết|trong\s+ảnh|trong\s*hình"
    r"|(?:\(|（)\s*(?:trái|phải|trên|dưới)\s*(?:\)|）)"
    r"|tổng\s*thống\s+.+\s+bắt\s*tay"
    r")",
    flags=re.IGNORECASE | re.UNICODE,
)


def _normalize_sentence_key(sentence: str) -> str:
    folded = unicodedata.normalize("NFC", sentence.strip().casefold())
    return re.sub(r"\s+", " ", folded)


def is_junk_sentence(sentence: str) -> bool:
    text = sentence.strip()
    if not text:
        return True
    if len(text) < _MIN_SENTENCE_CHARS:
        return True
    if len(text) > _MAX_SENTENCE_CHARS:
        return True
    words = re.findall(r"[^\W_]+", text, flags=re.UNICODE)
    if len(words) < _MIN_SENTENCE_WORDS:
        return True
    if _NOISE_LINE_RE.search(text) or _CAPTION_ONLY_RE.match(text) or _METADATA_ONLY_RE.match(text):
        return True
    if _CAPTION_INLINE_RE.search(text):
        return True
    return False


def filter_sentences_for_summarization(sentences: list[str]) -> tuple[list[str], dict[str, int]]:
    stats = {
        "sentences_in": len(sentences),
        "sentences_dropped_junk": 0,
        "sentences_dropped_duplicate": 0,
        "sentences_out": 0,
    }
    kept: list[str] = []
    seen: set[str] = set()
    for sentence in sentences:
        if is_junk_sentence(sentence):
            stats["sentences_dropped_junk"] += 1
            continue
        key = _normalize_sentence_key(sentence)
        if key in seen:
            stats["sentences_dropped_duplicate"] += 1
            continue
        seen.add(key)
        kept.append(sentence.strip())
    stats["sentences_out"] = len(kept)
    return kept, stats

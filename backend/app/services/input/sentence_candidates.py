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

# Bare URL lines (e.g. print-version URLs embedded in PDFs or HTML)
_URL_LINE_RE = re.compile(r"^https?://\S+$", re.IGNORECASE)

# Timestamp / publication-date lines scraped from news HTML
# e.g. "Thứ hai, 04/05/2026 - 06:00"  "Thứ 2, 12:30 ICT"  "08/06/2026 - 14:15"
_TIMESTAMP_RE = re.compile(
    r"^(?:thứ\s+(?:hai|ba|tư|năm|sáu|bảy|chủ\s+nhật),?\s*)?"
    r"\d{1,2}[/\-]\d{1,2}(?:[/\-]\d{2,4})?(?:\s*[-–]\s*\d{1,2}:\d{2})?$",
    flags=re.IGNORECASE | re.UNICODE,
)

# Very short headline-only fragments (≤ 12 words, no verb indicator)
# Used to catch related-article titles scraped from news sidebars.
# We only reject if the sentence has NO common Vietnamese verbal connectors.
_HEADLINE_FRAG_RE = re.compile(
    r"^[^.!?…]{10,120}$",   # no sentence-ending punctuation
    flags=re.UNICODE,
)
_HAS_VERB_INDICATOR_RE = re.compile(
    r"\b(?:là|đã|sẽ|đang|có|được|cho|với|về|trong|để|khi|nếu|vì|bởi|theo|qua|tại|từ|sau|trước)\b",
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
    # Reject bare URL lines (e.g. print-version URLs embedded in PDFs)
    if _URL_LINE_RE.match(text):
        return True
    # Reject timestamp / publication-date lines (e.g. "Thứ hai, 04/05/2026 - 06:00")
    if _TIMESTAMP_RE.match(text):
        return True
    # Reject short headline fragments without verbal connectors
    # (catches related-article titles scraped from news sidebars)
    if _HEADLINE_FRAG_RE.match(text) and len(words) <= 12 and not _HAS_VERB_INDICATOR_RE.search(text):
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

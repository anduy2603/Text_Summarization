from __future__ import annotations

import re
from typing import Any

from app.core.config import settings
from app.services.summarization.text_stats import repetition_rate

# Mojibake / runaway generation heuristics for Vietnamese news summaries.
_MOJIBAKE_RUN_RE = re.compile(r"(?:[ÓỒỚẠÙ]{2,}|ÓÓÓ)")
_CHAR_STUTTER_RE = re.compile(r"(.)\1{4,}", flags=re.UNICODE)
_ALLOWED_EXTRA_RE = re.compile(
    r"[^\w\s.,!?…:;\-\"'()\[\]À-ỹà-ỹĐđ]",
    flags=re.UNICODE,
)


def assess_vit5_lead_quality(
    text: str,
    *,
    source_text: str = "",
) -> tuple[bool, dict[str, Any]]:
    """
    Return (passed, details). Failed leads must not be shown to users.
    """
    stripped = text.strip()
    reasons: list[str] = []
    if not stripped:
        return False, {"passed": False, "reasons": ["empty"]}

    if len(stripped) > settings.vit5_lead_max_chars:
        reasons.append("too-long")

    if count_sentences_quick(stripped) > settings.vit5_lead_max_sentences:
        reasons.append("too-many-sentences")

    if _MOJIBAKE_RUN_RE.search(stripped):
        reasons.append("mojibake-pattern")

    if _CHAR_STUTTER_RE.search(stripped):
        reasons.append("char-stutter")

    weird = len(_ALLOWED_EXTRA_RE.findall(stripped))
    if len(stripped) > 0 and weird / len(stripped) > settings.vit5_lead_max_weird_char_ratio:
        reasons.append("high-weird-char-ratio")

    if repetition_rate(stripped) >= settings.vit5_lead_max_repetition_rate:
        reasons.append("high-repetition")

    passed = len(reasons) == 0
    return passed, {
        "passed": passed,
        "reasons": reasons,
        "summary_char_length": len(stripped),
        "summary_sentence_count": count_sentences_quick(stripped),
    }


def count_sentences_quick(text: str) -> int:
    parts = [p.strip() for p in re.split(r"(?<=[.!?…])\s+", text.strip()) if p.strip()]
    return len([p for p in parts if len(p) >= 8])

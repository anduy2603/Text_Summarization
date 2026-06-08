from __future__ import annotations

import re
import unicodedata
from typing import Any

# Photo captions / scene description (not summary bullets).
_CAPTION_PHRASE_RE = re.compile(
    r"(?:"
    r"bắt\s*tay|bắt\s*tay\s+trong|trong\s+lễ\s+ký\s+kết|trong\s+ảnh|trong\s*hình"
    r"|(?:\(|（)\s*(?:trái|phải|trên|dưới|giữa)\s*(?:\)|）)"
    r"|ảnh\s*chụp|đồng\s*thời\s*chụp|pose\s+for\s+photo"
    r"|tổng\s*thống\s+.+\s+bắt\s*tay"
    r"|chủ\s*tịch\s+.+\s+bắt\s*tay"
    r")",
    flags=re.IGNORECASE | re.UNICODE,
)

# Pronoun/deictic without enough anchor entities in the same sentence.
_DEICTIC_RE = re.compile(
    r"\b(?:công\s*thức|vấn\s*đề|điều|chi\s*tiết|điểm|vụ|sự\s*việc|phương\s*án|đề\s*xuất)\s+này\b",
    flags=re.IGNORECASE | re.UNICODE,
)

_VAGUE_OPENING_RE = re.compile(
    r"^(?:"
    r"một\s+số|những|vài|các"
    r")\s+(?:chi\s+tiết|điểm|vấn\s+đề|điều\s+kiện)\b",
    flags=re.IGNORECASE | re.UNICODE,
)

_SPEECH_FRAGMENT_RE = re.compile(
    r"\b(?:ông|bà|ông\s+ấy|bà\s+ấy|họ)\s+(?:nói\s+thêm|cho\s+biết\s+thêm|nhấn\s+mạnh|bổ\s+sung)\b",
    flags=re.IGNORECASE | re.UNICODE,
)

_CONTRAST_WITHOUT_ENTITY_RE = re.compile(
    r"^tuy\s+nhiên\b",
    flags=re.IGNORECASE | re.UNICODE,
)

_TOPIC_PATTERNS: list[tuple[re.Pattern[str], float]] = [
    (re.compile(r"sức\s*mạnh\s*siberia|siberia\s*2", re.I | re.U), 3.0),
    (re.compile(r"đường\s*ống|ống\s*dẫn", re.I | re.U), 2.5),
    (re.compile(r"khí\s*đốt|khí\s*thiên\s*nhiên", re.I | re.U), 2.5),
    (re.compile(r"giá\s*khí|điều\s*kiện\s*thương\s*mại", re.I | re.U), 2.5),
    (re.compile(r"lộ\s*trình|triển\s*khai|đàm\s*phán", re.I | re.U), 2.0),
    (re.compile(r"\bnga\b|\brussia\b", re.I | re.U), 1.5),
    (re.compile(r"trung\s*quốc|\btrung\s*quoc\b|beijing|bắc\s*kinh", re.I | re.U), 1.5),
    (re.compile(r"mông\s*cổ|mongolia", re.I | re.U), 1.5),
    (re.compile(r"châu\s*âu|eu\b", re.I | re.U), 1.0),
]

_ENTITY_RE = re.compile(
    r"\b(?:nga|trung\s*quốc|putin|xi\s*jinping|siberia|mông\s*cổ|đường\s*ống|khí\s*đốt)\b",
    flags=re.IGNORECASE | re.UNICODE,
)


def _fold(text: str) -> str:
    return unicodedata.normalize("NFC", text.casefold())


def is_unsuitable_bullet(sentence: str) -> tuple[bool, str | None]:
    text = sentence.strip()
    if not text:
        return True, "empty"
    if _CAPTION_PHRASE_RE.search(text):
        return True, "caption-or-photo"
    if _VAGUE_OPENING_RE.search(text) and not _ENTITY_RE.search(text):
        return True, "vague-fragment"
    if _SPEECH_FRAGMENT_RE.search(text) and not _ENTITY_RE.search(text):
        return True, "speech-fragment"
    if _DEICTIC_RE.search(text) and len(_ENTITY_RE.findall(text)) < 2:
        return True, "deictic-low-context"
    if _CONTRAST_WITHOUT_ENTITY_RE.search(text) and len(_ENTITY_RE.findall(text)) < 1:
        return True, "contrast-without-entity"
    return False, None


def score_bullet_candidate(sentence: str, *, position_index: int, total: int) -> float:
    text = _fold(sentence)
    score = 0.0
    for pattern, weight in _TOPIC_PATTERNS:
        if pattern.search(text):
            score += weight
    if _ENTITY_RE.search(text):
        score += 1.0
    if total > 0:
        # News leads: favor title/sapo/first sections (top ~35% of sentences).
        relative = position_index / max(total - 1, 1)
        if relative <= 0.35:
            score += 2.0 * (1.0 - relative / 0.35)
        elif relative <= 0.55:
            score += 0.5
    if len(text) < 40:
        score -= 1.0
    return score


def rank_sentences_for_bullets(
    sentences: list[str],
    *,
    pool_text: str = "",
    max_bullets: int,
    min_bullets: int = 0,
    redundancy_threshold: float = 0.45,
) -> tuple[list[str], dict[str, Any]]:
    """
    Pick standalone, topic-relevant bullets from TextRank pool (not score-only order).
    """
    from app.services.summarization.summary_length import is_redundant_with_text

    total = len(sentences)
    candidates: list[tuple[float, int, str]] = []
    dropped: list[dict[str, str]] = []

    for idx, sentence in enumerate(sentences):
        bad, reason = is_unsuitable_bullet(sentence)
        if bad:
            dropped.append({"index": str(idx), "reason": reason or "unsuitable"})
            continue
        if pool_text and is_redundant_with_text(sentence, pool_text, threshold=redundancy_threshold):
            dropped.append({"index": str(idx), "reason": "redundant-with-lead"})
            continue
        rel = score_bullet_candidate(sentence, position_index=idx, total=total)
        candidates.append((rel, idx, sentence.strip()))

    candidates.sort(key=lambda item: (-item[0], item[1]))

    selected: list[str] = []
    selected_indices: list[int] = []
    pool = pool_text
    for rel, idx, sentence in candidates:
        if pool and is_redundant_with_text(sentence, pool, threshold=redundancy_threshold):
            continue
        selected.append(sentence)
        selected_indices.append(idx)
        pool = f"{pool} {sentence}".strip() if pool else sentence
        if len(selected) >= max_bullets:
            break

    if len(selected) < min_bullets:
        for rel, idx, sentence in candidates:
            if sentence in selected:
                continue
            if pool and is_redundant_with_text(sentence, pool, threshold=redundancy_threshold):
                continue
            selected.append(sentence)
            selected_indices.append(idx)
            pool = f"{pool} {sentence}".strip() if pool else sentence
            if len(selected) >= min_bullets:
                break

    return selected, {
        "bullet_selection": "topic-relevance-plus-position",
        "candidates_scored": len(candidates),
        "dropped_unsuitable": dropped[:20],
        "selected_indices": selected_indices,
        "selected_scores": [
            {"index": idx, "score": rel} for rel, idx, _ in candidates if idx in selected_indices
        ],
    }

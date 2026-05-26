from __future__ import annotations

import re
from typing import Any

from app.core.config import settings
from app.services.summarization.bullet_selection import rank_sentences_for_bullets
from app.services.summarization.summary_quality import assess_vit5_lead_quality

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?…])\s+")
_TOKEN_RE = re.compile(r"[^\W_]+", flags=re.UNICODE)


def count_sentences(text: str) -> int:
    text = text.strip()
    if not text:
        return 0
    parts = [p.strip() for p in _SENTENCE_SPLIT_RE.split(text) if p.strip()]
    return len([p for p in parts if len(p) >= 12])


def resolve_min_output_sentences(target_k: int, length_tier: str) -> int:
    """Minimum ideas in final hybrid output (satisfied mainly by extractive bullets)."""
    k = max(1, int(target_k))
    if length_tier == "short":
        return max(1, min(2, k))
    if length_tier == "medium":
        return max(2, min(k, 4))
    return max(3, min(k, 6))


def resolve_vit5_lead_sentences(target_k: int, length_tier: str) -> int:
    """ViT5 only writes a short lead (1-2 sentences); never full document length."""
    cap = settings.vit5_lead_max_sentences
    if length_tier == "short":
        return min(1, cap, max(1, target_k))
    return min(2, cap)


def _token_set(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text)}


def is_redundant_with_text(candidate: str, existing: str, *, threshold: float = 0.55) -> bool:
    cand = _token_set(candidate)
    if not cand:
        return True
    pool = _token_set(existing)
    if not pool:
        return False
    overlap = len(cand & pool) / len(cand)
    return overlap >= threshold


def format_structured_hybrid_summary(lead: str, bullets: list[str]) -> str:
    lines: list[str] = []
    lead = lead.strip()
    if lead:
        lines.append("Điểm cốt lõi:")
        lines.append(lead)
    cleaned_bullets: list[str] = []
    for item in bullets:
        item = item.strip()
        if not item:
            continue
        if item.startswith("- "):
            cleaned_bullets.append(item)
        else:
            cleaned_bullets.append(f"- {item}")
    if cleaned_bullets:
        if lines:
            lines.append("")
        lines.append("Ý chính:")
        lines.extend(cleaned_bullets)
    return "\n".join(lines).strip()


def assemble_hybrid_document_summary(
    *,
    vit5_text: str,
    extractive_sentences: list[str],
    target_k: int,
    min_output_sentences: int,
    length_tier: str,
    source_text: str = "",
) -> tuple[str, dict[str, Any]]:
    """
    Hybrid document summary = short ViT5 lead (optional) + extractive bullets from TextRank.
    Length comes from extractive evidence, not from forcing ViT5 to generate more tokens.
    """
    raw_lead = vit5_text.strip()
    extractive = [s.strip() for s in extractive_sentences if s.strip()]

    lead = ""
    quality: dict[str, Any] = {"skipped": True, "reason": "no-vit5-input"}
    if raw_lead:
        passed, quality = assess_vit5_lead_quality(raw_lead, source_text=source_text)
        if passed:
            lead = raw_lead
        else:
            quality["discarded_lead_preview"] = raw_lead[:200]

    pool_text = lead
    max_bullets = max(0, target_k - (1 if lead else 0))
    if length_tier != "short":
        max_bullets = max(max_bullets, min_output_sentences - (1 if lead else 0))

    min_bullets = 0
    if length_tier != "short":
        min_bullets = max(0, min_output_sentences - (1 if lead else 0))

    bullets, bullet_meta = rank_sentences_for_bullets(
        extractive,
        pool_text=pool_text,
        max_bullets=max_bullets,
        min_bullets=min_bullets,
    )

    meta: dict[str, Any] = {
        "summary_format": "hybrid-structured",
        "vit5_lead_sentence_count": count_sentences(lead),
        "min_output_sentences": min_output_sentences,
        "target_k": target_k,
        "length_tier": length_tier,
        "bullet_count": len(bullets),
        "vit5_quality": quality,
        **bullet_meta,
    }

    if lead and bullets:
        combined = format_structured_hybrid_summary(lead, bullets)
        meta["augmentation"] = "hybrid-lead-plus-bullets"
    elif lead:
        combined = format_structured_hybrid_summary(lead, [])
        meta["augmentation"] = "hybrid-lead-only"
    elif bullets:
        combined = format_structured_hybrid_summary("", bullets)
        meta["augmentation"] = "hybrid-bullets-only"
    else:
        fallback = " ".join(extractive[:target_k])
        combined = format_structured_hybrid_summary("", extractive[:target_k])
        meta["augmentation"] = "extractive-fallback"
        if not combined:
            combined = fallback

    meta["output_sentence_count"] = count_sentences(
        lead + " " + " ".join(bullets) if lead or bullets else combined
    )
    return combined, meta

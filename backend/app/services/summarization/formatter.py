from __future__ import annotations

import re

from app.schemas.common import SummarizeResponse
from app.schemas.input import ProcessedInput
from app.services.summarization.text_stats import repetition_rate

# Trailing ellipsis / incomplete sentence markers
_TRAILING_ELLIPSIS_RE = re.compile(r"\s*\.{2,}\s*$|…\s*$", re.UNICODE)
# Bullet prefix left over from raw extraction
_BULLET_PREFIX_RE = re.compile(r"^[-•*]\s+", re.UNICODE)


def _clean_sentence(text: str) -> str:
    """Clean a single sentence: strip bullets, incomplete endings, fix capitalization."""
    t = _BULLET_PREFIX_RE.sub("", text).strip()
    t = _TRAILING_ELLIPSIS_RE.sub("", t).strip()
    # Capitalize first character (preserves Vietnamese diacritics)
    if t and t[0].islower():
        t = t[0].upper() + t[1:]
    return t


def _clean_summary(summary: str, engine_name: str) -> str:
    """
    Post-process final summary text.
    For hybrid: clean each bullet line independently.
    For extractive: clean each sentence.
    """
    if not summary.strip():
        return summary

    if engine_name == "hybrid" and "\n" in summary:
        lines = summary.split("\n")
        cleaned: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                cleaned.append("")
                continue
            # Section headers (e.g. "Điểm cốt lõi:", "Ý chính:") — keep as-is
            if stripped.endswith(":"):
                cleaned.append(stripped)
            elif stripped.startswith("- "):
                cleaned.append("- " + _clean_sentence(stripped[2:]))
            else:
                cleaned.append(_clean_sentence(stripped))
        return "\n".join(cleaned).strip()

    # Extractive / ViT5: single block of text
    return _clean_sentence(summary)


def build_summary_response(
    *,
    processed: ProcessedInput,
    selected_sentences: list[str],
    max_sentences: int | None,
    ratio: float | None,
    engine_name: str,
    engine_meta: dict | None = None,
    policy_target_k: int | None = None,
) -> SummarizeResponse:
    parts = [sentence.strip() for sentence in selected_sentences if sentence.strip()]
    if len(parts) == 1 and ("\n" in parts[0] or engine_name == "hybrid"):
        summary = parts[0]
    else:
        summary = " ".join(parts)
    summary = _clean_summary(summary, engine_name)
    source_char_len = len(processed.cleaned_text)
    summary_char_len = len(summary)
    source_sentence_count = len(processed.sentences)
    selected_sentence_count = len(selected_sentences)
    metadata = {
        "engine": engine_name,
        "target_sentences": max_sentences,
        "policy_target_k": policy_target_k,
        "target_ratio": ratio,
        "selected_sentence_count": selected_sentence_count,
        "resolved_target_k": policy_target_k if isinstance(policy_target_k, int) else selected_sentence_count,
        "source_type": processed.source_type,
        "sentence_count": source_sentence_count,
        "cleaned_char_length": source_char_len,
        "summary_char_length": summary_char_len,
        "compression_ratio_chars": (summary_char_len / source_char_len) if source_char_len > 0 else 0.0,
        "compression_ratio_sentences": (
            selected_sentence_count / source_sentence_count if source_sentence_count > 0 else 0.0
        ),
        "repetition_rate": repetition_rate(summary),
        "input_metadata": processed.metadata,
    }
    if engine_meta:
        resolved_k = engine_meta.get("resolved_target_k")
        if isinstance(resolved_k, int):
            metadata["resolved_target_k"] = resolved_k
        out_sents = engine_meta.get("output_sentence_count")
        if isinstance(out_sents, int):
            metadata["output_sentence_count"] = out_sents
        augment = engine_meta.get("augmentation")
        if isinstance(augment, dict):
            metadata["augmentation"] = augment
        latency = engine_meta.get("summarizer_latency_ms")
        if isinstance(latency, int):
            metadata["summarizer_latency_ms"] = latency
        safe_meta = {k: v for k, v in engine_meta.items() if k != "source_text"}
        metadata["engine_metadata"] = safe_meta
    return SummarizeResponse(summary=summary, metadata=metadata)

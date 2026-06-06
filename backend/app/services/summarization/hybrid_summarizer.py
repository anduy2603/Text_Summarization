from __future__ import annotations

import re
from typing import Any

from app.core.config import settings
from app.services.summarization.summary_length import (
    assemble_hybrid_document_summary,
    count_sentences,
    resolve_vit5_lead_sentences,
)
from app.services.summarization.textrank_summarizer import summarize_with_textrank
from app.services.summarization.vit5_abstractive import Vit5EngineNotReadyError, summarize_with_vit5

_PARAGRAPH_BREAK_RE = re.compile(r"\n{2,}")


def _length_tier_from_chars(char_len: int) -> str:
    if char_len < 1_500:
        return "short"
    if char_len < 6_000:
        return "medium"
    return "long"


def _chunk_text_by_paragraphs(text: str, max_chars: int) -> list[str]:
    paragraphs = [p.strip() for p in _PARAGRAPH_BREAK_RE.split(text) if p.strip()]
    if not paragraphs:
        return [text.strip()] if text.strip() else []
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for para in paragraphs:
        para_len = len(para)
        if current and current_len + para_len + 2 > max_chars:
            chunks.append("\n\n".join(current))
            current = [para]
            current_len = para_len
            continue
        current.append(para)
        current_len += para_len + 2
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def _preselect_floor(length_tier: str) -> int:
    if length_tier == "long":
        return settings.hybrid_preselect_floor_long
    if length_tier == "medium":
        return settings.hybrid_preselect_floor_medium
    return settings.hybrid_preselect_floor_short


def _preselect_k(target_k: int, sentence_count: int, length_tier: str) -> int:
    multiplier = max(1.0, settings.hybrid_preselect_multiplier)
    cap = max(target_k, settings.hybrid_preselect_cap)
    floor = _preselect_floor(length_tier)
    scaled = int(target_k * multiplier)
    return max(target_k, floor, min(scaled, cap, sentence_count))


def _textrank_on_text(
    text: str,
    *,
    pick_k: int,
    max_sentences: int | None,
    ratio: float | None,
) -> tuple[list[str], dict[str, Any]]:
    from app.services.input import sentence_candidates, sentence_splitter

    sentences = sentence_splitter.split_sentences(text)
    filtered, _ = sentence_candidates.filter_sentences_for_summarization(sentences)
    if not filtered and sentences:
        filtered = sentences[:1]
    return summarize_with_textrank(
        filtered,
        max_sentences=pick_k,
        ratio=ratio,
    )


def _finalize_hybrid_vit5_output(
    *,
    vit5_text: str,
    vit5_meta: dict[str, Any],
    extractive_sentences: list[str],
    target_k: int,
    min_output_sentences: int,
    length_tier: str,
    base_meta: dict[str, Any],
    strategy: str,
) -> tuple[list[str], dict[str, Any]]:
    combined, augment_meta = assemble_hybrid_document_summary(
        vit5_text=vit5_text,
        extractive_sentences=extractive_sentences,
        target_k=target_k,
        min_output_sentences=min_output_sentences,
        length_tier=length_tier,
        source_text="",
    )
    return [combined], {
        **base_meta,
        "strategy": strategy,
        "abstractive_stage": vit5_meta,
        "augmentation": augment_meta,
        "output_sentence_count": augment_meta.get("output_sentence_count", count_sentences(combined)),
        "resolved_target_k": target_k,
    }


def summarize_with_hybrid(
    *,
    cleaned_text: str,
    sentences: list[str],
    target_k: int,
    max_sentences: int | None = None,
    ratio: float | None = None,
    length_tier: str | None = None,
    min_output_sentences: int | None = None,
) -> tuple[list[str], dict[str, Any]]:
    """
    Hybrid document summary for real uploads:
    TextRank preselect (6-8 for medium/long) → ViT5 lead → augment if too short.
    """
    if not sentences and not cleaned_text.strip():
        return [], {"engine": "hybrid", "strategy": "empty-input", "method": "hybrid"}

    char_len = len(cleaned_text)
    tier = length_tier or _length_tier_from_chars(char_len)
    min_out = min_output_sentences if min_output_sentences is not None else max(2, min(target_k, 3))
    vit5_lead_k = resolve_vit5_lead_sentences(target_k, tier)

    use_vit5 = char_len >= settings.hybrid_vit5_min_chars
    is_long = char_len >= settings.hybrid_long_doc_chars

    meta: dict[str, Any] = {
        "engine": "hybrid",
        "method": "hybrid",
        "summary_format": "hybrid-structured",
        "resolved_target_k": target_k,
        "min_output_sentences": min_out,
        "length_tier": tier,
        "doc_char_length": char_len,
        "hybrid_use_vit5": use_vit5,
        "hybrid_long_doc": is_long,
        "vit5_lead_sentences": vit5_lead_k,
    }

    if is_long:
        chunks = _chunk_text_by_paragraphs(cleaned_text, settings.hybrid_chunk_chars)
        chunk_summaries: list[str] = []
        chunk_extractive: list[str] = []
        chunk_meta: list[dict[str, Any]] = []
        n_chunks = max(1, len(chunks))
        # Scale per-chunk selection so the candidate pool is proportional to target_k.
        # ceil(target_k / n_chunks) + 1 gives each chunk enough representatives,
        # capped at 8 to limit ViT5 context overhead.
        per_chunk_k = max(2, min(8, (target_k + n_chunks - 1) // n_chunks + 1))
        for idx, chunk in enumerate(chunks):
            picked, chunk_engine_meta = _textrank_on_text(
                chunk,
                pick_k=per_chunk_k,
                max_sentences=per_chunk_k,
                ratio=ratio,
            )
            chunk_extractive.extend(picked)
            joined = " ".join(picked).strip()
            if joined:
                chunk_summaries.append(joined)
            chunk_meta.append(
                {
                    "chunk_index": idx,
                    "chunk_char_length": len(chunk),
                    "selected_sentence_count": len(picked),
                    "engine_meta": chunk_engine_meta,
                }
            )
        interim = "\n\n".join(chunk_summaries).strip()
        meta["chunk_count"] = len(chunks)
        meta["chunk_summaries"] = chunk_meta
        meta["extractive_pool"] = chunk_extractive
        if not interim:
            return [], {**meta, "strategy": "chunk-extractive-empty"}
        if not use_vit5:
            parts = chunk_extractive[:target_k] if chunk_extractive else chunk_summaries[:target_k]
            return parts, {**meta, "strategy": "chunk-extractive-only-no-vit5"}

        try:
            summary, vit5_meta = summarize_with_vit5(
                interim,
                max_sentences=vit5_lead_k,
                ratio=ratio,
                hybrid_lead=True,
            )
            if summary.strip():
                return _finalize_hybrid_vit5_output(
                    vit5_text=summary,
                    vit5_meta=vit5_meta,
                    extractive_sentences=chunk_extractive,
                    target_k=target_k,
                    min_output_sentences=min_out,
                    length_tier=tier,
                    base_meta={**meta, "extractive_stage": "per-chunk-textrank"},
                    strategy="chunk-extractive-vit5-augmented",
                )
        except Vit5EngineNotReadyError as exc:
            meta["vit5_fallback_reason"] = str(exc)
        parts = chunk_extractive[:target_k] if chunk_extractive else chunk_summaries[:target_k]
        return parts, {**meta, "strategy": "chunk-extractive-only", "vit5_fallback": True}

    pre_k = _preselect_k(target_k, len(sentences), tier)
    selected, textrank_meta = summarize_with_textrank(
        sentences,
        max_sentences=pre_k,
        ratio=ratio,
    )
    interim = " ".join(selected).strip()
    meta["extractive_stage"] = textrank_meta
    meta["preselect_k"] = pre_k

    if not interim:
        return [], {**meta, "strategy": "hybrid-empty-extractive"}

    if not use_vit5:
        final = selected[:target_k]
        combined = " ".join(final).strip()
        return [combined] if combined else [], {
            **meta,
            "strategy": "hybrid-textrank-only-short-doc",
            "output_sentence_count": count_sentences(combined),
        }

    try:
        summary, vit5_meta = summarize_with_vit5(
            interim,
            max_sentences=vit5_lead_k,
            ratio=ratio,
            hybrid_lead=True,
        )
    except Vit5EngineNotReadyError as exc:
        final = selected[:target_k]
        combined = " ".join(final).strip()
        return [combined] if combined else [], {
            **meta,
            "strategy": "hybrid-textrank-fallback",
            "vit5_fallback_reason": str(exc),
            "output_sentence_count": count_sentences(combined),
        }

    if not summary.strip():
        final = selected[:target_k]
        combined = " ".join(final).strip()
        return [combined] if combined else [], {
            **meta,
            "strategy": "hybrid-textrank-fallback-empty-vit5",
            "output_sentence_count": count_sentences(combined),
        }

    return _finalize_hybrid_vit5_output(
        vit5_text=summary,
        vit5_meta=vit5_meta,
        extractive_sentences=selected,
        target_k=target_k,
        min_output_sentences=min_out,
        length_tier=tier,
        base_meta=meta,
        strategy="hybrid-textrank-vit5-augmented",
    )

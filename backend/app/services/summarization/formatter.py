from __future__ import annotations

from app.schemas.common import SummarizeResponse
from app.schemas.input import ProcessedInput


def build_summary_response(
    *,
    processed: ProcessedInput,
    selected_sentences: list[str],
    max_sentences: int | None,
    ratio: float | None,
    engine_name: str,
    engine_meta: dict | None = None,
) -> SummarizeResponse:
    summary = " ".join(sentence.strip() for sentence in selected_sentences if sentence.strip())
    source_char_len = len(processed.cleaned_text)
    summary_char_len = len(summary)
    source_sentence_count = len(processed.sentences)
    selected_sentence_count = len(selected_sentences)
    metadata = {
        "engine": engine_name,
        "target_sentences": max_sentences,
        "target_ratio": ratio,
        "selected_sentence_count": selected_sentence_count,
        "resolved_target_k": selected_sentence_count,
        "source_type": processed.source_type,
        "sentence_count": source_sentence_count,
        "cleaned_char_length": source_char_len,
        "summary_char_length": summary_char_len,
        "compression_ratio_chars": (summary_char_len / source_char_len) if source_char_len > 0 else 0.0,
        "compression_ratio_sentences": (
            selected_sentence_count / source_sentence_count if source_sentence_count > 0 else 0.0
        ),
        "input_metadata": processed.metadata,
    }
    if engine_meta:
        # Prefer engine-resolved target when available.
        resolved_k = engine_meta.get("resolved_target_k")
        if isinstance(resolved_k, int):
            metadata["resolved_target_k"] = resolved_k
        metadata["engine_metadata"] = engine_meta
    return SummarizeResponse(summary=summary, metadata=metadata)

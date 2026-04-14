from __future__ import annotations

from app.schemas.common import SummarizeResponse
from app.schemas.input import ProcessedInput


def build_summary_response(
    *,
    processed: ProcessedInput,
    selected_sentences: list[str],
    max_sentences: int,
    engine_name: str,
    engine_meta: dict | None = None,
) -> SummarizeResponse:
    summary = " ".join(sentence.strip() for sentence in selected_sentences if sentence.strip())
    metadata = {
        "engine": engine_name,
        "target_sentences": max_sentences,
        "selected_sentence_count": len(selected_sentences),
        "source_type": processed.source_type,
        "sentence_count": len(processed.sentences),
        "cleaned_char_length": len(processed.cleaned_text),
        "input_metadata": processed.metadata,
    }
    if engine_meta:
        metadata["engine_metadata"] = engine_meta
    return SummarizeResponse(summary=summary, metadata=metadata)

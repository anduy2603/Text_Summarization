from __future__ import annotations

from app.core.config import settings
from app.schemas.common import SummarizeResponse
from app.schemas.input import ProcessedInput
from app.services.summarization.formatter import build_summary_response
from app.services.summarization.tfidf_summarizer import summarize_with_tfidf


def summarize_processed_input(processed: ProcessedInput, max_sentences: int) -> SummarizeResponse:
    engine = settings.summary_engine.strip().lower()

    if engine == "tfidf":
        selected_sentences, engine_meta = summarize_with_tfidf(
            processed.sentences,
            max_sentences,
        )
        return build_summary_response(
            processed=processed,
            selected_sentences=selected_sentences,
            max_sentences=max_sentences,
            engine_name="tfidf",
            engine_meta=engine_meta,
        )

    raise ValueError(f"Unsupported summary engine: {engine!r}")

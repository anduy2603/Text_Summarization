from __future__ import annotations

from collections.abc import Callable
from typing import Any, Optional

from app.core.config import settings
from app.schemas.common import PLANNED_SUMMARY_ENGINES, SUPPORTED_SUMMARY_ENGINES, SummarizeResponse
from app.schemas.input import ProcessedInput
from app.services.summarization.formatter import build_summary_response
from app.services.summarization.textrank_summarizer import summarize_with_textrank
from app.services.summarization.tfidf_summarizer import summarize_with_tfidf

SummaryEngineFn = Callable[[list[str], Optional[int], Optional[float]], tuple[list[str], dict[str, Any]]]


class UnsupportedSummaryEngineError(RuntimeError):
    """Raised when a requested summary engine is not registered."""


class SummaryEngineNotReadyError(RuntimeError):
    """Raised when an engine exists in the roadmap but is not implemented yet."""


def _build_engine_registry() -> dict[str, SummaryEngineFn]:
    return {
        "tfidf": summarize_with_tfidf,
    }


SUMMARY_ENGINE_REGISTRY = _build_engine_registry()


def list_supported_summary_engines() -> list[str]:
    return sorted(SUMMARY_ENGINE_REGISTRY)


def list_planned_summary_engines() -> list[str]:
    return sorted(set(PLANNED_SUMMARY_ENGINES))


def resolve_summary_engine(engine_name: str | None = None) -> tuple[str, SummaryEngineFn]:
    requested = (engine_name or settings.summary_engine).strip().lower()
    engine = SUMMARY_ENGINE_REGISTRY.get(requested)
    if engine is not None:
        return requested, engine

    supported = ", ".join(list_supported_summary_engines())
    planned = ", ".join(list_planned_summary_engines())

    if requested in PLANNED_SUMMARY_ENGINES:
        raise SummaryEngineNotReadyError(
            f"Summary engine {requested!r} is planned but not ready yet. "
            f"Currently supported engines: {supported}. Planned engines: {planned}."
        )

    raise UnsupportedSummaryEngineError(
        f"Unsupported summary engine: {requested!r}. "
        f"Currently supported engines: {supported}. Planned engines: {planned}."
    )


def summarize_processed_input_raw(
    processed: ProcessedInput,
    max_sentences: int | None = None,
    ratio: float | None = None,
    engine_name: str | None = None,
) -> tuple[list[str], dict[str, Any]]:
    """
    Raw summarization output for experiments/notebooks.
    Returns selected sentences and engine metadata without API formatting.
    """
    resolved_engine_name, engine_fn = resolve_summary_engine(engine_name)
    selected_sentences, engine_meta = engine_fn(
        processed.sentences,
        max_sentences=max_sentences,
        ratio=ratio,
    )

    engine_meta = dict(engine_meta or {})
    engine_meta.setdefault("engine", resolved_engine_name)
    return selected_sentences, engine_meta


def summarize_processed_input(
    processed: ProcessedInput,
    max_sentences: int | None = None,
    ratio: float | None = None,
    engine_name: str | None = None,
) -> SummarizeResponse:
    selected_sentences, engine_meta = summarize_processed_input_raw(
        processed,
        max_sentences=max_sentences,
        ratio=ratio,
        engine_name=engine_name,
    )
    resolved_engine_name = str(engine_meta.get("engine") or engine_name or settings.summary_engine).strip().lower()
    return build_summary_response(
        processed=processed,
        selected_sentences=selected_sentences,
        max_sentences=max_sentences,
        ratio=ratio,
        engine_name=resolved_engine_name,
        engine_meta=engine_meta,
    )

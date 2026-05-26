from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, Optional

from app.core.config import settings
from app.schemas.common import PLANNED_SUMMARY_ENGINES, SUPPORTED_SUMMARY_ENGINES, SummarizeResponse
from app.schemas.input import ProcessedInput
from app.services.summarization.formatter import build_summary_response
from app.services.summarization.hybrid_summarizer import summarize_with_hybrid
from app.services.summarization.length_policy import resolve_target_k_from_policy
from app.services.summarization.phobert_extractive import (
    PhoBertEngineNotReadyError,
    summarize_with_phobert_extractive,
)
from app.services.summarization.textrank_summarizer import summarize_with_textrank
from app.services.summarization.tfidf_summarizer import summarize_with_tfidf
from app.services.summarization.vit5_abstractive import (
    Vit5EngineNotReadyError,
    summarize_with_vit5,
)

ExtractiveEngineFn = Callable[[list[str], Optional[int], Optional[float]], tuple[list[str], dict[str, Any]]]
AbstractiveEngineFn = Callable[[str, Optional[int], Optional[float]], tuple[str, dict[str, Any]]]
HybridEngineFn = Callable[
    [ProcessedInput, int, Optional[int], Optional[float]],
    tuple[list[str], dict[str, Any]],
]

class UnsupportedSummaryEngineError(RuntimeError):
    """Raised when a requested summary engine is not registered."""


class SummaryEngineNotReadyError(RuntimeError):
    """Raised when an engine exists in the roadmap but is not implemented yet."""


def _build_extractive_registry() -> dict[str, ExtractiveEngineFn]:
    return {
        "tfidf": summarize_with_tfidf,
        "textrank": summarize_with_textrank,
        "phobert-extractive": summarize_with_phobert_extractive,
    }


def _build_abstractive_registry() -> dict[str, AbstractiveEngineFn]:
    return {
        "vit5": summarize_with_vit5,
    }


def _summarize_hybrid_adapter(
    processed: ProcessedInput,
    target_k: int,
    max_sentences: int | None,
    ratio: float | None,
    length_meta: dict[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    return summarize_with_hybrid(
        cleaned_text=processed.cleaned_text,
        sentences=processed.sentences,
        target_k=target_k,
        max_sentences=max_sentences,
        ratio=ratio,
        length_tier=str(length_meta.get("length_tier") or ""),
        min_output_sentences=length_meta.get("min_output_sentences"),
    )


def _build_hybrid_registry() -> dict[str, HybridEngineFn]:
    return {"hybrid": _summarize_hybrid_adapter}


EXTRACTIVE_ENGINE_REGISTRY = _build_extractive_registry()
ABSTRACTIVE_ENGINE_REGISTRY = _build_abstractive_registry()
HYBRID_ENGINE_REGISTRY = _build_hybrid_registry()


def list_supported_summary_engines() -> list[str]:
    return sorted(
        set(EXTRACTIVE_ENGINE_REGISTRY)
        | set(ABSTRACTIVE_ENGINE_REGISTRY)
        | set(HYBRID_ENGINE_REGISTRY)
    )


def list_planned_summary_engines() -> list[str]:
    return sorted(set(PLANNED_SUMMARY_ENGINES))


def resolve_effective_max_sentences(max_sentences: int | None) -> int | None:
    """Apply server default when the client omits max_sentences (product/demo path)."""
    if max_sentences is not None:
        return max_sentences
    default = settings.summary_max_sentences
    if isinstance(default, int) and default >= 1:
        return default
    return None


def resolve_policy_target_k(
    processed: ProcessedInput,
    requested_max_sentences: int | None,
) -> tuple[int, dict[str, Any]]:
    requested = resolve_effective_max_sentences(requested_max_sentences)
    if requested is None:
        requested = 3
    return resolve_target_k_from_policy(
        requested,
        sentence_count=len(processed.sentences),
        char_length=len(processed.cleaned_text),
    )


def _is_abstractive_engine(engine_name: str) -> bool:
    return engine_name in ABSTRACTIVE_ENGINE_REGISTRY


def _is_hybrid_engine(engine_name: str) -> bool:
    return engine_name in HYBRID_ENGINE_REGISTRY


def resolve_summary_engine_name(engine_name: str | None = None) -> str:
    requested = (engine_name or settings.summary_engine).strip().lower()
    if (
        requested in EXTRACTIVE_ENGINE_REGISTRY
        or requested in ABSTRACTIVE_ENGINE_REGISTRY
        or requested in HYBRID_ENGINE_REGISTRY
    ):
        return requested

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
    Extractive: list of selected sentences. Abstractive: single-element list with generated summary.
    """
    resolved_engine_name = resolve_summary_engine_name(engine_name)
    effective_max_sentences = resolve_effective_max_sentences(max_sentences)
    target_k, length_meta = resolve_policy_target_k(processed, effective_max_sentences)

    _t0 = time.perf_counter()
    try:
        if _is_hybrid_engine(resolved_engine_name):
            selected_sentences, engine_meta = HYBRID_ENGINE_REGISTRY[resolved_engine_name](
                processed,
                target_k,
                effective_max_sentences,
                ratio,
                length_meta,
            )
        elif resolved_engine_name in ABSTRACTIVE_ENGINE_REGISTRY:
            summary_text, engine_meta = ABSTRACTIVE_ENGINE_REGISTRY[resolved_engine_name](
                processed.cleaned_text,
                max_sentences=target_k,
                ratio=ratio,
            )
            selected_sentences = [summary_text] if summary_text.strip() else []
        else:
            selected_sentences, engine_meta = EXTRACTIVE_ENGINE_REGISTRY[resolved_engine_name](
                processed.sentences,
                max_sentences=target_k,
                ratio=ratio,
            )
    except PhoBertEngineNotReadyError as exc:
        raise SummaryEngineNotReadyError(
            f"Summary engine 'phobert-extractive' is registered but not ready: {exc}"
        ) from exc
    except Vit5EngineNotReadyError as exc:
        raise SummaryEngineNotReadyError(
            f"Summary engine 'vit5' is registered but not ready: {exc}"
        ) from exc

    engine_meta = dict(engine_meta or {})
    engine_meta.setdefault("engine", resolved_engine_name)
    engine_meta.setdefault("resolved_target_k", target_k)
    engine_meta["length_policy"] = length_meta
    engine_meta["summarizer_latency_ms"] = round((time.perf_counter() - _t0) * 1000)
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
    effective_max_sentences = resolve_effective_max_sentences(max_sentences)
    target_k = engine_meta.get("resolved_target_k")
    return build_summary_response(
        processed=processed,
        selected_sentences=selected_sentences,
        max_sentences=effective_max_sentences,
        ratio=ratio,
        engine_name=resolved_engine_name,
        engine_meta=engine_meta,
        policy_target_k=target_k if isinstance(target_k, int) else None,
    )

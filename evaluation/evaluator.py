"""Unified metrics for summarization experiments (Phase 0 protocol)."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from statistics import mean, median, pstdev
from typing import Any, Callable, Iterable

from rouge_score import rouge_scorer

_TOKEN_BOUNDARY = re.compile(r"\s+", flags=re.UNICODE)


def _char_len(s: str) -> int:
    return len(s) if s else 0


def _normalize_light(text: str | None) -> str:
    """Light normalization for ROUGE-only comparison (whitespace collapse + strip)."""
    return " ".join(_TOKEN_BOUNDARY.split(_safe_to_text(text).strip()))


def _safe_to_text(value: Any) -> str:
    """Convert model output to safe text: None -> '', non-string -> str(value)."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def compression_ratio(source_text: str, summary_text: str) -> float:
    """Character-based compression ratio: len(summary_chars) / len(source_chars)."""
    src = _char_len(source_text)
    if src == 0:
        return 0.0
    return _char_len(summary_text) / float(src)


def repetition_rate(summary_text: str, n: int = 2) -> float:
    """
    n-gram repetition on whitespace-tokenized text.
    Formula: 1 - unique_ngrams / total_ngrams.
    Default n=2 (bigram repetition rate).
    This helper intentionally preserves original casing for Vietnamese summarization.
    Returns 0.0 when not enough tokens.
    """
    if not summary_text or n < 1:
        return 0.0
    tokens = [t for t in _TOKEN_BOUNDARY.split(summary_text.strip()) if t]
    if len(tokens) < n:
        return 0.0
    ngrams: list[tuple[str, ...]] = [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]
    total = len(ngrams)
    if total == 0:
        return 0.0
    unique = len(set(ngrams))
    return 1.0 - (unique / float(total))


@dataclass
class MetricBundle:
    rouge1_f: float
    rouge2_f: float
    rougeL_f: float
    latency_sec: float | None
    compression_ratio: float
    repetition_rate: float
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        out = {
            "rouge1_f": self.rouge1_f,
            "rouge2_f": self.rouge2_f,
            "rougeL_f": self.rougeL_f,
            "latency_sec": self.latency_sec,
            "compression_ratio": self.compression_ratio,
            "repetition_rate": self.repetition_rate,
        }
        out.update(self.extra)
        return out


@dataclass
class BatchEvaluation:
    per_sample: list[MetricBundle]
    aggregate: dict[str, float | int]

    def to_rows(self) -> list[dict[str, Any]]:
        """Export per-sample metrics (one dict per sample) for benchmark logging."""
        return [bundle.as_dict() for bundle in self.per_sample]


class Evaluator:
    """
    ROUGE (rouge-score), optional latency, compression ratio, repetition rate.
    ROUGE settings match configs/phase0_protocol.yaml (use_stemmer=False).
    NOTE: source/reference/prediction should be Phase 0 preprocessed text for fair comparison.
    Default normalize_before_rouge=False means evaluator does not alter text further.
    """

    def __init__(
        self,
        use_stemmer: bool = False,
        repetition_n: int = 2,
        normalize_before_rouge: bool = False,
    ) -> None:
        self._scorer = rouge_scorer.RougeScorer(
            ["rouge1", "rouge2", "rougeL"],
            use_stemmer=use_stemmer,
        )
        self._repetition_n = max(1, repetition_n)
        self._normalize_before_rouge = normalize_before_rouge

    def compute_rouge(self, reference: str, prediction: str) -> dict[str, float]:
        """Reference and prediction are single strings (e.g. gold abstract vs model summary)."""
        reference = _safe_to_text(reference)
        prediction = _safe_to_text(prediction)
        if self._normalize_before_rouge:
            reference = _normalize_light(reference)
            prediction = _normalize_light(prediction)
        scores = self._scorer.score(reference, prediction)
        return {
            "rouge1_f": scores["rouge1"].fmeasure,
            "rouge2_f": scores["rouge2"].fmeasure,
            "rougeL_f": scores["rougeL"].fmeasure,
        }

    def evaluate_one(
        self,
        *,
        source_text: str,
        reference_summary: str,
        predicted_summary: str,
        latency_sec: float | None = None,
        extra: dict[str, Any] | None = None,
    ) -> MetricBundle:
        source_text = _safe_to_text(source_text)
        reference_summary = _safe_to_text(reference_summary)
        predicted_summary = _safe_to_text(predicted_summary)
        rouge = self.compute_rouge(reference_summary, predicted_summary)
        return MetricBundle(
            rouge1_f=rouge["rouge1_f"],
            rouge2_f=rouge["rouge2_f"],
            rougeL_f=rouge["rougeL_f"],
            latency_sec=latency_sec,
            compression_ratio=compression_ratio(source_text, predicted_summary),
            repetition_rate=repetition_rate(predicted_summary, n=self._repetition_n),
            extra=extra or {},
        )

    def evaluate_with_timing(
        self,
        *,
        source_text: str,
        reference_summary: str,
        predict_fn: Callable[[str], Any],
    ) -> MetricBundle:
        """Runs predict_fn(source_text) and measures wall-clock latency."""
        t0 = time.perf_counter()
        predicted = _safe_to_text(predict_fn(source_text))
        latency = time.perf_counter() - t0
        return self.evaluate_one(
            source_text=source_text,
            reference_summary=reference_summary,
            predicted_summary=predicted,
            latency_sec=latency,
        )

    def evaluate_batch(self, samples: Iterable[dict[str, Any]]) -> BatchEvaluation:
        """
        Evaluate a batch of samples with keys:
        - source_text (required)
        - reference_summary (required)
        - predicted_summary (required)
        - latency_sec (optional)
        - extra (optional dict)
        Any other fields are preserved in per-sample `extra`.
        """
        bundles: list[MetricBundle] = []
        for sample in samples:
            user_extra = sample.get("extra")
            merged_extra: dict[str, Any] = {}
            if isinstance(user_extra, dict):
                merged_extra.update(user_extra)
            for key, value in sample.items():
                if key not in {"source_text", "reference_summary", "predicted_summary", "latency_sec", "extra"}:
                    merged_extra[key] = value
            bundles.append(
                self.evaluate_one(
                    source_text=sample.get("source_text", ""),
                    reference_summary=sample.get("reference_summary", ""),
                    predicted_summary=sample.get("predicted_summary", ""),
                    latency_sec=sample.get("latency_sec"),
                    extra=merged_extra,
                )
            )
        return BatchEvaluation(per_sample=bundles, aggregate=aggregate_metrics(bundles))


def aggregate_metrics(bundles: list[MetricBundle]) -> dict[str, float | int]:
    """Aggregate stats over bundles: num_samples, mean/median/std, and latency stats."""
    if not bundles:
        return {"num_samples": 0}
    keys = ["rouge1_f", "rouge2_f", "rougeL_f", "compression_ratio", "repetition_rate"]
    out: dict[str, float | int] = {"num_samples": len(bundles)}
    for k in keys:
        vals = [b.as_dict()[k] for b in bundles]
        out[f"mean_{k}"] = mean(vals)
        out[f"median_{k}"] = median(vals)
        out[f"std_{k}"] = pstdev(vals) if len(vals) > 1 else 0.0
    latencies = [b.latency_sec for b in bundles if b.latency_sec is not None]
    if latencies:
        out["num_latency_samples"] = len(latencies)
        out["mean_latency_sec"] = mean(latencies)
        out["median_latency_sec"] = median(latencies)
        out["std_latency_sec"] = pstdev(latencies) if len(latencies) > 1 else 0.0
    return out


def aggregate_means(bundles: list[MetricBundle]) -> dict[str, float | int]:
    """Backward-compatible alias. Prefer `aggregate_metrics`."""
    return aggregate_metrics(bundles)

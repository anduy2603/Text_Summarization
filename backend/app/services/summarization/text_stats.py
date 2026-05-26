"""Reference-free summary stats (aligned with evaluation/evaluator.repetition_rate)."""

from __future__ import annotations

import re

_TOKEN_BOUNDARY = re.compile(r"\s+", flags=re.UNICODE)


def repetition_rate(summary_text: str, n: int = 2) -> float:
    """
    Bigram repetition: 1 - unique_ngrams / total_ngrams.
    Matches evaluation.evaluator.repetition_rate defaults.
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

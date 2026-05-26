from __future__ import annotations

import math
from typing import Any


def _resolve_target_k(
    sentence_count: int,
    max_sentences: int | None,
    ratio: float | None,
) -> tuple[int, dict[str, Any]]:
    """
    Resolve final sentence count using one of two modes:
    - top-k mode: explicit max_sentences
    - ratio mode: k = max(1, ceil(ratio * sentence_count))
    Priority: max_sentences (if provided) > ratio > default.
    """
    if sentence_count <= 0:
        return 0, {"selection_mode": "empty-input"}

    if isinstance(max_sentences, int):
        k = max(1, min(max_sentences, sentence_count))
        return k, {
            "selection_mode": "max_sentences",
            "requested_max_sentences": max_sentences,
        }

    if ratio is not None and 0.0 < ratio <= 1.0:
        k = max(1, math.ceil(ratio * sentence_count))
        return min(k, sentence_count), {
            "selection_mode": "ratio",
            "requested_ratio": ratio,
        }

    k = min(3, sentence_count)
    return k, {
        "selection_mode": "fallback-default",
        "requested_max_sentences": 3,
    }

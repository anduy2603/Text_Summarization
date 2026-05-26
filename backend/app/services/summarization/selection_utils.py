from __future__ import annotations

import math
from collections import Counter
from typing import Any


def cosine_similarity_tokens(tokens_a: list[str], tokens_b: list[str]) -> float:
    if not tokens_a or not tokens_b:
        return 0.0
    tf_a = Counter(tokens_a)
    tf_b = Counter(tokens_b)
    dot = 0.0
    for token in set(tf_a).intersection(tf_b):
        dot += float(tf_a[token] * tf_b[token])
    norm_a = math.sqrt(sum(float(v * v) for v in tf_a.values()))
    norm_b = math.sqrt(sum(float(v * v) for v in tf_b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def position_boost(index: int, total: int, strength: float) -> float:
    if total <= 0 or strength <= 0.0:
        return 1.0
    decay = max(1.0, total * 0.25)
    return 1.0 + strength * math.exp(-index / decay)


def select_indices_mmr(
    scored: list[tuple[int, float]],
    tokenized_sentences: list[list[str]],
    k: int,
    *,
    lambda_param: float = 0.7,
    position_bias_strength: float = 0.12,
) -> list[int]:
    """
    Maximal Marginal Relevance on TextRank scores with light lead bias for news articles.
    """
    if k <= 0 or not scored:
        return []
    remaining = list(scored)
    selected: list[int] = []
    total = len(tokenized_sentences)

    while remaining and len(selected) < k:
        best_idx: int | None = None
        best_value = float("-inf")
        for idx, relevance in remaining:
            if selected:
                redundancy = max(
                    cosine_similarity_tokens(tokenized_sentences[idx], tokenized_sentences[s])
                    for s in selected
                )
            else:
                redundancy = 0.0
            mmr = lambda_param * relevance - (1.0 - lambda_param) * redundancy
            mmr *= position_boost(idx, total, position_bias_strength)
            if mmr > best_value:
                best_value = mmr
                best_idx = idx
        if best_idx is None:
            break
        selected.append(best_idx)
        remaining = [(i, s) for i, s in remaining if i != best_idx]

    return sorted(selected)

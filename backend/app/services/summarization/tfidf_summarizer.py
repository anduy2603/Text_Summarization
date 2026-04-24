from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

_TOKEN_RE = re.compile(r"[^\W_]+", flags=re.UNICODE)
_STOPWORDS = {
    "và",
    "là",
    "của",
    "cho",
    "với",
    "trong",
    "trên",
    "dưới",
    "tại",
    "từ",
    "đến",
    "các",
    "những",
    "một",
    "này",
    "đó",
    "khi",
    "đã",
    "đang",
    "về",
}


def _tokenize(text: str) -> list[str]:
    """
    Keep alphanumeric tokens so years, percentages, quantities, and identifiers
    remain available to the TF-IDF baseline for news-domain ranking.
    """
    tokens = [token.lower() for token in _TOKEN_RE.findall(text)]
    return [token for token in tokens if token not in _STOPWORDS]


def _build_idf(tokenized_sentences: list[list[str]]) -> dict[str, float]:
    sentence_count = len(tokenized_sentences)
    doc_freq: Counter[str] = Counter()
    for tokens in tokenized_sentences:
        if tokens:
            doc_freq.update(set(tokens))
    idf: dict[str, float] = {}
    for token, df in doc_freq.items():
        # Smoothed IDF to avoid division by zero on tiny inputs.
        idf[token] = math.log((1.0 + sentence_count) / (1.0 + df)) + 1.0
    return idf


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


def summarize_with_tfidf(
    sentences: list[str],
    max_sentences: int | None = None,
    ratio: float | None = None,
) -> tuple[list[str], dict[str, Any]]:
    """
    TF-IDF extractive summarization pipeline:
    1) Receive a sentence list.
    2) Vectorize each sentence with TF-IDF (dict token -> tf-idf weight).
    3) Compute sentence score = sum(tf-idf weights) from sentence vector.
    4) Select top-k by score descending (tie-break by lower original index).
    5) Re-sort selected sentence indices by original order for natural summary flow.
    """
    if not sentences:
        return [], {"engine": "tfidf", "strategy": "empty-input"}

    k, select_meta = _resolve_target_k(
        sentence_count=len(sentences),
        max_sentences=max_sentences,
        ratio=ratio,
    )
    tokenized = [_tokenize(sentence) for sentence in sentences]
    if not any(tokenized):
        return sentences[:k], {
            "engine": "tfidf",
            "strategy": "lead-fallback",
            "reason": "no-tokens",
            **select_meta,
            "resolved_target_k": k,
            "selected_indices_by_score": list(range(k)),
            "selected_indices": list(range(k)),
        }

    idf = _build_idf(tokenized)
    scored: list[tuple[int, float]] = []
    for idx, tokens in enumerate(tokenized):
        tf = Counter(tokens)
        length = len(tokens)
        if length == 0:
            scored.append((idx, 0.0))
            continue
        # Explicit TF-IDF vector per sentence.
        vector = {token: (count / length) * idf.get(token, 0.0) for token, count in tf.items()}
        scored.append((idx, sum(vector.values())))

    # Select by score descending; stable tie-break by original index.
    top_ranked = sorted(scored, key=lambda item: (-item[1], item[0]))[:k]
    selected_indices_by_score = [idx for idx, _ in top_ranked]
    # Restore original order for readable summary.
    selected_indices = sorted(idx for idx, _ in top_ranked)
    selected_sentences = [sentences[idx] for idx in selected_indices]

    return selected_sentences, {
        "engine": "tfidf",
        "strategy": "tfidf-sentence-ranking",
        **select_meta,
        "resolved_target_k": k,
        "sentence_scores": [{"index": idx, "score": score} for idx, score in scored],
        "selected_indices_by_score": selected_indices_by_score,
        "selected_indices": selected_indices,
    }

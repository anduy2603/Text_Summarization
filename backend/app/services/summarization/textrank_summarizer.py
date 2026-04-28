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
    tokens = [token.lower() for token in _TOKEN_RE.findall(text)]
    return [token for token in tokens if token not in _STOPWORDS]


def _resolve_target_k(
    sentence_count: int,
    max_sentences: int | None,
    ratio: float | None,
) -> tuple[int, dict[str, Any]]:
    if sentence_count <= 0:
        return 0, {"selection_mode": "empty-input"}
    if isinstance(max_sentences, int):
        k = max(1, min(max_sentences, sentence_count))
        return k, {"selection_mode": "max_sentences", "requested_max_sentences": max_sentences}
    if ratio is not None and 0.0 < ratio <= 1.0:
        k = max(1, math.ceil(ratio * sentence_count))
        return min(k, sentence_count), {"selection_mode": "ratio", "requested_ratio": ratio}
    k = min(3, sentence_count)
    return k, {"selection_mode": "fallback-default", "requested_max_sentences": 3}


def _cosine_similarity(tokens_a: list[str], tokens_b: list[str]) -> float:
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


def _build_similarity_graph(tokenized_sentences: list[list[str]]) -> list[list[float]]:
    n = len(tokenized_sentences)
    graph = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            sim = _cosine_similarity(tokenized_sentences[i], tokenized_sentences[j])
            graph[i][j] = sim
            graph[j][i] = sim
    return graph


def _run_pagerank(
    graph: list[list[float]],
    damping: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-6,
) -> list[float]:
    n = len(graph)
    if n == 0:
        return []
    scores = [1.0 / n] * n
    out_weights = [sum(row) for row in graph]
    for _ in range(max_iter):
        next_scores = [(1.0 - damping) / n for _ in range(n)]
        for j in range(n):
            if out_weights[j] == 0.0:
                # Distribute dangling node mass uniformly.
                share = damping * scores[j] / n
                for i in range(n):
                    next_scores[i] += share
                continue
            for i in range(n):
                w_ji = graph[j][i]
                if w_ji > 0.0:
                    next_scores[i] += damping * scores[j] * (w_ji / out_weights[j])
        diff = sum(abs(next_scores[i] - scores[i]) for i in range(n))
        scores = next_scores
        if diff < tol:
            break
    return scores


def summarize_with_textrank(
    sentences: list[str],
    max_sentences: int | None = None,
    ratio: float | None = None,
) -> tuple[list[str], dict[str, Any]]:
    if not sentences:
        return [], {"engine": "textrank", "strategy": "empty-input"}

    k, select_meta = _resolve_target_k(
        sentence_count=len(sentences),
        max_sentences=max_sentences,
        ratio=ratio,
    )
    tokenized = [_tokenize(sentence) for sentence in sentences]
    if not any(tokenized):
        return sentences[:k], {
            "engine": "textrank",
            "strategy": "lead-fallback",
            "reason": "no-tokens",
            **select_meta,
            "resolved_target_k": k,
            "selected_indices_by_score": list(range(k)),
            "selected_indices": list(range(k)),
        }

    graph = _build_similarity_graph(tokenized)
    scores = _run_pagerank(graph)
    scored = list(enumerate(scores))
    top_ranked = sorted(scored, key=lambda item: (-item[1], item[0]))[:k]
    selected_indices_by_score = [idx for idx, _ in top_ranked]
    selected_indices = sorted(selected_indices_by_score)
    selected_sentences = [sentences[idx] for idx in selected_indices]

    return selected_sentences, {
        "engine": "textrank",
        "strategy": "textrank-sentence-graph",
        "similarity_strategy": "cosine-tf",
        **select_meta,
        "resolved_target_k": k,
        "sentence_scores": [{"index": idx, "score": score} for idx, score in scored],
        "selected_indices_by_score": selected_indices_by_score,
        "selected_indices": selected_indices,
    }

from __future__ import annotations

import math
import re
from collections import Counter

_TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


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


def _score_sentence(tokens: list[str], idf: dict[str, float]) -> float:
    if not tokens:
        return 0.0
    tf = Counter(tokens)
    length = len(tokens)
    score = 0.0
    for token, count in tf.items():
        score += (count / length) * idf.get(token, 0.0)
    return score


def summarize_with_tfidf(sentences: list[str], max_sentences: int) -> tuple[list[str], dict]:
    """
    Rank sentences with TF-IDF and return selected sentences in original order.
    """
    if not sentences:
        return [], {"strategy": "empty-input"}

    k = max(1, min(max_sentences, len(sentences)))
    tokenized = [_tokenize(sentence) for sentence in sentences]
    if not any(tokenized):
        return sentences[:k], {"strategy": "lead-fallback", "reason": "no-tokens"}

    idf = _build_idf(tokenized)
    scored: list[tuple[int, float]] = []
    for idx, tokens in enumerate(tokenized):
        scored.append((idx, _score_sentence(tokens, idf)))

    top_ranked = sorted(scored, key=lambda item: (-item[1], item[0]))[:k]
    selected_indices = sorted(idx for idx, _ in top_ranked)
    selected_sentences = [sentences[idx] for idx in selected_indices]

    return selected_sentences, {
        "strategy": "tfidf-sentence-ranking",
        "selected_indices": selected_indices,
    }

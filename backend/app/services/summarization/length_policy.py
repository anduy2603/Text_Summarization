from __future__ import annotations

from typing import Any

from app.services.summarization.summary_length import resolve_min_output_sentences

_SHORT_DOC_CHARS = 1_500
_MEDIUM_DOC_CHARS = 6_000
_MAX_OUTPUT_SENTENCES = 8


def resolve_target_k_from_policy(
    requested_max_sentences: int,
    *,
    sentence_count: int,
    char_length: int,
) -> tuple[int, dict[str, Any]]:
    """
    Respect the user's requested sentence count exactly.
    delta was removed — silently adding +1/+2 caused user to receive more
    sentences than requested, undermining trust in length controls.
    """
    requested = max(1, int(requested_max_sentences))
    if char_length < _SHORT_DOC_CHARS:
        tier = "short"
    elif char_length < _MEDIUM_DOC_CHARS:
        tier = "medium"
    else:
        tier = "long"

    k = min(requested, _MAX_OUTPUT_SENTENCES)
    if sentence_count > 0:
        k = min(k, sentence_count)
    k = max(1, k)

    min_output_sentences = resolve_min_output_sentences(k, tier)

    return k, {
        "length_policy": "user_requested_exact",
        "length_tier": tier,
        "requested_max_sentences": requested,
        "doc_char_length": char_length,
        "resolved_target_k": k,
        "min_output_sentences": min_output_sentences,
    }

from __future__ import annotations

from typing import Any


def summarize_with_textrank(
    sentences: list[str],
    max_sentences: int | None = None,
    ratio: float | None = None,
) -> tuple[list[str], dict[str, Any]]:
    """
    Placeholder for the upcoming TextRank implementation.
    Keep the same callable shape as other engines so it plugs into the registry directly.
    """
    raise NotImplementedError(
        "TextRank summarizer is not implemented yet. Register the final algorithm here."
    )

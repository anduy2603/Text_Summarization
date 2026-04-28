"""Shared preprocessing for experiments — delegates to backend (Phase 0 protocol)."""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.services.input.cleaner import clean_text  # noqa: E402
from app.services.input.normalizer import normalize_text  # noqa: E402
from app.services.input.sentence_splitter import split_sentences  # noqa: E402

PROTOCOL_PREPROCESS_VERSION = "phase0_v2"


def preprocess_document(text: str | None) -> str:
    """clean_text → normalize_text (same order as input pipeline before splitting)."""
    safe_text = text if isinstance(text, str) else ""
    return normalize_text(clean_text(safe_text))


def preprocess_and_split(text: str | None) -> tuple[str, list[str]]:
    """Returns normalized document text and sentence list for evaluation / extractive models."""
    normalized = preprocess_document(text)
    if not normalized:
        return "", []
    sentences = split_sentences(normalized)
    return normalized, sentences

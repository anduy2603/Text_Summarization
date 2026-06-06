from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

import numpy as np

from app.services.summarization.engine_utils import _resolve_target_k
from app.services.summarization.model_utils import _set_huggingface_offline

PHOBERT_MODEL_NAME = "vinai/phobert-base-v2"
PHOBERT_SENTENCE_BATCH_SIZE = 8
PHOBERT_ALLOW_DOWNLOAD_ENV = "PHOBERT_ALLOW_DOWNLOAD"


class PhoBertEngineNotReadyError(RuntimeError):
    """Raised when PhoBERT dependencies/model weights are unavailable."""


def _load_phobert_from_cache() -> tuple[Any, Any]:
    from transformers import AutoTokenizer, RobertaModel

    tokenizer = AutoTokenizer.from_pretrained(
        PHOBERT_MODEL_NAME,
        local_files_only=True,
    )
    # Encoder-only: checkpoint is MLM (lm_head ignored); we mean-pool last_hidden_state, not pooler.
    model = RobertaModel.from_pretrained(
        PHOBERT_MODEL_NAME,
        local_files_only=True,
        use_safetensors=False,
        add_pooling_layer=False,
    )
    return tokenizer, model


def _load_phobert_online() -> tuple[Any, Any]:
    from transformers import AutoTokenizer, RobertaModel

    tokenizer = AutoTokenizer.from_pretrained(PHOBERT_MODEL_NAME)
    model = RobertaModel.from_pretrained(
        PHOBERT_MODEL_NAME,
        use_safetensors=False,
        add_pooling_layer=False,
    )
    return tokenizer, model


# Module-level cache — only populated on successful load; never caches failures.
# Use _clear_phobert_runtime_cache() in tests or to force a reload after env changes.
_phobert_runtime_cache: tuple[Any, Any, Any, Any] | None = None


def _get_phobert_runtime() -> tuple[Any, Any, Any, Any]:
    global _phobert_runtime_cache
    if _phobert_runtime_cache is not None:
        return _phobert_runtime_cache

    allow_download = os.environ.get(PHOBERT_ALLOW_DOWNLOAD_ENV) == "1"
    if not allow_download:
        _set_huggingface_offline()

    try:
        import torch
    except Exception as exc:  # pragma: no cover - environment dependent
        hint = (
            "PhoBERT engine requires `torch` and `transformers` to be installed "
            "and importable in this environment."
        )
        root = exc
        while getattr(root, "__cause__", None) is not None:
            root = root.__cause__
        root_msg = str(root).strip()
        if root_msg and root_msg not in hint:
            hint = f"{hint} Root error: {type(root).__name__}: {root_msg}"
        raise PhoBertEngineNotReadyError(hint) from exc

    try:
        if allow_download:
            tokenizer, model = _load_phobert_online()
        else:
            tokenizer, model = _load_phobert_from_cache()
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.eval()
    except Exception as exc:  # pragma: no cover - environment dependent
        download_hint = (
            f"Set {PHOBERT_ALLOW_DOWNLOAD_ENV}=1 to allow a one-time HuggingFace download "
            "when internet access is available."
        )
        raise PhoBertEngineNotReadyError(
            f"Unable to load PhoBERT model '{PHOBERT_MODEL_NAME}'. "
            f"Check local HuggingFace cache. {download_hint}"
        ) from exc

    _phobert_runtime_cache = (tokenizer, model, torch, device)
    return _phobert_runtime_cache


def _clear_phobert_runtime_cache() -> None:
    """Reset the runtime cache, forcing a reload on next call. Used in tests."""
    global _phobert_runtime_cache
    _phobert_runtime_cache = None


def _encode_sentences(sentences: list[str]) -> np.ndarray:
    tokenizer, model, torch, device = _get_phobert_runtime()
    batches: list[np.ndarray] = []
    for start in range(0, len(sentences), PHOBERT_SENTENCE_BATCH_SIZE):
        batch = sentences[start : start + PHOBERT_SENTENCE_BATCH_SIZE]
        encoded = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="pt",
        )
        encoded = {k: v.to(device) for k, v in encoded.items()}
        with torch.no_grad():
            outputs = model(**encoded)
            hidden = outputs.last_hidden_state
            mask = encoded["attention_mask"].unsqueeze(-1).float()
            summed = (hidden * mask).sum(dim=1)
            denom = mask.sum(dim=1).clamp(min=1e-9)
            sentence_embeddings = summed / denom
        batches.append(sentence_embeddings.cpu().numpy())
    return np.concatenate(batches, axis=0) if batches else np.empty((0, 0), dtype=np.float32)


@lru_cache(maxsize=1)
def _resolve_segmenter() -> tuple[Any | None, str]:
    try:
        from pyvi import ViTokenizer
    except Exception as exc:
        raise PhoBertEngineNotReadyError(
            "PhoBERT engine requires `pyvi` word segmentation for reproducible benchmarking."
        ) from exc
    return ViTokenizer, "pyvi-vitokenizer"


def _segment_for_phobert(sentences: list[str]) -> tuple[list[str], dict[str, Any]]:
    segmenter, method = _resolve_segmenter()
    segmented: list[str] = []
    before_tokens = 0
    after_tokens = 0
    for sentence in sentences:
        clean = sentence.strip()
        before_tokens += len(clean.split())
        if segmenter is None:
            seg = clean
        else:
            seg = str(segmenter.tokenize(clean))
        segmented.append(seg)
        after_tokens += len(seg.split())
    return segmented, {
        "sentence_segmentation": method,
        "token_count_before_segmentation": before_tokens,
        "token_count_after_segmentation": after_tokens,
    }


def _cosine_similarity_rows(matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
    vec_norm = np.linalg.norm(vector)
    mat_norm = np.linalg.norm(matrix, axis=1)
    denom = np.clip(vec_norm * mat_norm, a_min=1e-12, a_max=None)
    return np.dot(matrix, vector) / denom


def summarize_with_phobert_extractive(
    sentences: list[str],
    max_sentences: int | None = None,
    ratio: float | None = None,
) -> tuple[list[str], dict[str, Any]]:
    if not sentences:
        return [], {"engine": "phobert-extractive", "strategy": "empty-input"}

    k, select_meta = _resolve_target_k(
        sentence_count=len(sentences),
        max_sentences=max_sentences,
        ratio=ratio,
    )

    clean_sentences = [sentence.strip() for sentence in sentences]
    if not any(clean_sentences):
        return sentences[:k], {
            "engine": "phobert-extractive",
            "strategy": "lead-fallback",
            "reason": "no-non-empty-sentences",
            **select_meta,
            "resolved_target_k": k,
            "selected_indices_by_score": list(range(k)),
            "selected_indices": list(range(k)),
        }

    segmented_sentences, preprocessing_meta = _segment_for_phobert(clean_sentences)
    embeddings = _encode_sentences(segmented_sentences)
    document_vector = embeddings.mean(axis=0)
    scores = _cosine_similarity_rows(embeddings, document_vector)

    scored = [(idx, float(score)) for idx, score in enumerate(scores.tolist())]
    top_ranked = sorted(scored, key=lambda item: (-item[1], item[0]))[:k]
    selected_indices_by_score = [idx for idx, _ in top_ranked]
    selected_indices = sorted(selected_indices_by_score)
    selected_sentences = [sentences[idx] for idx in selected_indices]

    return selected_sentences, {
        "engine": "phobert-extractive",
        "strategy": "phobert-sentence-document-similarity",
        "model_name": PHOBERT_MODEL_NAME,
        "sentence_batch_size": PHOBERT_SENTENCE_BATCH_SIZE,
        "preprocessing": preprocessing_meta,
        **select_meta,
        "resolved_target_k": k,
        "sentence_scores": [{"index": idx, "score": score} for idx, score in scored],
        "selected_indices_by_score": selected_indices_by_score,
        "selected_indices": selected_indices,
    }

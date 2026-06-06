from __future__ import annotations

import os
from typing import Any

from app.core.config import settings
from app.services.summarization.model_utils import _set_huggingface_offline

VIT5_ALLOW_DOWNLOAD_ENV = "VIT5_ALLOW_DOWNLOAD"
# ViT5 tokenizer.json triggers KeyError/TypeError on transformers 5.x (see HF PR #44452).


def _check_transformers_version() -> None:
    try:
        import transformers

        major = int(transformers.__version__.split(".", maxsplit=1)[0])
    except Exception as exc:  # pragma: no cover
        raise Vit5EngineNotReadyError("Cannot determine `transformers` version.") from exc
    if major >= 5:
        raise Vit5EngineNotReadyError(
            f"ViT5 engine requires transformers 4.x (installed {transformers.__version__}). "
            "Upgrade/downgrade with: pip install 'transformers>=4.46.3,<5.0.0'"
        )


class Vit5EngineNotReadyError(RuntimeError):
    """Raised when ViT5 dependencies or model weights are unavailable."""


def _load_vit5_from_cache() -> tuple[Any, Any]:
    from transformers import AutoModelForSeq2SeqLM, T5Tokenizer

    tokenizer = T5Tokenizer.from_pretrained(
        settings.vit5_model_name,
        local_files_only=True,
    )
    model = AutoModelForSeq2SeqLM.from_pretrained(
        settings.vit5_model_name,
        local_files_only=True,
        use_safetensors=False,
    )
    return tokenizer, model


def _load_vit5_online() -> tuple[Any, Any]:
    from transformers import AutoModelForSeq2SeqLM, T5Tokenizer

    tokenizer = T5Tokenizer.from_pretrained(settings.vit5_model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        settings.vit5_model_name,
        use_safetensors=False,
    )
    return tokenizer, model


def resolve_max_new_tokens(max_sentences: int | None, ratio: float | None) -> tuple[int, dict[str, Any]]:
    """Map API max_sentences to decoder budget (abstractive has no source sentence pick)."""
    if isinstance(max_sentences, int) and max_sentences >= 1:
        per_sentence = max(48, settings.vit5_tokens_per_sentence)
        cap = settings.vit5_max_new_tokens
        tokens = min(cap, max_sentences * per_sentence)
        return tokens, {
            "length_control": "max_sentences_to_tokens",
            "requested_max_sentences": max_sentences,
            "resolved_max_new_tokens": tokens,
        }
    if ratio is not None and 0.0 < ratio <= 1.0:
        cap = settings.vit5_max_new_tokens
        tokens = max(48, min(cap, int(cap * ratio)))
        return tokens, {
            "length_control": "ratio_to_tokens",
            "requested_ratio": ratio,
            "resolved_max_new_tokens": tokens,
        }
    default = min(settings.vit5_max_new_tokens, 2 * settings.vit5_tokens_per_sentence)
    return default, {
        "length_control": "default-token-budget",
        "resolved_max_new_tokens": default,
    }


def resolve_generation_length_bounds(
    max_sentences: int | None,
    ratio: float | None,
    *,
    hybrid_lead: bool = False,
) -> tuple[int, int | None, dict[str, Any]]:
    """
    Decoder token budget. Hybrid lead uses a low max cap and never sets min_new_tokens
    (forcing min length causes hallucination / mojibake on ViT5).
    """
    if hybrid_lead:
        lead_sents = min(
            settings.vit5_lead_max_sentences,
            max_sentences if isinstance(max_sentences, int) and max_sentences >= 1 else 2,
        )
        per = max(40, settings.vit5_tokens_per_sentence)
        max_new_tokens = min(settings.vit5_max_new_tokens, lead_sents * per)
        return max_new_tokens, None, {
            "length_control": "hybrid-lead-cap",
            "generation_profile": "hybrid_lead",
            "requested_max_sentences": lead_sents,
            "resolved_max_new_tokens": max_new_tokens,
            "resolved_min_new_tokens": None,
        }

    max_new_tokens, meta = resolve_max_new_tokens(max_sentences, ratio)
    meta["generation_profile"] = "default"
    meta["resolved_min_new_tokens"] = None
    return max_new_tokens, None, meta


# Module-level cache — only populated on successful load; never caches failures.
# Use _clear_vit5_runtime_cache() in tests or to force a reload after env changes.
_vit5_runtime_cache: tuple[Any, Any, Any, Any] | None = None


def _get_vit5_runtime() -> tuple[Any, Any, Any, Any]:
    global _vit5_runtime_cache
    if _vit5_runtime_cache is not None:
        return _vit5_runtime_cache

    _check_transformers_version()
    allow_download = os.environ.get(VIT5_ALLOW_DOWNLOAD_ENV) == "1"
    if not allow_download:
        _set_huggingface_offline()

    try:
        import torch
    except Exception as exc:  # pragma: no cover - environment dependent
        hint = (
            "ViT5 engine requires `torch` and `transformers` to be installed "
            "and importable in this environment."
        )
        root = exc
        while getattr(root, "__cause__", None) is not None:
            root = root.__cause__
        root_msg = str(root).strip()
        if root_msg and root_msg not in hint:
            hint = f"{hint} Root error: {type(root).__name__}: {root_msg}"
        raise Vit5EngineNotReadyError(hint) from exc

    try:
        if allow_download:
            tokenizer, model = _load_vit5_online()
        else:
            tokenizer, model = _load_vit5_from_cache()
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.eval()
    except Exception as exc:  # pragma: no cover - environment dependent
        download_hint = (
            f"Set {VIT5_ALLOW_DOWNLOAD_ENV}=1 to allow a one-time HuggingFace download "
            "when internet access is available."
        )
        raise Vit5EngineNotReadyError(
            f"Unable to load ViT5 model '{settings.vit5_model_name}'. "
            f"Check local HuggingFace cache. {download_hint}"
        ) from exc

    _vit5_runtime_cache = (tokenizer, model, torch, device)
    return _vit5_runtime_cache


def _clear_vit5_runtime_cache() -> None:
    """Reset the runtime cache, forcing a reload on next call. Used in tests."""
    global _vit5_runtime_cache
    _vit5_runtime_cache = None


def summarize_with_vit5(
    cleaned_text: str,
    max_sentences: int | None = None,
    ratio: float | None = None,
    *,
    hybrid_lead: bool = False,
) -> tuple[str, dict[str, Any]]:
    """
    Abstractive summarization with VietAI ViT5 (VietNews fine-tune).
    Returns generated summary text and engine metadata.
    """
    text = cleaned_text.strip()
    if not text:
        return "", {
            "engine": "vit5",
            "strategy": "empty-input",
            "method": "abstractive",
        }

    max_new_tokens, min_new_tokens, length_meta = resolve_generation_length_bounds(
        max_sentences,
        ratio,
        hybrid_lead=hybrid_lead,
    )
    tokenizer, model, torch, device = _get_vit5_runtime()

    model_input = text if text.endswith("</s>") else f"{text}</s>"
    encoded = tokenizer(
        model_input,
        return_tensors="pt",
        truncation=True,
        max_length=settings.vit5_max_input_tokens,
    )
    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)
    input_token_count = int(input_ids.shape[1])
    source_char_len = len(text)

    gen_kwargs: dict[str, Any] = {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "max_new_tokens": max_new_tokens,
        "num_beams": settings.vit5_num_beams,
        "early_stopping": True,
        "no_repeat_ngram_size": 3,
    }
    if min_new_tokens is not None and min_new_tokens > 0:
        gen_kwargs["min_new_tokens"] = min_new_tokens

    with torch.no_grad():
        outputs = model.generate(**gen_kwargs)

    summary = tokenizer.decode(outputs[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)
    summary = summary.strip()

    truncated = input_token_count >= settings.vit5_max_input_tokens

    from app.services.summarization.summary_length import count_sentences

    out_sents = count_sentences(summary)

    return summary, {
        "engine": "vit5",
        "strategy": "vit5-seq2seq-generate",
        "method": "abstractive",
        "model_name": settings.vit5_model_name,
        "input_truncation": "head" if truncated else "none",
        "input_tokens_used": input_token_count,
        "source_char_length": source_char_len,
        "summary_char_length": len(summary),
        "output_sentence_count": out_sents,
        "resolved_target_k": out_sents if out_sents else (1 if summary else 0),
        "selected_sentence_count": out_sents if out_sents else (1 if summary else 0),
        **length_meta,
    }

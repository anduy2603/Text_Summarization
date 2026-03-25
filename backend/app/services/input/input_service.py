from __future__ import annotations

from pathlib import PurePath

from app.services.input import cleaner, normalizer, sentence_splitter
from app.services.input.exceptions import InputLoadError, InputValidationError
from app.services.input.loaders import load_docx_bytes, load_pdf_bytes, load_txt_bytes, load_url_text
from app.services.input.validator import validate_file_size, validate_filename, validate_non_empty_text
from app.schemas.input import ProcessedInput, SourceType


def _run_text_pipeline(raw: str, source_type: SourceType, extra_meta: dict | None = None) -> ProcessedInput:
    cleaned = cleaner.clean_text(raw)
    normalized = normalizer.normalize_text(cleaned)
    if not normalized:
        raise InputValidationError("No text content after cleaning.")
    sents = sentence_splitter.split_sentences(normalized)
    meta = {
        "raw_char_length": len(raw),
        "cleaned_char_length": len(normalized),
        "sentence_count": len(sents),
        **(extra_meta or {}),
    }
    return ProcessedInput(
        cleaned_text=normalized,
        sentences=sents,
        source_type=source_type,
        metadata=meta,
    )


def process_from_text(text: str) -> ProcessedInput:
    raw = validate_non_empty_text(text, label="Text")
    return _run_text_pipeline(raw, "text")


def process_from_bytes(filename: str, content: bytes) -> ProcessedInput:
    name = validate_filename(filename)
    validate_file_size(len(content))
    suffix = PurePath(name).suffix.lower()
    if suffix == ".txt":
        raw = load_txt_bytes(content)
        st: SourceType = "txt"
    elif suffix == ".docx":
        raw = load_docx_bytes(content)
        st = "docx"
    elif suffix == ".pdf":
        raw = load_pdf_bytes(content)
        st = "pdf"
    else:
        raise InputValidationError(f"Unhandled extension {suffix!r}.")
    return _run_text_pipeline(raw, st, extra_meta={"filename": name})


def process_from_url(url: str) -> ProcessedInput:
    raw, ctype = load_url_text(url)
    return _run_text_pipeline(
        raw,
        "url",
        extra_meta={"content_type": ctype, "url": url.strip()},
    )

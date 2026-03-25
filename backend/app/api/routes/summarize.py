from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.schemas.common import SummarizeRequest, SummarizeResponse
from app.schemas.input import ProcessedInput, UrlIngestRequest
from app.services.input import (
    InputLoadError,
    InputValidationError,
    process_from_bytes,
    process_from_text,
    process_from_url,
)

router = APIRouter()


def _skeleton_summary(processed: ProcessedInput, max_sentences: int) -> SummarizeResponse:
    text = processed.cleaned_text
    preview = text[:240]
    if len(text) > 240:
        preview += "..."

    return SummarizeResponse(
        summary=preview if preview else "No content provided.",
        metadata={
            "engine": "skeleton-echo",
            "target_sentences": max_sentences,
            "source_type": processed.source_type,
            "sentence_count": len(processed.sentences),
            "cleaned_char_length": len(processed.cleaned_text),
            "input_metadata": processed.metadata,
        },
    )


def _map_input_errors(exc: Exception) -> HTTPException:
    if isinstance(exc, InputValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, InputLoadError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail="Unexpected input error.")


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(payload: SummarizeRequest) -> SummarizeResponse:
    try:
        processed = process_from_text(payload.text)
    except (InputValidationError, InputLoadError) as exc:
        raise _map_input_errors(exc) from exc
    return _skeleton_summary(processed, payload.max_sentences)


@router.post("/summarize/file", response_model=SummarizeResponse)
async def summarize_file(
    file: UploadFile = File(...),
    max_sentences: int = Query(default=3, ge=1, le=20),
) -> SummarizeResponse:
    content = await file.read()
    try:
        processed = process_from_bytes(file.filename or "", content)
    except (InputValidationError, InputLoadError) as exc:
        raise _map_input_errors(exc) from exc
    return _skeleton_summary(processed, max_sentences)


@router.post("/summarize/url", response_model=SummarizeResponse)
async def summarize_url(
    payload: UrlIngestRequest,
    max_sentences: int = Query(default=3, ge=1, le=20),
) -> SummarizeResponse:
    try:
        processed = process_from_url(payload.url)
    except (InputValidationError, InputLoadError) as exc:
        raise _map_input_errors(exc) from exc
    return _skeleton_summary(processed, max_sentences)

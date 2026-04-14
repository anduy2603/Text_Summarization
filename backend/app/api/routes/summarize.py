from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.schemas.common import SummarizeRequest, SummarizeResponse
from app.schemas.input import UrlIngestRequest
from app.services.input import (
    InputLoadError,
    InputValidationError,
    process_from_bytes,
    process_from_text,
    process_from_url,
)
from app.services.summarization import summarize_processed_input

router = APIRouter()


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
    return summarize_processed_input(processed, payload.max_sentences)


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
    return summarize_processed_input(processed, max_sentences)


@router.post("/summarize/url", response_model=SummarizeResponse)
async def summarize_url(
    payload: UrlIngestRequest,
    max_sentences: int = Query(default=3, ge=1, le=20),
) -> SummarizeResponse:
    try:
        processed = process_from_url(payload.url)
    except (InputValidationError, InputLoadError) as exc:
        raise _map_input_errors(exc) from exc
    return summarize_processed_input(processed, max_sentences)

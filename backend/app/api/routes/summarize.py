from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.schemas.common import SummarizeRequest, SummarizeResponse, SummaryControls
from app.schemas.input import UrlIngestRequest
from app.services.input import (
    InputLoadError,
    InputValidationError,
    process_from_bytes,
    process_from_text,
    process_from_url,
)
from app.services.summarization import summarize_processed_input
from app.services.summarization.summary_service import SummaryEngineNotReadyError, UnsupportedSummaryEngineError

router = APIRouter()


def _map_input_errors(exc: Exception) -> HTTPException:
    if isinstance(exc, InputValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, InputLoadError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail="Unexpected input error.")


def _summary_controls_from_query(
    max_sentences: Optional[int] = Query(
        default=None,
        ge=1,
        le=20,
        description="Preferred top-k sentence count. Takes priority over ratio when provided.",
    ),
    ratio: Optional[float] = Query(
        default=None,
        gt=0.0,
        le=1.0,
        description="Optional extractive ratio. Used only when max_sentences is None.",
    ),
    engine: Optional[str] = Query(
        default=None,
        description="Optional summarization engine override.",
    ),
) -> SummaryControls:
    return SummaryControls(max_sentences=max_sentences, ratio=ratio, engine=engine)


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(payload: SummarizeRequest) -> SummarizeResponse:
    try:
        processed = process_from_text(payload.text)
    except (InputValidationError, InputLoadError) as exc:
        raise _map_input_errors(exc) from exc
    try:
        return summarize_processed_input(
            processed,
            max_sentences=payload.max_sentences,
            ratio=payload.ratio,
            engine_name=payload.engine,
        )
    except SummaryEngineNotReadyError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except UnsupportedSummaryEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/summarize/file", response_model=SummarizeResponse)
async def summarize_file(
    file: UploadFile = File(...),
    controls: SummaryControls = Depends(_summary_controls_from_query),
) -> SummarizeResponse:
    content = await file.read()
    try:
        processed = process_from_bytes(file.filename or "", content)
    except (InputValidationError, InputLoadError) as exc:
        raise _map_input_errors(exc) from exc
    try:
        return summarize_processed_input(
            processed,
            max_sentences=controls.max_sentences,
            ratio=controls.ratio,
            engine_name=controls.engine,
        )
    except SummaryEngineNotReadyError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except UnsupportedSummaryEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/summarize/url", response_model=SummarizeResponse)
async def summarize_url(
    payload: UrlIngestRequest,
    controls: SummaryControls = Depends(_summary_controls_from_query),
) -> SummarizeResponse:
    try:
        processed = process_from_url(payload.url)
    except (InputValidationError, InputLoadError) as exc:
        raise _map_input_errors(exc) from exc
    try:
        return summarize_processed_input(
            processed,
            max_sentences=controls.max_sentences,
            ratio=controls.ratio,
            engine_name=controls.engine,
        )
    except SummaryEngineNotReadyError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except UnsupportedSummaryEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

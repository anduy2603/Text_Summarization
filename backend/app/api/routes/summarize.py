from fastapi import APIRouter

from app.schemas.common import SummarizeRequest, SummarizeResponse

router = APIRouter()


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(payload: SummarizeRequest) -> SummarizeResponse:
    text = payload.text.strip()
    preview = text[:240]
    if len(text) > 240:
        preview += "..."

    return SummarizeResponse(
        summary=preview if preview else "No content provided.",
        metadata={
            "engine": "skeleton-echo",
            "input_length": len(text),
            "target_sentences": payload.max_sentences,
        },
    )

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


SUPPORTED_SUMMARY_ENGINES = ("tfidf", "textrank", "phobert-extractive")
PLANNED_SUMMARY_ENGINES = (
    "vit5",
    "bartpho",
    "gemini",
)


class HealthResponse(BaseModel):
    status: str = "ok"


class SummaryControls(BaseModel):
    max_sentences: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Preferred top-k sentence count. Takes priority over ratio when provided.",
    )
    ratio: Optional[float] = Field(
        default=None,
        gt=0.0,
        le=1.0,
        description="Optional extractive ratio. Used only when max_sentences is None.",
    )
    engine: Optional[str] = Field(
        default=None,
        description=(
            "Optional summarization engine override. "
            "Currently supported: tfidf, textrank, phobert-extractive. "
            "Planned but not ready: vit5, bartpho, gemini."
        ),
    )


class SummarizeRequest(SummaryControls):
    text: str = Field(default="", description="Raw input text to summarize")


class SummarizeResponse(BaseModel):
    summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

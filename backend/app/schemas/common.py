from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class SummarizeRequest(BaseModel):
    text: str = Field(default="", description="Raw input text to summarize")
    max_sentences: int = Field(default=3, ge=1, le=20)


class SummarizeResponse(BaseModel):
    summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

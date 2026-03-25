from typing import Any, Literal

from pydantic import BaseModel, Field


SourceType = Literal["text", "txt", "docx", "pdf", "url"]


class ProcessedInput(BaseModel):
    """Unified output of the input pipeline (after load → clean → normalize → split)."""

    cleaned_text: str
    sentences: list[str]
    source_type: SourceType
    metadata: dict[str, Any] = Field(default_factory=dict)


class UrlIngestRequest(BaseModel):
    url: str = Field(..., min_length=1, description="HTTP(S) URL to fetch and normalize")

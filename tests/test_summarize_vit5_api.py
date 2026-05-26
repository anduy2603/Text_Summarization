from __future__ import annotations

import pytest

from app.services.input import process_from_text
from app.services.summarization.summary_service import (
    SummaryEngineNotReadyError,
    summarize_processed_input,
)

VIET_SAMPLE = (
    "Thành phố Hồ Chí Minh triển khai tuyến xe buýt điện. "
    "Người dân phản hồi tích cực về chất lượng dịch vụ. "
    "Dự án nhằm giảm ô nhiễm và cải thiện giao thông trong khu vực nội thành."
)


def test_summarize_processed_input_vit5_engine_metadata() -> None:
    processed = process_from_text(VIET_SAMPLE)
    try:
        response = summarize_processed_input(
            processed,
            max_sentences=2,
            engine_name="vit5",
        )
    except SummaryEngineNotReadyError as exc:
        pytest.skip(f"ViT5 not ready: {exc}")

    assert response.summary.strip()
    assert response.metadata["engine"] == "vit5"
    engine_meta = response.metadata.get("engine_metadata") or {}
    assert engine_meta.get("method") == "abstractive"

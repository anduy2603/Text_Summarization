from __future__ import annotations

import pytest

from app.services.input import InputValidationError, process_from_text


def test_process_from_text_rejects_empty() -> None:
    with pytest.raises(InputValidationError, match="Text is empty"):
        process_from_text("")


def test_process_from_text_rejects_whitespace_only() -> None:
    with pytest.raises(InputValidationError, match="Text is empty"):
        process_from_text("   \n\t  ")


def test_process_from_text_handles_vietnamese_text() -> None:
    raw = (
        "Thành phố Hồ Chí Minh có mưa lớn vào chiều nay. "
        "Người dân cần chú ý khi lưu thông."
    )
    processed = process_from_text(raw)

    assert processed.cleaned_text
    assert "Hồ Chí Minh" in processed.cleaned_text
    assert processed.source_type == "text"
    assert len(processed.sentences) >= 2
    assert processed.metadata["sentence_count"] == len(processed.sentences)

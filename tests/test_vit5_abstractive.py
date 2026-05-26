from __future__ import annotations

import pytest

from app.services.summarization.vit5_abstractive import (
    resolve_max_new_tokens,
    summarize_with_vit5,
)


def test_resolve_max_new_tokens_from_max_sentences() -> None:
    tokens, meta = resolve_max_new_tokens(max_sentences=2, ratio=None)
    assert tokens >= 48
    assert meta["length_control"] == "max_sentences_to_tokens"
    assert meta["requested_max_sentences"] == 2


def test_resolve_max_new_tokens_empty_input_metadata() -> None:
    summary, meta = summarize_with_vit5("", max_sentences=2)
    assert summary == ""
    assert meta["strategy"] == "empty-input"
    assert meta["method"] == "abstractive"


@pytest.mark.skipif(
    not __import__("importlib").util.find_spec("torch"),
    reason="torch not installed",
)
def test_summarize_with_vit5_short_article() -> None:
    article = (
        "Thành phố Hồ Chí Minh triển khai tuyến xe buýt điện. "
        "Người dân phản hồi tích cực về chất lượng dịch vụ giao thông công cộng."
    )
    try:
        summary, meta = summarize_with_vit5(article, max_sentences=2)
    except Exception as exc:
        pytest.skip(f"ViT5 model not available in this environment: {exc}")

    assert meta["engine"] == "vit5"
    assert meta["method"] == "abstractive"
    assert isinstance(summary, str)


def test_list_engines_includes_vit5() -> None:
    from app.services.summarization.summary_service import list_supported_summary_engines

    assert "vit5" in list_supported_summary_engines()

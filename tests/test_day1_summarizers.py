from __future__ import annotations

from app.services.summarization.tfidf_summarizer import summarize_with_tfidf
from app.services.summarization.textrank_summarizer import summarize_with_textrank


SENTENCES = [
    "Hôm nay thị trường chứng khoán tăng mạnh.",
    "Nhiều cổ phiếu ngân hàng ghi nhận mức tăng tích cực.",
    "Nhà đầu tư vẫn thận trọng trước các biến động quốc tế.",
    "Chuyên gia khuyến nghị quản trị rủi ro danh mục.",
]


def _assert_common_engine_metadata(meta: dict, expected_engine: str) -> None:
    assert meta.get("engine") == expected_engine
    assert isinstance(meta.get("resolved_target_k"), int)
    assert meta["resolved_target_k"] >= 1
    assert isinstance(meta.get("selected_indices"), list)
    assert len(meta["selected_indices"]) == meta["resolved_target_k"]


def test_tfidf_returns_non_empty_summary_and_metadata() -> None:
    selected_sentences, metadata = summarize_with_tfidf(SENTENCES, max_sentences=2)
    assert selected_sentences
    assert len(selected_sentences) == 2
    _assert_common_engine_metadata(metadata, "tfidf")


def test_textrank_returns_non_empty_summary_and_metadata() -> None:
    selected_sentences, metadata = summarize_with_textrank(SENTENCES, max_sentences=2)
    assert selected_sentences
    assert len(selected_sentences) == 2
    _assert_common_engine_metadata(metadata, "textrank")

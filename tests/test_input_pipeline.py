from __future__ import annotations

from app.services.input import cleaner, sentence_candidates, sentence_splitter
from app.services.input.document_line_filters import is_noise_line
from app.services.summarization.length_policy import resolve_target_k_from_policy
from app.services.summarization.textrank_summarizer import summarize_with_textrank


def test_cleaner_drops_noise_and_duplicate_title() -> None:
    raw = (
        "Tiêu đề bài viết\n"
        "Tiêu đề bài viết\n"
        "Quảng cáo\n"
        "Ảnh: AP\n"
        "Nguồn: Reuters\n"
        "Thành phố triển khai tuyến xe buýt điện mới. "
        "Người dân phản hồi tích cực về chất lượng dịch vụ."
    )
    cleaned = cleaner.clean_text(raw)
    assert "Quảng cáo" not in cleaned
    assert "Ảnh: AP" not in cleaned
    assert cleaned.count("Tiêu đề bài viết") == 1
    assert "tuyến xe buýt điện" in cleaned


def test_is_noise_line_patterns() -> None:
    assert is_noise_line("Quảng cáo")
    assert is_noise_line("Ảnh: AP")
    assert not is_noise_line("Thành phố triển khai tuyến xe buýt điện mới.")


def test_split_sentences_respects_paragraph_breaks() -> None:
    text = "Tiêu đề ngắn\n\nCâu đầu tiên của bài. Câu thứ hai quan trọng."
    sents = sentence_splitter.split_sentences(text)
    assert len(sents) >= 2
    assert sents[0] == "Tiêu đề ngắn"


def test_filter_sentences_drops_caption_and_duplicates() -> None:
    sents = [
        "Ảnh: AP",
        "Thành phố triển khai tuyến xe buýt điện mới.",
        "Thành phố triển khai tuyến xe buýt điện mới.",
        "Người dân phản hồi tích cực về chất lượng dịch vụ công cộng.",
    ]
    filtered, stats = sentence_candidates.filter_sentences_for_summarization(sents)
    assert len(filtered) == 2
    assert stats["sentences_dropped_junk"] >= 1
    assert stats["sentences_dropped_duplicate"] == 1


def test_length_policy_scales_with_doc_size() -> None:
    k_short, meta_short = resolve_target_k_from_policy(2, sentence_count=20, char_length=800)
    k_long, meta_long = resolve_target_k_from_policy(2, sentence_count=20, char_length=20_000)
    assert k_short == 2
    assert meta_short["length_tier"] == "short"
    assert meta_short["min_output_sentences"] == 2
    assert k_long == 4
    assert meta_long["length_tier"] == "long"
    assert meta_long["min_output_sentences"] >= 3


def test_textrank_mmr_reduces_near_duplicate_selection() -> None:
    sentences = [
        "Thành phố triển khai tuyến xe buýt điện mới trong nội thành.",
        "Thành phố triển khai tuyến xe buýt điện mới tại khu vực trung tâm.",
        "Người dân phản hồi tích cực về chất lượng dịch vụ công cộng.",
        "Dự án nhằm giảm ô nhiễm và cải thiện giao thông đô thị.",
    ]
    selected, meta = summarize_with_textrank(sentences, max_sentences=2)
    assert meta["selection_strategy"] == "mmr-with-position-bias"
    assert len(selected) == 2
    assert selected[0] != selected[1]

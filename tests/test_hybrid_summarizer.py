from __future__ import annotations

from app.schemas.input import ProcessedInput
from app.services.input.input_service import process_from_text
from app.services.summarization.hybrid_summarizer import summarize_with_hybrid
from app.services.summarization.summary_length import count_sentences
from app.services.summarization.vit5_abstractive import Vit5EngineNotReadyError


VIET_ARTICLE = (
    "Thành phố Hồ Chí Minh triển khai tuyến xe buýt điện. "
    "Người dân phản hồi tích cực về chất lượng dịch vụ. "
    "Dự án nhằm giảm ô nhiễm và cải thiện giao thông công cộng trong khu vực nội thành. "
    "Ảnh: AP\n"
    "Quảng cáo\n"
    "Nguồn: Reuters"
)


def test_hybrid_short_doc_uses_textrank_path_without_vit5(monkeypatch) -> None:
    processed = process_from_text(VIET_ARTICLE)
    monkeypatch.setattr(
        "app.services.summarization.hybrid_summarizer.settings.hybrid_vit5_min_chars",
        50_000,
    )
    selected, meta = summarize_with_hybrid(
        cleaned_text=processed.cleaned_text,
        sentences=processed.sentences,
        target_k=2,
        max_sentences=2,
    )
    assert len(selected) >= 1
    assert meta["engine"] == "hybrid"
    assert meta["strategy"] == "hybrid-textrank-only-short-doc"
    assert "Ảnh" not in " ".join(selected)


def test_hybrid_falls_back_when_vit5_unavailable(monkeypatch) -> None:
    processed = process_from_text(VIET_ARTICLE)
    monkeypatch.setattr(
        "app.services.summarization.hybrid_summarizer.settings.hybrid_vit5_min_chars",
        1,
    )

    def _raise_vit5(*_args, **_kwargs):
        raise Vit5EngineNotReadyError("vit5 offline in test")

    monkeypatch.setattr(
        "app.services.summarization.hybrid_summarizer.summarize_with_vit5",
        _raise_vit5,
    )
    selected, meta = summarize_with_hybrid(
        cleaned_text=processed.cleaned_text,
        sentences=processed.sentences,
        target_k=2,
        max_sentences=2,
    )
    assert len(selected) >= 1
    assert meta["strategy"] == "hybrid-textrank-fallback"
    assert "vit5_fallback_reason" in meta


def test_hybrid_augment_when_vit5_returns_one_sentence(monkeypatch) -> None:
    processed = process_from_text(
        "Nga và Trung Quốc đạt hiểu biết chung về dự án đường ống Sức mạnh Siberia 2. "
        "Hai bên chưa có lộ trình triển khai cụ thể do bất đồng về giá khí đốt. "
        "Dự án có ý nghĩa lớn với Nga khi nước này mất khách hàng châu Âu. "
        "Tuyến ống sẽ vận chuyển khí từ Siberia sang Trung Quốc qua Mông Cổ. "
        "Đàm phán thương mại vẫn tiếp tục trong các vòng tới."
    )
    monkeypatch.setattr(
        "app.services.summarization.hybrid_summarizer.settings.hybrid_vit5_min_chars",
        1,
    )

    def _short_vit5(_text, max_sentences=None, ratio=None, **kwargs):
        return (
            "Lãnh đạo Nga và Trung Quốc cho rằng dự án chưa có lộ trình cụ thể.",
            {"engine": "vit5", "output_sentence_count": 1},
        )

    monkeypatch.setattr(
        "app.services.summarization.hybrid_summarizer.summarize_with_vit5",
        _short_vit5,
    )
    selected, meta = summarize_with_hybrid(
        cleaned_text=processed.cleaned_text,
        sentences=processed.sentences,
        target_k=4,
        max_sentences=4,
        length_tier="medium",
        min_output_sentences=3,
    )
    assert len(selected) == 1
    assert count_sentences(selected[0]) >= 3
    assert meta["strategy"] == "hybrid-textrank-vit5-augmented"
    assert meta["augmentation"]["augmentation"] in (
        "hybrid-lead-plus-bullets",
        "hybrid-bullets-only",
        "hybrid-lead-only",
    )


def test_process_from_text_filters_noise_lines() -> None:
    processed = process_from_text(VIET_ARTICLE)
    assert processed.metadata.get("sentence_filter", {}).get("sentences_dropped_junk", 0) >= 0
    joined = " ".join(processed.sentences)
    assert "Quảng cáo" not in joined
    assert "Ảnh:" not in joined

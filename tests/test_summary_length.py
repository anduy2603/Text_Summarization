from __future__ import annotations

from app.services.summarization.length_policy import resolve_target_k_from_policy
from app.services.summarization.summary_length import (
    assemble_hybrid_document_summary,
    count_sentences,
    resolve_min_output_sentences,
)


def test_count_sentences_multisentence() -> None:
    text = "Câu một về dự án. Câu hai về giá khí. Câu ba về lộ trình."
    assert count_sentences(text) == 3


def test_min_output_sentences_by_tier() -> None:
    assert resolve_min_output_sentences(3, "medium") == 3
    assert resolve_min_output_sentences(5, "long") == 5


def test_assemble_augment_when_vit5_one_sentence() -> None:
    vit5 = "Lãnh đạo Nga và Trung Quốc cho rằng dự án chưa có lộ trình cụ thể."
    extractive = [
        "Hai bên vẫn bất đồng về giá khí đốt và điều kiện thương mại.",
        "Dự án có ý nghĩa lớn với Nga sau khi mất khách hàng châu Âu.",
        "Đường ống sẽ vận chuyển khí từ Siberia sang Trung Quốc qua Mông Cổ.",
    ]
    combined, meta = assemble_hybrid_document_summary(
        vit5_text=vit5,
        extractive_sentences=extractive,
        target_k=4,
        min_output_sentences=3,
        length_tier="medium",
    )
    assert meta["augmentation"] == "hybrid-lead-plus-bullets"
    assert "Điểm cốt lõi:" in combined
    assert "Ý chính:" in combined
    assert "giá khí" in combined


def test_length_policy_includes_min_output() -> None:
    k, meta = resolve_target_k_from_policy(4, sentence_count=30, char_length=8_000)
    assert k >= 5
    assert meta["length_tier"] == "long"
    assert meta["min_output_sentences"] >= 3

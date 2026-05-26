from __future__ import annotations

from app.services.summarization.summary_length import assemble_hybrid_document_summary
from app.services.summarization.summary_quality import assess_vit5_lead_quality
from app.services.summarization.vit5_abstractive import resolve_generation_length_bounds


def test_hybrid_lead_bounds_no_min_new_tokens() -> None:
    max_tok, min_tok, meta = resolve_generation_length_bounds(4, None, hybrid_lead=True)
    assert min_tok is None
    assert meta["generation_profile"] == "hybrid_lead"
    assert max_tok <= 4 * 64


def test_quality_gate_rejects_mojibake() -> None:
    bad = "ÓÓÓỚ ( Hà Nội )ẠÙ ngừng bắn Ukraine."
    passed, details = assess_vit5_lead_quality(bad)
    assert passed is False
    assert "mojibake-pattern" in details["reasons"]


def test_assemble_discards_bad_lead_uses_bullets() -> None:
    vit5 = "ÓÓÓỚ ngừng bắn tại Hà Nội không liên quan."
    extractive = [
        "Nga và Trung Quốc đạt hiểu biết chung về dự án Sức mạnh Siberia 2.",
        "Hai bên chưa có lộ trình do bất đồng về giá khí đốt.",
        "Dự án quan trọng với Nga sau khi mất thị trường châu Âu.",
    ]
    combined, meta = assemble_hybrid_document_summary(
        vit5_text=vit5,
        extractive_sentences=extractive,
        target_k=4,
        min_output_sentences=3,
        length_tier="medium",
    )
    assert meta["augmentation"] == "hybrid-bullets-only"
    assert "ÓÓÓ" not in combined
    assert "Ý chính:" in combined
    assert "Siberia" in combined

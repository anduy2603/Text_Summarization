from __future__ import annotations

from app.services.input.sentence_candidates import is_junk_sentence
from app.services.summarization.bullet_selection import (
    is_unsuitable_bullet,
    rank_sentences_for_bullets,
)


def test_is_junk_rejects_photo_caption_sentence() -> None:
    cap = "Tổng thống Nga Vladimir Putin và Chủ tịch Trung Quốc bắt tay trong lễ ký kết."
    assert is_junk_sentence(cap) is True


def test_unsuitable_bullet_detects_caption_and_deictic() -> None:
    bad_cap, r1 = is_unsuitable_bullet(
        "Ông Putin và ông Tập bắt tay trước ống kính (trái)."
    )
    bad_deictic, r2 = is_unsuitable_bullet(
        "Tuy nhiên, Trung Quốc dường như chưa nhất trí với công thức này."
    )
    bad_vague, r3 = is_unsuitable_bullet("Một số chi tiết vẫn cần được hoàn thiện.")
    assert bad_cap and r1 == "caption-or-photo"
    assert bad_deictic and r2 == "deictic-low-context"
    assert bad_vague and r3 == "vague-fragment"


def test_rank_prefers_topic_sentences_over_caption() -> None:
    sentences = [
        "Nga và Trung Quốc đạt hiểu biết chung về dự án đường ống Sức mạnh Siberia 2.",
        "Tổng thống Nga Vladimir Putin bắt tay Chủ tịch Trung Quốc trong lễ ký kết.",
        "Hai bên vẫn bất đồng về giá khí đốt và điều kiện thương mại.",
        "Tuyến ống dự kiến đưa khí đốt từ Siberia sang Trung Quốc qua Mông Cổ.",
        "Dự án quan trọng với Nga khi mất khách hàng khí đốt châu Âu.",
    ]
    picked, meta = rank_sentences_for_bullets(sentences, max_bullets=3, min_bullets=2)
    joined = " ".join(picked)
    assert "bắt tay" not in joined
    assert "Siberia" in joined or "khí đốt" in joined
    assert meta["candidates_scored"] >= 3

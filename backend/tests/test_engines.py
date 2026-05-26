"""Unit tests for individual summarization engines."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from tests.conftest import SAMPLE_SENTENCES


# ---------------------------------------------------------------------------
# TF-IDF engine — no model required
# ---------------------------------------------------------------------------

class TestTfidfEngine:
    def setup_method(self):
        from app.services.summarization.tfidf_summarizer import summarize_with_tfidf
        self.summarize = summarize_with_tfidf

    def test_returns_correct_k(self):
        result, meta = self.summarize(SAMPLE_SENTENCES, max_sentences=2)
        assert len(result) == 2
        assert meta["resolved_target_k"] == 2

    def test_sentences_in_original_order(self):
        result, _ = self.summarize(SAMPLE_SENTENCES, max_sentences=3)
        indices = [SAMPLE_SENTENCES.index(s) for s in result]
        assert indices == sorted(indices)

    def test_empty_input_returns_empty(self):
        result, meta = self.summarize([], max_sentences=3)
        assert result == []
        assert meta["strategy"] == "empty-input"

    def test_k_capped_at_sentence_count(self):
        short = SAMPLE_SENTENCES[:2]
        result, _ = self.summarize(short, max_sentences=10)
        assert len(result) <= 2

    def test_ratio_mode(self):
        result, meta = self.summarize(SAMPLE_SENTENCES, ratio=0.5)
        assert len(result) >= 1
        assert meta.get("selection_mode") == "ratio"

    def test_engine_name_in_meta(self):
        _, meta = self.summarize(SAMPLE_SENTENCES, max_sentences=2)
        assert meta["engine"] == "tfidf"

    def test_stopwords_reduce_common_words(self):
        # "và", "là", "của" should not drive sentence scoring
        from app.services.input.vietnamese_stopwords import VIETNAMESE_STOPWORDS
        assert "và" in VIETNAMESE_STOPWORDS
        assert "là" in VIETNAMESE_STOPWORDS
        assert "của" in VIETNAMESE_STOPWORDS

    def test_single_sentence(self):
        single = ["Đây là một câu đơn độc trong tài liệu ngắn về kinh tế Việt Nam."]
        result, _ = self.summarize(single, max_sentences=3)
        assert result == single


# ---------------------------------------------------------------------------
# TextRank engine — no model required
# ---------------------------------------------------------------------------

class TestTextrankEngine:
    def setup_method(self):
        from app.services.summarization.textrank_summarizer import summarize_with_textrank
        self.summarize = summarize_with_textrank

    def test_returns_correct_k(self):
        result, meta = self.summarize(SAMPLE_SENTENCES, max_sentences=2)
        assert len(result) == 2

    def test_sentences_in_original_order(self):
        result, _ = self.summarize(SAMPLE_SENTENCES, max_sentences=3)
        indices = [SAMPLE_SENTENCES.index(s) for s in result]
        assert indices == sorted(indices)

    def test_empty_input_returns_empty(self):
        result, meta = self.summarize([], max_sentences=3)
        assert result == []

    def test_engine_name_in_meta(self):
        _, meta = self.summarize(SAMPLE_SENTENCES, max_sentences=2)
        assert meta["engine"] == "textrank"

    def test_meta_has_sentence_scores(self):
        _, meta = self.summarize(SAMPLE_SENTENCES, max_sentences=2)
        assert "sentence_scores" in meta
        assert len(meta["sentence_scores"]) == len(SAMPLE_SENTENCES)

    def test_mmr_reduces_redundancy(self):
        # Two nearly identical sentences — MMR should avoid picking both
        near_dup = [
            "Kinh tế Việt Nam tăng trưởng mạnh trong quý đầu năm 2024 so với cùng kỳ.",
            "Kinh tế Việt Nam tăng trưởng mạnh mẽ trong quý đầu năm 2024 so với cùng kỳ.",
            "Lĩnh vực nông nghiệp đóng góp quan trọng vào tăng trưởng GDP cả nước năm nay.",
            "Đầu tư nước ngoài vào Việt Nam tăng đáng kể trong sáu tháng đầu năm 2024.",
        ]
        result, _ = self.summarize(near_dup, max_sentences=2)
        assert len(result) == 2
        # Both near-duplicates should NOT be selected simultaneously
        both_selected = (near_dup[0] in result and near_dup[1] in result)
        assert not both_selected, "MMR should suppress near-duplicate sentences"

    def test_single_sentence(self):
        single = ["Đây là một câu đơn độc về nền kinh tế Việt Nam năm 2024."]
        result, _ = self.summarize(single, max_sentences=3)
        assert result == single


# ---------------------------------------------------------------------------
# Vietnamese stopwords
# ---------------------------------------------------------------------------

class TestVietnameseStopwords:
    def test_min_coverage(self):
        from app.services.input.vietnamese_stopwords import VIETNAMESE_STOPWORDS
        assert len(VIETNAMESE_STOPWORDS) >= 60, "Stopword list should have at least 60 entries"

    def test_core_function_words_present(self):
        from app.services.input.vietnamese_stopwords import VIETNAMESE_STOPWORDS
        must_have = {"và", "là", "của", "các", "những", "trong", "đã", "đang", "sẽ", "không"}
        missing = must_have - VIETNAMESE_STOPWORDS
        assert not missing, f"Missing core stopwords: {missing}"

    def test_is_frozenset(self):
        from app.services.input.vietnamese_stopwords import VIETNAMESE_STOPWORDS
        assert isinstance(VIETNAMESE_STOPWORDS, frozenset)


# ---------------------------------------------------------------------------
# PhoBERT engine — mocked (no model weights required)
# ---------------------------------------------------------------------------

class TestPhobertEngine:
    """
    Mocks _encode_sentences and _segment_for_phobert so tests run without
    the PhoBERT model weights or GPU.
    """

    def _make_embeddings(self, n: int, dim: int = 768) -> np.ndarray:
        rng = np.random.default_rng(seed=42)
        return rng.random((n, dim)).astype(np.float32)

    def test_returns_top_k(self):
        from app.services.summarization.phobert_extractive import summarize_with_phobert_extractive

        n = len(SAMPLE_SENTENCES)
        fake_embeddings = self._make_embeddings(n)

        with (
            patch("app.services.summarization.phobert_extractive._segment_for_phobert") as mock_seg,
            patch("app.services.summarization.phobert_extractive._encode_sentences") as mock_enc,
        ):
            mock_seg.return_value = (SAMPLE_SENTENCES, {"sentence_segmentation": "mock"})
            mock_enc.return_value = fake_embeddings

            result, meta = summarize_with_phobert_extractive(SAMPLE_SENTENCES, max_sentences=2)

        assert len(result) == 2
        assert meta["engine"] == "phobert-extractive"

    def test_sentences_in_original_order(self):
        from app.services.summarization.phobert_extractive import summarize_with_phobert_extractive

        n = len(SAMPLE_SENTENCES)
        fake_embeddings = self._make_embeddings(n)

        with (
            patch("app.services.summarization.phobert_extractive._segment_for_phobert") as mock_seg,
            patch("app.services.summarization.phobert_extractive._encode_sentences") as mock_enc,
        ):
            mock_seg.return_value = (SAMPLE_SENTENCES, {"sentence_segmentation": "mock"})
            mock_enc.return_value = fake_embeddings

            result, meta = summarize_with_phobert_extractive(SAMPLE_SENTENCES, max_sentences=3)

        indices = meta["selected_indices"]
        assert indices == sorted(indices)

    def test_empty_input_returns_empty(self):
        from app.services.summarization.phobert_extractive import summarize_with_phobert_extractive

        result, meta = summarize_with_phobert_extractive([], max_sentences=3)
        assert result == []
        assert meta["strategy"] == "empty-input"

    def test_meta_has_scores(self):
        from app.services.summarization.phobert_extractive import summarize_with_phobert_extractive

        n = len(SAMPLE_SENTENCES)
        fake_embeddings = self._make_embeddings(n)

        with (
            patch("app.services.summarization.phobert_extractive._segment_for_phobert") as mock_seg,
            patch("app.services.summarization.phobert_extractive._encode_sentences") as mock_enc,
        ):
            mock_seg.return_value = (SAMPLE_SENTENCES, {"sentence_segmentation": "mock"})
            mock_enc.return_value = fake_embeddings

            _, meta = summarize_with_phobert_extractive(SAMPLE_SENTENCES, max_sentences=2)

        assert "sentence_scores" in meta
        assert len(meta["sentence_scores"]) == n


# ---------------------------------------------------------------------------
# ViT5 engine — tests graceful unavailability
# ---------------------------------------------------------------------------

class TestVit5Engine:
    """
    Tests ViT5 behaviour when the model is not available (expected in CI / dev
    without downloaded weights). The engine should raise Vit5EngineNotReadyError,
    which the service layer converts to SummaryEngineNotReadyError (HTTP 501).
    """

    def test_raises_when_not_ready(self):
        from app.services.summarization.vit5_abstractive import (
            Vit5EngineNotReadyError,
            summarize_with_vit5,
        )
        with patch(
            "app.services.summarization.vit5_abstractive._get_vit5_runtime",
            side_effect=Vit5EngineNotReadyError("Model not cached"),
        ):
            with pytest.raises(Vit5EngineNotReadyError):
                summarize_with_vit5("Đây là văn bản cần tóm tắt với ViT5.")

    def test_empty_text_returns_empty(self):
        from app.services.summarization.vit5_abstractive import summarize_with_vit5
        # Empty text short-circuits before calling runtime — no mock needed
        result, meta = summarize_with_vit5("")
        assert result == ""
        assert meta["strategy"] == "empty-input"

    def test_resolve_max_new_tokens_from_sentences(self):
        from app.services.summarization.vit5_abstractive import resolve_max_new_tokens
        tokens, meta = resolve_max_new_tokens(max_sentences=3, ratio=None)
        assert tokens > 0
        assert meta["length_control"] == "max_sentences_to_tokens"

    def test_resolve_max_new_tokens_from_ratio(self):
        from app.services.summarization.vit5_abstractive import resolve_max_new_tokens
        tokens, meta = resolve_max_new_tokens(max_sentences=None, ratio=0.5)
        assert tokens > 0
        assert meta["length_control"] == "ratio_to_tokens"

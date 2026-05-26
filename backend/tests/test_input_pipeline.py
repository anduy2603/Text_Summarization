"""Tests for the input processing pipeline (text, bytes, sentence splitting)."""
from __future__ import annotations

import pytest

from app.services.input.exceptions import InputValidationError
from app.services.input.input_service import process_from_bytes, process_from_text
from app.services.input.sentence_splitter import split_sentences
from app.services.input.sentence_candidates import filter_sentences_for_summarization
from app.services.input.cleaner import clean_text
from tests.conftest import SAMPLE_VI_TEXT


# ---------------------------------------------------------------------------
# process_from_text
# ---------------------------------------------------------------------------

class TestProcessFromText:
    def test_returns_processed_input(self):
        result = process_from_text(SAMPLE_VI_TEXT)
        assert result.cleaned_text
        assert len(result.sentences) >= 1
        assert result.source_type == "text"

    def test_sentence_count_reasonable(self):
        result = process_from_text(SAMPLE_VI_TEXT)
        # Sample text has 8 sentences; at least half should survive filtering
        assert len(result.sentences) >= 3

    def test_metadata_keys_present(self):
        result = process_from_text(SAMPLE_VI_TEXT)
        meta = result.metadata
        assert "raw_char_length" in meta
        assert "sentence_count" in meta
        assert "raw_sentence_count" in meta

    def test_empty_text_raises(self):
        with pytest.raises(InputValidationError):
            process_from_text("")

    def test_whitespace_only_raises(self):
        with pytest.raises(InputValidationError):
            process_from_text("   \n\t  ")

    def test_too_long_text_raises(self):
        # Default max is 1_000_000 chars; generate something bigger
        huge = "Đây là văn bản rất dài. " * 50_000  # ~1.1M chars
        with pytest.raises(InputValidationError, match="too long"):
            process_from_text(huge)


# ---------------------------------------------------------------------------
# process_from_bytes — TXT loader
# ---------------------------------------------------------------------------

class TestProcessFromBytes:
    def test_txt_file(self):
        content = SAMPLE_VI_TEXT.encode("utf-8")
        result = process_from_bytes("article.txt", content)
        assert result.source_type == "txt"
        assert len(result.sentences) >= 3
        assert result.metadata.get("filename") == "article.txt"

    def test_unsupported_extension_raises(self):
        with pytest.raises(InputValidationError):
            process_from_bytes("doc.xlsx", b"content")

    def test_empty_filename_raises(self):
        with pytest.raises(InputValidationError):
            process_from_bytes("", b"some content")

    def test_file_too_large_raises(self):
        big = b"a" * (11 * 1024 * 1024)  # 11 MB > 10 MB default
        with pytest.raises(InputValidationError, match="too large"):
            process_from_bytes("big.txt", big)


# ---------------------------------------------------------------------------
# sentence_splitter
# ---------------------------------------------------------------------------

class TestSentenceSplitter:
    def test_splits_basic_sentences(self):
        text = "Câu một. Câu hai. Câu ba."
        sents = split_sentences(text)
        assert len(sents) >= 2

    def test_empty_text_returns_empty(self):
        assert split_sentences("") == []
        assert split_sentences("   ") == []

    def test_paragraph_break_is_boundary(self):
        text = "Đoạn văn thứ nhất có nội dung quan trọng.\n\nĐoạn văn thứ hai có nội dung khác."
        sents = split_sentences(text)
        assert len(sents) == 2

    def test_preserves_sentence_content(self):
        text = "Hà Nội là thủ đô của Việt Nam. Thành phố có lịch sử hơn nghìn năm."
        sents = split_sentences(text)
        assert any("Hà Nội" in s for s in sents)


# ---------------------------------------------------------------------------
# sentence_candidates
# ---------------------------------------------------------------------------

class TestSentenceCandidates:
    def test_filters_short_sentences(self):
        sents = ["Ok.", "Đây là câu đủ dài để vượt qua bộ lọc câu ngắn của pipeline."]
        kept, stats = filter_sentences_for_summarization(sents)
        assert len(kept) == 1
        assert stats["sentences_dropped_junk"] == 1

    def test_filters_duplicates(self):
        s = "Đây là một câu đủ dài để vượt qua bộ lọc với nội dung bình thường."
        sents = [s, s, s]
        kept, stats = filter_sentences_for_summarization(sents)
        assert len(kept) == 1
        assert stats["sentences_dropped_duplicate"] == 2

    def test_good_sentences_pass_through(self):
        from tests.conftest import SAMPLE_SENTENCES
        kept, stats = filter_sentences_for_summarization(SAMPLE_SENTENCES)
        assert len(kept) == len(SAMPLE_SENTENCES)
        assert stats["sentences_dropped_junk"] == 0


# ---------------------------------------------------------------------------
# clean_text
# ---------------------------------------------------------------------------

class TestCleanText:
    def test_removes_zero_width_chars(self):
        text = "Văn​bản‌sạch‍."
        result = clean_text(text)
        assert "​" not in result
        assert "‌" not in result
        assert "‍" not in result

    def test_normalizes_crlf(self):
        text = "Dòng một.\r\nDòng hai."
        result = clean_text(text)
        assert "\r" not in result

    def test_collapses_multiple_blanks(self):
        text = "Dòng một.\n\n\n\nDòng hai."
        result = clean_text(text)
        assert "\n\n\n" not in result

    def test_empty_returns_empty(self):
        assert clean_text("") == ""

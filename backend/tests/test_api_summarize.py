"""Integration tests for the summarization API endpoints."""
from __future__ import annotations

import io

import pytest

from tests.conftest import SAMPLE_VI_TEXT


# ---------------------------------------------------------------------------
# Health & capability endpoints
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_ok(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "ok"


class TestEnginesEndpoint:
    def test_returns_supported_engines(self, client):
        resp = client.get("/api/v1/engines")
        assert resp.status_code == 200
        data = resp.json()
        assert "supported_engines" in data
        assert isinstance(data["supported_engines"], list)
        assert len(data["supported_engines"]) > 0

    def test_known_engines_present(self, client):
        resp = client.get("/api/v1/engines")
        engines = set(resp.json()["supported_engines"])
        assert "tfidf" in engines
        assert "textrank" in engines

    def test_default_engine_is_supported(self, client):
        data = resp = client.get("/api/v1/engines").json()
        default = data.get("default_engine")
        if default is not None:
            assert default in data["supported_engines"]

    def test_default_max_sentences_positive(self, client):
        data = client.get("/api/v1/engines").json()
        assert data.get("default_max_sentences", 1) >= 1


# ---------------------------------------------------------------------------
# POST /summarize  (text input)
# ---------------------------------------------------------------------------

class TestSummarizeText:
    def test_tfidf_returns_summary(self, client):
        resp = client.post(
            "/api/v1/summarize",
            json={"text": SAMPLE_VI_TEXT, "max_sentences": 2, "engine": "tfidf"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert len(data["summary"]) > 0

    def test_textrank_returns_summary(self, client):
        resp = client.post(
            "/api/v1/summarize",
            json={"text": SAMPLE_VI_TEXT, "max_sentences": 2, "engine": "textrank"},
        )
        assert resp.status_code == 200
        assert len(resp.json()["summary"]) > 0

    def test_metadata_contains_engine_field(self, client):
        resp = client.post(
            "/api/v1/summarize",
            json={"text": SAMPLE_VI_TEXT, "max_sentences": 2, "engine": "tfidf"},
        )
        meta = resp.json()["metadata"]
        assert meta.get("engine") == "tfidf"

    def test_metadata_has_compression_ratio(self, client):
        resp = client.post(
            "/api/v1/summarize",
            json={"text": SAMPLE_VI_TEXT, "max_sentences": 2, "engine": "textrank"},
        )
        meta = resp.json()["metadata"]
        ratio = meta.get("compression_ratio_chars")
        assert ratio is not None
        assert 0.0 < ratio < 1.0

    def test_metadata_has_sentence_counts(self, client):
        resp = client.post(
            "/api/v1/summarize",
            json={"text": SAMPLE_VI_TEXT, "max_sentences": 3, "engine": "tfidf"},
        )
        meta = resp.json()["metadata"]
        assert "sentence_count" in meta
        assert "selected_sentence_count" in meta
        assert meta["selected_sentence_count"] <= meta["sentence_count"]

    def test_empty_text_returns_400(self, client):
        resp = client.post(
            "/api/v1/summarize",
            json={"text": "", "engine": "tfidf"},
        )
        assert resp.status_code == 400

    def test_unsupported_engine_returns_400(self, client):
        resp = client.post(
            "/api/v1/summarize",
            json={"text": SAMPLE_VI_TEXT, "engine": "nonexistent_engine_xyz"},
        )
        assert resp.status_code == 400

    def test_model_not_ready_returns_501(self, client):
        """phobert / vit5 / hybrid should return 501 if model weights are absent."""
        from unittest.mock import patch
        from app.services.summarization.phobert_extractive import PhoBertEngineNotReadyError

        with patch(
            "app.services.summarization.phobert_extractive._get_phobert_runtime",
            side_effect=PhoBertEngineNotReadyError("Model not cached"),
        ):
            resp = client.post(
                "/api/v1/summarize",
                json={"text": SAMPLE_VI_TEXT, "engine": "phobert-extractive"},
            )
        assert resp.status_code == 501

    def test_max_sentences_respected(self, client):
        for k in (1, 2, 3):
            resp = client.post(
                "/api/v1/summarize",
                json={"text": SAMPLE_VI_TEXT, "max_sentences": k, "engine": "tfidf"},
            )
            assert resp.status_code == 200
            meta = resp.json()["metadata"]
            # selected_sentence_count should not exceed requested k
            assert meta["selected_sentence_count"] <= k

    def test_ratio_parameter(self, client):
        resp = client.post(
            "/api/v1/summarize",
            json={"text": SAMPLE_VI_TEXT, "ratio": 0.3, "engine": "tfidf"},
        )
        assert resp.status_code == 200
        assert len(resp.json()["summary"]) > 0

    def test_max_sentences_out_of_range_returns_422(self, client):
        # max_sentences=0 violates ge=1 constraint
        resp = client.post(
            "/api/v1/summarize",
            json={"text": SAMPLE_VI_TEXT, "max_sentences": 0, "engine": "tfidf"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /summarize/file  (TXT upload)
# ---------------------------------------------------------------------------

class TestSummarizeFile:
    def test_txt_file_upload(self, client):
        content = SAMPLE_VI_TEXT.encode("utf-8")
        resp = client.post(
            "/api/v1/summarize/file?engine=tfidf&max_sentences=2",
            files={"file": ("article.txt", io.BytesIO(content), "text/plain")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["summary"]) > 0

    def test_metadata_source_type_txt(self, client):
        content = SAMPLE_VI_TEXT.encode("utf-8")
        resp = client.post(
            "/api/v1/summarize/file?engine=tfidf&max_sentences=2",
            files={"file": ("article.txt", io.BytesIO(content), "text/plain")},
        )
        assert resp.json()["metadata"]["source_type"] == "txt"

    def test_unsupported_extension_returns_400(self, client):
        resp = client.post(
            "/api/v1/summarize/file",
            files={"file": ("doc.xyz", io.BytesIO(b"content"), "application/octet-stream")},
        )
        assert resp.status_code in (400, 422)

    def test_max_sentences_query_param(self, client):
        content = SAMPLE_VI_TEXT.encode("utf-8")
        resp = client.post(
            "/api/v1/summarize/file?engine=textrank&max_sentences=1",
            files={"file": ("article.txt", io.BytesIO(content), "text/plain")},
        )
        assert resp.status_code == 200
        assert resp.json()["metadata"]["selected_sentence_count"] <= 1


# ---------------------------------------------------------------------------
# POST /export/docx
# ---------------------------------------------------------------------------

class TestExportDocx:
    def test_returns_docx_bytes(self, client):
        resp = client.post(
            "/api/v1/export/docx",
            json={"title": "Báo cáo kinh tế", "summary": SAMPLE_VI_TEXT},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert len(resp.content) > 0

    def test_filename_in_header(self, client):
        resp = client.post(
            "/api/v1/export/docx",
            json={"title": "Báo cáo kinh tế", "summary": "Nội dung tóm tắt."},
        )
        assert "content-disposition" in resp.headers

    def test_empty_summary_returns_422(self, client):
        resp = client.post(
            "/api/v1/export/docx",
            json={"title": "Test", "summary": ""},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Latency metadata
# ---------------------------------------------------------------------------

class TestLatencyMetadata:
    def test_latency_present_in_response(self, client):
        resp = client.post(
            "/api/v1/summarize",
            json={"text": SAMPLE_VI_TEXT, "engine": "tfidf", "max_sentences": 2},
        )
        assert resp.status_code == 200
        meta = resp.json()["metadata"]
        assert "summarizer_latency_ms" in meta
        assert isinstance(meta["summarizer_latency_ms"], int)
        assert meta["summarizer_latency_ms"] >= 0

    def test_latency_reasonable_for_extractive(self, client):
        resp = client.post(
            "/api/v1/summarize",
            json={"text": SAMPLE_VI_TEXT, "engine": "textrank", "max_sentences": 2},
        )
        latency = resp.json()["metadata"]["summarizer_latency_ms"]
        assert latency < 5_000, f"TextRank took too long: {latency} ms"

from __future__ import annotations

from io import BytesIO

import fitz
import pytest
from fastapi.testclient import TestClient

from app.main import app
from scripts.shared.multiformat_experiment import build_docx_bytes, build_pdf_bytes, build_txt_bytes

VIET_SAMPLE = (
    "Thành phố Hồ Chí Minh triển khai tuyến xe buýt điện. "
    "Người dân phản hồi tích cực về chất lượng dịch vụ. "
    "Dự án nhằm giảm ô nhiễm và cải thiện giao thông công cộng trong khu vực nội thành."
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _blank_pdf_bytes() -> bytes:
    doc = fitz.open()
    doc.new_page()
    return doc.tobytes()


def test_engines_default_hybrid_and_three_sentences(client: TestClient) -> None:
    resp = client.get("/api/v1/engines")
    assert resp.status_code == 200
    data = resp.json()
    assert data["default_engine"] == "hybrid"
    assert data["default_max_sentences"] == 3
    assert "hybrid" in data["supported_engines"]
    assert "textrank" in data["supported_engines"]


def test_summarize_file_txt_uses_defaults(client: TestClient) -> None:
    content = build_txt_bytes(VIET_SAMPLE)
    resp = client.post(
        "/api/v1/summarize/file",
        files={"file": ("article.txt", content, "text/plain")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["summary"], str)
    assert len(body["summary"].strip()) > 0
    meta = body["metadata"]
    assert meta["engine"] == "hybrid"
    assert meta["resolved_target_k"] == 3
    assert meta["policy_target_k"] == 3
    assert meta["source_type"] == "txt"


def test_summarize_file_docx(client: TestClient) -> None:
    content = build_docx_bytes(VIET_SAMPLE)
    resp = client.post(
        "/api/v1/summarize/file",
        files={
            "file": (
                "article.docx",
                content,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert resp.status_code == 200
    assert resp.json()["metadata"]["source_type"] == "docx"


def test_summarize_file_pdf_with_text(client: TestClient) -> None:
    content = build_pdf_bytes(VIET_SAMPLE)
    resp = client.post(
        "/api/v1/summarize/file",
        files={"file": ("article.pdf", content, "application/pdf")},
    )
    assert resp.status_code == 200
    assert resp.json()["metadata"]["source_type"] == "pdf"


def test_summarize_file_pdf_no_extractable_text(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/summarize/file",
        files={"file": ("blank.pdf", _blank_pdf_bytes(), "application/pdf")},
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert isinstance(detail, str)
    assert "không chứa văn bản" in detail.lower() or "PDF" in detail


def test_summarize_file_unsupported_extension(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/summarize/file",
        files={"file": ("notes.md", b"# hello", "text/markdown")},
    )
    assert resp.status_code == 400


def test_summarize_file_max_sentences_query(client: TestClient) -> None:
    content = build_txt_bytes(VIET_SAMPLE)
    resp = client.post(
        "/api/v1/summarize/file?max_sentences=3",
        files={"file": ("article.txt", content, "text/plain")},
    )
    assert resp.status_code == 200
    meta = resp.json()["metadata"]
    assert meta["resolved_target_k"] == 3
    assert meta["policy_target_k"] == 3


def test_summarize_file_engine_override(client: TestClient) -> None:
    content = build_txt_bytes(VIET_SAMPLE)
    resp = client.post(
        "/api/v1/summarize/file?engine=tfidf&max_sentences=2",
        files={"file": ("article.txt", content, "text/plain")},
    )
    assert resp.status_code == 200
    assert resp.json()["metadata"]["engine"] == "tfidf"

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_list_engines_returns_supported_and_planned() -> None:
    resp = client.get("/api/v1/engines")
    assert resp.status_code == 200
    body = resp.json()
    assert "supported_engines" in body
    assert "planned_engines" in body
    assert "default_engine" in body
    assert "tfidf" in body["supported_engines"]
    assert "textrank" in body["supported_engines"]
    assert "phobert-extractive" in body["supported_engines"]
    assert "vit5" in body["planned_engines"]
    assert body["default_engine"] == "tfidf"


def test_summarize_happy_path_tfidf() -> None:
    payload = {
        "text": "Hà Nội đang tăng cường cây xanh đô thị. Dự án mới giúp cải thiện chất lượng không khí.",
        "max_sentences": 2,
        "engine": "tfidf",
    }
    resp = client.post("/api/v1/summarize", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body.get("summary"), str)
    assert body["summary"].strip() != ""
    assert body["metadata"]["engine"] == "tfidf"


def test_summarize_unsupported_engine_returns_400() -> None:
    payload = {
        "text": "Đây là một bản tin ngắn để test lỗi engine không hỗ trợ.",
        "max_sentences": 2,
        "engine": "not-a-real-engine",
    }
    resp = client.post("/api/v1/summarize", json=payload)
    assert resp.status_code == 400
    assert "Unsupported summary engine" in resp.json().get("detail", "")


def test_summarize_planned_engine_returns_not_ready() -> None:
    payload = {
        "text": "Đây là dữ liệu test cho planned engine.",
        "max_sentences": 2,
        "engine": "vit5",
    }
    resp = client.post("/api/v1/summarize", json=payload)
    assert resp.status_code == 501
    assert "planned but not ready yet" in resp.json().get("detail", "")


def test_summarize_file_txt_happy_path() -> None:
    content = (
        "Hà Nội đang tăng cường cây xanh đô thị. "
        "Dự án mới giúp cải thiện chất lượng không khí.\n"
    ).encode("utf-8")
    files = {"file": ("snippet.txt", content, "text/plain")}
    resp = client.post(
        "/api/v1/summarize/file",
        files=files,
        params={"max_sentences": 2, "engine": "tfidf"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body.get("summary"), str)
    assert body["summary"].strip() != ""
    assert body["metadata"]["engine"] == "tfidf"


def test_summarize_file_rejects_unknown_extension() -> None:
    files = {"file": ("data.bin", b"opaque-bytes", "application/octet-stream")}
    resp = client.post(
        "/api/v1/summarize/file",
        files=files,
        params={"max_sentences": 2, "engine": "tfidf"},
    )
    assert resp.status_code == 400
    detail = resp.json().get("detail", "")
    assert ".bin" in detail and ("Unsupported" in detail or "Allowed" in detail)


def test_summarize_url_rejects_non_http_scheme() -> None:
    resp = client.post(
        "/api/v1/summarize/url",
        json={"url": "ftp://example.com/resource"},
        params={"max_sentences": 2, "engine": "tfidf"},
    )
    assert resp.status_code == 400
    detail = resp.json().get("detail", "")
    assert "http" in detail.lower()


def test_summarize_url_rejects_missing_host() -> None:
    resp = client.post(
        "/api/v1/summarize/url",
        json={"url": "https:///path-only"},
        params={"max_sentences": 2, "engine": "tfidf"},
    )
    assert resp.status_code == 400
    assert "host" in resp.json().get("detail", "").lower()


def test_summarize_vietnamese_smoke_no_encoding_crash() -> None:
    payload = {
        "text": "Tiếng Việt có dấu: Thành phố Hồ Chí Minh đang triển khai thêm tuyến xe buýt điện.",
        "max_sentences": 1,
        "engine": "textrank",
    }
    resp = client.post("/api/v1/summarize", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body.get("summary"), str)
    assert body["summary"].strip() != ""

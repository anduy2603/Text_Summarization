"""Shared fixtures for the test suite."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# Sample Vietnamese texts
# ---------------------------------------------------------------------------

# 8 câu, ~600 ký tự — đủ dài để chạy qua mọi pipeline
SAMPLE_VI_TEXT = (
    "Hà Nội, ngày 15 tháng 5 năm 2024, Ủy ban Nhân dân thành phố đã tổ chức hội nghị "
    "về phát triển kinh tế - xã hội quý đầu năm. "
    "Tại hội nghị, Chủ tịch UBND thành phố trình bày báo cáo tổng kết quý I với nhiều "
    "số liệu tích cực. "
    "Theo báo cáo, tăng trưởng kinh tế đạt 7,2%, vượt mục tiêu đề ra từ đầu năm 2024. "
    "Lĩnh vực công nghiệp chế biến chế tạo tiếp tục dẫn đầu với mức tăng trưởng 8,5% "
    "so với cùng kỳ. "
    "Ngành dịch vụ cũng ghi nhận kết quả tích cực với mức tăng 6,8% so với cùng kỳ năm ngoái. "
    "Thu hút đầu tư nước ngoài đạt 1,2 tỷ USD, tăng 15% so với cùng kỳ năm trước. "
    "Thành phố tiếp tục đẩy mạnh cải cách thủ tục hành chính nhằm cải thiện môi trường "
    "đầu tư kinh doanh cho doanh nghiệp. "
    "Các chỉ tiêu về phát triển hạ tầng giao thông và đô thị cũng được hoàn thành đúng tiến độ."
)

SAMPLE_SENTENCES = [
    "Hà Nội tổ chức hội nghị về phát triển kinh tế - xã hội quý đầu năm 2024.",
    "Tăng trưởng kinh tế thành phố đạt 7,2%, vượt mục tiêu đề ra từ đầu năm.",
    "Lĩnh vực công nghiệp chế biến chế tạo tiếp tục dẫn đầu với mức tăng 8,5%.",
    "Thu hút đầu tư nước ngoài đạt 1,2 tỷ USD, tăng 15% so với cùng kỳ năm ngoái.",
    "Thành phố đẩy mạnh cải cách thủ tục hành chính để cải thiện môi trường kinh doanh.",
    "Các chỉ tiêu hạ tầng giao thông và đô thị hoàn thành đúng tiến độ đề ra.",
]


@pytest.fixture
def sample_text() -> str:
    return SAMPLE_VI_TEXT


@pytest.fixture
def sample_sentences() -> list[str]:
    return list(SAMPLE_SENTENCES)

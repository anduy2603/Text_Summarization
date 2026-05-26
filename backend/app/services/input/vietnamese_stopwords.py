"""Shared Vietnamese stopwords for TF-IDF and TextRank summarizers.

Covers function words, conjunctions, prepositions, auxiliaries, and pronouns
that rarely carry semantic content in Vietnamese news-domain text.
"""
from __future__ import annotations

VIETNAMESE_STOPWORDS: frozenset[str] = frozenset({
    # Liên từ (conjunctions)
    "và", "hay", "hoặc", "nhưng", "mà", "thì", "rằng", "vì", "nên",
    "bởi", "do", "tuy", "dù", "song", "nếu", "thế nhưng",
    # Giới từ (prepositions)
    "của", "cho", "với", "trong", "trên", "dưới", "tại", "từ", "đến", "về",
    "ngoài", "giữa", "bên", "phía", "qua", "theo", "bằng", "như", "sau",
    "trước", "vào", "ra", "lên", "xuống", "cùng", "suốt",
    # Mạo từ / từ chỉ số lượng (determiners)
    "các", "những", "một", "mọi", "cả", "toàn", "tất", "từng", "mỗi",
    "vài", "đôi",
    # Chỉ từ (demonstratives)
    "này", "đó", "kia", "đây", "đấy", "ấy", "nọ",
    # Trợ động từ / từ hư (auxiliaries)
    "là", "đã", "đang", "sẽ", "sắp", "bị", "không", "chưa", "chẳng", "chả",
    "được", "cần", "phải", "hãy", "đừng",
    # Đại từ nhân xưng (pronouns)
    "tôi", "bạn", "họ", "ta", "mình", "nó", "chúng",
    "ông", "bà", "anh", "chị", "em", "hắn", "cô", "chú",
    # Đại từ nghi vấn (interrogatives)
    "ai", "gì", "nào", "đâu", "bao", "sao",
    # Phó từ chỉ mức độ / tần suất (degree / frequency adverbs)
    "rất", "quá", "khá", "cũng", "đều", "chỉ", "vẫn", "còn", "lại", "nữa",
    "thêm", "rồi", "vậy", "thế", "thường", "luôn", "ngay", "liền",
    "thật", "thực", "chính", "đúng", "vừa", "mới",
    # Từ chỉ thời gian dùng như hư từ (time words used as function-like)
    "khi", "lúc", "hồi",
    # Từ kết nối / chuyển tiếp (connectives / discourse markers)
    "để", "nhằm", "tức", "nghĩa là", "đó là",
    "vì vậy", "do đó", "vì thế", "cho nên", "bởi vì",
    "tuy nhiên", "mặc dù", "tuy vậy", "dù sao",
    "theo đó", "qua đó", "từ đó", "về phía",
})

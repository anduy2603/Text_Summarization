from __future__ import annotations

import re
import unicodedata

# Standalone noise lines common in news uploads (PDF/DOCX/web).
_NOISE_LINE_RE = re.compile(
    r"^\s*(?:"
    r"quảng\s*cáo|quang\s*cao"
    r"|(?:ảnh|anh|hình\s*ảnh|photo|image)\s*:"
    r"|(?:đồ\s*hoạ|do\s*hoa|graphic|infographic)\s*:"
    r"|(?:bảng|bang|table)\s*:"
    r"|(?:nguồn|nguon|source)\s*:"
    r"|(?:theo|credit)\s*:"
    r"|(?:xem\s*thêm|xem\s*them|đọc\s*thêm|doc\s*them)"
    r"|(?:chia\s*sẻ|chia\s*se|like\s*page)"
    r")\b",
    flags=re.IGNORECASE | re.UNICODE,
)

_CAPTION_ONLY_RE = re.compile(
    r"^\s*(?:ảnh|anh|hình\s*ảnh|photo|image|đồ\s*hoạ|do\s*hoa)\s*:\s*.+$",
    flags=re.IGNORECASE | re.UNICODE,
)

_METADATA_ONLY_RE = re.compile(
    r"^\s*(?:"
    r"(?:nguồn|nguon|source|theo|credit)\s*:[^\n]{0,120}"
    r"|(?:ap|reuters|afp|getty)\b[^\n]{0,80}"
    r")\s*$",
    flags=re.IGNORECASE | re.UNICODE,
)

_MIN_CONTENT_LINE_CHARS = 12


def _normalize_line_key(line: str) -> str:
    folded = unicodedata.normalize("NFC", line.strip().casefold())
    folded = re.sub(r"\s+", " ", folded)
    return folded


def is_noise_line(line: str) -> bool:
    if not line or not line.strip():
        return True
    stripped = line.strip()
    if len(stripped) < _MIN_CONTENT_LINE_CHARS:
        if not re.search(r"[.!?…]", stripped):
            return True
    if _NOISE_LINE_RE.search(stripped):
        return True
    if _CAPTION_ONLY_RE.match(stripped):
        return True
    if _METADATA_ONLY_RE.match(stripped):
        return True
    return False


def filter_document_lines(lines: list[str]) -> tuple[list[str], dict[str, int]]:
    """
    Drop ads/captions/metadata/duplicate titles and ultra-short junk lines.
    """
    stats = {
        "lines_in": len(lines),
        "lines_dropped_noise": 0,
        "lines_dropped_duplicate_title": 0,
        "lines_out": 0,
    }
    kept: list[str] = []
    prev_key: str | None = None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            kept.append("")
            prev_key = None
            continue
        if is_noise_line(stripped):
            stats["lines_dropped_noise"] += 1
            continue
        key = _normalize_line_key(stripped)
        if prev_key and key == prev_key:
            stats["lines_dropped_duplicate_title"] += 1
            continue
        kept.append(stripped)
        prev_key = key
    stats["lines_out"] = len([ln for ln in kept if ln])
    return kept, stats

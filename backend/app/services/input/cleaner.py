import re

from app.services.input.document_line_filters import filter_document_lines


# Zero-width and BOM-like characters that often leak from PDFs/web.
_ZW_RE = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]")
# Other C0 controls except tab/newline; allow \n \t for structure.
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
# News-source attribution prefix, e.g. "(D\u00e2n tr\u00ed) - ", "(VnExpress) - ", "(TTXVN) - "
# Appears at the start of the first paragraph in Vietnamese online news articles.
_NEWS_ATTR_RE = re.compile(r"^\([^)]{1,40}\)\s*[-\u2013]\s+", re.UNICODE)


def _normalize_whitespace_lines(text: str) -> list[str]:
    lines = [ln.strip() for ln in text.splitlines()]
    cleaned_lines: list[str] = []
    blank_run = 0
    for line in lines:
        if not line:
            blank_run += 1
            if blank_run <= 1:
                cleaned_lines.append("")
            continue
        blank_run = 0
        line = re.sub(r"[ \t]{2,}", " ", line)
        # Strip news-source attribution prefix at start of line
        line = _NEWS_ATTR_RE.sub("", line).strip()
        if line:
            cleaned_lines.append(line)
    return cleaned_lines


def clean_text(text: str) -> str:
    if not text:
        return ""
    t = text
    t = _ZW_RE.sub("", t)
    t = _CTRL_RE.sub("", t)
    t = t.replace("\xa0", " ")
    t = t.replace("\r\n", "\n").replace("\r", "\n")

    lines = _normalize_whitespace_lines(t)
    filtered_lines, _line_stats = filter_document_lines(lines)
    t = "\n".join(filtered_lines)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

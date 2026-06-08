from __future__ import annotations

import fitz

from app.services.input.exceptions import InputLoadError


import re as _re

_ENDS_SENTENCE_RE = _re.compile(r"[.!?…]\s*$")


def _extract_page_text(page: "fitz.Page") -> str:
    """
    Extract text from one PDF page using text blocks (paragraph units).
    Blocks preserve natural paragraph breaks better than raw line-by-line text,
    reducing fragmented sentences caused by visual line wraps in the PDF layout.
    """
    try:
        blocks = page.get_text("blocks")  # list of (x0,y0,x1,y1,text,block_no,type)
    except Exception:
        # Fallback to plain text if blocks API fails
        return (page.get_text("text") or "").strip()

    # Sort by vertical then horizontal position (reading order)
    text_blocks = sorted(
        (b for b in blocks if b[6] == 0 and b[4].strip()),  # type 0 = text block
        key=lambda b: (round(b[1] / 10) * 10, b[0]),
    )
    paragraphs: list[str] = []
    for block in text_blocks:
        raw = block[4].strip()
        if not raw:
            continue
        # Join soft-wrapped lines within a block: if an intermediate line does
        # not end with sentence punctuation, it is a continuation of the next line.
        lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]
        if len(lines) <= 1:
            paragraphs.append(raw.replace("\n", " ").strip())
            continue
        joined_lines: list[str] = []
        buf = ""
        for ln in lines:
            if buf:
                buf = buf + " " + ln
            else:
                buf = ln
            if _ENDS_SENTENCE_RE.search(ln):
                joined_lines.append(buf)
                buf = ""
        if buf:
            joined_lines.append(buf)
        paragraphs.append("\n".join(joined_lines))

    return "\n\n".join(paragraphs).strip()


def load_pdf_bytes(content: bytes) -> str:
    if not content:
        raise InputLoadError("PDF file is empty.")
    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        raise InputLoadError("Could not open PDF.") from exc
    try:
        parts: list[str] = []
        for page in doc:
            t = _extract_page_text(page)
            if t:
                parts.append(t)
    finally:
        doc.close()
    text = "\n\n".join(parts).strip()
    if not text:
        raise InputLoadError(
            "PDF không chứa văn bản có thể trích xuất. "
            "Có thể là bản scan ảnh, PDF trống, hoặc chỉ có hình — hãy dùng TXT/DOCX "
            "hoặc bản PDF có lớp văn bản (text layer)."
        )
    return text

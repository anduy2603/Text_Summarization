from __future__ import annotations

import fitz

from app.services.input.exceptions import InputLoadError


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
            t = page.get_text("text") or ""
            t = t.strip()
            if t:
                parts.append(t)
    finally:
        doc.close()
    text = "\n\n".join(parts).strip()
    if not text:
        raise InputLoadError("PDF contains no extractable text.")
    return text

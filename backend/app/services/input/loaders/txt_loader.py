from __future__ import annotations

import chardet

from app.services.input.exceptions import InputLoadError


def load_txt_bytes(content: bytes) -> str:
    if not content:
        raise InputLoadError("TXT file is empty.")
    detected = chardet.detect(content)
    encoding = (detected.get("encoding") or "utf-8").lower()
    try:
        text = content.decode(encoding, errors="replace")
    except LookupError:
        text = content.decode("utf-8", errors="replace")
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        raise InputLoadError("TXT contains no extractable text.")
    return text

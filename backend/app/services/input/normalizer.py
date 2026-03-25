import unicodedata


def normalize_text(text: str) -> str:
    if not text:
        return ""
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = unicodedata.normalize("NFC", t)
    return t.strip()

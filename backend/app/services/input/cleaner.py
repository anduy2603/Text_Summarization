import re


# Zero-width and BOM-like characters that often leak from PDFs/web.
_ZW_RE = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]")
# Other C0 controls except tab/newline; allow \n \t for structure.
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(text: str) -> str:
    if not text:
        return ""
    t = text
    t = _ZW_RE.sub("", t)
    t = _CTRL_RE.sub("", t)
    t = t.replace("\xa0", " ")
    lines = [ln.strip() for ln in t.splitlines()]
    t = "\n".join(line for line in lines if line)
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

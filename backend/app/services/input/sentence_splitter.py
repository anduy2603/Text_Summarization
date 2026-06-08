from __future__ import annotations

import re

_PARAGRAPH_BREAK_RE = re.compile(r"\n{2,}")
_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?…])\s+")
_ENDS_WITH_PUNCT_RE = re.compile(r"[.!?…]\s*$")


def split_paragraphs(text: str) -> list[str]:
    if not text or not text.strip():
        return []
    parts = _PARAGRAPH_BREAK_RE.split(text)
    return [part.strip() for part in parts if part.strip()]


def _split_paragraph_sentences(paragraph: str) -> list[str]:
    paragraph = paragraph.strip()
    if not paragraph:
        return []

    lines = [ln.strip() for ln in paragraph.split("\n") if ln.strip()]
    # Title/sapo blocks without terminal punctuation: keep each line as its own unit.
    if len(lines) > 1 and not re.search(r"[.!?…]", paragraph):
        return lines

    parts = _SENTENCE_BOUNDARY_RE.split(paragraph)
    sentences: list[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if "\n" in part:
            sub_lines = [ln.strip() for ln in part.split("\n") if ln.strip()]
            # If intermediate lines have no sentence-ending punctuation they are
            # likely a single sentence wrapped by PDF/DOCX line breaks — join them.
            if all(not _ENDS_WITH_PUNCT_RE.search(ln) for ln in sub_lines[:-1]):
                sentences.append(" ".join(sub_lines))
            else:
                sentences.extend(sub_lines)
        else:
            sentences.append(part)
    return sentences


def split_sentences(text: str) -> list[str]:
    """
    Paragraph-aware sentence splitting.
    Double newlines are strong boundaries; within a paragraph, split on .!?…
    """
    if not text or not text.strip():
        return []
    sentences: list[str] = []
    for paragraph in split_paragraphs(text):
        sentences.extend(_split_paragraph_sentences(paragraph))
    return [sentence for sentence in sentences if sentence]

from __future__ import annotations

import re
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.logger import get_logger
from app.services.input.exceptions import InputLoadError, InputValidationError
from app.services.input.validator import build_url_request, validate_url

_logger = get_logger(__name__)
_CHARSET_RE = re.compile(r"charset=([\w.-]+)", flags=re.IGNORECASE)


def _decode_body(body: bytes, content_type_header: str) -> str:
    match = _CHARSET_RE.search(content_type_header or "")
    if match:
        encoding = match.group(1).strip().strip('"').strip("'")
        try:
            return body.decode(encoding, errors="replace")
        except LookupError:
            _logger.warning("Unknown charset from response header: %s", encoding)
    return body.decode("utf-8", errors="replace")


def _compact_lines(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def load_url_text(url: str) -> tuple[str, str]:
    """
    Fetch URL and return (raw_text, content_type_or_empty).
    HTML is converted to visible text; non-HTML is decoded from charset/UTF-8.
    """
    validated = validate_url(url)
    req = build_url_request(validated)
    max_bytes = settings.input_url_max_bytes
    chunk = 64 * 1024
    out = bytearray()
    content_type = ""
    raw_content_type = ""
    try:
        with urlopen(req, timeout=settings.input_url_timeout_sec) as resp:  # noqa: S310
            raw_content_type = resp.headers.get("Content-Type", "") or ""
            content_type = raw_content_type.split(";")[0].strip().lower()
            while len(out) < max_bytes + 1:
                block = resp.read(chunk)
                if not block:
                    break
                out.extend(block)
    except HTTPError as exc:
        _logger.exception("HTTP error while fetching URL: %s", validated)
        raise InputLoadError(f"HTTP error fetching URL: {exc.code}") from exc
    except URLError as exc:
        _logger.exception("Network error while fetching URL: %s", validated)
        raise InputLoadError(f"Failed to fetch URL: {exc.reason}") from exc
    except InputValidationError:
        raise
    except Exception as exc:
        _logger.exception("Unexpected fetch error for URL: %s", validated)
        raise InputLoadError("Unexpected error while fetching URL.") from exc

    if len(out) > max_bytes:
        raise InputValidationError(f"Response body exceeds limit ({max_bytes} bytes).")

    body = bytes(out)
    if "html" in content_type or body.lstrip().startswith((b"<", b"<!DOCTYPE", b"<!doctype")):
        soup = BeautifulSoup(body, "lxml")
        for tag in soup(["script", "style", "noscript", "template", "header", "footer", "nav", "aside"]):
            tag.decompose()
        text = _compact_lines(soup.get_text(separator="\n"))
        if not text:
            raise InputLoadError("URL contains no extractable text.")
        return text, content_type or "text/html"

    text = _compact_lines(_decode_body(body, raw_content_type))
    if not text:
        raise InputLoadError("URL response contains no extractable text.")
    return text, content_type or "application/octet-stream"

from __future__ import annotations

from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from bs4 import BeautifulSoup

from app.core.config import settings
from app.services.input.exceptions import InputLoadError, InputValidationError
from app.services.input.validator import build_url_request, validate_url


def load_url_text(url: str) -> tuple[str, str]:
    """
    Fetch URL and return (raw_text, content_type_or_empty).
    HTML is converted to visible text; other types are decoded as UTF-8 with replacement.
    """
    validated = validate_url(url)
    req = build_url_request(validated)
    max_bytes = settings.input_url_max_bytes
    chunk = 64 * 1024
    out = bytearray()
    ctype = ""
    try:
        with urlopen(req, timeout=settings.input_url_timeout_sec) as resp:  # noqa: S310
            raw_ct = resp.headers.get("Content-Type", "") or ""
            ctype = raw_ct.split(";")[0].strip().lower()
            while len(out) < max_bytes + 1:
                block = resp.read(chunk)
                if not block:
                    break
                out.extend(block)
    except HTTPError as exc:
        raise InputLoadError(f"HTTP error fetching URL: {exc.code}") from exc
    except URLError as exc:
        raise InputLoadError(f"Failed to fetch URL: {exc.reason}") from exc
    except InputValidationError:
        raise
    except Exception as exc:
        raise InputLoadError("Unexpected error while fetching URL.") from exc

    if len(out) > max_bytes:
        raise InputValidationError(f"Response body exceeds limit ({max_bytes} bytes).")

    body = bytes(out)
    if "html" in ctype or body.lstrip().startswith((b"<", b"<!DOCTYPE", b"<!doctype")):
        soup = BeautifulSoup(body, "lxml")
        for tag in soup(["script", "style", "noscript", "template"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        return text, ctype or "text/html"

    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        text = body.decode("utf-8", errors="replace")
    return text, ctype or "application/octet-stream"

from __future__ import annotations

import ipaddress
import socket
from pathlib import PurePath
from urllib.parse import urlparse
from urllib.request import Request

from app.core.config import settings
from app.services.input.exceptions import InputValidationError


def _allowed_extensions() -> set[str]:
    return settings.input_allowed_extensions_set


def validate_filename(filename: str | None) -> str:
    if not filename or not filename.strip():
        raise InputValidationError("File name is required.")
    name = PurePath(filename).name
    if not name:
        raise InputValidationError("Invalid file name.")
    suffix = PurePath(name).suffix.lower()
    allowed = _allowed_extensions()
    if suffix not in allowed:
        raise InputValidationError(
            f"Unsupported file type {suffix!r}. Allowed: {', '.join(sorted(allowed))}."
        )
    return name


def validate_file_size(size: int) -> None:
    if size < 0:
        raise InputValidationError("Invalid file size.")
    if size > settings.input_max_file_bytes:
        raise InputValidationError(
            f"File too large (max {settings.input_max_file_bytes} bytes)."
        )


def validate_non_empty_text(text: str, *, label: str = "text") -> str:
    if text is None:
        raise InputValidationError(f"{label} is required.")
    stripped = text.strip()
    if not stripped:
        raise InputValidationError(f"{label} is empty.")
    return stripped


def _hostname_blocked(hostname: str) -> bool:
    h = hostname.lower().strip(".")
    if h in ("localhost", "127.0.0.1", "::1"):
        return True
    return False


def _is_disallowed_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
    )


def _check_url_host_resolves_safe(hostname: str) -> None:
    if _hostname_blocked(hostname):
        if not settings.input_url_allow_private_hosts:
            raise InputValidationError("URL host is not allowed.")
        return
    if settings.input_url_allow_private_hosts:
        return
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise InputValidationError(f"Cannot resolve URL host: {exc}") from exc
    for info in infos:
        sockaddr = info[4]
        if not sockaddr:
            continue
        ip_str = sockaddr[0]
        if _is_disallowed_ip(ip_str):
            raise InputValidationError("URL resolves to a disallowed network address.")


def validate_url(url: str) -> str:
    stripped = validate_non_empty_text(url, label="URL")
    parsed = urlparse(stripped)
    if parsed.scheme not in ("http", "https"):
        raise InputValidationError("URL must use http or https.")
    if not parsed.netloc:
        raise InputValidationError("URL is missing a host.")
    host = parsed.hostname
    if not host:
        raise InputValidationError("URL host is invalid.")
    _check_url_host_resolves_safe(host)
    return stripped


def build_url_request(url: str) -> Request:
    return Request(
        url,
        headers={"User-Agent": settings.input_url_user_agent},
        method="GET",
    )

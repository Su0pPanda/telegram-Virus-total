from __future__ import annotations

from ipaddress import ip_address
from urllib.parse import urlsplit, urlunsplit

from src.domain.enums import InputType
from src.domain.errors import MalformedInputError


def classify_text(raw_value: str) -> tuple[InputType, str]:
    value = raw_value.strip()
    if not value:
        raise MalformedInputError("input is empty")
    try:
        return InputType.IP, str(ip_address(value))
    except ValueError:
        pass
    try:
        parsed = urlsplit(value)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            raise ValueError
        if parsed.username or parsed.password:
            raise ValueError
        hostname = parsed.hostname.lower()
        if ":" in hostname:
            hostname = f"[{hostname}]"
        netloc = hostname
        if parsed.port is not None:
            netloc += f":{parsed.port}"
        normalized = urlunsplit(
            (parsed.scheme.lower(), netloc, parsed.path or "/", parsed.query, "")
        )
        return InputType.URL, normalized
    except (ValueError, UnicodeError) as exc:
        raise MalformedInputError("text is not a supported URL or IP address") from exc


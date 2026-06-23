from math import ceil


def invalid_input_message() -> str:
    return "Send a document, a full http(s) URL, or an IPv4/IPv6 address."


def oversized_file_message(max_bytes: int) -> str:
    return f"This file is too large. The bot limit is {ceil(max_bytes / 1024 / 1024)} MB. You can check it manually on VirusTotal."


def rate_limit_message(retry_after_seconds: int) -> str:
    return f"Too many checks. Please try again in about {max(1, retry_after_seconds)} seconds."


def provider_overload_message() -> str:
    return "VirusTotal is busy or its quota is temporarily exhausted. Please try again later."


def processing_error_message() -> str:
    return "The item could not be checked. Please verify it and try again."


def progress_message() -> str:
    return "No finished report was found. VirusTotal analysis is now in progress..."


import pytest

from src.domain.enums import InputType
from src.domain.errors import MalformedInputError
from src.domain.validators import classify_text


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://example.com/a?b=1", (InputType.URL, "https://example.com/a?b=1")),
        ("  HTTP://EXAMPLE.COM  ", (InputType.URL, "http://example.com/")),
        ("192.0.2.1", (InputType.IP, "192.0.2.1")),
        ("2001:db8::1", (InputType.IP, "2001:db8::1")),
    ],
)
def test_classifies_supported_text(raw, expected) -> None:
    assert classify_text(raw) == expected


@pytest.mark.parametrize("raw", ["example.com", "ftp://example.com", "999.1.1.1", "hello world", ""])
def test_rejects_ambiguous_or_unsupported_text(raw) -> None:
    with pytest.raises(MalformedInputError):
        classify_text(raw)


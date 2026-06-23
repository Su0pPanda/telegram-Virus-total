from __future__ import annotations

import pytest

from src.domain.entities import CheckResult
from src.domain.enums import InputType, ResultSource
from src.domain.errors import MalformedInputError, ProviderQuotaError
from src.services.lookup_service import LookupService


class FakeProvider:
    async def lookup_url(self, value: str, *, request_id: str) -> CheckResult:
        return make_result(request_id, InputType.URL, value)

    async def lookup_ip(self, value: str, *, request_id: str) -> CheckResult:
        return make_result(request_id, InputType.IP, value)


def make_result(request_id: str, input_type: InputType, value: str) -> CheckResult:
    return CheckResult(
        request_id=request_id,
        input_type=input_type,
        subject_label=value,
        detection_count=0,
        engine_total=90,
        report_url="https://www.virustotal.com/gui/report",
        source=ResultSource.PROVIDER_EXISTING,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("value", "input_type"),
    [("https://example.com", InputType.URL), ("2001:db8::5", InputType.IP)],
)
async def test_lookup_dispatches_by_classified_input(value, input_type) -> None:
    result = await LookupService(FakeProvider()).lookup(
        value, request_id="r1", user_id="u1", chat_id="c1"
    )
    assert result.input_type is input_type


@pytest.mark.asyncio
async def test_malformed_text_never_reaches_provider() -> None:
    with pytest.raises(MalformedInputError):
        await LookupService(FakeProvider()).lookup("not an indicator", request_id="r1", user_id="u1", chat_id="c1")


@pytest.mark.asyncio
async def test_provider_quota_error_is_preserved() -> None:
    class QuotaProvider(FakeProvider):
        async def lookup_url(self, value: str, *, request_id: str):
            raise ProviderQuotaError("quota")

    with pytest.raises(ProviderQuotaError):
        await LookupService(QuotaProvider()).lookup("https://example.com", request_id="r1", user_id="u1", chat_id="c1")

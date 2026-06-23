from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from src.domain.enums import ResultSource
from src.domain.errors import ProcessingError, ProviderQuotaError
from src.integrations.virustotal_client import VirusTotalClient


@dataclass
class FakeResponse:
    status: int
    payload: Any

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.requests: list[tuple[str, str]] = []

    def request(self, method: str, url: str, **_kwargs):
        self.requests.append((method, url))
        return self.responses.pop(0)


def file_payload(status: str | None = None) -> dict[str, Any]:
    attributes: dict[str, Any] = {
        "last_analysis_stats": {"malicious": 2, "suspicious": 1, "undetected": 67},
        "last_analysis_results": {
            "Engine A": {"category": "malicious", "result": "Trojan.Test"},
        },
    }
    if status is not None:
        attributes["status"] = status
        attributes["stats"] = attributes.pop("last_analysis_stats")
    return {"data": {"id": "analysis-1", "attributes": attributes}}


@pytest.mark.asyncio
async def test_hash_lookup_normalizes_provider_result() -> None:
    session = FakeSession([FakeResponse(200, file_payload())])
    client = VirusTotalClient(session, "key")

    result = await client.lookup_file_by_hash("a" * 64, request_id="r1", display_name="sample.bin")

    assert result is not None
    assert result.detection_count == 3
    assert result.engine_total == 70
    assert result.highlights == ["Trojan.Test"]
    assert result.source is ResultSource.PROVIDER_EXISTING


@pytest.mark.asyncio
async def test_hash_lookup_returns_none_for_unknown_file() -> None:
    client = VirusTotalClient(FakeSession([FakeResponse(404, {})]), "key")
    assert await client.lookup_file_by_hash("b" * 64, request_id="r1", display_name="x") is None


@pytest.mark.asyncio
async def test_file_upload_returns_analysis_id(tmp_path) -> None:
    path = tmp_path / "sample.bin"
    path.write_bytes(b"sample")
    client = VirusTotalClient(
        FakeSession([FakeResponse(200, {"data": {"id": "analysis-upload"}})]), "key"
    )
    assert await client.submit_file_for_analysis("a" * 64, path, "sample.bin") == "analysis-upload"


@pytest.mark.asyncio
async def test_poll_returns_new_result_without_waiting() -> None:
    client = VirusTotalClient(FakeSession([FakeResponse(200, file_payload("completed"))]), "key")
    result = await client.poll_analysis_result(
        "analysis-1",
        request_id="r1",
        input_type=result_input_type(),
        subject_label="sample.bin",
        report_url="https://www.virustotal.com/gui/file/hash",
    )
    assert result.source is ResultSource.PROVIDER_NEW


def result_input_type():
    from src.domain.enums import InputType

    return InputType.FILE


@pytest.mark.asyncio
async def test_quota_response_is_retryable_domain_error() -> None:
    client = VirusTotalClient(FakeSession([FakeResponse(429, {})]), "key")
    with pytest.raises(ProviderQuotaError):
        await client.lookup_file_by_hash("c" * 64, request_id="r1", display_name="x")


@pytest.mark.asyncio
async def test_malformed_payload_is_not_exposed() -> None:
    client = VirusTotalClient(FakeSession([FakeResponse(200, {"unexpected": True})]), "key")
    with pytest.raises(ProcessingError):
        await client.lookup_file_by_hash("d" * 64, request_id="r1", display_name="x")

from __future__ import annotations

from typing import Any

import pytest

from src.domain.enums import InputType
from src.domain.errors import ProviderUnavailableError
from src.integrations.virustotal_client import VirusTotalClient
from tests.contract.test_virustotal_file_contract import FakeResponse, FakeSession


def lookup_payload() -> dict[str, Any]:
    return {
        "data": {
            "attributes": {
                "last_analysis_stats": {"malicious": 1, "suspicious": 0, "harmless": 89},
                "last_analysis_results": {
                    "Engine A": {"category": "malicious", "result": "phishing"}
                },
            }
        }
    }


@pytest.mark.asyncio
async def test_url_lookup_returns_normalized_report() -> None:
    client = VirusTotalClient(FakeSession([FakeResponse(200, lookup_payload())]), "key")
    result = await client.lookup_url("https://example.com/path", request_id="r1")
    assert result.input_type is InputType.URL
    assert result.detection_count == 1
    assert result.report_url.startswith("https://www.virustotal.com/gui/url/")


@pytest.mark.asyncio
async def test_ip_lookup_returns_normalized_report() -> None:
    client = VirusTotalClient(FakeSession([FakeResponse(200, lookup_payload())]), "key")
    result = await client.lookup_ip("203.0.113.5", request_id="r2")
    assert result.input_type is InputType.IP
    assert result.report_url.endswith("/203.0.113.5")


@pytest.mark.asyncio
async def test_provider_outage_is_retryable() -> None:
    client = VirusTotalClient(FakeSession([FakeResponse(503, {})]), "key")
    with pytest.raises(ProviderUnavailableError):
        await client.lookup_ip("203.0.113.5", request_id="r2")


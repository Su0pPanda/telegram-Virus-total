from __future__ import annotations

import asyncio
import base64
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiohttp

from src.domain.entities import CheckResult
from src.domain.enums import InputType, ResultSource
from src.domain.errors import (
    AnalysisTimeoutError,
    ProcessingError,
    ProviderQuotaError,
    ProviderUnavailableError,
)


class VirusTotalClient:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_key: str,
        *,
        base_url: str = "https://www.virustotal.com/api/v3",
        poll_interval: float = 5.0,
        poll_timeout: float = 170.0,
    ) -> None:
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.headers = {"x-apikey": api_key}
        self.poll_interval = poll_interval
        self.poll_timeout = poll_timeout

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        allow_not_found: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        try:
            async with self.session.request(
                method, f"{self.base_url}{path}", headers=self.headers, **kwargs
            ) as response:
                if allow_not_found and response.status == 404:
                    return None
                if response.status == 429:
                    raise ProviderQuotaError("VirusTotal quota exhausted")
                if response.status >= 500:
                    raise ProviderUnavailableError("VirusTotal is temporarily unavailable")
                if response.status >= 400:
                    raise ProcessingError(f"VirusTotal rejected the request ({response.status})")
                payload = await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise ProviderUnavailableError("VirusTotal request failed") from exc
        if not isinstance(payload, dict):
            raise ProcessingError("VirusTotal returned an invalid payload")
        return payload

    def _normalize(
        self,
        payload: dict[str, Any],
        *,
        request_id: str,
        input_type: InputType,
        subject_label: str,
        source: ResultSource,
        report_url: str,
    ) -> CheckResult:
        try:
            attributes = payload["data"]["attributes"]
            stats = attributes.get("last_analysis_stats") or attributes.get("stats") or {}
            detection_count = int(stats.get("malicious", 0)) + int(stats.get("suspicious", 0))
            engine_total = sum(int(value) for value in stats.values())
            analysis_results = attributes.get("last_analysis_results", {})
        except (KeyError, TypeError, ValueError) as exc:
            raise ProcessingError("VirusTotal result is missing required fields") from exc
        highlights = [
            str(item.get("result") or engine)
            for engine, item in analysis_results.items()
            if isinstance(item, dict) and item.get("category") in {"malicious", "suspicious"}
        ][:5]
        return CheckResult(
            request_id=request_id,
            input_type=input_type,
            subject_label=subject_label,
            detection_count=detection_count,
            engine_total=engine_total,
            highlights=highlights,
            report_url=report_url,
            source=source,
            completed_at=datetime.now(UTC),
        )

    async def lookup_file_by_hash(self, sha256: str, *, request_id: str, display_name: str) -> CheckResult | None:
        payload = await self._request_json("GET", f"/files/{sha256}", allow_not_found=True)
        if payload is None:
            return None
        return self._normalize(
            payload,
            request_id=request_id,
            input_type=InputType.FILE,
            subject_label=display_name,
            source=ResultSource.PROVIDER_EXISTING,
            report_url=f"https://www.virustotal.com/gui/file/{sha256}",
        )

    async def submit_file_for_analysis(self, sha256: str, file_path: Path, display_name: str) -> str:
        with file_path.open("rb") as file_handle:
            form = aiohttp.FormData()
            form.add_field("file", file_handle, filename=display_name, content_type="application/octet-stream")
            payload = await self._request_json("POST", "/files", data=form)
        try:
            return str(payload["data"]["id"])
        except (KeyError, TypeError) as exc:
            raise ProcessingError("VirusTotal upload response has no analysis id") from exc

    async def poll_analysis_result(
        self,
        analysis_id: str,
        *,
        request_id: str,
        input_type: InputType,
        subject_label: str,
        report_url: str,
    ) -> CheckResult:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self.poll_timeout
        while loop.time() < deadline:
            payload = await self._request_json("GET", f"/analyses/{analysis_id}")
            try:
                status = payload["data"]["attributes"]["status"]
            except (KeyError, TypeError) as exc:
                raise ProcessingError("VirusTotal analysis response has no status") from exc
            if status == "completed":
                return self._normalize(
                    payload,
                    request_id=request_id,
                    input_type=input_type,
                    subject_label=subject_label,
                    source=ResultSource.PROVIDER_NEW,
                    report_url=report_url,
                )
            if status in {"failed", "error"}:
                raise ProcessingError("VirusTotal analysis failed")
            await asyncio.sleep(self.poll_interval)
        raise AnalysisTimeoutError("VirusTotal analysis timed out")

    async def lookup_url(self, url: str, *, request_id: str) -> CheckResult:
        url_id = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
        payload = await self._request_json("GET", f"/urls/{url_id}", allow_not_found=True)
        if payload is None:
            submitted = await self._request_json("POST", "/urls", data={"url": url})
            try:
                analysis_id = str(submitted["data"]["id"])
            except (KeyError, TypeError) as exc:
                raise ProcessingError("VirusTotal URL response has no analysis id") from exc
            return await self.poll_analysis_result(
                analysis_id,
                request_id=request_id,
                input_type=InputType.URL,
                subject_label=url,
                report_url=f"https://www.virustotal.com/gui/url/{url_id}",
            )
        return self._normalize(
            payload,
            request_id=request_id,
            input_type=InputType.URL,
            subject_label=url,
            source=ResultSource.PROVIDER_EXISTING,
            report_url=f"https://www.virustotal.com/gui/url/{url_id}",
        )

    async def lookup_ip(self, ip_address: str, *, request_id: str) -> CheckResult:
        payload = await self._request_json("GET", f"/ip_addresses/{ip_address}")
        return self._normalize(
            payload,
            request_id=request_id,
            input_type=InputType.IP,
            subject_label=ip_address,
            source=ResultSource.PROVIDER_EXISTING,
            report_url=f"https://www.virustotal.com/gui/ip-address/{ip_address}",
        )


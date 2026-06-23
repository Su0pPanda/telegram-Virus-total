from __future__ import annotations

from src.domain.entities import CheckRequest, CheckResult
from src.domain.enums import InputType
from src.domain.validators import classify_text
from src.integrations.virustotal_client import VirusTotalClient


class LookupService:
    def __init__(self, provider: VirusTotalClient) -> None:
        self.provider = provider

    async def lookup(
        self,
        raw_value: str,
        *,
        request_id: str,
        user_id: str,
        chat_id: str,
    ) -> CheckResult:
        input_type, value = classify_text(raw_value)
        request = CheckRequest(
            request_id=request_id,
            user_id=user_id,
            chat_id=chat_id,
            input_type=input_type,
            submitted_value=value,
            display_name=value,
        )
        if request.input_type is InputType.URL:
            return await self.provider.lookup_url(value, request_id=request.request_id)
        return await self.provider.lookup_ip(value, request_id=request.request_id)


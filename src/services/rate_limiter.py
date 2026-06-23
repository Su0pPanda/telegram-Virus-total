from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import ceil

from src.domain.entities import RateLimitEntry, utc_now
from src.integrations.storage import SQLiteStorage


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int = 0


class RateLimiter:
    def __init__(self, storage: SQLiteStorage, *, limit: int = 5, window_seconds: int = 60) -> None:
        self.storage = storage
        self.limit = limit
        self.window_seconds = window_seconds

    async def check_and_record(
        self,
        user_id: str,
        request_id: str,
        *,
        now: datetime | None = None,
    ) -> RateLimitDecision:
        accepted, retry_after = await self.storage.try_add_rate_entry(
            RateLimitEntry(user_id=user_id, request_id=request_id, counted_at=now or utc_now()),
            limit=self.limit,
            window_seconds=self.window_seconds,
        )
        return RateLimitDecision(accepted, ceil(retry_after) if not accepted else 0)


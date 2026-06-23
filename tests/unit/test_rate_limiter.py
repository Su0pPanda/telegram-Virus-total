from datetime import UTC, datetime, timedelta

import pytest

from src.integrations.storage import SQLiteStorage
from src.services.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_sixth_request_in_rolling_window_is_rejected(database_path) -> None:
    storage = SQLiteStorage(database_path)
    await storage.initialize()
    limiter = RateLimiter(storage, limit=5, window_seconds=60)
    now = datetime(2026, 1, 1, tzinfo=UTC)

    decisions = [
        await limiter.check_and_record("user", f"r{index}", now=now + timedelta(seconds=index))
        for index in range(6)
    ]

    assert all(decision.allowed for decision in decisions[:5])
    assert not decisions[5].allowed
    assert decisions[5].retry_after_seconds == 55


@pytest.mark.asyncio
async def test_expired_entry_allows_next_request(database_path) -> None:
    storage = SQLiteStorage(database_path)
    await storage.initialize()
    limiter = RateLimiter(storage, limit=1, window_seconds=60)
    now = datetime(2026, 1, 1, tzinfo=UTC)
    assert (await limiter.check_and_record("user", "old", now=now)).allowed
    assert (await limiter.check_and_record("user", "new", now=now + timedelta(seconds=60))).allowed


@pytest.mark.asyncio
async def test_limits_are_independent_per_user(database_path) -> None:
    storage = SQLiteStorage(database_path)
    await storage.initialize()
    limiter = RateLimiter(storage, limit=1, window_seconds=60)
    now = datetime(2026, 1, 1, tzinfo=UTC)
    assert (await limiter.check_and_record("a", "a1", now=now)).allowed
    assert (await limiter.check_and_record("b", "b1", now=now)).allowed


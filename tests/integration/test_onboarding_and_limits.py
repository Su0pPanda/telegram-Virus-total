from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from src.bot.handlers.start import handle_start
from src.bot.middleware.rate_limit import RateLimitMiddleware
from src.services.rate_limiter import RateLimitDecision


@dataclass
class FakeUser:
    id: int = 42


@dataclass
class FakeMessage:
    text: str | None = "https://example.com"
    document: Any = None
    from_user: FakeUser = field(default_factory=FakeUser)
    replies: list[dict[str, Any]] = field(default_factory=list)

    async def answer(self, text: str, **kwargs: Any) -> None:
        self.replies.append({"text": text, **kwargs})

    async def answer_photo(self, photo: Any, **kwargs: Any) -> None:
        self.replies.append({"photo": photo, **kwargs})


@pytest.mark.asyncio
async def test_start_sends_one_photo_with_guidance_and_buttons(tmp_path: Path) -> None:
    image = tmp_path / "welcome.png"
    image.write_bytes(b"image")
    message = FakeMessage(text="/start")
    await handle_start(message, welcome_image=image)
    assert len(message.replies) == 1
    assert "file" in message.replies[0]["caption"].lower()
    assert len(message.replies[0]["reply_markup"].inline_keyboard) == 3


@pytest.mark.asyncio
async def test_rate_limit_middleware_stops_handler_on_sixth_request() -> None:
    class DenyingLimiter:
        async def check_and_record(self, _user_id: str, _request_id: str):
            return RateLimitDecision(False, 30)

    called = False

    async def handler(_event, _data):
        nonlocal called
        called = True

    event = FakeMessage()
    await RateLimitMiddleware(DenyingLimiter())(handler, event, {})
    assert not called
    assert "30 seconds" in event.replies[0]["text"]


@pytest.mark.asyncio
async def test_rate_limit_middleware_passes_shared_request_context() -> None:
    class AllowingLimiter:
        async def check_and_record(self, _user_id: str, _request_id: str):
            return RateLimitDecision(True)

    received: dict[str, Any] = {}

    async def handler(_event, data):
        received.update(data)

    await RateLimitMiddleware(AllowingLimiter())(handler, FakeMessage(), {})
    assert received["rate_limit_checked"] is True
    assert received["request_id"]

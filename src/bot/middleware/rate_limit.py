from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.bot.presenters.messages import rate_limit_message
from src.services.rate_limiter import RateLimiter


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, rate_limiter: RateLimiter) -> None:
        self.rate_limiter = rate_limiter

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        text = getattr(event, "text", None)
        document = getattr(event, "document", None)
        user = getattr(event, "from_user", None)
        is_check = document is not None or (isinstance(text, str) and text and not text.startswith("/"))
        if not is_check or user is None:
            return await handler(event, data)
        request_id = str(uuid4())
        decision = await self.rate_limiter.check_and_record(str(user.id), request_id)
        if not decision.allowed:
            await event.answer(rate_limit_message(decision.retry_after_seconds))
            return None
        data["request_id"] = request_id
        data["rate_limit_checked"] = True
        return await handler(event, data)


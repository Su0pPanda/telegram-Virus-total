from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from time import monotonic
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class DuplicateUpdateMiddleware(BaseMiddleware):
    """Ignore repeated message and callback-query updates from Telegram."""

    def __init__(self, ttl_seconds: float = 300.0) -> None:
        self.ttl_seconds = ttl_seconds
        self._seen: dict[tuple[str, int | str, int | None], float] = {}
        self._lock = asyncio.Lock()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        key = self._deduplication_key(event)
        if key is None:
            return await handler(event, data)

        now = monotonic()
        async with self._lock:
            cutoff = now - self.ttl_seconds
            self._seen = {
                seen_key: seen_at
                for seen_key, seen_at in self._seen.items()
                if seen_at >= cutoff
            }
            if key in self._seen:
                return None
            self._seen[key] = now

        return await handler(event, data)

    @staticmethod
    def _deduplication_key(
        event: TelegramObject,
    ) -> tuple[str, int | str, int | None] | None:
        callback_query = getattr(event, "callback_query", None)
        callback_id = getattr(callback_query, "id", None)
        if isinstance(callback_id, str) and callback_id:
            return ("callback", callback_id, None)

        message = getattr(event, "message", None)
        chat = getattr(message, "chat", None)
        chat_id = getattr(chat, "id", None)
        message_id = getattr(message, "message_id", None)
        if isinstance(chat_id, int) and isinstance(message_id, int):
            return ("message", chat_id, message_id)
        return None

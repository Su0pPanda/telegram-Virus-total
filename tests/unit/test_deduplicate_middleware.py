from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.bot.middleware.deduplicate import DuplicateUpdateMiddleware


@dataclass
class FakeChat:
    id: int


@dataclass
class FakeMessage:
    chat: FakeChat
    message_id: int


@dataclass
class FakeUpdate:
    message: FakeMessage | None = None
    callback_query: "FakeCallbackQuery | None" = None


@dataclass
class FakeCallbackQuery:
    id: str


@pytest.mark.asyncio
async def test_duplicate_message_is_handled_only_once() -> None:
    middleware = DuplicateUpdateMiddleware()
    calls = 0

    async def handler(_event, _data):
        nonlocal calls
        calls += 1

    first = FakeUpdate(FakeMessage(FakeChat(42), 7))
    duplicate = FakeUpdate(FakeMessage(FakeChat(42), 7))

    await middleware(handler, first, {})
    await middleware(handler, duplicate, {})

    assert calls == 1


@pytest.mark.asyncio
async def test_same_message_id_in_different_chats_is_not_duplicate() -> None:
    middleware = DuplicateUpdateMiddleware()
    calls = 0

    async def handler(_event, _data):
        nonlocal calls
        calls += 1

    await middleware(handler, FakeUpdate(FakeMessage(FakeChat(1), 7)), {})
    await middleware(handler, FakeUpdate(FakeMessage(FakeChat(2), 7)), {})

    assert calls == 2


@pytest.mark.asyncio
async def test_non_message_update_is_passed_through() -> None:
    middleware = DuplicateUpdateMiddleware()
    calls = 0

    async def handler(_event, _data):
        nonlocal calls
        calls += 1

    await middleware(handler, FakeUpdate(None), {})

    assert calls == 1


@pytest.mark.asyncio
async def test_duplicate_callback_query_is_handled_only_once() -> None:
    middleware = DuplicateUpdateMiddleware()
    calls = 0

    async def handler(_event, _data):
        nonlocal calls
        calls += 1

    callback = FakeCallbackQuery("callback-123")
    await middleware(handler, FakeUpdate(callback_query=callback), {})
    await middleware(handler, FakeUpdate(callback_query=callback), {})

    assert calls == 1


@pytest.mark.asyncio
async def test_different_callback_queries_are_both_handled() -> None:
    middleware = DuplicateUpdateMiddleware()
    calls = 0

    async def handler(_event, _data):
        nonlocal calls
        calls += 1

    await middleware(handler, FakeUpdate(callback_query=FakeCallbackQuery("first")), {})
    await middleware(handler, FakeUpdate(callback_query=FakeCallbackQuery("second")), {})

    assert calls == 2

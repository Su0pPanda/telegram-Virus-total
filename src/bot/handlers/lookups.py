from __future__ import annotations

from uuid import uuid4

from aiogram import F, Router
from aiogram.types import Message

from src.bot.presenters.lookup_results import present_lookup_result
from src.bot.presenters.messages import (
    invalid_input_message,
    processing_error_message,
    provider_overload_message,
    rate_limit_message,
)
from src.domain.errors import MalformedInputError, ProcessingError, ProviderError
from src.services.lookup_service import LookupService
from src.services.rate_limiter import RateLimiter


router = Router(name="lookups")


@router.message(F.text)
async def handle_text_lookup(
    message: Message,
    lookup_service: LookupService,
    rate_limiter: RateLimiter,
    request_id: str | None = None,
    rate_limit_checked: bool = False,
) -> None:
    if not message.text or not message.from_user or message.text.startswith("/"):
        return
    current_request_id = request_id or str(uuid4())
    if not rate_limit_checked:
        decision = await rate_limiter.check_and_record(str(message.from_user.id), current_request_id)
        if not decision.allowed:
            await message.answer(rate_limit_message(decision.retry_after_seconds))
            return
    try:
        result = await lookup_service.lookup(
            message.text,
            request_id=current_request_id,
            user_id=str(message.from_user.id),
            chat_id=str(message.chat.id),
        )
        text, keyboard = present_lookup_result(result)
        await message.answer(text, reply_markup=keyboard)
    except MalformedInputError:
        await message.answer(invalid_input_message())
    except ProviderError:
        await message.answer(provider_overload_message())
    except ProcessingError:
        await message.answer(processing_error_message())


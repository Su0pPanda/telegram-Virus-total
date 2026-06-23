from __future__ import annotations

from uuid import uuid4

from aiogram import F, Router
from aiogram.types import Message

from src.bot.keyboards.common import manual_virustotal_keyboard
from src.bot.presenters.file_results import present_file_result
from src.bot.presenters.messages import (
    oversized_file_message,
    processing_error_message,
    progress_message,
    provider_overload_message,
    rate_limit_message,
)
from src.config.settings import Settings
from src.domain.entities import CheckRequest
from src.domain.enums import InputType
from src.domain.errors import FileTooLargeError, ProcessingError, ProviderError
from src.services.file_scanner import FileScanner
from src.services.rate_limiter import RateLimiter


router = Router(name="files")


@router.message(F.document)
async def handle_document(
    message: Message,
    file_scanner: FileScanner,
    rate_limiter: RateLimiter,
    settings: Settings,
    request_id: str | None = None,
    rate_limit_checked: bool = False,
) -> None:
    if message.document is None or message.from_user is None:
        return
    current_request_id = request_id or str(uuid4())
    if not rate_limit_checked:
        decision = await rate_limiter.check_and_record(str(message.from_user.id), current_request_id)
        if not decision.allowed:
            await message.answer(rate_limit_message(decision.retry_after_seconds))
            return
    size = message.document.file_size or 0
    if size > settings.max_upload_bytes:
        await message.answer(
            oversized_file_message(settings.max_upload_bytes),
            reply_markup=manual_virustotal_keyboard(),
        )
        return
    await message.answer("File received. Checking VirusTotal...")
    request = CheckRequest(
        request_id=current_request_id,
        user_id=str(message.from_user.id),
        chat_id=str(message.chat.id),
        input_type=InputType.FILE,
        submitted_value=message.document.file_id,
        display_name=message.document.file_name or "uploaded file",
    )

    async def show_progress(_event: str) -> None:
        await message.answer(progress_message())

    try:
        result = await file_scanner.scan(
            message.bot, request, expected_size=size, on_progress=show_progress
        )
        text, keyboard = present_file_result(result)
        await message.answer(text, reply_markup=keyboard)
    except FileTooLargeError:
        await message.answer(
            oversized_file_message(settings.max_upload_bytes),
            reply_markup=manual_virustotal_keyboard(),
        )
    except ProviderError:
        await message.answer(provider_overload_message())
    except (ProcessingError, OSError):
        await message.answer(processing_error_message())


from __future__ import annotations

from pathlib import Path

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, FSInputFile, Message

from src.bot.keyboards.start import start_keyboard


router = Router(name="start")
DEFAULT_WELCOME_IMAGE = Path("assets/virustotal-welcome.png")
WELCOME_TEXT = (
    "Check suspicious items with VirusTotal. Send a document directly, paste a full "
    "http(s) URL, or send an IPv4/IPv6 address. Uploaded files are removed after checking."
)
HELP_TEXT = {
    "help:file": "Send the file as a Telegram document. The automated limit is 100 MB.",
    "help:url": "Paste a complete URL beginning with http:// or https://.",
    "help:ip": "Send one IPv4 or IPv6 address as plain text.",
}


@router.message(CommandStart())
async def handle_start(
    message: Message,
    welcome_image: Path = DEFAULT_WELCOME_IMAGE,
) -> None:
    await message.answer_photo(
        FSInputFile(welcome_image),
        caption=WELCOME_TEXT,
        reply_markup=start_keyboard(),
    )


@router.callback_query(F.data.startswith("help:"))
async def handle_help_callback(callback: CallbackQuery) -> None:
    text = HELP_TEXT.get(callback.data or "", WELCOME_TEXT)
    if callback.message is not None:
        await callback.message.answer(text)
    await callback.answer()


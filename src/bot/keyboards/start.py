from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Check a file", callback_data="help:file")],
            [InlineKeyboardButton(text="Check a URL", callback_data="help:url")],
            [InlineKeyboardButton(text="Check an IP", callback_data="help:ip")],
        ]
    )


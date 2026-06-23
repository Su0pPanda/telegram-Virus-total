from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


VIRUSTOTAL_HOME = "https://www.virustotal.com/gui/home/upload"


def report_keyboard(report_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Open full report", url=report_url)]]
    )


def manual_virustotal_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Open VirusTotal", url=VIRUSTOTAL_HOME)]]
    )


def informational_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Check a file", callback_data="help:file")],
            [InlineKeyboardButton(text="Check a URL", callback_data="help:url")],
            [InlineKeyboardButton(text="Check an IP", callback_data="help:ip")],
        ]
    )

"""Validate configured provider credentials without printing secret values."""

from __future__ import annotations

import asyncio

import aiohttp
from aiogram import Bot

from src.config.settings import Settings
from src.integrations.virustotal_client import VirusTotalClient


async def main() -> None:
    settings = Settings()
    bot = Bot(settings.bot_token.get_secret_value())
    try:
        identity = await bot.get_me()
        if not identity.is_bot:
            raise RuntimeError("Telegram credential does not belong to a bot")
        print("TELEGRAM_AUTH_OK")
    finally:
        await bot.session.close()

    timeout = aiohttp.ClientTimeout(total=settings.request_timeout_seconds)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        client = VirusTotalClient(session, settings.vt_api_key.get_secret_value())
        result = await client.lookup_ip("8.8.8.8", request_id="credential-check")
        if not result.report_url:
            raise RuntimeError("VirusTotal response did not include a report URL")
        print("VIRUSTOTAL_AUTH_OK")


if __name__ == "__main__":
    asyncio.run(main())

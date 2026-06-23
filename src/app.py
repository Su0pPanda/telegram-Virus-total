from __future__ import annotations

import asyncio

import aiohttp
from aiogram import Bot, Dispatcher

from src.bot.middleware.deduplicate import DuplicateUpdateMiddleware
from src.bot.routing import build_router
from src.config.logging import configure_logging
from src.config.settings import Settings
from src.console_control import start_console_stop_listener
from src.integrations.storage import SQLiteStorage
from src.integrations.telegram_files import TelegramFileStore
from src.integrations.virustotal_client import VirusTotalClient
from src.services.file_scanner import FileScanner
from src.services.lookup_service import LookupService
from src.services.rate_limiter import RateLimiter
from src.services.result_cache import ResultCache


async def run() -> None:
    settings = Settings()
    configure_logging(settings.log_level)
    settings.prepare_directories()

    storage = SQLiteStorage(settings.database_path)
    await storage.initialize()
    file_store = TelegramFileStore(
        settings.temp_dir, max_upload_bytes=settings.max_upload_bytes
    )
    await file_store.cleanup_orphans()
    rate_limiter = RateLimiter(
        storage,
        limit=settings.rate_limit_count,
        window_seconds=settings.rate_limit_window_seconds,
    )

    timeout = aiohttp.ClientTimeout(total=settings.request_timeout_seconds)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        provider = VirusTotalClient(
            session,
            settings.vt_api_key.get_secret_value(),
            base_url=settings.vt_base_url,
            poll_interval=settings.poll_interval_seconds,
            poll_timeout=settings.poll_timeout_seconds,
        )
        file_scanner = FileScanner(file_store, ResultCache(storage), provider)
        lookup_service = LookupService(provider)
        dispatcher = Dispatcher()
        dispatcher.update.outer_middleware(DuplicateUpdateMiddleware())
        dispatcher.include_router(build_router(rate_limiter))
        bot = Bot(settings.bot_token.get_secret_value())
        console_stop_requested = asyncio.Event()
        start_console_stop_listener(
            asyncio.get_running_loop(), console_stop_requested.set
        )

        async def stop_from_console() -> None:
            await console_stop_requested.wait()
            await dispatcher.stop_polling()

        console_stop_task = asyncio.create_task(stop_from_console())
        try:
            await dispatcher.start_polling(
                bot,
                file_scanner=file_scanner,
                lookup_service=lookup_service,
                rate_limiter=rate_limiter,
                settings=settings,
            )
        finally:
            console_stop_task.cancel()
            await asyncio.gather(console_stop_task, return_exceptions=True)
            await bot.session.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

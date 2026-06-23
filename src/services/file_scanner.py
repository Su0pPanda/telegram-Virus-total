from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any

from src.domain.entities import CheckRequest, CheckResult
from src.domain.enums import InputType
from src.domain.errors import ProcessingError
from src.integrations.telegram_files import TelegramFileStore
from src.integrations.virustotal_client import VirusTotalClient
from src.services.result_cache import ResultCache


class FileScanner:
    def __init__(
        self,
        file_store: TelegramFileStore,
        cache: ResultCache,
        provider: VirusTotalClient,
    ) -> None:
        self.file_store = file_store
        self.cache = cache
        self.provider = provider

    async def scan(
        self,
        bot: Any,
        request: CheckRequest,
        *,
        expected_size: int,
        on_progress: Callable[[str], Any] | None = None,
    ) -> CheckResult:
        upload = await self.file_store.download(
            bot, request.submitted_value, request.request_id, expected_size
        )
        try:
            if upload.sha256 is None:
                raise ProcessingError("file fingerprint was not computed")
            cached = await self.cache.get(upload.sha256, request)
            if cached is not None:
                return cached
            existing = await self.provider.lookup_file_by_hash(
                upload.sha256,
                request_id=request.request_id,
                display_name=request.display_name,
            )
            if existing is not None:
                await self.cache.save(upload.sha256, request.display_name, existing)
                return existing
            analysis_id = await self.provider.submit_file_for_analysis(
                upload.sha256, upload.path, request.display_name
            )
            if on_progress is not None:
                progress_result = on_progress("analysis_submitted")
                if inspect.isawaitable(progress_result):
                    await progress_result
            result = await self.provider.poll_analysis_result(
                analysis_id,
                request_id=request.request_id,
                input_type=InputType.FILE,
                subject_label=request.display_name,
                report_url=f"https://www.virustotal.com/gui/file/{upload.sha256}",
            )
            await self.cache.save(upload.sha256, request.display_name, result)
            return result
        finally:
            await self.file_store.cleanup(upload)


from __future__ import annotations

from src.domain.entities import CachedFileResult, CheckRequest, CheckResult
from src.domain.enums import ResultSource
from src.integrations.storage import SQLiteStorage


class ResultCache:
    def __init__(self, storage: SQLiteStorage) -> None:
        self.storage = storage

    async def get(self, sha256: str, request: CheckRequest) -> CheckResult | None:
        cached = await self.storage.get_cached_file(sha256)
        if cached is None:
            return None
        return CheckResult(
            request_id=request.request_id,
            input_type=request.input_type,
            subject_label=request.display_name or cached.file_name or sha256,
            detection_count=cached.detection_count,
            engine_total=cached.engine_total,
            highlights=cached.highlights,
            report_url=cached.report_url,
            source=ResultSource.CACHE,
            completed_at=cached.checked_at,
        )

    async def save(self, sha256: str, file_name: str, result: CheckResult) -> None:
        await self.storage.upsert_cached_file(
            CachedFileResult(
                sha256=sha256,
                file_name=file_name,
                detection_count=result.detection_count,
                engine_total=result.engine_total,
                highlights=result.highlights,
                report_url=result.report_url,
                checked_at=result.completed_at,
            )
        )


from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from typing import Any

from src.domain.entities import TemporaryUpload
from src.domain.enums import CleanupStatus
from src.domain.errors import FileTooLargeError, ProcessingError


class TelegramFileStore:
    def __init__(self, temp_dir: Path, *, max_upload_bytes: int) -> None:
        self.temp_dir = temp_dir.resolve()
        self.max_upload_bytes = max_upload_bytes
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def _request_path(self, request_id: str) -> Path:
        safe_id = "".join(character for character in request_id if character.isalnum() or character in "-_")
        if not safe_id:
            raise ProcessingError("invalid request id")
        candidate = (self.temp_dir / f"{safe_id}.upload").resolve()
        if candidate.parent != self.temp_dir:
            raise ProcessingError("temporary upload path escaped its directory")
        return candidate

    async def download(
        self,
        bot: Any,
        file_id: str,
        request_id: str,
        expected_size: int,
    ) -> TemporaryUpload:
        if expected_size > self.max_upload_bytes:
            raise FileTooLargeError("file exceeds configured upload limit")
        path = self._request_path(request_id)
        upload = TemporaryUpload(request_id=request_id, path=path, size_bytes=expected_size)
        try:
            await bot.download(file_id, destination=path)
            actual_size = path.stat().st_size
            if actual_size > self.max_upload_bytes:
                raise FileTooLargeError("downloaded file exceeds configured upload limit")
            upload.size_bytes = actual_size
            upload.sha256 = await asyncio.to_thread(self.calculate_sha256, path)
            return upload
        except BaseException:
            path.unlink(missing_ok=True)
            upload.cleanup_status = CleanupStatus.DELETED
            raise

    @staticmethod
    def calculate_sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    async def cleanup(self, upload: TemporaryUpload) -> None:
        try:
            upload.path.unlink(missing_ok=True)
            upload.cleanup_status = CleanupStatus.DELETED
        except OSError:
            upload.cleanup_status = CleanupStatus.FAILED
            raise

    async def cleanup_orphans(self) -> int:
        removed = 0
        for candidate in self.temp_dir.glob("*.upload"):
            candidate.unlink(missing_ok=True)
            removed += 1
        return removed


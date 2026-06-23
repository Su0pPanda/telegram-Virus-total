from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from src.domain.errors import FileTooLargeError
from src.integrations.telegram_files import TelegramFileStore


class FakeBot:
    def __init__(self, content: bytes) -> None:
        self.content = content

    async def download(self, _file_id: str, destination: Path) -> None:
        destination.write_bytes(self.content)


@pytest.mark.asyncio
async def test_download_streams_hash_and_cleanup(temp_dir: Path) -> None:
    content = b"safe test content"
    store = TelegramFileStore(temp_dir, max_upload_bytes=1024)
    upload = await store.download(FakeBot(content), "telegram-id", "request-1", len(content))

    assert upload.sha256 == hashlib.sha256(content).hexdigest()
    assert upload.path.is_file()

    await store.cleanup(upload)
    await store.cleanup(upload)
    assert not upload.path.exists()


@pytest.mark.asyncio
async def test_size_is_rejected_before_download(temp_dir: Path) -> None:
    store = TelegramFileStore(temp_dir, max_upload_bytes=3)
    with pytest.raises(FileTooLargeError):
        await store.download(FakeBot(b"large"), "telegram-id", "request-1", 5)
    assert list(temp_dir.iterdir()) == []


@pytest.mark.asyncio
async def test_partial_file_is_removed_when_download_fails(temp_dir: Path) -> None:
    class FailingBot:
        async def download(self, _file_id: str, destination: Path) -> None:
            destination.write_bytes(b"partial")
            raise RuntimeError("network dropped")

    store = TelegramFileStore(temp_dir, max_upload_bytes=1024)
    with pytest.raises(RuntimeError):
        await store.download(FailingBot(), "telegram-id", "request-1", 7)
    assert list(temp_dir.iterdir()) == []


def test_request_path_cannot_escape_temp_directory(temp_dir: Path) -> None:
    store = TelegramFileStore(temp_dir, max_upload_bytes=1024)
    path = store._request_path("../../outside")
    assert path.parent == temp_dir.resolve()


@pytest.mark.asyncio
async def test_startup_cleanup_removes_only_upload_artifacts(temp_dir: Path) -> None:
    store = TelegramFileStore(temp_dir, max_upload_bytes=1024)
    (temp_dir / "old.upload").write_bytes(b"old")
    (temp_dir / "keep.txt").write_text("keep")
    assert await store.cleanup_orphans() == 1
    assert not (temp_dir / "old.upload").exists()
    assert (temp_dir / "keep.txt").exists()

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from src.domain.entities import CachedFileResult, CheckRequest, CheckResult, TemporaryUpload
from src.domain.enums import InputType, ResultSource
from src.services.file_scanner import FileScanner


class FakeFileStore:
    def __init__(self, upload: TemporaryUpload) -> None:
        self.upload = upload
        self.cleaned = False

    async def download(self, *_args):
        return self.upload

    async def cleanup(self, _upload):
        self.cleaned = True


class FakeCache:
    def __init__(self, cached: CheckResult | None = None) -> None:
        self.cached = cached
        self.saved: list[tuple[str, CheckResult]] = []

    async def get(self, _sha256: str, _request: CheckRequest):
        return self.cached

    async def save(self, sha256: str, _name: str, result: CheckResult):
        self.saved.append((sha256, result))


class FakeProvider:
    def __init__(self, existing: CheckResult | None, final: CheckResult) -> None:
        self.existing = existing
        self.final = final
        self.uploads = 0

    async def lookup_file_by_hash(self, *_args, **_kwargs):
        return self.existing

    async def submit_file_for_analysis(self, *_args, **_kwargs):
        self.uploads += 1
        return "analysis-1"

    async def poll_analysis_result(self, *_args, **_kwargs):
        return self.final


def result(source: ResultSource) -> CheckResult:
    return CheckResult(
        request_id="request-1",
        input_type=InputType.FILE,
        subject_label="sample.bin",
        detection_count=1,
        engine_total=70,
        report_url="https://www.virustotal.com/gui/file/hash",
        source=source,
    )


def request() -> CheckRequest:
    return CheckRequest(
        request_id="request-1",
        user_id="user-1",
        chat_id="chat-1",
        input_type=InputType.FILE,
        submitted_value="telegram-file",
        display_name="sample.bin",
    )


@pytest.mark.asyncio
async def test_cached_file_skips_provider_and_cleans_upload(tmp_path: Path) -> None:
    upload = TemporaryUpload("request-1", tmp_path / "upload", 4, "a" * 64)
    store = FakeFileStore(upload)
    cache = FakeCache(result(ResultSource.CACHE))
    provider = FakeProvider(None, result(ResultSource.PROVIDER_NEW))

    actual = await FileScanner(store, cache, provider).scan(object(), request(), expected_size=4)

    assert actual.source is ResultSource.CACHE
    assert provider.uploads == 0
    assert store.cleaned


@pytest.mark.asyncio
async def test_unknown_file_uploads_reports_progress_and_is_cached(tmp_path: Path) -> None:
    upload = TemporaryUpload("request-1", tmp_path / "upload", 4, "b" * 64)
    store = FakeFileStore(upload)
    cache = FakeCache()
    provider = FakeProvider(None, result(ResultSource.PROVIDER_NEW))
    progress: list[str] = []

    actual = await FileScanner(store, cache, provider).scan(
        object(), request(), expected_size=4, on_progress=progress.append
    )

    assert actual.source is ResultSource.PROVIDER_NEW
    assert provider.uploads == 1
    assert progress == ["analysis_submitted"]
    assert cache.saved[0][0] == "b" * 64
    assert store.cleaned


@pytest.mark.asyncio
async def test_provider_known_file_skips_upload_and_is_cached(tmp_path: Path) -> None:
    upload = TemporaryUpload("request-1", tmp_path / "upload", 4, "d" * 64)
    store = FakeFileStore(upload)
    cache = FakeCache()
    existing = result(ResultSource.PROVIDER_EXISTING)
    provider = FakeProvider(existing, result(ResultSource.PROVIDER_NEW))

    actual = await FileScanner(store, cache, provider).scan(object(), request(), expected_size=4)

    assert actual.source is ResultSource.PROVIDER_EXISTING
    assert provider.uploads == 0
    assert cache.saved[0][0] == "d" * 64
    assert store.cleaned


@pytest.mark.asyncio
async def test_cleanup_runs_when_provider_fails(tmp_path: Path) -> None:
    upload = TemporaryUpload("request-1", tmp_path / "upload", 4, "c" * 64)
    store = FakeFileStore(upload)

    class FailingProvider(FakeProvider):
        async def lookup_file_by_hash(self, *_args, **_kwargs):
            raise RuntimeError("provider failed")

    with pytest.raises(RuntimeError):
        await FileScanner(store, FakeCache(), FailingProvider(None, result(ResultSource.PROVIDER_NEW))).scan(
            object(), request(), expected_size=4
        )
    assert store.cleaned

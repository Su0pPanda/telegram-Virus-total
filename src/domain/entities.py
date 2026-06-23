from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from src.domain.enums import CleanupStatus, InputType, RequestStatus, ResultSource


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class CheckRequest:
    user_id: str
    chat_id: str
    input_type: InputType
    submitted_value: str
    display_name: str
    request_id: str = field(default_factory=lambda: str(uuid4()))
    status: RequestStatus = RequestStatus.RECEIVED
    created_at: datetime = field(default_factory=utc_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failure_reason: str | None = None


@dataclass(slots=True)
class CheckResult:
    request_id: str
    input_type: InputType
    subject_label: str
    detection_count: int
    engine_total: int
    report_url: str
    source: ResultSource
    highlights: list[str] = field(default_factory=list)
    completed_at: datetime = field(default_factory=utc_now)
    result_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if self.detection_count < 0 or self.engine_total < 0:
            raise ValueError("detection totals cannot be negative")
        if not self.report_url.startswith(("https://", "http://")):
            raise ValueError("report_url must be an HTTP URL")


@dataclass(slots=True)
class CachedFileResult:
    sha256: str
    detection_count: int
    engine_total: int
    report_url: str
    checked_at: datetime
    file_name: str | None = None
    highlights: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if len(self.sha256) != 64 or any(c not in "0123456789abcdef" for c in self.sha256.lower()):
            raise ValueError("sha256 must be 64 hexadecimal characters")


@dataclass(slots=True)
class RateLimitEntry:
    user_id: str
    request_id: str
    counted_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class TemporaryUpload:
    request_id: str
    path: Path
    size_bytes: int
    sha256: str | None = None
    cleanup_status: CleanupStatus = CleanupStatus.PENDING


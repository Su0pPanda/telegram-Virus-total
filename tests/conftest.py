from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import shutil
from typing import Any
from uuid import uuid4

import pytest


@pytest.fixture
def tmp_path() -> Path:
    """Workspace-local temp path for restricted Windows test environments."""
    path = Path(".test-runtime") / str(uuid4())
    path.mkdir(parents=True)
    try:
        yield path.resolve()
    finally:
        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    return tmp_path / "test.sqlite3"


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    path = tmp_path / "uploads"
    path.mkdir()
    return path


@dataclass
class FakeMessage:
    text: str | None = None
    document: Any | None = None
    replies: list[dict[str, Any]] = field(default_factory=list)

    async def answer(self, text: str, **kwargs: Any) -> None:
        self.replies.append({"kind": "message", "text": text, **kwargs})

    async def answer_photo(self, photo: Any, **kwargs: Any) -> None:
        self.replies.append({"kind": "photo", "photo": photo, **kwargs})


@pytest.fixture
def fake_message_factory():
    return FakeMessage

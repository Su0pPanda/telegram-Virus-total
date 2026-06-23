from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import aiosqlite

from src.domain.entities import CachedFileResult, RateLimitEntry


class SQLiteStorage:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    async def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS cached_file_results (
                    sha256 TEXT PRIMARY KEY,
                    file_name TEXT,
                    detection_count INTEGER NOT NULL,
                    engine_total INTEGER NOT NULL,
                    report_url TEXT NOT NULL,
                    highlights_json TEXT NOT NULL,
                    checked_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS rate_limit_entries (
                    user_id TEXT NOT NULL,
                    request_id TEXT NOT NULL UNIQUE,
                    counted_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_rate_user_time
                    ON rate_limit_entries(user_id, counted_at);
                """
            )
            await db.commit()

    async def get_cached_file(self, sha256: str) -> CachedFileResult | None:
        async with aiosqlite.connect(self.database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM cached_file_results WHERE sha256 = ?", (sha256.lower(),)
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return CachedFileResult(
            sha256=row["sha256"],
            file_name=row["file_name"],
            detection_count=row["detection_count"],
            engine_total=row["engine_total"],
            report_url=row["report_url"],
            highlights=json.loads(row["highlights_json"]),
            checked_at=datetime.fromisoformat(row["checked_at"]),
        )

    async def upsert_cached_file(self, result: CachedFileResult) -> None:
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute(
                """
                INSERT INTO cached_file_results (
                    sha256, file_name, detection_count, engine_total,
                    report_url, highlights_json, checked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sha256) DO UPDATE SET
                    file_name = excluded.file_name,
                    detection_count = excluded.detection_count,
                    engine_total = excluded.engine_total,
                    report_url = excluded.report_url,
                    highlights_json = excluded.highlights_json,
                    checked_at = excluded.checked_at
                """,
                (
                    result.sha256.lower(),
                    result.file_name,
                    result.detection_count,
                    result.engine_total,
                    result.report_url,
                    json.dumps(result.highlights),
                    result.checked_at.isoformat(),
                ),
            )
            await db.commit()

    async def try_add_rate_entry(
        self,
        entry: RateLimitEntry,
        *,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, float]:
        cutoff = entry.counted_at - timedelta(seconds=window_seconds)
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("BEGIN IMMEDIATE")
            await db.execute("DELETE FROM rate_limit_entries WHERE counted_at <= ?", (cutoff.isoformat(),))
            cursor = await db.execute(
                "SELECT counted_at FROM rate_limit_entries WHERE user_id = ? ORDER BY counted_at",
                (entry.user_id,),
            )
            rows = await cursor.fetchall()
            if len(rows) >= limit:
                oldest = datetime.fromisoformat(rows[0][0])
                retry_after = max(0.0, (oldest + timedelta(seconds=window_seconds) - entry.counted_at).total_seconds())
                await db.rollback()
                return False, retry_after
            await db.execute(
                "INSERT INTO rate_limit_entries(user_id, request_id, counted_at) VALUES (?, ?, ?)",
                (entry.user_id, entry.request_id, entry.counted_at.isoformat()),
            )
            await db.commit()
            return True, 0.0

    async def prune_rate_entries(self, before: datetime | None = None) -> int:
        threshold = before or datetime.now(UTC) - timedelta(minutes=10)
        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute(
                "DELETE FROM rate_limit_entries WHERE counted_at <= ?", (threshold.isoformat(),)
            )
            await db.commit()
            return cursor.rowcount


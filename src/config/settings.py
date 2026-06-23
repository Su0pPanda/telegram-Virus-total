from __future__ import annotations

from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: SecretStr
    vt_api_key: SecretStr
    database_path: Path = Path("data/bot.sqlite3")
    temp_dir: Path = Path("data/tmp")
    log_level: str = "INFO"
    max_upload_bytes: int = 100 * 1024 * 1024
    rate_limit_count: int = 5
    rate_limit_window_seconds: int = 60
    poll_interval_seconds: float = 5.0
    poll_timeout_seconds: float = 170.0
    request_timeout_seconds: float = 30.0
    vt_base_url: str = "https://www.virustotal.com/api/v3"

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("unsupported log level")
        return normalized

    @field_validator("database_path", "temp_dir")
    @classmethod
    def require_non_empty_path(cls, value: Path) -> Path:
        if not str(value).strip():
            raise ValueError("path cannot be empty")
        return value

    def prepare_directories(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)


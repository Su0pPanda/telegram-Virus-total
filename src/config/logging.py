from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime


SECRET_PATTERNS = (
    re.compile(r"(?i)(x-apikey|bot_token|vt_api_key|authorization)[=: ]+[^\s,]+"),
    re.compile(r"(?i)bearer\s+[a-z0-9._-]+"),
)


class SecretFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        rendered = record.getMessage()
        for pattern in SECRET_PATTERNS:
            rendered = pattern.sub("[REDACTED]", rendered)
        record.msg = rendered
        record.args = ()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.addFilter(SecretFilter())
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


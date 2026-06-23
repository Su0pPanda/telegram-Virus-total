FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/app/data/bot.sqlite3 \
    TEMP_DIR=/app/data/tmp

RUN groupadd --system bot && useradd --system --gid bot --home /app bot
WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY assets ./assets
RUN pip install --no-cache-dir . && mkdir -p /app/data/tmp && chown -R bot:bot /app

USER bot
VOLUME ["/app/data"]
STOPSIGNAL SIGTERM

CMD ["python", "-m", "src.app"]


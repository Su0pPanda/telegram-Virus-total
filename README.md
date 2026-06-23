# VirusTotal Telegram Bot

An async Telegram bot that checks files, URLs, IPv4 addresses, and IPv6 addresses with VirusTotal. It reuses completed file results by SHA-256, limits each Telegram user to five checks per rolling minute, and deletes uploaded file contents after every terminal outcome.

## Local setup

Requirements: Python 3.12, a Telegram bot token, and a VirusTotal API key.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
Copy-Item .env.example .env
```

Set `BOT_TOKEN` and `VT_API_KEY` in `.env`, then start polling:

```powershell
python -m src.app
```

While the bot is running in an interactive terminal, type `stop` and press
Enter to shut it down cleanly. The aliases `exit` and `quit` also work.

Validate both credentials with read-only provider requests (the script never prints secret values):

```powershell
python scripts/validate_credentials.py
```

The optional settings `DATABASE_PATH`, `TEMP_DIR`, and `LOG_LEVEL` are documented in `.env.example`. Do not commit `.env`.

## Tests

```powershell
pytest tests/unit
pytest tests/integration
pytest tests/contract
```

Automated tests mock Telegram and VirusTotal. Live credentials are only needed for the manual flow in `specs/001-virustotal-telegram-bot/quickstart.md`.

## Privacy and retention

Uploaded files exist only under `TEMP_DIR` while a check is active and are removed in success and failure paths. SQLite stores completed file summaries keyed by SHA-256 and rate-limit timestamps; it does not store Telegram file content or raw VirusTotal payloads. Logs redact recognized authorization fields and must not include submitted file bytes.

## Docker and Scalingo

Build with `docker build -t vt-telegram-bot .`. The image runs as an unprivileged user and stores both SQLite and temporary uploads under `/app/data`.

For Scalingo, configure `BOT_TOKEN`, `VT_API_KEY`, `DATABASE_PATH=/app/data/bot.sqlite3`, and `TEMP_DIR=/app/data/tmp`. Attach persistent storage for `/app/data`; without it, cached results and rate-limit state reset whenever the container is replaced. Run one bot process per SQLite volume.

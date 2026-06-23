from __future__ import annotations

import asyncio
import sys
from collections.abc import Callable
from threading import Thread


STOP_COMMANDS = frozenset({"stop", "exit", "quit"})


def is_stop_command(value: str) -> bool:
    return value.strip().casefold() in STOP_COMMANDS


def start_console_stop_listener(
    loop: asyncio.AbstractEventLoop,
    request_stop: Callable[[], None],
) -> None:
    """Listen for a stop command without blocking the bot event loop."""
    if not sys.stdin.isatty():
        return

    print("Bot is running. Type 'stop' and press Enter to stop it.")

    def listen() -> None:
        while True:
            try:
                command = input()
            except (EOFError, KeyboardInterrupt):
                return

            if is_stop_command(command):
                loop.call_soon_threadsafe(request_stop)
                return

            if command.strip():
                print("Unknown command. Type 'stop' to stop the bot.")

    Thread(target=listen, name="console-stop-listener", daemon=True).start()

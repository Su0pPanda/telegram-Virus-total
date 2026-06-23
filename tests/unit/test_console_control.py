import asyncio

import pytest

from src.console_control import is_stop_command
from src.console_control import start_console_stop_listener


def test_stop_commands_are_case_insensitive_and_ignore_spaces() -> None:
    assert is_stop_command("stop")
    assert is_stop_command("  STOP  ")
    assert is_stop_command("Exit")
    assert is_stop_command("quit")


def test_other_console_input_does_not_stop_bot() -> None:
    assert not is_stop_command("")
    assert not is_stop_command("start")


@pytest.mark.asyncio
async def test_console_stop_command_notifies_event_loop(monkeypatch) -> None:
    stopped = asyncio.Event()
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda: "stop")

    start_console_stop_listener(asyncio.get_running_loop(), stopped.set)

    await asyncio.wait_for(stopped.wait(), timeout=1)

from src.bot.keyboards.start import start_keyboard
from src.bot.presenters.messages import provider_overload_message, rate_limit_message


def test_start_keyboard_exposes_all_supported_inputs() -> None:
    labels = [button.text for row in start_keyboard().inline_keyboard for button in row]
    assert labels == ["Check a file", "Check a URL", "Check an IP"]


def test_recovery_messages_have_an_actionable_next_step() -> None:
    assert "30 seconds" in rate_limit_message(30)
    assert "try again later" in provider_overload_message().lower()


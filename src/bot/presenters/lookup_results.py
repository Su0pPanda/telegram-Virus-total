from src.bot.keyboards.common import report_keyboard
from src.domain.entities import CheckResult
from src.domain.enums import InputType


def present_lookup_result(result: CheckResult) -> tuple[str, object]:
    kind = "URL" if result.input_type is InputType.URL else "IP address"
    reputation = "No malicious signals found." if result.detection_count == 0 else "Potentially malicious signals found."
    lines = [
        f"{kind}: {result.subject_label}",
        reputation,
        f"Detections: {result.detection_count}/{result.engine_total or '?'}",
    ]
    if result.highlights:
        lines.append("Signals: " + ", ".join(result.highlights[:5]))
    return "\n".join(lines), report_keyboard(result.report_url)


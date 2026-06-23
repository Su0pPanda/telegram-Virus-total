from src.bot.keyboards.common import report_keyboard
from src.domain.entities import CheckResult
from src.domain.enums import ResultSource


def present_file_result(result: CheckResult) -> tuple[str, object]:
    status = "No engines flagged this file." if result.detection_count == 0 else "Potential threats were detected."
    lines = [
        f"File: {result.subject_label}",
        status,
        f"Detections: {result.detection_count}/{result.engine_total or '?'}",
    ]
    if result.highlights:
        lines.append("Notable detections: " + ", ".join(result.highlights[:5]))
    if result.source is ResultSource.CACHE:
        lines.append("Result source: previous completed check")
    return "\n".join(lines), report_keyboard(result.report_url)


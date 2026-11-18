
import re

from backend.app.services.ocr_layout_service import OCRLayoutService


class TaskExtractionService:

    STATUS_PATTERNS = [
        "in progress",
        "completed",
        "pending",
        "not started",
        "in review",
        "blocked",
        "cancelled",
    ]

    def __init__(self, layout_service=None):
        self.layout_service = layout_service or OCRLayoutService()

    def extract_tasks(self, image_path: str) -> list[dict]:
        lines = self.layout_service.group_into_lines(image_path)

        tasks = []

        for line in lines:
            text = line["text"].strip()
            normalized = text.lower()

            detected_status = None

            for status in self.STATUS_PATTERNS:
                pattern = rf"\b{re.escape(status)}\b"

                if re.search(pattern, normalized):
                    detected_status = status
                    break

            if detected_status is None:
                continue

            task_name = re.sub(
                rf"\b{re.escape(detected_status)}\b",
                "",
                text,
                flags=re.IGNORECASE,
            ).strip()

            if not task_name:
                continue

            tasks.append({
                "name": task_name,
                "status": detected_status.title(),
                "evidence": text,
                "confidence": line["confidence"],
            })

        return tasks

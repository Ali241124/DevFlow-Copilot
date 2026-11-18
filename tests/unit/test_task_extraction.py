
import json
from pathlib import Path

from backend.app.services.task_extraction_service import (
    TaskExtractionService,
)


def main():
    dataset_path = Path(
        "evaluation/datasets/multimodal_cases.json"
    )

    dataset = json.loads(
        dataset_path.read_text(encoding="utf-8")
    )

    case = next(
        item for item in dataset["cases"]
        if item["id"] == "IMG-003"
    )

    image_path = case["image"]

    service = TaskExtractionService()
    tasks = service.extract_tasks(image_path)

    print("\nDEVFLOW COPILOT - TASK EXTRACTION")
    print("=" * 75)

    for index, task in enumerate(tasks, start=1):
        print(f"\nTask {index}")
        print("Name:", task["name"])
        print("Status:", task["status"])
        print("Evidence:", task["evidence"])
        print("OCR confidence:", task["confidence"])

    print("\n" + "=" * 75)
    print("Total extracted tasks:", len(tasks))


if __name__ == "__main__":
    main()

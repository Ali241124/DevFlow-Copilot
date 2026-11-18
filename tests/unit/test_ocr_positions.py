
import json
from pathlib import Path

from backend.app.services.ocr_layout_service import OCRLayoutService


def main():
    dataset_path = Path("evaluation/datasets/multimodal_cases.json")
    dataset = json.loads(
        dataset_path.read_text(encoding="utf-8")
    )

    case = next(
        item for item in dataset["cases"]
        if item["id"] == "IMG-003"
    )

    service = OCRLayoutService()
    lines = service.group_into_lines(case["image"])

    print("\nDEVFLOW COPILOT - OCR LINE GROUPING")
    print("=" * 75)

    for line in lines:
        print(
            f"Y={line['y']:<5} "
            f"X={line['x_start']:<5} "
            f"Confidence={line['confidence']:<6} "
            f"Text={line['text']}"
        )

    print("=" * 75)
    print(f"Total detected lines: {len(lines)}")


if __name__ == "__main__":
    main()

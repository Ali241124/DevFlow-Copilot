
from collections import Counter

from backend.app.services.context_builder import ContextBuilder


def main():
    image_path = (
        "data/evaluation_images/IMG-003-task-dashboard.png"
    )

    print("\nDEVFLOW COPILOT - REAL OCR CONTEXT INTEGRATION")
    print("=" * 70)

    builder = ContextBuilder()

    context = builder.build(
        image_paths=[image_path]
    )

    print("\nINPUT MODE:", context.input_mode)
    print("TOTAL EVIDENCE ITEMS:", len(context.evidence))

    source_counts = Counter(
        item.source for item in context.evidence
    )

    print("\nEVIDENCE SOURCES:")
    for source, count in source_counts.items():
        print(f"{source}: {count}")

    ocr_items = [
        item for item in context.evidence
        if "OCR extracted from screenshot" in item.evidence_note
    ]

    print("\nOCR EXTRACTED TASKS:")
    print("-" * 70)

    for index, item in enumerate(ocr_items, start=1):
        print(f"\nTask {index}")
        print("Observation:", item.content)
        print("Evidence:", item.evidence_note)
        print("Status:", item.status)

    print("\n" + "=" * 70)
    print("TOTAL OCR TASKS:", len(ocr_items))


if __name__ == "__main__":
    main()

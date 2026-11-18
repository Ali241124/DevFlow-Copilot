
from backend.app.services.vision_service import VisionService


def main():
    print("=" * 60)
    print("DEVFLOW COPILOT - STRUCTURED VISION TEST")
    print("=" * 60)

    service = VisionService()

    try:
        print("\nAnalyzing screenshot...\n")

        result = service.analyze_screenshot(
            "data/uploads/sample_ui.png"
        )

        print("STRUCTURED VISION ANALYSIS")
        print("-" * 60)

        print(result.model_dump_json(indent=4))

        print("\nVISION ANALYSIS SUCCESSFUL!")

    except Exception as error:
        print(f"\nVISION ANALYSIS FAILED: {error}")


if __name__ == "__main__":
    main()

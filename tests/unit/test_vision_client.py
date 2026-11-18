
from backend.app.llm.vision_client import VisionClient


def main():
    print("=" * 60)
    print("DEVFLOW COPILOT - VISION MODEL TEST")
    print("=" * 60)

    image_path = "data/uploads/sample_ui.png"

    prompt = """
Look carefully at the attached screenshot.

Describe what you can actually see in the image.
Mention the page layout, visible text, buttons,
input fields, and other interface elements.

Do not repeat these instructions.
Do not invent anything that is not visible.
"""

    vision_client = VisionClient()

    try:
        print("\nAnalyzing screenshot...\n")

        result = vision_client.analyze_image(
            image_path=image_path,
            prompt=prompt
        )

        print("VISION ANALYSIS")
        print("-" * 60)
        print(result)

    except Exception as error:
        print(f"TEST FAILED: {error}")


if __name__ == "__main__":
    main()

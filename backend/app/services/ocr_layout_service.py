
from backend.app.llm.ocr_client import OCRClient


class OCRLayoutService:
    """
    Groups OCR word detections into visual text lines.
    """

    def __init__(self, ocr_client=None):
        self.ocr_client = ocr_client or OCRClient()

    def group_into_lines(self, image_path: str) -> list[dict]:
        blocks = self.ocr_client.extract_text_blocks(image_path)

        # Sort words from top to bottom, then left to right.
        blocks.sort(key=lambda item: (item["y"], item["x"]))

        lines = []

        for block in blocks:
            matched_line = None

            for line in lines:
                # Allow small vertical differences between words.
                if abs(block["y"] - line["y"]) <= 10:
                    matched_line = line
                    break

            if matched_line is None:
                lines.append({
                    "y": block["y"],
                    "words": [block],
                })
            else:
                matched_line["words"].append(block)

                # Update average vertical position.
                matched_line["y"] = round(
                    sum(word["y"] for word in matched_line["words"])
                    / len(matched_line["words"])
                )

        result = []

        for line in lines:
            words = sorted(
                line["words"],
                key=lambda item: item["x"]
            )

            result.append({
                "text": " ".join(word["text"] for word in words),
                "y": line["y"],
                "x_start": min(word["x"] for word in words),
                "x_end": max(
                    word["x"] + word["width"] for word in words
                ),
                "confidence": round(
                    sum(word["confidence"] for word in words)
                    / len(words),
                    2,
                ),
            })

        return result

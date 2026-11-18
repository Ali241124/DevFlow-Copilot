
from pathlib import Path

import pytesseract
from PIL import Image, UnidentifiedImageError


class OCRClient:
    """
    Extracts visible text from screenshots using local Tesseract OCR.
    """

    def __init__(
        self,
        language: str = "eng",
        tesseract_path: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    ):
        self.language = language
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def extract_text(self, image_path: str) -> str:
        path = Path(image_path)

        if not path.is_file():
            raise FileNotFoundError(
                f"Image file not found: {path}"
            )

        try:
            with Image.open(path) as image:
                image.load()
                text = pytesseract.image_to_string(
                    image,
                    lang=self.language,
                    config="--psm 6",
                )

            return text.strip()

        except (UnidentifiedImageError, OSError) as error:
            raise ValueError(
                f"Could not read screenshot: {error}"
            ) from error

        except pytesseract.TesseractNotFoundError as error:
            raise RuntimeError(
                "Tesseract executable was not found."
            ) from error

        except pytesseract.TesseractError as error:
            raise RuntimeError(
                f"OCR processing failed: {error}"
            ) from error

    def extract_text_blocks(self, image_path: str) -> list[dict]:
        """
        Extract individual words with their positions and confidence.
        """

        path = Path(image_path)

        if not path.is_file():
            raise FileNotFoundError(
                f"Image file not found: {path}"
            )

        try:
            with Image.open(path) as image:
                image.load()

                data = pytesseract.image_to_data(
                    image,
                    lang=self.language,
                    config="--psm 6",
                    output_type=pytesseract.Output.DICT,
                )

            blocks = []

            for index, raw_text in enumerate(data["text"]):
                text = raw_text.strip()

                if not text:
                    continue

                try:
                    confidence = float(data["conf"][index])
                except (ValueError, TypeError):
                    continue

                if confidence < 0:
                    continue

                blocks.append({
                    "text": text,
                    "confidence": confidence,
                    "x": data["left"][index],
                    "y": data["top"][index],
                    "width": data["width"][index],
                    "height": data["height"][index],
                    "block_num": data["block_num"][index],
                    "par_num": data["par_num"][index],
                    "line_num": data["line_num"][index],
                })

            return blocks

        except (UnidentifiedImageError, OSError) as error:
            raise ValueError(
                f"Could not read screenshot: {error}"
            ) from error

        except pytesseract.TesseractError as error:
            raise RuntimeError(
                f"OCR processing failed: {error}"
            ) from error


from pathlib import Path

import ollama


class VisionClient:
    """
    Handles communication with a local vision model
    through Ollama.
    """

    def __init__(
        self,
        model: str = "moondream",
        host: str = "http://localhost:11434"
    ):
        self.model = model
        self.client = ollama.Client(host=host)

    def analyze_image(
        self,
        image_path: str,
        prompt: str
    ) -> str:
        """
        Send an image and a text prompt to the vision model.

        Returns the model's textual description of the image.
        """

        path = Path(image_path)

        # Check that the image exists.
        if not path.is_file():
            raise FileNotFoundError(
                f"Image file not found: {path}"
            )

        # Accept common image formats only.
        allowed_extensions = {
            ".png", ".jpg", ".jpeg", ".webp"
        }

        if path.suffix.lower() not in allowed_extensions:
            raise ValueError(
                "Unsupported image format. "
                "Use PNG, JPG, JPEG or WEBP."
            )

        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [str(path)]
                    }
                ],
                options={
                    "temperature": 0.1,
                    "num_ctx": 2048,
                    "num_predict": 512
                }
            )

            return response.message.content.strip()

        except ollama.ResponseError as error:
            raise RuntimeError(
                f"Vision model error: {error}"
            ) from error

        except Exception as error:
            raise RuntimeError(
                f"Could not analyze image: {error}"
            ) from error

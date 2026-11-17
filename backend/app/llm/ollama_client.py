
import ollama


class OllamaClient:
    """
    Handles communication between DevFlow Copilot
    and a locally running Ollama model.
    """

    def __init__(
        self,
        model: str = "qwen2.5:1.5b",
        host: str = "http://localhost:11434"
    ):
        self.model = model
        self.client = ollama.Client(host=host)

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        response_format: dict | str | None = None
    ) -> str:
        """
        Send a prompt to the local LLM and return its response.

        response_format optionally constrains the output
        to a JSON format or JSON schema.
        """

        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        messages.append({
            "role": "user",
            "content": prompt
        })

        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_ctx": 2048,
                    "num_predict": 512
                },
                format=response_format if response_format else ""
            )

            return response.message.content.strip()

        except ollama.ResponseError as error:
            raise RuntimeError(
                f"Ollama model error: {error}"
            ) from error

        except Exception as error:
            raise RuntimeError(
                f"Could not communicate with Ollama: {error}"
            ) from error

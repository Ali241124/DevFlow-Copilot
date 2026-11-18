
import json
import logging
from pydantic import ValidationError

from backend.app.llm.vision_client import VisionClient
from backend.app.llm.ollama_client import OllamaClient
from backend.app.schemas.vision import VisionAnalysis

logger = logging.getLogger(__name__)

class VisionService:
    """
    Analyzes screenshots using a vision model,
    then converts the observations into structured JSON
    using a lightweight text model.
    """

    def __init__(
        self,
        vision_client=None,
        text_client=None
    ):
        self.vision_client = vision_client or VisionClient()
        self.text_client = text_client or OllamaClient(
            model="qwen2.5:1.5b"
        )

    def analyze_screenshot(self, image_path: str) -> VisionAnalysis:

        # STEP 1: Extract visual information.
        vision_prompt = """
Analyze this screenshot as a software UI analyst.

Carefully inspect the visual layout and report:

1. Page title and main heading.
2. Supporting text and subtitles.
3. Visible buttons.
4. Repeated UI elements such as cards, rows, or table entries.
5. Text displayed inside each repeated element.
6. Status labels associated with each element.
7. Other clearly visible interface elements.

IMPORTANT RULES:

- Distinguish headings from card contents.
- Distinguish buttons from ordinary text.
- A text label is not a button just because it looks clickable.
- Do not describe task names as section headings.
- Preserve the exact visible wording.
- Associate status labels with the correct task or item.
- Do not invent buttons, controls, text, or functionality.
- Do not infer behavior that cannot be seen.
- If something is unclear, leave it out.

Describe only what is visually present.
Be concise, accurate, and organized.
"""

        visual_description = self.vision_client.analyze_image(
            image_path=image_path,
            prompt=vision_prompt
        )

        if not visual_description.strip():
            raise ValueError(
                "Vision model returned an empty description."
            )

        # STEP 2: Convert visual findings into structured JSON.
        system_prompt = """
You are a strict UI screenshot analysis assistant.

Convert the supplied visual description into the required JSON schema.

RULES:

1. Use only information explicitly present in the visual description.
2. Never invent buttons, fields, labels, pages or functionality.
3. Every visible component must be supported by the description.
4. Mark visible components as observed.
5. Mark possible interactions as assumed unless their behavior
   is explicitly confirmed.
6. Do not invent interaction behavior.
7. Do not repeat components or visible text.
8. Do not add generic assumptions about browsers, accessibility,
   devices, screen sizes or compatibility.
9. Include at most 5 important unknowns.
10. Unknowns must describe genuinely missing information
    relevant to the visible interface.
11. If no components or interactions are identified,
    return empty arrays.
12. Keep descriptions short and factual.

Return only valid JSON matching the supplied schema.
"""

        conversion_prompt = f"""
Convert this visual description into structured UI analysis.

VISUAL DESCRIPTION:
{visual_description}

Requirements:
- Extract only clearly supported observations.
- Do not repeat information.
- Do not generate more than 5 unknowns.
- Do not guess missing interface elements.
- Use empty arrays when information is unavailable.

Return JSON matching the supplied schema.
"""

        try:
            raw_response = self.text_client.generate(
                prompt=conversion_prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                response_format=VisionAnalysis.model_json_schema()
            )
            print("\nQWEN RAW RESPONSE:")
            print("-" * 60)
            print(repr(raw_response))

            parsed_data = json.loads(raw_response.strip())

            if not isinstance(parsed_data, dict):
                raise ValueError("Vision model must return a JSON object.")

            # Maximum permitted items for each list field.
            list_limits = {
                "components": 20,
                "visible_text": 30,
                "interactions": 15,
                "evidence_notes": 20,
                "unknowns": 5,
            }

            # Prevent oversized model output from breaking schema validation.
            for field, limit in list_limits.items():
                value = parsed_data.get(field)

                if isinstance(value, list) and len(value) > limit:
                    original_count = len(value)
                    parsed_data[field] = value[:limit]

                    logger.warning(
                        "Vision model returned %s items in '%s'. "
                        "Keeping the first %s items.",
                        original_count,
                        field,
                        limit,
                    )

            return VisionAnalysis.model_validate(parsed_data)

        except json.JSONDecodeError as error:
            raise ValueError(
                "Text model returned invalid JSON."
            ) from error

        except ValidationError as error:
            raise ValueError(
                f"Vision analysis failed schema validation: {error}"
            ) from error

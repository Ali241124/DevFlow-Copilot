
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["client_text", "screenshot"]

    category: Literal[
        "requirement",
        "visual_observation",
        "assumption",
        "unknown"
    ]

    content: str

    status: Literal[
        "provided",
        "observed",
        "assumed",
        "unknown"
    ]

    evidence_note: str = ""


class NormalizedContext(BaseModel):
    """
    Common representation of text and screenshot evidence.
    """

    model_config = ConfigDict(extra="forbid")

    client_text: str = ""

    image_paths: list[str] = Field(
        default_factory=list
    )

    input_mode: Literal[
        "text_only",
        "image_only",
        "combined"
    ]

    evidence: list[EvidenceItem] = Field(
        default_factory=list
    )

    assumptions: list[str] = Field(
        default_factory=list
    )

    open_questions: list[str] = Field(
        default_factory=list
    )

    def validate_input_mode(self):
        has_text = bool(self.client_text.strip())
        has_images = bool(self.image_paths)

        expected_mode = (
            "combined" if has_text and has_images
            else "text_only" if has_text
            else "image_only" if has_images
            else None
        )

        if expected_mode is None:
            raise ValueError(
                "At least client text or one screenshot is required."
            )

        if self.input_mode != expected_mode:
            raise ValueError(
                f"Input mode mismatch. Expected {expected_mode}."
            )

        return self

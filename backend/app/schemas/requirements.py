
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Feature(BaseModel):
    """Represents one feature extracted from a client brief."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str

    priority: Literal["high", "medium", "low"] = "medium"

    source_text: str = Field(
    description=(
        "Supporting text from the original client brief. "
        "Must be empty if no matching evidence is found."
    )
)

    status: Literal[
        "confirmed",
        "needs_clarification"
    ] = "confirmed"


class RequirementsAnalysis(BaseModel):
    """Structured requirements analysis for a software project."""

    model_config = ConfigDict(extra="forbid")

    project_summary: str

    features: list[Feature] = Field(default_factory=list)

    assumptions: list[str] = Field(default_factory=list)

    open_questions: list[str] = Field(default_factory=list)

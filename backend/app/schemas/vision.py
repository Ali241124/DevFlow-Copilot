
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UIComponent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    component_type: str
    visible_text: str = ""
    evidence_note: str

    status: Literal["observed", "assumed"] = "observed"


class UIInteraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    control: str
    possible_action: str
    behavior: str = ""

    # A visible button is observed, but what it does
    # after being clicked may only be an assumption.
    status: Literal["observed", "assumed"]

    evidence_note: str

class VisionAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_description: str
    components: list[UIComponent] = Field(
        default_factory=list,
        max_length=20
    )
    visible_text: list[str] = Field(
        default_factory=list,
        max_length=30
    )
    current_state: str
    interactions: list[UIInteraction] = Field(
        default_factory=list,
        max_length=15
    )
    evidence_notes: list[str] = Field(
        default_factory=list,
        max_length=20
    )
    unknowns: list[str] = Field(
        default_factory=list,
        max_length=5
    )
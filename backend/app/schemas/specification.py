"""
Day 2 — Canonical Project Specification Schema
==============================================
Implements the full artifact schema defined in SRS §10.
All artifact types that the LLM returns are validated here.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Sub-schemas
# ---------------------------------------------------------------------------

class SpecificationFeature(BaseModel):
    """One feature extracted from the combined multimodal context."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    priority: Literal["high", "medium", "low"] = "medium"
    source: Literal["client_text", "screenshot", "combined", "assumed"] = "assumed"


class UserStory(BaseModel):
    """One user story in role/goal/benefit format."""

    model_config = ConfigDict(extra="forbid")

    story_id: str = Field(
        description="Unique story reference, e.g. US-001."
    )
    role: str
    goal: str
    benefit: str


class AcceptanceCriterion(BaseModel):
    """One Given/When/Then acceptance criterion tied to a story."""

    model_config = ConfigDict(extra="forbid")

    story_id: str
    given: str
    when: str
    then: str


class ImplementationPlan(BaseModel):
    """High-level implementation breakdown."""

    model_config = ConfigDict(extra="forbid")

    frontend: list[str] = Field(default_factory=list)
    backend: list[str] = Field(default_factory=list)
    data: list[str] = Field(default_factory=list)
    apis: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class TestCase(BaseModel):
    """One QA test case."""

    __test__ = False  # Prevent pytest from treating this as a test class

    model_config = ConfigDict(extra="forbid")

    test_id: str
    type: Literal["positive", "negative", "edge"] = "positive"
    title: str
    steps: list[str] = Field(default_factory=list)
    expected_result: str


class EvidenceNote(BaseModel):
    """Traceability note linking a generated claim to its source."""

    model_config = ConfigDict(extra="forbid")

    claim: str
    source: Literal["client_text", "screenshot", "combined", "assumed"]
    note: str


# ---------------------------------------------------------------------------
# Top-level schema (SRS §10 canonical artifact)
# ---------------------------------------------------------------------------

class ProjectSpecification(BaseModel):
    """
    Full structured project specification.

    This is the canonical Day 2 output artifact.
    Every field maps directly to SRS §10 canonical schema.
    """

    model_config = ConfigDict(extra="forbid")

    project_summary: str = Field(
        description="One-paragraph description of the project."
    )

    features: list[SpecificationFeature] = Field(
        default_factory=list,
        description="Features derived from all combined evidence."
    )

    user_stories: list[UserStory] = Field(
        default_factory=list,
        description="User stories derived from features."
    )

    acceptance_criteria: list[AcceptanceCriterion] = Field(
        default_factory=list,
        description="Given/When/Then criteria tied to stories."
    )

    implementation_plan: ImplementationPlan = Field(
        default_factory=ImplementationPlan,
        description="Frontend/backend/data/API breakdown."
    )

    test_cases: list[TestCase] = Field(
        default_factory=list,
        description="QA test cases: positive, negative, edge."
    )

    developer_prompt: str = Field(
        default="",
        description="Context-rich prompt for a developer to implement the spec."
    )

    assumptions: list[str] = Field(
        default_factory=list,
        description="Things assumed but not explicitly confirmed."
    )

    open_questions: list[str] = Field(
        default_factory=list,
        description="Information missing from input that must be clarified."
    )

    evidence_notes: list[EvidenceNote] = Field(
        default_factory=list,
        description="Traceability between claims and their source evidence."
    )

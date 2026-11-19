"""
Day 3 & Day 4 Artifact Schemas
==============================
Defines Pydantic schemas for:
- UserStoryArtifact (US collection with story_id, role, goal, benefit, priority)
- AcceptanceCriteriaArtifact (Given/When/Then tied to stories)
- ImplementationPlanArtifact (frontend, backend, data, APIs, dependencies, risks)
- QATestSuiteArtifact (positive, negative, edge test cases)
- DeveloperPromptArtifact (structured, context-rich developer instructions)
- ClientUpdateArtifact (professional client progress/status summaries)
- ReleaseNotesArtifact (semantic version release notes, changes, migrations)
- EngineeringArtifactPackage (composite artifact containing all generated components)
"""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class UserStoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    story_id: str = Field(description="Unique story identifier, e.g. US-001")
    title: str = Field(description="Short title for the story")
    role: str = Field(description="User persona or role")
    goal: str = Field(description="What the user wants to accomplish")
    benefit: str = Field(description="Business or user value gained")
    priority: Literal["high", "medium", "low"] = "medium"
    acceptance_criteria_ids: list[str] = Field(default_factory=list)


class UserStoriesArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = ""
    stories: list[UserStoryItem] = Field(default_factory=list)
    total_count: int = 0


class GivenWhenThenCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion_id: str = Field(description="Unique AC id, e.g. AC-001")
    story_id: str = Field(description="Linked user story ID, e.g. US-001")
    given: str = Field(description="Precondition / Context")
    when: str = Field(description="Action / Trigger event")
    then: str = Field(description="Expected outcome / System behavior")


class AcceptanceCriteriaArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = ""
    criteria: list[GivenWhenThenCriterion] = Field(default_factory=list)


class ImplementationPlanArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    frontend: list[str] = Field(default_factory=list)
    backend: list[str] = Field(default_factory=list)
    data: list[str] = Field(default_factory=list)
    apis: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class QATestCaseItem(BaseModel):
    __test__ = False  # Avoid pytest collection
    model_config = ConfigDict(extra="forbid")

    test_id: str = Field(description="Unique ID e.g. TC-001")
    story_id: str = Field(default="", description="Linked story ID if applicable")
    type: Literal["positive", "negative", "edge"]
    title: str
    preconditions: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    expected_result: str


class QATestSuiteArtifact(BaseModel):
    __test__ = False  # Avoid pytest collection
    model_config = ConfigDict(extra="forbid")

    project_id: str = ""
    test_cases: list[QATestCaseItem] = Field(default_factory=list)
    positive_count: int = 0
    negative_count: int = 0
    edge_count: int = 0


class DeveloperPromptArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_summary: str
    tech_stack_assumptions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    acceptance_checklist: list[str] = Field(default_factory=list)
    full_prompt_text: str = Field(description="Ready-to-copy context-rich prompt for coding agents")


class ClientUpdateArtifact(BaseModel):
    """Secondary artifact: Professional status/progress summary for stakeholders."""
    model_config = ConfigDict(extra="forbid")

    project_name: str
    report_date: str
    period_summary: str
    completed_features: list[str] = Field(default_factory=list)
    in_progress_features: list[str] = Field(default_factory=list)
    upcoming_milestones: list[str] = Field(default_factory=list)
    items_needing_client_input: list[str] = Field(default_factory=list)


class ReleaseNotesArtifact(BaseModel):
    """Secondary artifact: Release notes with semantic versioning."""
    model_config = ConfigDict(extra="forbid")

    version: str = "v1.0.0"
    release_date: str
    summary: str
    new_features: list[str] = Field(default_factory=list)
    enhancements: list[str] = Field(default_factory=list)
    bug_fixes: list[str] = Field(default_factory=list)
    known_issues: list[str] = Field(default_factory=list)
    migration_notes: str = ""


class EngineeringArtifactPackage(BaseModel):
    """
    Composite bundle of all engineering artifacts linked to a generation run.
    """
    model_config = ConfigDict(extra="forbid")

    run_id: str
    project_id: str
    user_stories: UserStoriesArtifact
    acceptance_criteria: AcceptanceCriteriaArtifact
    implementation_plan: ImplementationPlanArtifact
    qa_test_suite: QATestSuiteArtifact
    developer_prompt: DeveloperPromptArtifact
    client_update: ClientUpdateArtifact
    release_notes: ReleaseNotesArtifact

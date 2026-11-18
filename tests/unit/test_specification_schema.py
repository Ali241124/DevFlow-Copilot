"""
Day 2 — Unit Tests: ProjectSpecification Schema
================================================
Tests that the canonical artifact schema validates correctly,
rejects invalid input, and enforces structural rules.
"""

import pytest
from pydantic import ValidationError

from backend.app.schemas.specification import (
    ProjectSpecification,
    SpecificationFeature,
    UserStory,
    AcceptanceCriterion,
    ImplementationPlan,
    TestCase,
    EvidenceNote,
)


# ---------------------------------------------------------------------------
# SpecificationFeature
# ---------------------------------------------------------------------------

class TestSpecificationFeature:

    def test_valid_feature(self):
        feature = SpecificationFeature(
            name="Task creation",
            description="Users can create tasks.",
            priority="high",
            source="client_text",
        )
        assert feature.name == "Task creation"
        assert feature.priority == "high"
        assert feature.source == "client_text"

    def test_default_priority_is_medium(self):
        feature = SpecificationFeature(
            name="Dashboard",
            description="A summary dashboard.",
        )
        assert feature.priority == "medium"

    def test_default_source_is_assumed(self):
        feature = SpecificationFeature(
            name="Dashboard",
            description="A summary dashboard.",
        )
        assert feature.source == "assumed"

    def test_invalid_priority_rejected(self):
        with pytest.raises(ValidationError):
            SpecificationFeature(
                name="Dashboard",
                description="A summary dashboard.",
                priority="critical",  # not allowed
            )

    def test_invalid_source_rejected(self):
        with pytest.raises(ValidationError):
            SpecificationFeature(
                name="Dashboard",
                description="A summary dashboard.",
                source="unknown_source",  # not allowed
            )

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            SpecificationFeature(
                name="Dashboard",
                description="...",
                extra_field="oops",
            )


# ---------------------------------------------------------------------------
# UserStory
# ---------------------------------------------------------------------------

class TestUserStory:

    def test_valid_story(self):
        story = UserStory(
            story_id="US-001",
            role="project manager",
            goal="create a project",
            benefit="track all deliverables in one place",
        )
        assert story.story_id == "US-001"

    def test_missing_role_rejected(self):
        with pytest.raises(ValidationError):
            UserStory(
                story_id="US-001",
                goal="create a project",
                benefit="track deliverables",
            )


# ---------------------------------------------------------------------------
# AcceptanceCriterion
# ---------------------------------------------------------------------------

class TestAcceptanceCriterion:

    def test_valid_criterion(self):
        ac = AcceptanceCriterion(
            story_id="US-001",
            given="the user is on the project creation page",
            when="they submit a valid project name",
            then="a new project is created and listed in the sidebar",
        )
        assert ac.story_id == "US-001"

    def test_missing_given_rejected(self):
        with pytest.raises(ValidationError):
            AcceptanceCriterion(
                story_id="US-001",
                when="they submit",
                then="it works",
            )


# ---------------------------------------------------------------------------
# TestCase
# ---------------------------------------------------------------------------

class TestTestCaseSchema:

    def test_valid_positive_case(self):
        tc = TestCase(
            test_id="TC-001",
            type="positive",
            title="Create task with valid input",
            steps=["Navigate to task creation", "Fill in title", "Submit"],
            expected_result="Task is created and shown in the list.",
        )
        assert tc.type == "positive"

    def test_valid_negative_case(self):
        tc = TestCase(
            test_id="TC-002",
            type="negative",
            title="Submit empty task title",
            expected_result="Validation error is displayed.",
        )
        assert tc.type == "negative"

    def test_valid_edge_case(self):
        tc = TestCase(
            test_id="TC-003",
            type="edge",
            title="Create task with 500-character title",
            expected_result="System accepts or rejects it gracefully.",
        )
        assert tc.type == "edge"

    def test_invalid_type_rejected(self):
        with pytest.raises(ValidationError):
            TestCase(
                test_id="TC-004",
                type="regression",  # not allowed
                title="...",
                expected_result="...",
            )


# ---------------------------------------------------------------------------
# ProjectSpecification
# ---------------------------------------------------------------------------

class TestProjectSpecification:

    def _make_valid_spec(self) -> dict:
        return {
            "project_summary": "A task management application.",
            "features": [
                {
                    "name": "Create tasks",
                    "description": "Users can create tasks.",
                    "priority": "high",
                    "source": "client_text",
                }
            ],
            "user_stories": [
                {
                    "story_id": "US-001",
                    "role": "user",
                    "goal": "create a task",
                    "benefit": "track my work",
                }
            ],
            "acceptance_criteria": [
                {
                    "story_id": "US-001",
                    "given": "the user is on the task page",
                    "when": "they submit a task title",
                    "then": "the task is saved",
                }
            ],
            "implementation_plan": {
                "frontend": ["Task creation form"],
                "backend": ["POST /tasks endpoint"],
                "data": ["tasks table"],
                "apis": [],
                "risks": [],
            },
            "test_cases": [
                {
                    "test_id": "TC-001",
                    "type": "positive",
                    "title": "Create task with valid input",
                    "steps": ["Go to task page", "Submit"],
                    "expected_result": "Task is created.",
                }
            ],
            "developer_prompt": "Build a task creation form...",
            "assumptions": ["Task editing is not in scope."],
            "open_questions": ["Should tasks have due dates?"],
            "evidence_notes": [
                {
                    "claim": "Task creation feature",
                    "source": "client_text",
                    "note": "Directly stated in the client brief.",
                }
            ],
        }

    def test_valid_full_spec(self):
        data = self._make_valid_spec()
        spec = ProjectSpecification.model_validate(data)
        assert spec.project_summary == "A task management application."
        assert len(spec.features) == 1
        assert len(spec.user_stories) == 1
        assert len(spec.acceptance_criteria) == 1
        assert len(spec.test_cases) == 1

    def test_missing_project_summary_rejected(self):
        data = self._make_valid_spec()
        del data["project_summary"]
        with pytest.raises(ValidationError):
            ProjectSpecification.model_validate(data)

    def test_empty_lists_are_valid(self):
        """Specification is valid even with no stories or test cases yet."""
        spec = ProjectSpecification(
            project_summary="A minimal project.",
        )
        assert spec.features == []
        assert spec.user_stories == []
        assert spec.test_cases == []

    def test_extra_fields_rejected(self):
        data = self._make_valid_spec()
        data["invented_field"] = "not allowed"
        with pytest.raises(ValidationError):
            ProjectSpecification.model_validate(data)

    def test_implementation_plan_defaults_to_empty_lists(self):
        spec = ProjectSpecification(
            project_summary="A project.",
            implementation_plan=ImplementationPlan(),
        )
        assert spec.implementation_plan.frontend == []
        assert spec.implementation_plan.risks == []

    def test_json_serialisation_roundtrip(self):
        data = self._make_valid_spec()
        spec = ProjectSpecification.model_validate(data)
        serialised = spec.model_dump()
        restored = ProjectSpecification.model_validate(serialised)
        assert restored.project_summary == spec.project_summary
        assert len(restored.features) == len(spec.features)

    def test_evidence_note_source_values(self):
        """All valid source values for EvidenceNote must be accepted."""
        for source in ("client_text", "screenshot", "combined", "assumed"):
            note = EvidenceNote(
                claim="Some claim",
                source=source,
                note="Evidence detail.",
            )
            assert note.source == source

    def test_evidence_note_invalid_source_rejected(self):
        with pytest.raises(ValidationError):
            EvidenceNote(
                claim="Some claim",
                source="fabricated",
                note="...",
            )

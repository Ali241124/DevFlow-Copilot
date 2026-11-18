"""
Day 2 — Unit Tests: SpecificationService
==========================================
Tests for the specification generation service using mock LLM clients.

Covers (SRS §22.1 + §22.2):
- Successful generation (text, image, combined)
- Schema validation on model output
- Reliability checks (empty developer_prompt, missing features)
- Context carryover (open questions, assumptions preserved)
- Failure handling (invalid JSON, schema mismatch, empty context)

All tests use fake LLM clients — no Ollama required.
"""

import json
import pytest
from unittest.mock import MagicMock

from backend.app.schemas.context import NormalizedContext, EvidenceItem
from backend.app.schemas.specification import ProjectSpecification
from backend.app.services.specification_service import SpecificationService


# ---------------------------------------------------------------------------
# Minimal valid spec JSON that the fake LLM returns
# ---------------------------------------------------------------------------

VALID_SPEC_JSON = json.dumps({
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
            "steps": ["Go to task page", "Submit form"],
            "expected_result": "Task is created.",
        }
    ],
    "developer_prompt": (
        "Build a task management application with a task creation form. "
        "The form should accept a task title and submit it to a REST API. "
        "Display a list of all created tasks on the main page. "
        "No authentication or database choice is specified — confirm with client."
    ),
    "assumptions": ["Task editing is not in scope."],
    "open_questions": ["Should tasks have due dates?"],
    "evidence_notes": [
        {
            "claim": "Task creation feature",
            "source": "client_text",
            "note": "Directly stated in the client brief.",
        }
    ],
})


def _make_fake_llm(response_json: str = VALID_SPEC_JSON) -> MagicMock:
    """Return a fake OllamaClient that returns the given JSON string."""
    fake_llm = MagicMock()
    fake_llm.model = "fake-model"
    fake_llm.generate.return_value = response_json
    return fake_llm


def _text_context(text: str = "Build a task manager.") -> NormalizedContext:
    return NormalizedContext(
        client_text=text,
        input_mode="text_only",
        evidence=[
            EvidenceItem(
                source="client_text",
                category="requirement",
                content=text,
                status="provided",
            )
        ],
    )


def _image_context() -> NormalizedContext:
    return NormalizedContext(
        image_paths=["fake/path/sample.png"],
        input_mode="image_only",
        evidence=[
            EvidenceItem(
                source="screenshot",
                category="visual_observation",
                content="A task list UI with Add Task button observed.",
                status="observed",
            )
        ],
    )


def _combined_context() -> NormalizedContext:
    return NormalizedContext(
        client_text="Build a task manager.",
        image_paths=["fake/path/sample.png"],
        input_mode="combined",
        evidence=[
            EvidenceItem(
                source="client_text",
                category="requirement",
                content="Build a task manager.",
                status="provided",
            ),
            EvidenceItem(
                source="screenshot",
                category="visual_observation",
                content="Task list UI observed with Add Task button.",
                status="observed",
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Core generation tests (5 text-only scenarios)
# ---------------------------------------------------------------------------

class TestTextOnlyGeneration:

    def test_generates_valid_specification(self):
        service = SpecificationService(llm_client=_make_fake_llm())
        spec, metadata = service.generate(_text_context())
        assert isinstance(spec, ProjectSpecification)
        assert spec.project_summary == "A task management application."

    def test_metadata_contains_model_name(self):
        service = SpecificationService(llm_client=_make_fake_llm())
        _, metadata = service.generate(_text_context())
        assert metadata["model_name"] == "fake-model"

    def test_metadata_contains_prompt_version(self):
        service = SpecificationService(llm_client=_make_fake_llm())
        _, metadata = service.generate(_text_context())
        assert metadata["prompt_version"] == "spec_v1"

    def test_metadata_contains_generated_at(self):
        service = SpecificationService(llm_client=_make_fake_llm())
        _, metadata = service.generate(_text_context())
        assert "generated_at" in metadata
        assert "T" in metadata["generated_at"]  # ISO timestamp

    def test_artifact_is_draft_by_default(self):
        """GEN-008: Generated artifact must be draft until human approves."""
        service = SpecificationService(llm_client=_make_fake_llm())
        _, metadata = service.generate(_text_context())
        assert metadata["review_status"] == "draft"
        assert metadata["ai_generated_draft"] is True

    def test_context_open_questions_carried_forward(self):
        """GEN-005: Open questions from context must appear in spec."""
        context = _text_context()
        context.open_questions = ["What is the target platform?"]

        service = SpecificationService(llm_client=_make_fake_llm())
        spec, _ = service.generate(context)

        assert "What is the target platform?" in spec.open_questions

    def test_context_assumptions_carried_forward(self):
        """GEN-001: Assumptions from context must be preserved."""
        context = _text_context()
        context.assumptions = ["No authentication required."]

        service = SpecificationService(llm_client=_make_fake_llm())
        spec, _ = service.generate(context)

        assert "No authentication required." in spec.assumptions

    def test_empty_context_raises_value_error(self):
        service = SpecificationService(llm_client=_make_fake_llm())
        empty_context = NormalizedContext(
            client_text="",
            image_paths=[],
            input_mode="text_only",  # will fail our check
        )
        # Manually bypass mode validation
        object.__setattr__(empty_context, "client_text", "")
        object.__setattr__(empty_context, "image_paths", [])

        with pytest.raises(ValueError, match="no text or image evidence"):
            service.generate(empty_context)

    def test_invalid_json_from_model_raises_value_error(self):
        fake_llm = _make_fake_llm("this is not JSON {}")
        service = SpecificationService(llm_client=fake_llm)
        with pytest.raises(ValueError, match="invalid JSON"):
            service.generate(_text_context())

    def test_schema_mismatch_raises_value_error(self):
        """Model returns valid JSON but wrong fields → schema error."""
        bad_json = json.dumps({"wrong_field": "unexpected"})
        fake_llm = _make_fake_llm(bad_json)
        service = SpecificationService(llm_client=fake_llm)
        with pytest.raises(ValueError, match="schema validation"):
            service.generate(_text_context())


# ---------------------------------------------------------------------------
# Image-only scenarios (5 image-only tests)
# ---------------------------------------------------------------------------

class TestImageOnlyGeneration:

    def test_generates_spec_from_screenshot_evidence(self):
        service = SpecificationService(llm_client=_make_fake_llm())
        spec, metadata = service.generate(_image_context())
        assert isinstance(spec, ProjectSpecification)

    def test_input_mode_recorded_in_metadata(self):
        service = SpecificationService(llm_client=_make_fake_llm())
        _, metadata = service.generate(_image_context())
        assert metadata["input_mode"] == "image_only"

    def test_screenshot_evidence_included_in_prompt(self):
        """The LLM must receive screenshot evidence in its prompt."""
        fake_llm = _make_fake_llm()
        service = SpecificationService(llm_client=fake_llm)
        service.generate(_image_context())

        # Check that generate was called with a prompt containing evidence.
        call_kwargs = fake_llm.generate.call_args
        prompt_arg = call_kwargs[1].get("prompt", call_kwargs[0][0] if call_kwargs[0] else "")
        assert "SCREENSHOT OBSERVATIONS" in prompt_arg or "OBSERVED" in prompt_arg

    def test_missing_feature_flag_added_when_no_features(self):
        """Reliability check: flag when model returns empty features."""
        empty_spec = json.dumps({
            "project_summary": "A project.",
            "features": [],  # deliberately empty
            "user_stories": [],
            "acceptance_criteria": [],
            "implementation_plan": {
                "frontend": [], "backend": [], "data": [], "apis": [], "risks": []
            },
            "test_cases": [],
            "developer_prompt": "Some prompt.",
            "assumptions": [],
            "open_questions": [],
            "evidence_notes": [],
        })
        fake_llm = _make_fake_llm(empty_spec)
        service = SpecificationService(llm_client=fake_llm)
        spec, _ = service.generate(_image_context())

        assert any(
            "SYSTEM" in q and "features" in q.lower()
            for q in spec.open_questions
        )

    def test_empty_developer_prompt_flagged(self):
        """Reliability check: flag when developer_prompt is empty."""
        spec_with_empty_prompt = json.dumps({
            "project_summary": "A project.",
            "features": [
                {"name": "Feature A", "description": "...",
                 "priority": "medium", "source": "screenshot"}
            ],
            "user_stories": [],
            "acceptance_criteria": [],
            "implementation_plan": {
                "frontend": [], "backend": [], "data": [], "apis": [], "risks": []
            },
            "test_cases": [],
            "developer_prompt": "",  # deliberately empty
            "assumptions": [],
            "open_questions": [],
            "evidence_notes": [],
        })
        fake_llm = _make_fake_llm(spec_with_empty_prompt)
        service = SpecificationService(llm_client=fake_llm)
        spec, _ = service.generate(_image_context())

        assert any(
            "developer_prompt" in q
            for q in spec.open_questions
        )


# ---------------------------------------------------------------------------
# Combined input scenarios (5 combined tests)
# ---------------------------------------------------------------------------

class TestCombinedGeneration:

    def test_combined_input_mode_recorded(self):
        service = SpecificationService(llm_client=_make_fake_llm())
        _, metadata = service.generate(_combined_context())
        assert metadata["input_mode"] == "combined"

    def test_combined_evidence_in_prompt(self):
        """Prompt must contain both client text and screenshot sections."""
        fake_llm = _make_fake_llm()
        service = SpecificationService(llm_client=fake_llm)
        service.generate(_combined_context())

        call_kwargs = fake_llm.generate.call_args
        prompt = call_kwargs[1].get("prompt", call_kwargs[0][0] if call_kwargs[0] else "")

        assert "CLIENT REQUIREMENT TEXT" in prompt
        assert "SCREENSHOT OBSERVATIONS" in prompt

    def test_combined_spec_has_features(self):
        service = SpecificationService(llm_client=_make_fake_llm())
        spec, _ = service.generate(_combined_context())
        assert len(spec.features) > 0

    def test_combined_spec_has_user_stories(self):
        service = SpecificationService(llm_client=_make_fake_llm())
        spec, _ = service.generate(_combined_context())
        assert len(spec.user_stories) > 0

    def test_combined_spec_has_test_cases(self):
        service = SpecificationService(llm_client=_make_fake_llm())
        spec, _ = service.generate(_combined_context())
        assert len(spec.test_cases) > 0

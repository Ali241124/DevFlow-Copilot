
import pytest

from backend.app.services.context_builder import ContextBuilder

from backend.app.schemas.requirements import (
    Feature,
    RequirementsAnalysis
)

from backend.app.schemas.vision import (
    UIComponent,
    UIInteraction,
    VisionAnalysis
)


class FakeRequirementsService:

    def analyze(self, client_text):

        return RequirementsAnalysis(
            project_summary="A task management application.",
            features=[
                Feature(
                    name="Create tasks",
                    description="Users can create tasks.",
                    priority="high",
                    source_text="Users can create tasks.",
                    status="confirmed"
                )
            ],
            assumptions=["Task editing permissions are unspecified."],
            open_questions=["Should tasks have due dates?"]
        )


class FakeVisionService:

    def analyze_screenshot(self, image_path):

        return VisionAnalysis(
            page_description="A task management interface.",
            components=[
                UIComponent(
                    name="Create Task button",
                    component_type="button",
                    visible_text="Create Task",
                    evidence_note="The button is visible.",
                    status="observed"
                )
            ],
            visible_text=["Create Task"],
            current_state="Task management page is displayed.",
            interactions=[
                UIInteraction(
                    control="Create Task button",
                    possible_action="Open task creation form",
                    behavior="The resulting behavior is unknown.",
                    status="assumed",
                    evidence_note="Only the button is visible."
                )
            ],
            evidence_notes=["A task creation button is visible."],
            unknowns=["The result of clicking the button is unknown."]
        )


class FakeTaskExtractionService:

    def extract_tasks(self, image_path):

        return [
            {
                "name": "Design homepage",
                "status": "In Progress",
                "evidence": "Design homepage In Progress",
                "confidence": 95.5
            }
        ]

def make_builder():
    return ContextBuilder(
        requirements_service=FakeRequirementsService(),
        vision_service=FakeVisionService(),
        task_extraction_service=FakeTaskExtractionService()
    )


def test_text_only():
    context = make_builder().build(
        client_text="Build a task management application."
    )

    assert context.input_mode == "text_only"
    assert context.client_text != ""
    assert context.image_paths == []


def test_image_only():
    context = make_builder().build(
        image_paths=["sample.png"]
    )

    assert context.input_mode == "image_only"
    assert context.client_text == ""
    assert len(context.evidence) > 0


def test_combined_input():
    context = make_builder().build(
        client_text="Build a task management application.",
        image_paths=["sample.png"]
    )

    assert context.input_mode == "combined"

    sources = {item.source for item in context.evidence}

    assert "client_text" in sources
    assert "screenshot" in sources


def test_observed_and_assumed_are_separate():
    context = make_builder().build(
        image_paths=["sample.png"]
    )

    statuses = {item.status for item in context.evidence}

    assert "observed" in statuses
    assert "assumed" in statuses


def test_empty_input_fails():
    with pytest.raises(ValueError):
        make_builder().build()

def test_screenshot_evidence_is_preserved():
    context = make_builder().build(
        image_paths=["sample.png"]
    )

    evidence_contents = [
        item.content for item in context.evidence
    ]

    # Page description must be preserved.
    assert any(
        "task management interface" in content.lower()
        for content in evidence_contents
    )

    # Visible text must be preserved.
    assert any(
        "Create Task" in content
        for content in evidence_contents
    )

    # Current page state must be preserved.
    assert any(
        "Task management page is displayed." in content
        for content in evidence_contents
    )

    # UI component evidence must be preserved.
    assert any(
        "Create Task button" in content
        for content in evidence_contents
    )

    # Interaction evidence must be preserved.
    assert any(
        "Open task creation form" in content
        for content in evidence_contents
    )

    # Unknown information must be preserved.
    assert any(
        "result of clicking the button is unknown"
        in question.lower()
        for question in context.open_questions
    )

    # Assumed interaction must remain explicitly assumed.
    assert any(
        item.status == "assumed"
        and "Create Task button" in item.content
        for item in context.evidence
    )

def test_ocr_task_evidence_is_preserved():
    context = make_builder().build(
        image_paths=["sample.png"]
    )

    ocr_evidence = [
        item for item in context.evidence
        if "OCR extracted from screenshot" in item.evidence_note
    ]

    assert len(ocr_evidence) == 1

    task = ocr_evidence[0]

    assert task.source == "screenshot"
    assert task.category == "visual_observation"
    assert task.status == "observed"

    assert task.content == (
        "Task: Design homepage | Status: In Progress"
    )

    assert "95.5%" in task.evidence_note
    assert "Design homepage In Progress" in task.evidence_note


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))

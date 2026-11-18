
import pytest

from backend.app.services.task_extraction_service import (
    TaskExtractionService,
)


class FakeLayoutService:
    """Provides predefined OCR lines without reading an image."""

    def __init__(self, lines):
        self.lines = lines

    def group_into_lines(self, image_path):
        return self.lines


def test_extracts_four_tasks_with_correct_statuses():
    lines = [
        {
            "text": "Design homepage In Progress",
            "confidence": 95.5,
        },
        {
            "text": "Fix login validation Pending",
            "confidence": 96.0,
        },
        {
            "text": "Write API tests Completed",
            "confidence": 95.75,
        },
        {
            "text": "Prepare documentation Pending",
            "confidence": 96.0,
        },
    ]

    service = TaskExtractionService(
        layout_service=FakeLayoutService(lines)
    )

    tasks = service.extract_tasks("fake.png")

    assert len(tasks) == 4

    assert tasks[0]["name"] == "Design homepage"
    assert tasks[0]["status"] == "In Progress"

    assert tasks[1]["name"] == "Fix login validation"
    assert tasks[1]["status"] == "Pending"

    assert tasks[2]["name"] == "Write API tests"
    assert tasks[2]["status"] == "Completed"

    assert tasks[3]["name"] == "Prepare documentation"
    assert tasks[3]["status"] == "Pending"


def test_ignores_lines_without_recognized_status():
    lines = [
        {
            "text": "My Tasks",
            "confidence": 96.0,
        },
        {
            "text": "Manage your daily work",
            "confidence": 95.0,
        },
    ]

    service = TaskExtractionService(
        layout_service=FakeLayoutService(lines)
    )

    tasks = service.extract_tasks("fake.png")

    assert tasks == []


def test_preserves_original_evidence():
    line = {
        "text": "Design homepage In Progress",
        "confidence": 95.5,
    }

    service = TaskExtractionService(
        layout_service=FakeLayoutService([line])
    )

    tasks = service.extract_tasks("fake.png")

    assert tasks[0]["evidence"] == line["text"]
    assert tasks[0]["confidence"] == 95.5


def test_recognizes_not_started_status():
    lines = [
        {
            "text": "Build dashboard Not Started",
            "confidence": 94.0,
        }
    ]

    service = TaskExtractionService(
        layout_service=FakeLayoutService(lines)
    )

    tasks = service.extract_tasks("fake.png")

    assert len(tasks) == 1
    assert tasks[0]["name"] == "Build dashboard"
    assert tasks[0]["status"] == "Not Started"

"""
Day 2 — Unit Tests: Export Service
=====================================
Tests that Markdown and JSON exports produce valid output.
"""

import json
import pytest
from pathlib import Path

from backend.app.services.export_service import export_json, export_markdown


SAMPLE_SPEC = {
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
        "risks": ["Unclear scope for editing"],
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
    "developer_prompt": "Build the task creation endpoint...",
    "assumptions": ["No authentication required."],
    "open_questions": ["What is the deployment target?"],
    "evidence_notes": [
        {
            "claim": "Task creation",
            "source": "client_text",
            "note": "Directly in brief.",
        }
    ],
}


class TestExportJSON:

    def test_creates_json_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "backend.app.services.export_service.EXPORT_DIR",
            tmp_path
        )
        filepath = export_json(SAMPLE_SPEC, filename_prefix="test")
        assert filepath.exists()
        assert filepath.suffix == ".json"

    def test_json_content_is_valid(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "backend.app.services.export_service.EXPORT_DIR",
            tmp_path
        )
        filepath = export_json(SAMPLE_SPEC)
        content = json.loads(filepath.read_text(encoding="utf-8"))
        assert content["project_summary"] == SAMPLE_SPEC["project_summary"]

    def test_json_is_pretty_printed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "backend.app.services.export_service.EXPORT_DIR",
            tmp_path
        )
        filepath = export_json(SAMPLE_SPEC)
        raw = filepath.read_text(encoding="utf-8")
        assert "\n" in raw  # pretty-printed has newlines


class TestExportMarkdown:

    def test_creates_markdown_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "backend.app.services.export_service.EXPORT_DIR",
            tmp_path
        )
        filepath = export_markdown(SAMPLE_SPEC, project_name="Test App")
        assert filepath.exists()
        assert filepath.suffix == ".md"

    def test_markdown_contains_project_name(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "backend.app.services.export_service.EXPORT_DIR",
            tmp_path
        )
        filepath = export_markdown(SAMPLE_SPEC, project_name="My CRM App")
        content = filepath.read_text(encoding="utf-8")
        assert "My CRM App" in content

    def test_markdown_contains_draft_warning(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "backend.app.services.export_service.EXPORT_DIR",
            tmp_path
        )
        filepath = export_markdown(SAMPLE_SPEC)
        content = filepath.read_text(encoding="utf-8")
        assert "AI-generated draft" in content

    def test_markdown_contains_features(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "backend.app.services.export_service.EXPORT_DIR",
            tmp_path
        )
        filepath = export_markdown(SAMPLE_SPEC)
        content = filepath.read_text(encoding="utf-8")
        assert "Create tasks" in content

    def test_markdown_contains_user_stories(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "backend.app.services.export_service.EXPORT_DIR",
            tmp_path
        )
        filepath = export_markdown(SAMPLE_SPEC)
        content = filepath.read_text(encoding="utf-8")
        assert "US-001" in content

    def test_markdown_contains_open_questions(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "backend.app.services.export_service.EXPORT_DIR",
            tmp_path
        )
        filepath = export_markdown(SAMPLE_SPEC)
        content = filepath.read_text(encoding="utf-8")
        assert "Open Questions" in content
        assert "What is the deployment target?" in content

    def test_markdown_contains_assumptions(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "backend.app.services.export_service.EXPORT_DIR",
            tmp_path
        )
        filepath = export_markdown(SAMPLE_SPEC)
        content = filepath.read_text(encoding="utf-8")
        assert "No authentication required." in content

    def test_markdown_contains_evidence_traceability(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "backend.app.services.export_service.EXPORT_DIR",
            tmp_path
        )
        filepath = export_markdown(SAMPLE_SPEC)
        content = filepath.read_text(encoding="utf-8")
        assert "Evidence Traceability" in content

    def test_empty_spec_does_not_crash(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "backend.app.services.export_service.EXPORT_DIR",
            tmp_path
        )
        filepath = export_markdown({}, project_name="Empty")
        assert filepath.exists()

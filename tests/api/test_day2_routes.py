"""
Day 2 — API Tests: Project + Generation Endpoints
==================================================
Tests for the extended API routes:
- Project CRUD
- Specification generation (mocked LLM + context builder)
- Artifact review (approve/reject)
- Export endpoints

All tests use mocked services — no Ollama required.
"""

import json
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app
from backend.app.api import routes
from backend.app.schemas.context import NormalizedContext, EvidenceItem
from backend.app.schemas.specification import ProjectSpecification
from backend.app.storage.database import (
    ProjectStore,
    InputDocumentStore,
    GenerationRunStore,
    ArtifactStore,
)


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

VALID_SPEC = ProjectSpecification(
    project_summary="A task management application.",
    features=[],
    user_stories=[],
    acceptance_criteria=[],
    test_cases=[],
    developer_prompt="Build a task manager.",
    assumptions=["No auth required."],
    open_questions=[],
    evidence_notes=[],
)

VALID_METADATA = {
    "model_name": "fake-model",
    "prompt_version": "spec_v1",
    "generated_at": "2026-11-18T10:00:00+00:00",
    "input_mode": "text_only",
    "review_status": "draft",
    "ai_generated_draft": True,
}


class FakeContextBuilder:
    def build(self, client_text="", image_paths=None):
        image_paths = image_paths or []
        if client_text and image_paths:
            mode = "combined"
        elif client_text:
            mode = "text_only"
        elif image_paths:
            mode = "image_only"
        else:
            raise ValueError(
                "At least client text or one screenshot is required."
            )
        return NormalizedContext(
            client_text=client_text,
            image_paths=image_paths,
            input_mode=mode,
            evidence=[
                EvidenceItem(
                    source="client_text",
                    category="requirement",
                    content=client_text or "image evidence",
                    status="provided",
                )
            ],
        )


class FakeSpecService:
    model_name = "fake-model"
    prompt_version = "spec_v1"

    def generate(self, context):
        return VALID_SPEC, VALID_METADATA


def create_png_bytes() -> bytes:
    img = Image.new("RGB", (100, 100), color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"

    monkeypatch.setattr(routes, "ContextBuilder", FakeContextBuilder)
    monkeypatch.setattr(routes, "SpecificationService", lambda: FakeSpecService())
    monkeypatch.setattr(routes, "UPLOAD_DIR", tmp_path)

    # Use isolated stores for each test.
    monkeypatch.setattr(routes, "project_store", ProjectStore(db_path=db_path))
    monkeypatch.setattr(routes, "input_store", InputDocumentStore(db_path=db_path))
    monkeypatch.setattr(routes, "run_store", GenerationRunStore(db_path=db_path))
    monkeypatch.setattr(routes, "artifact_store", ArtifactStore(db_path=db_path))

    return TestClient(app)


def create_project(client, name="Test Project") -> str:
    """Helper: create a project and return its ID."""
    response = client.post(
        "/api/v1/projects",
        data={"name": name, "description": "A test project."},
    )
    assert response.status_code == 200
    return response.json()["project"]["project_id"]


# ---------------------------------------------------------------------------
# Project CRUD tests
# ---------------------------------------------------------------------------

class TestProjectEndpoints:

    def test_create_project(self, client):
        response = client.post(
            "/api/v1/projects",
            data={"name": "My App", "description": "An app."},
        )
        assert response.status_code == 200
        assert response.json()["project"]["name"] == "My App"

    def test_create_project_empty_name_rejected(self, client):
        response = client.post(
            "/api/v1/projects",
            data={"name": ""},
        )
        assert response.status_code == 400

    def test_list_projects(self, client):
        create_project(client, "Project A")
        create_project(client, "Project B")
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        projects = response.json()["projects"]
        assert len(projects) == 2

    def test_get_project(self, client):
        pid = create_project(client, "GetMe")
        response = client.get(f"/api/v1/projects/{pid}")
        assert response.status_code == 200
        assert response.json()["project"]["project_id"] == pid

    def test_get_nonexistent_project(self, client):
        response = client.get("/api/v1/projects/nonexistent")
        assert response.status_code == 404

    def test_delete_project(self, client):
        pid = create_project(client, "DeleteMe")
        response = client.delete(f"/api/v1/projects/{pid}")
        assert response.status_code == 200
        # Verify it's gone.
        get_response = client.get(f"/api/v1/projects/{pid}")
        assert get_response.status_code == 404


# ---------------------------------------------------------------------------
# Specification generation tests
# ---------------------------------------------------------------------------

class TestGenerationEndpoints:

    def test_generate_text_only(self, client):
        pid = create_project(client)
        response = client.post(
            f"/api/v1/projects/{pid}/generate",
            data={"client_text": "Build a task manager."},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["review_status"] == "draft"
        assert result["ai_generated_draft"] is True

    def test_generate_image_only(self, client):
        pid = create_project(client)
        response = client.post(
            f"/api/v1/projects/{pid}/generate",
            files={"file": ("sample.png", create_png_bytes(), "image/png")},
        )
        assert response.status_code == 200
        assert response.json()["review_status"] == "draft"

    def test_generate_combined(self, client):
        pid = create_project(client)
        response = client.post(
            f"/api/v1/projects/{pid}/generate",
            data={"client_text": "Build a task manager."},
            files={"file": ("sample.png", create_png_bytes(), "image/png")},
        )
        assert response.status_code == 200

    def test_generate_empty_input_rejected(self, client):
        pid = create_project(client)
        response = client.post(f"/api/v1/projects/{pid}/generate")
        assert response.status_code == 400

    def test_generate_nonexistent_project_rejected(self, client):
        response = client.post(
            "/api/v1/projects/nonexistent/generate",
            data={"client_text": "Build something."},
        )
        assert response.status_code == 404

    def test_generate_response_contains_artifact_id(self, client):
        pid = create_project(client)
        response = client.post(
            f"/api/v1/projects/{pid}/generate",
            data={"client_text": "Build a task manager."},
        )
        assert "artifact_id" in response.json()

    def test_generate_response_contains_run_id(self, client):
        pid = create_project(client)
        response = client.post(
            f"/api/v1/projects/{pid}/generate",
            data={"client_text": "Build a task manager."},
        )
        assert "run_id" in response.json()

    def test_generate_stores_run(self, client):
        pid = create_project(client)
        client.post(
            f"/api/v1/projects/{pid}/generate",
            data={"client_text": "Build a task manager."},
        )
        runs_response = client.get(f"/api/v1/projects/{pid}/runs")
        assert runs_response.status_code == 200
        assert len(runs_response.json()["runs"]) == 1


# ---------------------------------------------------------------------------
# Artifact review tests (FR-015, GEN-008)
# ---------------------------------------------------------------------------

class TestArtifactReview:

    def _generate_and_get_artifact_id(self, client) -> str:
        pid = create_project(client)
        response = client.post(
            f"/api/v1/projects/{pid}/generate",
            data={"client_text": "Build a task manager."},
        )
        return response.json()["artifact_id"]

    def test_approve_artifact(self, client):
        aid = self._generate_and_get_artifact_id(client)
        response = client.post(
            f"/api/v1/artifacts/{aid}/review",
            data={"status": "approved", "note": "Looks good."},
        )
        assert response.status_code == 200
        assert response.json()["review_status"] == "approved"

    def test_reject_artifact(self, client):
        aid = self._generate_and_get_artifact_id(client)
        response = client.post(
            f"/api/v1/artifacts/{aid}/review",
            data={"status": "rejected", "note": "Missing features."},
        )
        assert response.status_code == 200
        assert response.json()["review_status"] == "rejected"

    def test_invalid_review_status_rejected(self, client):
        aid = self._generate_and_get_artifact_id(client)
        response = client.post(
            f"/api/v1/artifacts/{aid}/review",
            data={"status": "auto_approved"},
        )
        assert response.status_code == 400

    def test_artifact_starts_as_draft(self, client):
        """GEN-008: Generated artifacts must start as draft."""
        aid = self._generate_and_get_artifact_id(client)
        response = client.get(f"/api/v1/artifacts/{aid}")
        assert response.status_code == 200
        assert response.json()["artifact"]["review_status"] == "draft"

    def test_review_nonexistent_artifact(self, client):
        response = client.post(
            "/api/v1/artifacts/nonexistent/review",
            data={"status": "approved"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Screenshot upload tests (backward compat)
# ---------------------------------------------------------------------------

class TestScreenshotUpload:

    def test_valid_png_accepted(self, client):
        response = client.post(
            "/api/v1/screenshots/upload",
            files={"file": ("sample.png", create_png_bytes(), "image/png")},
        )
        assert response.status_code == 200

    def test_unsupported_format_rejected(self, client):
        response = client.post(
            "/api/v1/screenshots/upload",
            files={
                "file": (
                    "document.txt",
                    BytesIO(b"not an image"),
                    "text/plain",
                )
            },
        )
        assert response.status_code == 415

    def test_corrupted_image_rejected(self, client):
        response = client.post(
            "/api/v1/screenshots/upload",
            files={
                "file": (
                    "corrupted.png",
                    BytesIO(b"not a valid PNG"),
                    "image/png",
                )
            },
        )
        assert response.status_code == 400

    def test_oversized_image_rejected(self, client):
        oversized = b"x" * (5 * 1024 * 1024 + 1)
        response = client.post(
            "/api/v1/screenshots/upload",
            files={"file": ("large.png", BytesIO(oversized), "image/png")},
        )
        assert response.status_code == 413

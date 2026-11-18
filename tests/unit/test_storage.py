"""
Day 2 — Unit Tests: SQLite Storage Layer
=========================================
Tests that Projects, InputDocuments, GenerationRuns and Artifacts
can be created, read, updated, and deleted correctly.

All tests use in-memory or temporary SQLite databases — no test
writes to the production data/devflow.db file.
"""

import json
import pytest
from pathlib import Path

from backend.app.storage.database import (
    ProjectStore,
    InputDocumentStore,
    GenerationRunStore,
    ArtifactStore,
    init_db,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_path(tmp_path) -> Path:
    """Return a fresh temporary database path for each test."""
    return tmp_path / "test_devflow.db"


@pytest.fixture
def project_store(db_path):
    return ProjectStore(db_path=db_path)


@pytest.fixture
def input_store(db_path):
    return InputDocumentStore(db_path=db_path)


@pytest.fixture
def run_store(db_path):
    return GenerationRunStore(db_path=db_path)


@pytest.fixture
def artifact_store(db_path):
    return ArtifactStore(db_path=db_path)


@pytest.fixture
def sample_project(project_store):
    return project_store.create(
        name="Test Project",
        description="A test project.",
        tech_stack="React, FastAPI",
    )


# ---------------------------------------------------------------------------
# ProjectStore
# ---------------------------------------------------------------------------

class TestProjectStore:

    def test_create_project(self, project_store):
        project = project_store.create(
            name="My App",
            description="An app.",
        )
        assert project["project_id"]
        assert project["name"] == "My App"
        assert project["description"] == "An app."

    def test_create_project_empty_name_rejected(self, project_store):
        with pytest.raises(ValueError, match="cannot be empty"):
            project_store.create(name="")

    def test_get_project(self, project_store, sample_project):
        project = project_store.get(sample_project["project_id"])
        assert project is not None
        assert project["name"] == "Test Project"

    def test_get_nonexistent_project_returns_none(self, project_store):
        result = project_store.get("nonexistent")
        assert result is None

    def test_list_projects(self, project_store):
        project_store.create(name="Project A")
        project_store.create(name="Project B")
        projects = project_store.list_all()
        assert len(projects) == 2

    def test_list_empty_returns_empty_list(self, project_store):
        assert project_store.list_all() == []

    def test_delete_project(self, project_store, sample_project):
        pid = sample_project["project_id"]
        deleted = project_store.delete(pid)
        assert deleted is True
        assert project_store.get(pid) is None

    def test_delete_nonexistent_returns_false(self, project_store):
        result = project_store.delete("does_not_exist")
        assert result is False

    def test_project_has_created_at(self, project_store):
        project = project_store.create(name="Timestamped")
        assert "created_at" in project
        assert "T" in project["created_at"]  # ISO format


# ---------------------------------------------------------------------------
# InputDocumentStore
# ---------------------------------------------------------------------------

class TestInputDocumentStore:

    def test_create_text_input(self, project_store, input_store):
        project = project_store.create(name="P1")
        doc = input_store.create(
            project_id=project["project_id"],
            input_type="text",
            source_text="Build a CRM.",
        )
        assert doc["input_id"]
        assert doc["input_type"] == "text"
        assert doc["source_text"] == "Build a CRM."

    def test_create_image_input(self, project_store, input_store):
        project = project_store.create(name="P2")
        doc = input_store.create(
            project_id=project["project_id"],
            input_type="image",
            file_path="/data/uploads/sample.png",
        )
        assert doc["input_type"] == "image"
        assert doc["file_path"] == "/data/uploads/sample.png"

    def test_create_combined_input(self, project_store, input_store):
        project = project_store.create(name="P3")
        doc = input_store.create(
            project_id=project["project_id"],
            input_type="combined",
            source_text="Build a CRM.",
            file_path="/data/uploads/crm_ui.png",
        )
        assert doc["input_type"] == "combined"

    def test_invalid_input_type_rejected(self, project_store, input_store):
        project = project_store.create(name="P4")
        with pytest.raises(ValueError, match="input_type must be one of"):
            input_store.create(
                project_id=project["project_id"],
                input_type="voice",  # not allowed
            )

    def test_list_for_project(self, project_store, input_store):
        project = project_store.create(name="P5")
        input_store.create(
            project_id=project["project_id"],
            input_type="text",
            source_text="Req 1",
        )
        input_store.create(
            project_id=project["project_id"],
            input_type="text",
            source_text="Req 2",
        )
        docs = input_store.list_for_project(project["project_id"])
        assert len(docs) == 2


# ---------------------------------------------------------------------------
# GenerationRunStore
# ---------------------------------------------------------------------------

class TestGenerationRunStore:

    def test_create_run(self, project_store, run_store):
        project = project_store.create(name="R1")
        run = run_store.create(
            project_id=project["project_id"],
            model_name="qwen3:4b",
            prompt_version="spec_v1",
        )
        assert run["run_id"]
        assert run["status"] == "pending"
        assert run["model_name"] == "qwen3:4b"
        assert run["prompt_version"] == "spec_v1"

    def test_update_status_to_running(self, project_store, run_store):
        project = project_store.create(name="R2")
        run = run_store.create(
            project_id=project["project_id"],
            model_name="qwen3:4b",
            prompt_version="spec_v1",
        )
        run_store.update_status(run["run_id"], "running")
        updated = run_store.get(run["run_id"])
        assert updated["status"] == "running"

    def test_update_status_to_success(self, project_store, run_store):
        project = project_store.create(name="R3")
        run = run_store.create(
            project_id=project["project_id"],
            model_name="qwen3:4b",
            prompt_version="spec_v1",
        )
        run_store.update_status(run["run_id"], "success")
        updated = run_store.get(run["run_id"])
        assert updated["status"] == "success"
        assert updated["completed_at"] is not None

    def test_update_status_with_error(self, project_store, run_store):
        project = project_store.create(name="R4")
        run = run_store.create(
            project_id=project["project_id"],
            model_name="qwen3:4b",
            prompt_version="spec_v1",
        )
        run_store.update_status(run["run_id"], "failed", "Model timeout.")
        updated = run_store.get(run["run_id"])
        assert updated["status"] == "failed"
        assert updated["error_message"] == "Model timeout."

    def test_list_runs_for_project(self, project_store, run_store):
        project = project_store.create(name="R5")
        run_store.create(
            project_id=project["project_id"],
            model_name="qwen3:4b",
            prompt_version="spec_v1",
        )
        run_store.create(
            project_id=project["project_id"],
            model_name="qwen2.5:1.5b",
            prompt_version="spec_v1",
        )
        runs = run_store.list_for_project(project["project_id"])
        assert len(runs) == 2

    def test_get_nonexistent_run_returns_none(self, run_store):
        assert run_store.get("does_not_exist") is None


# ---------------------------------------------------------------------------
# ArtifactStore
# ---------------------------------------------------------------------------

class TestArtifactStore:

    def _make_project_and_run(self, project_store, run_store) -> dict:
        project = project_store.create(name="A1")
        run = run_store.create(
            project_id=project["project_id"],
            model_name="qwen3:4b",
            prompt_version="spec_v1",
        )
        return {"project": project, "run": run}

    def test_create_artifact(self, project_store, run_store, artifact_store):
        pr = self._make_project_and_run(project_store, run_store)
        content = {"project_summary": "A test project."}

        artifact = artifact_store.create(
            run_id=pr["run"]["run_id"],
            artifact_type="project_specification",
            content=content,
        )

        assert artifact["artifact_id"]
        assert artifact["review_status"] == "draft"
        assert artifact["content"]["project_summary"] == "A test project."

    def test_get_artifact(self, project_store, run_store, artifact_store):
        pr = self._make_project_and_run(project_store, run_store)
        created = artifact_store.create(
            run_id=pr["run"]["run_id"],
            artifact_type="project_specification",
            content={"project_summary": "Test"},
        )
        fetched = artifact_store.get(created["artifact_id"])
        assert fetched is not None
        assert fetched["artifact_id"] == created["artifact_id"]
        assert fetched["content"]["project_summary"] == "Test"

    def test_artifact_content_roundtrips_json(
        self, project_store, run_store, artifact_store
    ):
        pr = self._make_project_and_run(project_store, run_store)
        content = {
            "project_summary": "Test",
            "features": [{"name": "Login", "description": "...", "priority": "high"}],
            "open_questions": ["What is the deployment target?"],
        }
        artifact = artifact_store.create(
            run_id=pr["run"]["run_id"],
            artifact_type="project_specification",
            content=content,
        )
        fetched = artifact_store.get(artifact["artifact_id"])
        assert fetched["content"]["features"][0]["name"] == "Login"

    def test_new_artifact_is_draft(self, project_store, run_store, artifact_store):
        pr = self._make_project_and_run(project_store, run_store)
        artifact = artifact_store.create(
            run_id=pr["run"]["run_id"],
            artifact_type="spec",
            content={},
        )
        assert artifact["review_status"] == "draft"

    def test_approve_artifact(self, project_store, run_store, artifact_store):
        pr = self._make_project_and_run(project_store, run_store)
        artifact = artifact_store.create(
            run_id=pr["run"]["run_id"],
            artifact_type="spec",
            content={},
        )
        artifact_store.review(artifact["artifact_id"], "approved", "LGTM")
        fetched = artifact_store.get(artifact["artifact_id"])
        assert fetched["review_status"] == "approved"
        assert fetched["reviewer_note"] == "LGTM"

    def test_reject_artifact(self, project_store, run_store, artifact_store):
        pr = self._make_project_and_run(project_store, run_store)
        artifact = artifact_store.create(
            run_id=pr["run"]["run_id"],
            artifact_type="spec",
            content={},
        )
        artifact_store.review(artifact["artifact_id"], "rejected", "Missing features.")
        fetched = artifact_store.get(artifact["artifact_id"])
        assert fetched["review_status"] == "rejected"

    def test_invalid_review_status_rejected(
        self, project_store, run_store, artifact_store
    ):
        pr = self._make_project_and_run(project_store, run_store)
        artifact = artifact_store.create(
            run_id=pr["run"]["run_id"],
            artifact_type="spec",
            content={},
        )
        with pytest.raises(ValueError, match="review status must be one of"):
            artifact_store.review(artifact["artifact_id"], "auto_approved")

    def test_artifact_cannot_be_auto_approved(
        self, project_store, run_store, artifact_store
    ):
        """
        GEN-008: The system must not auto-approve an artifact.
        Approval requires an explicit human review call.
        """
        pr = self._make_project_and_run(project_store, run_store)
        artifact = artifact_store.create(
            run_id=pr["run"]["run_id"],
            artifact_type="spec",
            content={"project_summary": "Auto draft"},
        )
        # Artifact must start as draft — not auto-approved.
        assert artifact["review_status"] == "draft"
        fetched = artifact_store.get(artifact["artifact_id"])
        assert fetched["review_status"] == "draft"

    def test_list_artifacts_for_run(
        self, project_store, run_store, artifact_store
    ):
        pr = self._make_project_and_run(project_store, run_store)
        artifact_store.create(
            run_id=pr["run"]["run_id"],
            artifact_type="spec",
            content={},
        )
        artifact_store.create(
            run_id=pr["run"]["run_id"],
            artifact_type="spec",
            content={},
        )
        artifacts = artifact_store.list_for_run(pr["run"]["run_id"])
        assert len(artifacts) == 2

    def test_get_nonexistent_artifact_returns_none(self, artifact_store):
        assert artifact_store.get("does_not_exist") is None

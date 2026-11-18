"""
Day 2 — SQLite Storage Layer
=============================
Provides local persistence for Projects, InputDocuments,
GenerationRuns and Artifacts.

Design rules (SRS §18):
- No secrets stored in the database.
- No auto-deployment or autonomous actions triggered from here.
- Generated artifacts remain drafts until a human reviews them.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


# ---------------------------------------------------------------------------
# Database location
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DB_PATH = PROJECT_ROOT / "data" / "devflow.db"


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Return a SQLite connection with foreign-key enforcement enabled."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    project_id   TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    description  TEXT NOT NULL DEFAULT '',
    tech_stack   TEXT NOT NULL DEFAULT '',
    created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS input_documents (
    input_id     TEXT PRIMARY KEY,
    project_id   TEXT NOT NULL REFERENCES projects(project_id),
    input_type   TEXT NOT NULL CHECK (input_type IN ('text', 'image', 'combined')),
    source_text  TEXT NOT NULL DEFAULT '',
    file_path    TEXT NOT NULL DEFAULT '',
    created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS generation_runs (
    run_id          TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL REFERENCES projects(project_id),
    input_id        TEXT REFERENCES input_documents(input_id),
    model_name      TEXT NOT NULL,
    prompt_version  TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('pending', 'running', 'success', 'failed')),
    error_message   TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL,
    completed_at    TEXT
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id    TEXT PRIMARY KEY,
    run_id         TEXT NOT NULL REFERENCES generation_runs(run_id),
    artifact_type  TEXT NOT NULL,
    content_json   TEXT NOT NULL,
    review_status  TEXT NOT NULL DEFAULT 'draft'
                   CHECK (review_status IN ('draft', 'approved', 'rejected')),
    reviewer_note  TEXT NOT NULL DEFAULT '',
    created_at     TEXT NOT NULL,
    reviewed_at    TEXT
);
"""


def init_db(db_path: Path = DB_PATH) -> None:
    """Create tables if they do not already exist."""
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA_SQL)


# ---------------------------------------------------------------------------
# Helper: current UTC timestamp
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------

class ProjectStore:

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        init_db(db_path)

    def create(
        self,
        name: str,
        description: str = "",
        tech_stack: str = ""
    ) -> dict:
        if not name.strip():
            raise ValueError("Project name cannot be empty.")

        project_id = uuid4().hex
        created_at = _now()

        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO projects
                    (project_id, name, description, tech_stack, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (project_id, name.strip(), description.strip(),
                 tech_stack.strip(), created_at)
            )

        return {
            "project_id": project_id,
            "name": name.strip(),
            "description": description.strip(),
            "tech_stack": tech_stack.strip(),
            "created_at": created_at,
        }

    def get(self, project_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM projects WHERE project_id = ?",
                (project_id,)
            ).fetchone()

        return dict(row) if row else None

    def list_all(self) -> list[dict]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM projects ORDER BY created_at DESC"
            ).fetchall()

        return [dict(r) for r in rows]

    def delete(self, project_id: str) -> bool:
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM projects WHERE project_id = ?",
                (project_id,)
            )

        return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# InputDocument CRUD
# ---------------------------------------------------------------------------

class InputDocumentStore:

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        init_db(db_path)

    def create(
        self,
        project_id: str,
        input_type: str,
        source_text: str = "",
        file_path: str = ""
    ) -> dict:
        allowed_types = {"text", "image", "combined"}

        if input_type not in allowed_types:
            raise ValueError(
                f"input_type must be one of {allowed_types}."
            )

        input_id = uuid4().hex
        created_at = _now()

        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO input_documents
                    (input_id, project_id, input_type,
                     source_text, file_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (input_id, project_id, input_type,
                 source_text, file_path, created_at)
            )

        return {
            "input_id": input_id,
            "project_id": project_id,
            "input_type": input_type,
            "source_text": source_text,
            "file_path": file_path,
            "created_at": created_at,
        }

    def get(self, input_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM input_documents WHERE input_id = ?",
                (input_id,)
            ).fetchone()

        return dict(row) if row else None

    def list_for_project(self, project_id: str) -> list[dict]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM input_documents
                WHERE project_id = ?
                ORDER BY created_at DESC
                """,
                (project_id,)
            ).fetchall()

        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# GenerationRun CRUD
# ---------------------------------------------------------------------------

class GenerationRunStore:

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        init_db(db_path)

    def create(
        self,
        project_id: str,
        model_name: str,
        prompt_version: str,
        input_id: str | None = None
    ) -> dict:
        run_id = uuid4().hex
        created_at = _now()

        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO generation_runs
                    (run_id, project_id, input_id, model_name,
                     prompt_version, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'pending', ?)
                """,
                (run_id, project_id, input_id,
                 model_name, prompt_version, created_at)
            )

        return {
            "run_id": run_id,
            "project_id": project_id,
            "input_id": input_id,
            "model_name": model_name,
            "prompt_version": prompt_version,
            "status": "pending",
            "error_message": "",
            "created_at": created_at,
            "completed_at": None,
        }

    def update_status(
        self,
        run_id: str,
        status: str,
        error_message: str = ""
    ) -> None:
        completed_at = _now() if status in ("success", "failed") else None

        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                UPDATE generation_runs
                SET status = ?, error_message = ?, completed_at = ?
                WHERE run_id = ?
                """,
                (status, error_message, completed_at, run_id)
            )

    def get(self, run_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM generation_runs WHERE run_id = ?",
                (run_id,)
            ).fetchone()

        return dict(row) if row else None

    def list_for_project(self, project_id: str) -> list[dict]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM generation_runs
                WHERE project_id = ?
                ORDER BY created_at DESC
                """,
                (project_id,)
            ).fetchall()

        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Artifact CRUD
# ---------------------------------------------------------------------------

class ArtifactStore:

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        init_db(db_path)

    def create(
        self,
        run_id: str,
        artifact_type: str,
        content: dict
    ) -> dict:
        artifact_id = uuid4().hex
        created_at = _now()
        content_json = json.dumps(content, ensure_ascii=False)

        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO artifacts
                    (artifact_id, run_id, artifact_type,
                     content_json, review_status, created_at)
                VALUES (?, ?, ?, ?, 'draft', ?)
                """,
                (artifact_id, run_id, artifact_type,
                 content_json, created_at)
            )

        return {
            "artifact_id": artifact_id,
            "run_id": run_id,
            "artifact_type": artifact_type,
            "content": content,
            "review_status": "draft",
            "reviewer_note": "",
            "created_at": created_at,
            "reviewed_at": None,
        }

    def review(
        self,
        artifact_id: str,
        status: str,
        note: str = ""
    ) -> bool:
        """
        Set artifact review status.
        Only 'approved' or 'rejected' are accepted.
        A reviewer action is required — this is not automatic.
        """
        allowed = {"approved", "rejected"}

        if status not in allowed:
            raise ValueError(
                f"review status must be one of {allowed}."
            )

        reviewed_at = _now()

        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE artifacts
                SET review_status = ?, reviewer_note = ?, reviewed_at = ?
                WHERE artifact_id = ?
                """,
                (status, note, reviewed_at, artifact_id)
            )

        return cursor.rowcount > 0

    def get(self, artifact_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM artifacts WHERE artifact_id = ?",
                (artifact_id,)
            ).fetchone()

        if not row:
            return None

        result = dict(row)
        result["content"] = json.loads(result["content_json"])
        return result

    def list_for_run(self, run_id: str) -> list[dict]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM artifacts
                WHERE run_id = ?
                ORDER BY created_at DESC
                """,
                (run_id,)
            ).fetchall()

        result = []

        for row in rows:
            item = dict(row)
            item["content"] = json.loads(item["content_json"])
            result.append(item)

        return result

    def list_approved_for_project(self, project_id: str) -> list[dict]:
        """Return all approved artifacts for a project (across all runs)."""
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT a.*
                FROM artifacts a
                JOIN generation_runs r ON a.run_id = r.run_id
                WHERE r.project_id = ?
                  AND a.review_status = 'approved'
                ORDER BY a.created_at DESC
                """,
                (project_id,)
            ).fetchall()

        result = []

        for row in rows:
            item = dict(row)
            item["content"] = json.loads(item["content_json"])
            result.append(item)

        return result

"""
Day 2 — Full API Routes
========================
Adds:
  - Project CRUD endpoints
  - Full specification generation endpoint (text + image → ProjectSpecification)
  - Artifact review endpoint (approve / reject)
  - Export endpoint (Markdown + JSON)

All endpoints operate locally. No data leaves the machine.
"""

from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from backend.app.services.context_builder import ContextBuilder
from backend.app.services.specification_service import SpecificationService
from backend.app.services.export_service import export_json, export_markdown
from backend.app.storage.database import (
    ProjectStore,
    InputDocumentStore,
    GenerationRunStore,
    ArtifactStore,
)

router = APIRouter(prefix="/api/v1", tags=["DevFlow Copilot"])

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_FORMATS = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".webp": "WEBP",
}

# ---------------------------------------------------------------------------
# Shared stores (lazy initialization — created on first use)
# Can be overridden in tests via monkeypatch.
# ---------------------------------------------------------------------------

def _get_project_store():
    global project_store
    if project_store is None:
        project_store = ProjectStore()
    return project_store


def _get_input_store():
    global input_store
    if input_store is None:
        input_store = InputDocumentStore()
    return input_store


def _get_run_store():
    global run_store
    if run_store is None:
        run_store = GenerationRunStore()
    return run_store


def _get_artifact_store():
    global artifact_store
    if artifact_store is None:
        artifact_store = ArtifactStore()
    return artifact_store


project_store = None
input_store = None
run_store = None
artifact_store = None


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@router.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy", "day": 2}


# ---------------------------------------------------------------------------
# Screenshot upload helper (reused internally)
# ---------------------------------------------------------------------------

async def _save_upload(file: UploadFile) -> dict:
    """Validate and save an uploaded image. Returns upload metadata."""
    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=415,
            detail="Unsupported image format. Use PNG, JPG, JPEG or WEBP.",
        )

    contents = await file.read(MAX_FILE_SIZE + 1)
    await file.close()

    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image is too large. Maximum allowed size is 5 MB.",
        )

    try:
        with Image.open(BytesIO(contents)) as image:
            actual_format = image.format
            image.verify()

        if actual_format != ALLOWED_FORMATS[extension]:
            raise HTTPException(
                status_code=415,
                detail="File extension does not match the actual image format.",
            )

    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(
            status_code=400,
            detail="Invalid or corrupted image file.",
        )

    filename = f"{uuid4().hex}{extension}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOAD_DIR / filename
    file_path.write_bytes(contents)

    return {
        "filename": filename,
        "path": str(file_path),
        "size_bytes": len(contents),
        "format": actual_format,
    }


# ---------------------------------------------------------------------------
# Screenshot upload endpoint (kept for backward compatibility)
# ---------------------------------------------------------------------------

@router.post("/screenshots/upload", tags=["Screenshots"])
async def upload_screenshot(file: UploadFile = File(...)):
    result = await _save_upload(file)
    return {
        "message": "Screenshot uploaded successfully.",
        **result,
    }


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------

@router.post("/projects", tags=["Projects"])
def create_project(
    name: str = Form(default=""),
    description: str = Form(default=""),
    tech_stack: str = Form(default=""),
):
    """Create a new project container."""
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="Project name cannot be empty.")
    try:
        project = _get_project_store().create(
            name=name,
            description=description,
            tech_stack=tech_stack,
        )
        return {"message": "Project created.", "project": project}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/projects", tags=["Projects"])
def list_projects():
    """List all projects."""
    return {"projects": _get_project_store().list_all()}


@router.get("/projects/{project_id}", tags=["Projects"])
def get_project(project_id: str):
    """Get a single project."""
    project = _get_project_store().get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return {"project": project}


@router.delete("/projects/{project_id}", tags=["Projects"])
def delete_project(project_id: str):
    """Delete a project."""
    deleted = _get_project_store().delete(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found.")
    return {"message": "Project deleted."}


# ---------------------------------------------------------------------------
# Full multimodal requirement analysis (Day 1 endpoint — context only)
# ---------------------------------------------------------------------------

@router.post("/requirements/analyze", tags=["Requirements"])
async def analyze_requirements(
    client_text: str = Form(default=""),
    file: UploadFile | None = File(default=None),
):
    """
    Build a NormalizedContext from text and/or screenshot.
    Returns the evidence-annotated context (not a full spec).
    """
    image_paths = []

    if file is not None:
        upload_result = await _save_upload(file)
        image_paths.append(upload_result["path"])

    try:
        context_builder = ContextBuilder()
        context = context_builder.build(
            client_text=client_text,
            image_paths=image_paths,
        )
        return {
            "message": "Requirement analysis completed.",
            "result": context.model_dump(),
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


# ---------------------------------------------------------------------------
# Full specification generation (Day 2 primary endpoint)
# ---------------------------------------------------------------------------

@router.post("/projects/{project_id}/generate", tags=["Generation"])
async def generate_specification(
    project_id: str,
    client_text: str = Form(default=""),
    file: UploadFile | None = File(default=None),
):
    """
    Full multimodal pipeline:
      1. Upload + validate screenshot (if provided).
      2. Store InputDocument.
      3. Build NormalizedContext.
      4. Generate ProjectSpecification via LLM.
      5. Store GenerationRun + Artifact.
      6. Return specification as draft (requires human review).

    GEN-008: The artifact is DRAFT until a human reviewer approves it.
    """
    # Verify project exists.
    project = _get_project_store().get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    # --- Step 1: Handle image upload ---
    image_paths = []
    file_path_str = ""

    if file is not None:
        upload_result = await _save_upload(file)
        image_paths.append(upload_result["path"])
        file_path_str = upload_result["path"]

    # --- Step 2: Validate we have at least one input ---
    if not client_text.strip() and not image_paths:
        raise HTTPException(
            status_code=400,
            detail="Provide client_text or upload a screenshot.",
        )

    # Determine input type for storage.
    has_text = bool(client_text.strip())
    has_image = bool(image_paths)

    if has_text and has_image:
        input_type = "combined"
    elif has_text:
        input_type = "text"
    else:
        input_type = "image"

    # --- Step 3: Store InputDocument ---
    input_doc = _get_input_store().create(
        project_id=project_id,
        input_type=input_type,
        source_text=client_text,
        file_path=file_path_str,
    )

    # --- Step 4: Create GenerationRun record ---
    spec_service = SpecificationService()
    run = _get_run_store().create(
        project_id=project_id,
        model_name=spec_service.model_name,
        prompt_version=spec_service.prompt_version,
        input_id=input_doc["input_id"],
    )
    _get_run_store().update_status(run["run_id"], "running")

    # --- Step 5: Build context + generate specification ---
    try:
        context_builder = ContextBuilder()
        context = context_builder.build(
            client_text=client_text,
            image_paths=image_paths,
        )

        spec, metadata = spec_service.generate(context)

        # --- Step 6: Store artifact ---
        artifact_content = {
            **spec.model_dump(),
            "_metadata": metadata,
        }

        artifact = _get_artifact_store().create(
            run_id=run["run_id"],
            artifact_type="project_specification",
            content=artifact_content,
        )

        _get_run_store().update_status(run["run_id"], "success")

        return {
            "message": (
                "Specification generated. "
                "Status: DRAFT — requires human review."
            ),
            "artifact_id": artifact["artifact_id"],
            "run_id": run["run_id"],
            "input_id": input_doc["input_id"],
            "review_status": "draft",
            "ai_generated_draft": True,
            "specification": spec.model_dump(),
            "metadata": metadata,
        }

    except (ValueError, RuntimeError) as error:
        _get_run_store().update_status(
            run["run_id"], "failed", error_message=str(error)
        )
        raise HTTPException(status_code=422, detail=str(error)) from error


# ---------------------------------------------------------------------------
# List runs and artifacts for a project
# ---------------------------------------------------------------------------

@router.get("/projects/{project_id}/runs", tags=["Generation"])
def list_runs(project_id: str):
    """List all generation runs for a project."""
    if not _get_project_store().get(project_id):
        raise HTTPException(status_code=404, detail="Project not found.")
    runs = _get_run_store().list_for_project(project_id)
    return {"runs": runs}


@router.get("/runs/{run_id}/artifacts", tags=["Artifacts"])
def list_artifacts(run_id: str):
    """List all artifacts for a generation run."""
    return {"artifacts": _get_artifact_store().list_for_run(run_id)}


@router.get("/artifacts/{artifact_id}", tags=["Artifacts"])
def get_artifact(artifact_id: str):
    """Get a single artifact."""
    artifact = _get_artifact_store().get(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found.")
    return {"artifact": artifact}


# ---------------------------------------------------------------------------
# Human review endpoint (FR-015, GEN-008)
# ---------------------------------------------------------------------------

@router.post("/artifacts/{artifact_id}/review", tags=["Review"])
def review_artifact(
    artifact_id: str,
    status: str = Form(...),
    note: str = Form(default=""),
):
    """
    Human review gate: approve or reject an artifact.

    GEN-008: Artifacts remain draft until a human action is taken here.
    No artifact is ever auto-approved by the system.
    """
    allowed = {"approved", "rejected"}

    if status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Status must be one of: {', '.join(sorted(allowed))}.",
        )

    updated = _get_artifact_store().review(
        artifact_id=artifact_id,
        status=status,
        note=note,
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Artifact not found.")

    return {
        "message": f"Artifact {status}.",
        "artifact_id": artifact_id,
        "review_status": status,
    }


# ---------------------------------------------------------------------------
# Export endpoints (FR-017)
# ---------------------------------------------------------------------------

@router.post("/artifacts/{artifact_id}/export/json", tags=["Export"])
def export_artifact_json(artifact_id: str):
    """Export an artifact as JSON."""
    artifact = _get_artifact_store().get(artifact_id)

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found.")

    filepath = export_json(
        content=artifact["content"],
        filename_prefix=f"artifact_{artifact_id[:8]}"
    )

    return {
        "message": "Exported as JSON.",
        "file_path": str(filepath),
    }


@router.post("/artifacts/{artifact_id}/export/markdown", tags=["Export"])
def export_artifact_markdown(
    artifact_id: str,
    project_name: str = Form(default="Project"),
):
    """Export an artifact as Markdown."""
    artifact = _get_artifact_store().get(artifact_id)

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found.")

    filepath = export_markdown(
        content=artifact["content"],
        project_name=project_name,
        filename_prefix=f"artifact_{artifact_id[:8]}"
    )

    return {
        "message": "Exported as Markdown.",
        "file_path": str(filepath),
    }

# DevFlow Copilot Architecture & System Design

## 1. System Overview
**MoinSystems AI DevFlow Copilot** is a local-first Generative AI software development pipeline designed specifically for software houses and development agencies. It converts raw, unstructured client inputs (text briefs, meeting transcripts, wireframe screenshots, diagrams) into machine-validated, developer-ready delivery artifacts.

### Guiding Principles:
1. **Zero-Paid-API Rule**: 100% free and open-source local execution (FastAPI, Streamlit, Ollama, Qwen open models, Moondream, Tesseract OCR, SQLite).
2. **Evidence Fidelity & Anti-Hallucination**: Observable UI facts (`observed`) are strictly isolated from inferred behaviors (`assumed`) and missing details (`open_questions`).
3. **Mandatory Human-in-the-Loop Review Gate (`GEN-008`)**: All generated artifacts default to `draft` and cannot be approved or deployed autonomously.
4. **End-to-End Traceability (`GEN-003`, `GEN-007`)**: Every artifact links to input documents, generation run metadata, model checkpoint, prompt version, and human review decisions.

---

## 2. Logical Architecture Diagram

```mermaid
graph TD
    subgraph ClientLayer ["Client & Interaction Layer"]
        UI["Streamlit Frontend (Browser)"]
    end

    subgraph ServiceLayer ["FastAPI Backend Layer (Port 8000)"]
        API["REST API Router (/api/v1)"]
        CB["ContextBuilder"]
        SS["SpecificationService (spec_v1 / spec_v2)"]
        EAG["EngineeringArtifactGenerator"]
        EXP["ExportService (JSON / Markdown)"]
        EVAL["GenAIEvaluator (Benchmark Suite)"]
    end

    subgraph ModelLayer ["Local AI & Vision Engines (Ollama Runtime)"]
        QWEN["Qwen3:4b / Qwen2.5:1.5b (Text LLM)"]
        MOON["Moondream (Vision Model)"]
        OCR["Tesseract OCR (Spatial Text Extraction)"]
    end

    subgraph StorageLayer ["Persistence & File Storage"]
        DB[(SQLite: devflow.db)]
        UPLOADS["Local Uploads (data/uploads/)"]
        EXPORTS["Export Storage (data/exports/)"]
    end

    UI -->|HTTP / Multipart| API
    API --> CB
    API --> SS
    API --> EAG
    API --> EXP
    API --> EVAL

    CB --> OCR
    CB --> MOON
    SS --> QWEN

    API --> DB
    API --> UPLOADS
    EXP --> EXPORTS
```

---

## 3. End-to-End Workflow Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Reviewer
    participant UI as Streamlit UI
    participant API as FastAPI Backend
    participant AI as Local Models (Ollama)
    participant DB as SQLite Storage

    User->>UI: Create Project & Submit Brief / Screenshot
    UI->>API: POST /projects/{id}/generate (Text + File)
    API->>DB: Store InputDocument & Initialize GenerationRun (status: running)
    API->>AI: Image Analysis (Moondream) + OCR (Tesseract)
    AI-->>API: Extracted UI Components & Visual State
    API->>AI: Generate ProjectSpecification (Qwen3 with spec_v2)
    AI-->>API: Canonical JSON Specification
    API->>API: Schema Validation & Reliability Checks
    API->>API: Generate Engineering Artifacts (Stories, ACs, QA, Dev Prompt, Release Notes)
    API->>DB: Persist Artifacts (review_status: 'draft')
    API-->>UI: Return Draft Artifact Package
    UI-->>User: Display Specification, Evidence & Open Questions
    
    alt Review Decision: Approve
        User->>UI: Click 'Approve' with audit note
        UI->>API: POST /artifacts/{id}/review (status: approved)
        API->>DB: Update review_status='approved'
    else Review Decision: Edit
        User->>UI: Modify JSON & Save
        UI->>API: POST /artifacts/{id}/edit
        API->>DB: Update content_json & reviewer_note
    else Review Decision: Regenerate
        User->>UI: Provide feedback & Regenerate
        UI->>API: POST /projects/{id}/regenerate
        API->>AI: Re-run with prompt containing reviewer corrections
    end

    User->>UI: Request Export (Markdown or JSON)
    UI->>API: POST /artifacts/{id}/export/{format}
    API-->>UI: Downloadable validated artifact files
```

---

## 4. Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    PROJECT ||--o{ INPUT_DOCUMENT : contains
    PROJECT ||--o{ GENERATION_RUN : tracks
    INPUT_DOCUMENT ||--o| GENERATION_RUN : feeds
    GENERATION_RUN ||--o{ ARTIFACT : produces
    ARTIFACT ||--o{ REVIEW_FEEDBACK : audits

    PROJECT {
        string project_id PK
        string name
        string description
        string tech_stack
        string created_at
    }

    INPUT_DOCUMENT {
        string input_id PK
        string project_id FK
        string input_type "text | image | combined"
        string source_text
        string file_path
        string created_at
    }

    GENERATION_RUN {
        string run_id PK
        string project_id FK
        string input_id FK
        string model_name
        string prompt_version
        string status "pending | running | success | failed"
        string error_message
        string created_at
        string completed_at
    }

    ARTIFACT {
        string artifact_id PK
        string run_id FK
        string artifact_type "specification | user_stories | qa_suite | dev_prompt | etc"
        json content_json
        string review_status "draft | approved | rejected"
        string reviewer_note
        string created_at
        string reviewed_at
    }

    REVIEW_FEEDBACK {
        string feedback_id PK
        string artifact_id FK
        string action "approved | rejected | edited"
        string reviewer_note
        string timestamp
    }
```

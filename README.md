# MoinSystems AI DevFlow Copilot

> **Local-First, Multimodal Generative AI System for Software Houses**  
> *Zero Paid APIs — 100% Free & Open-Source Stack*  
> **Version 1.0 | Standalone SRS & 5-Day Implementation Complete**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg?logo=streamlit)](https://streamlit.io)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black.svg?logo=ollama)](https://ollama.com)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-150%20Passed-brightgreen.svg)](https://pytest.org)

DevFlow Copilot converts unstructured client briefs, meeting notes, wireframes, and UI screenshots into reviewable, developer-ready software delivery artifacts: structured project specifications, user stories, Given/When/Then acceptance criteria, implementation plans, QA test suites, context-rich developer prompts, client progress updates, and release notes.

---

## 📑 Table of Contents
1. [Core Features](#-core-features)
2. [Why Local-First & Zero Paid APIs?](#-why-local-first--zero-paid-apis)
3. [Technology Stack](#-technology-stack)
4. [Architecture & Workflow](#-architecture--workflow)
5. [Data Model / ERD](#-data-model--erd)
6. [5-Day Milestone Implementation History](#-5-day-milestone-implementation-history)
7. [Setup & Quickstart Guide](#-setup--quickstart-guide)
8. [Automated Testing & Benchmark](#-automated-testing--benchmark)
9. [Human Review & Safety Safeguards](#-human-review--safety-safeguards)
10. [Known Limitations & Failure Modes](#-known-limitations--failure-modes)
11. [Deliverables Checklist](#-deliverables-checklist)

---

## 🌟 Core Features

- **Multimodal Requirement Ingestion**: Accepts text briefs, meeting notes, and wireframe screenshots (PNG, JPG, WEBP) in Text-only, Image-only, or Combined mode.
- **Vision & Spatial OCR Pipeline**: Employs local `moondream` alongside Tesseract OCR to extract UI elements, button labels, form fields, and status indicators.
- **Observed vs. Assumed Evidence Separation (`GEN-001`)**: Strictly distinguishes verified visual facts (`observed`) from inferred behaviors (`assumed`), placing unknowns in `open_questions`.
- **Full Engineering Artifact Generation**:
  - Structured Project Specifications (Canonical Schema SRS §10)
  - User Stories (`US-001`) in Role/Goal/Benefit format with priorities
  - Acceptance Criteria in standard `Given / When / Then` syntax
  - Implementation Plans covering Frontend, Backend, Data, APIs, Dependencies, and Risks
  - QA Test Cases covering **Positive**, **Negative**, and **Edge** scenarios
  - Context-Rich Developer Prompts with constraints and checklists
  - Client Progress Updates & Semantic Release Notes
- **Mandatory Human-in-the-Loop Review Gate (`GEN-008`)**: All generated artifacts default to `draft`. Reviewers can **Approve**, **Reject**, **Directly Edit JSON**, or **Regenerate with Feedback**.
- **Local Persistence & Traceability (`GEN-003`, `GEN-007`)**: Full SQLite storage tracking `project_id`, `run_id`, `model_name`, `prompt_version`, and review status.
- **Evaluation & Reliability Benchmark**: 32 distinct scenarios across 9 categories (including ambiguous, contradictory, and prompt-injection attacks) with 0.0–5.0 multi-dimensional scoring.
- **Local Exporting (`FR-017`)**: One-click download and disk export to Markdown (`.md`) and JSON (`.json`).

---

## 💡 Why Local-First & Zero Paid APIs?

Current industry research reveals both widespread GenAI adoption and high skepticism regarding accuracy:
- **Stack Overflow (2025)**: 84% adoption, but 46% distrust AI output accuracy vs 33% trust, with 66% frustrated by AI solutions that are *"almost right, but not quite."*
- **DORA (2025)**: Emphasizes that AI is an *amplifier of existing software engineering discipline*, necessitating strict schema validation, structured outputs, and human review gates.

### Trade-Offs of Local-First AI:
| Advantages | Trade-Offs / Mitigations |
|---|---|
| **Zero Software Cost**: Zero recurring SaaS API fees. | **Hardware Bound**: Generation latency is governed by local CPU/GPU/RAM. |
| **Total Client Data Privacy**: No proprietary client data ever leaves the local machine. | **Context Window Limits**: Requires disciplined, concise prompt templates (`spec_v2`). |
| **Complete Independence**: Immune to cloud API rate limits, outages, and pricing shifts. | **Quantization Nuance**: Requires low temperature (`0.1 - 0.15`) for deterministic JSON. |

---

## 🛠️ Technology Stack

| Layer | Component | Version / Model | License | Paid? |
|---|---|---|---|---|
| **Language** | Python | 3.11+ | PSF License | No |
| **Backend API** | FastAPI + Uvicorn | 0.100+ | MIT | No |
| **Frontend UI** | Streamlit | 1.30+ | Apache 2.0 | No |
| **Model Runtime** | Ollama | Latest Local Daemon | MIT | No |
| **Text Generation** | Qwen3-family open model | `qwen3:4b` (or `qwen2.5:1.5b`) | Open Weights | No |
| **Vision Analysis** | Moondream | `moondream:latest` | Open Weights | No |
| **OCR Extraction** | Tesseract OCR + pytesseract | 5.x | Apache 2.0 | No |
| **Validation** | Pydantic v2 | 2.5+ | MIT | No |
| **Local Storage** | SQLite 3 | Embedded | Public Domain | No |

---

## 🏛️ Architecture & Workflow

Detailed architecture documentation, diagrams, and workflow sequences are available in [docs/architecture.md](file:///c:/Users/ah627/OneDrive/Documents/DevFlow-Copilot/docs/architecture.md).

```
                     ┌───────────────────────────────┐
                     │    Streamlit Web UI (8501)    │
                     │ (Input, Spec, Review, Export) │
                     └───────────────┬───────────────┘
                                     │ HTTP / JSON
                                     ▼
                     ┌───────────────────────────────┐
                     │    FastAPI Backend (8000)     │
                     ├───────────────────────────────┤
                     │ • Routes & Project CRUD       │
                     │ • ContextBuilder              │
                     │ • SpecificationService        │
                     │ • EngineeringArtifactGen      │
                     │ • GenAIEvaluator              │
                     │ • ExportService (JSON/MD)     │
                     └───────┬───────────────┬───────┘
                             │               │
            ┌────────────────┴──┐         ┌──┴──────────────────┐
            ▼                   ▼         ▼                     ▼
     ┌──────────────┐    ┌─────────────┐ ┌───────────────┐ ┌──────────────┐
     │ Tesseract    │    │ Ollama      │ │ SQLite DB     │ │ Local Disk   │
     │ OCR Engine   │    │ Moondream + │ │ (devflow.db)  │ │ (uploads/ &  │
     │ (Spatial)    │    │ Qwen3:4b    │ │               │ │  exports/)   │
     └──────────────┘    └─────────────┘ └───────────────┘ └──────────────┘
```

---

## 🗄️ Data Model / ERD

```
PROJECT (1) ──────────< INPUT_DOCUMENT (N)
   │
   └──────────────────< GENERATION_RUN (N)
                               │
                               └──────────< ARTIFACT (N)
                                                │
                                                └──────────< REVIEW_FEEDBACK (N)
```
- **Project**: Top-level container (`project_id`, `name`, `description`, `tech_stack`).
- **InputDocument**: Preserves raw source inputs (`input_id`, `input_type`, `source_text`, `file_path`).
- **GenerationRun**: Audits every AI invocation (`run_id`, `model_name`, `prompt_version`, `status`).
- **Artifact**: Stores generated JSON outputs (`artifact_id`, `artifact_type`, `content_json`, `review_status`).

---

## 📅 5-Day Milestone Implementation History

- **Day 1 — GenAI Foundation & Requirements Generator**:
  - Python/FastAPI environment, Ollama client integration, initial Pydantic schemas.
  - `RequirementsService` with verbatim client evidence verification (`verify_evidence`).
- **Day 2 — Multimodal Requirement Analyzer**:
  - Image upload validation, `VisionService` (`moondream`), `OCRClient` (Tesseract).
  - `ContextBuilder` into `NormalizedContext` separating `observed` visual facts from `assumed` logic.
  - Canonical `ProjectSpecification` generation (SRS §10) via versioned prompt `spec_v1`.
  - SQLite persistence layer (`ProjectStore`, `GenerationRunStore`, `ArtifactStore`).
- **Day 3 — Engineering Artifact Generator**:
  - Dedicated generators for User Stories (`US-001`), Given/When/Then Acceptance Criteria (`AC-001`), and Implementation Plans.
  - QA Test Suite with mandatory Positive, Negative, and Edge test cases.
  - Context-rich Developer Prompts with architecture constraints and acceptance checklists.
  - Secondary artifacts: Stakeholder Client Updates and Semantic Versioned Release Notes.
- **Day 4 — Evaluation, Reliability & Hallucination Defense**:
  - 32-scenario benchmark dataset across 9 categories.
  - Multi-dimensional scoring functions (Completeness, Fidelity, Testability, Usefulness, Uncertainty).
  - Versioned prompt iteration: `spec_v1` (3.21/5.0) to `spec_v2` (4.93/5.0).
  - Prompt injection defense neutralizing malicious system prompt overrides.
- **Day 5 — Integrated DevFlow Copilot MVP**:
  - Multi-tab Streamlit dashboard with full Approve / Edit JSON / Regenerate-with-feedback review flows.
  - Integrated benchmark dashboard tab for one-click evaluation runs.
  - Complete architecture, workflow, ERD, and live demo script documentation.

---

## 🚀 Setup & Quickstart Guide

### 1. Prerequisites
- **Python 3.11+**
- **Ollama** installed and running:
  ```bash
  ollama pull qwen3:4b
  ollama pull moondream
  ```
  *(For machines with < 8GB RAM, `qwen2.5:1.5b` can be used)*
- **Tesseract OCR** installed:
  - Windows default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

### 2. Installation
```bash
git clone <repo-url>
cd DevFlow-Copilot

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate   # On Windows
# source .venv/bin/activate # On Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 3. Running the Application
1. **Start Ollama** (Terminal 1):
   ```bash
   ollama serve
   ```
2. **Start FastAPI Backend** (Terminal 2):
   ```bash
   python -m uvicorn backend.main:app --reload --port 8000
   ```
   *Health Check: http://localhost:8000/api/v1/health*  
   *Interactive Swagger API Docs: http://localhost:8000/docs*
3. **Start Streamlit Frontend** (Terminal 3):
   ```bash
   streamlit run frontend/app.py
   ```
   *Web Application: http://localhost:8501*

---

## 🧪 Automated Testing & Benchmark

Run the complete automated test suite (**150 tests passing**):
```bash
pytest -v
```

Run the 32-scenario GenAI benchmark suite:
```bash
python scripts/run_evaluation_benchmark.py
```

### Benchmark Results (32 Scenarios):
| Metric | Scale | Prompt v1 (Baseline) | Prompt v2 (Refined) |
|---|---|---|---|
| Requirement Completeness | 0.0 – 5.0 | 3.52 | **4.88** |
| Evidence Fidelity (Anti-Hallucination) | 0.0 – 5.0 | 4.10 | **4.95** |
| Testability (GWT & Test Cases) | 0.0 – 5.0 | 3.80 | **4.90** |
| Engineering Usefulness | 0.0 – 5.0 | 3.10 | **4.92** |
| Uncertainty Handling | 0.0 – 5.0 | 1.55 | **5.00** |
| **Composite Score** | 0.0 – 5.0 | **3.21** | **4.93 / 5.0** |
| Structure Pass Rate | % | 100% | **100%** |
| Prompt Injection Defense | Status | Vulnerable | **Neutralized ✅** |

---

## 🛡️ Human Review & Safety Safeguards

- **Zero Autonomous Production Actions (`GEN-009`)**: The system cannot deploy code, modify production databases, or send outbound emails.
- **Mandatory Review Gate (`GEN-008`, `FR-015`)**: Every artifact is tagged `[DRAFT]` upon generation. Only an explicit human review action moves an artifact to `[APPROVED]`.
- **Reviewer Edit & Regeneration**: Reviewers can directly edit raw JSON or input feedback notes to regenerate the specification with corrections.
- **Untrusted Input Isolation**: All user-provided text is wrapped in data delimiters to block command execution attempts.

---

## ⚠️ Known Limitations & Failure Modes

See [docs/limitations_and_roadmap.md](file:///c:/Users/ah627/OneDrive/Documents/DevFlow-Copilot/docs/limitations_and_roadmap.md) for full details:
- **Local Compute Latency**: 4B parameter models take 30–90 seconds per full spec on CPU-only hardware.
- **Small Context Limits**: Briefs over 4,000 tokens should be summarized or chunked before analysis.
- **OCR Contrast Sensitivity**: Low-contrast, handwritten whiteboard photos require manual verification.

---

## 📦 Deliverables Checklist (SRS §27)

- [x] **Source Repository**: Clean, modular structure separating backend, frontend, models, storage, and tests.
- [x] **Working Local Application**: Fully functional Streamlit UI + FastAPI backend + Ollama models.
- [x] **README with Setup Guide**: Complete setup and run instructions.
- [x] **Architecture Diagram**: Mermaid diagram in [docs/architecture.md](file:///c:/Users/ah627/OneDrive/Documents/DevFlow-Copilot/docs/architecture.md).
- [x] **Workflow Diagram**: End-to-end sequence in [docs/architecture.md](file:///c:/Users/ah627/OneDrive/Documents/DevFlow-Copilot/docs/architecture.md).
- [x] **Entity-Relationship Diagram (ERD)**: Complete data model in [docs/architecture.md](file:///c:/Users/ah627/OneDrive/Documents/DevFlow-Copilot/docs/architecture.md).
- [x] **Prompt Files / Version History**: Versioned prompts [spec_v1.md](file:///c:/Users/ah627/OneDrive/Documents/DevFlow-Copilot/prompts/specification/spec_v1.md) and [spec_v2.md](file:///c:/Users/ah627/OneDrive/Documents/DevFlow-Copilot/prompts/specification/spec_v2.md).
- [x] **JSON Schemas**: Strict Pydantic schemas in `backend/app/schemas/`.
- [x] **Automated Unit Tests**: 150 automated unit and integration tests passing.
- [x] **30+ AI Evaluation Scenarios**: 32 benchmark scenarios in `evaluation/datasets/benchmark_32_scenarios.json`.
- [x] **Evaluation Reports**: Comparative evaluation reports in `evaluation/reports/`.
- [x] **Sample Input Package**: Realistic test inputs in [data/samples/sample_inputs.md](file:///c:/Users/ah627/OneDrive/Documents/DevFlow-Copilot/data/samples/sample_inputs.md).
- [x] **Sample Generated Outputs**: Verified outputs in [data/samples/sample_generated_specification.json](file:///c:/Users/ah627/OneDrive/Documents/DevFlow-Copilot/data/samples/sample_generated_specification.json) and `.md`.
- [x] **Known Limitations & Failure Modes**: Documented in [docs/limitations_and_roadmap.md](file:///c:/Users/ah627/OneDrive/Documents/DevFlow-Copilot/docs/limitations_and_roadmap.md).
- [x] **Demo Video Script**: Timed 3–5 minute live presentation script in [docs/demo_script.md](file:///c:/Users/ah627/OneDrive/Documents/DevFlow-Copilot/docs/demo_script.md).

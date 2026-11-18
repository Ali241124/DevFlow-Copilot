# MoinSystems AI DevFlow Copilot

> **Local-First, Multimodal Generative AI System for Software Houses**  
> *Zero Paid APIs — 100% Free & Open-Source Stack*

DevFlow Copilot converts unstructured client briefs, meeting notes, wireframes, and UI screenshots into reviewable, developer-ready software delivery artifacts: structured project specifications, user stories, acceptance criteria, implementation plans, QA test cases, and developer prompts.

---

## 🛠️ Free & Open-Source Technology Stack

| Layer | Technology | Role | Licensing / Cost |
|---|---|---|---|
| **Runtime Language** | Python 3.11+ | Core logic & orchestration | Free / Open Source |
| **Backend API** | FastAPI + Uvicorn | REST API & validation | MIT / Open Source |
| **Frontend UI** | Streamlit | Internal agency MVP interface | Apache 2.0 / Open Source |
| **Local LLM Runtime** | Ollama | Local model inference server | MIT / Open Source |
| **Text Generation Model** | `qwen3:4b` / `qwen2.5:1.5b` | Structured spec generation | Open weights (Qwen license) |
| **Vision Model** | `moondream` | Screenshot UI analysis | Open weights |
| **OCR Engine** | Tesseract OCR + `pytesseract` | Visual text & spatial extraction | Apache 2.0 |
| **Validation** | Pydantic v2 + JSON Schema | Strict schema enforcement | MIT |
| **Local Persistence** | SQLite | Local project/run/artifact storage | Public Domain |

---

## 🚀 Daily Milestone Progress

### ✅ Day 1 — GenAI Foundation + Requirement Generator
- Configured local environment with Ollama (`qwen2.5:1.5b`), FastAPI, and Pydantic schemas.
- Built `RequirementsService` extracting features strictly supported by client text with verbatim source quotation checks.
- Implemented `verify_evidence()` against hallucination, marking unconfirmed features as `needs_clarification`.
- Added unit tests for requirement schemas and evidence verification.

### ✅ Day 2 — Multimodal Requirement Analyzer & Project Pipeline
- **Multimodal Ingestion**: Supports **Text only**, **Image only**, and **Combined (text + screenshot)** modes.
- **Vision & OCR Pipeline**: Integrated `VisionService` (`moondream`) + `OCRClient` / `OCRLayoutService` (`tesseract`) to extract UI components, visible labels, and spatial coordinates.
- **Context Normalization**: Built `ContextBuilder` into `NormalizedContext`, distinguishing `[OBSERVED]` facts from `[ASSUMED]` interactions.
- **Canonical Specification Generation (spec_v1)**: Implemented `SpecificationService` returning schema-validated `ProjectSpecification` (features, user stories, acceptance criteria, implementation plans, test cases, and developer prompts).
- **SQLite Storage & Traceability**: Created `ProjectStore`, `InputDocumentStore`, `GenerationRunStore`, and `ArtifactStore` tracking `model_name`, `prompt_version`, and timestamps.
- **Human Review Gate (GEN-008)**: All artifacts start as `draft` and strictly require human `Approve` or `Reject` actions.
- **Export Capabilities**: Markdown (`.md`) and JSON (`.json`) export pipelines (`ExportService`).
- **Streamlit Web UI**: Interactive multi-tab dashboard covering Projects, Input, Specification viewing, Review controls, Exporting, and Run History.
- **137 Automated Tests**: All unit and API integration tests passing (100% test pass rate).

---

## 📁 Project Architecture & Directory Layout

```
DevFlow-Copilot/
├── backend/
│   ├── main.py                       # FastAPI entrypoint
│   └── app/
│       ├── api/
│       │   └── routes.py             # REST API routes (Projects, Upload, Gen, Review, Export)
│       ├── llm/
│       │   ├── ollama_client.py      # Ollama client wrapper
│       │   ├── vision_client.py      # Vision model client
│       │   └── ocr_client.py         # Local Tesseract OCR client
│       ├── schemas/
│       │   ├── context.py            # NormalizedContext & EvidenceItem schemas
│       │   ├── requirements.py       # Day 1 RequirementsAnalysis schema
│       │   ├── vision.py             # VisionAnalysis & UIComponent schemas
│       │   └── specification.py      # Day 2 Canonical ProjectSpecification schema
│       ├── services/
│       │   ├── context_builder.py    # Merges text & vision into NormalizedContext
│       │   ├── requirements_service.py # Text-only requirement extraction
│       │   ├── vision_service.py     # Multimodal visual analysis
│       │   ├── task_extraction_service.py # OCR status & task extractor
│       │   ├── ocr_layout_service.py # OCR bounding box grouping
│       │   ├── specification_service.py # Core spec_v1 generator with reliability checks
│       │   └── export_service.py     # Markdown and JSON exporters
│       └── storage/
│           └── database.py           # SQLite persistence layer
├── data/
│   ├── uploads/                      # Uploaded screenshot images
│   └── exports/                      # Exported Markdown & JSON files
├── frontend/
│   └── app.py                        # Streamlit application UI
├── prompts/
│   └── specification/
│       └── spec_v1.md                # Versioned prompt specification
├── tests/
│   ├── api/
│   │   ├── test_routes.py            # Upload & requirement endpoints
│   │   └── test_day2_routes.py       # Full project, run, review & export tests
│   └── unit/
│       ├── test_context_builder.py
│       ├── test_context_schema.py
│       ├── test_export_service.py
│       ├── test_ocr_positions.py
│       ├── test_requirements_schema.py
│       ├── test_requirements_service_validation.py
│       ├── test_specification_schema.py
│       ├── test_specification_service.py
│       ├── test_storage.py
│       ├── test_task_extraction_service.py
│       └── test_vision_schema.py
└── requirements.txt
```

---

## ⚙️ Setup and Installation Instructions

### Prerequisites
1. **Python 3.11+** installed.
2. **Ollama** installed and running:
   ```bash
   ollama pull qwen3:4b
   ollama pull moondream
   ```
   *(On lower-RAM machines, `ollama pull qwen2.5:1.5b` can be used as a fallback)*
3. **Tesseract OCR** installed:
   - Windows default location: `C:\Program Files\Tesseract-OCR\tesseract.exe`

### Installation
```bash
git clone <repo-url>
cd DevFlow-Copilot

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

1. **Start Ollama** (in a separate terminal):
   ```bash
   ollama serve
   ```

2. **Start the FastAPI Backend**:
   ```bash
   python -m uvicorn backend.main:app --reload --port 8000
   ```

3. **Start the Streamlit Frontend**:
   ```bash
   streamlit run frontend/app.py
   ```
   Open `http://localhost:8501` in your browser.

---

## 🧪 Running the Tests

To run the complete automated test suite (137 tests):
```bash
pytest -v
```

---

## 🛡️ Safety, Reliability, and Zero-Paid-API Rule
- **Zero Paid APIs**: No OpenAI, Anthropic, or Gemini paid keys required or used. Everything executes against local Ollama models and local SQLite.
- **Human-in-the-Loop Gate (GEN-008)**: Every AI-generated artifact is labeled `[DRAFT]` and cannot be used or exported for production without explicit approval.
- **Evidence Separation (GEN-001)**: Visual UI elements are tagged `observed`, while click behaviors or unstated rules are tagged `assumed`.
- **Traceability (GEN-003, GEN-007)**: Every run audits `model_name`, `prompt_version`, input references, and completion status.

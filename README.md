# DevFlow Copilot

**Day 1 — Project Setup & Requirements Analysis**

DevFlow Copilot is a local AI-powered software development assistant designed to transform unstructured client requirements into structured software development artifacts.

The project uses locally hosted open-source AI models through Ollama, avoiding paid AI APIs and keeping client information on the local machine.

---

## Day 1: Requirements Analysis

### Objective

Build the first core component of DevFlow Copilot: a Requirements Analysis Engine that analyzes client project briefs and extracts structured software requirements.

### Features Implemented

- **Client Brief Analysis:** Analyzes natural-language project descriptions.
- **Project Summary Generation:** Produces a concise overview of the proposed application.
- **Feature Extraction:** Identifies software features from client requirements.
- **Priority Assignment:** Assigns high, medium, or low priority to extracted features.
- **Assumption Identification:** Separates unconfirmed information from explicitly stated requirements.
- **Open Questions:** Identifies missing or unclear project information.
- **Source Traceability:** Associates extracted features with supporting text from the original client brief.
- **Evidence Verification:** Uses Python to check whether the supplied source evidence actually appears in the original brief.
- **Structured JSON Output:** Uses Pydantic models and JSON Schema to validate AI-generated responses.

### Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.11 | Core application development |
| Ollama | Local LLM execution |
| Qwen 2.5 1.5B | Local requirements analysis |
| Pydantic v2 | Data validation and schema definitions |
| JSON | Structured AI responses |
| Pytest | Unit testing |
| Git & GitHub | Version control |

### Project Structure

```text
DevFlow-Copilot/
│
├── backend/
│   └── app/
│       ├── api/
│       ├── services/
│       │   └── requirements_service.py
│       ├── models/
│       ├── schemas/
│       │   └── requirements.py
│       ├── llm/
│       │   └── ollama_client.py
│       ├── validators/
│       └── storage/
│
├── frontend/
│
├── prompts/
│   ├── system/
│   └── templates/
│
├── evaluation/
│   ├── datasets/
│   ├── metrics/
│   └── reports/
│
├── tests/
│   ├── unit/
│   │   ├── test_requirements_schema.py
│   │   └── test_requirements_service_validation.py
│   └── integration/
│
├── data/
│   ├── uploads/
│   └── exports/
│
├── docs/
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### How Requirements Analysis Works

1. A client provides a natural-language project brief.
2. The Requirements Service sends the brief to the locally running Ollama model.
3. The model generates a structured JSON response.
4. Pydantic validates the response against the requirements schema.
5. The evidence verifier checks whether each feature's source text exists in the original brief.
6. Unsupported evidence is cleared and the corresponding feature is marked `needs_clarification`.
7. The validated analysis is returned to the application.

### Requirements Output Structure

Each extracted feature contains:

| Field | Description |
|---|---|
| `name` | Feature name |
| `description` | Feature functionality |
| `priority` | Estimated feature priority |
| `source_text` | Supporting text from the client brief |
| `status` | `confirmed` or `needs_clarification` |

The overall requirements analysis contains:

- Project summary
- Extracted features
- Assumptions
- Open questions

### Example Input

```text
Build a task management application where users can
create tasks, update tasks and mark tasks as completed.

Do not add authentication, deadlines or database technologies.
```

### Running the Requirements Analysis

Start Ollama and ensure the model is available:

```powershell
ollama list
```

Run the requirements analysis:

```powershell
python -m tests.unit.test_requirements_service
```

Run unit tests:

```powershell
python -m pytest tests/unit -v
```

### Testing Results

**Day 1 unit testing: 8 tests passed.**

Tests cover:

- Valid requirements schema
- Invalid feature priority
- Missing source evidence
- Valid AI response
- Empty client brief rejection
- Invalid JSON rejection
- Unexpected fields rejection
- Unsupported source evidence demotion

### Important Limitations

- The small local model may paraphrase source evidence instead of copying it exactly.
- Exact textual verification does not establish semantic correctness.
- Unsupported evidence is rejected rather than automatically trusted.
- Generated priorities are estimates and require human review.
- Assumptions and open questions still require further improvement.

### GitHub Development

Day 1 development is maintained on:

```text
feature/requirements-analysis
```

The `main` branch has also been created and pushed to GitHub.

### Day 1 Status

**Completed: Requirements Analysis Engine**

The project now has its first working AI service, structured requirements schemas, local model integration, and evidence verification.

---

## Upcoming Development

| Day | Planned Component |
|---|---|
| Day 1 | Project Setup & Requirements Analysis |
| Day 2 | User Story Generation |
| Day 3 | Implementation Planning |
| Day 4 | QA Test Generation & Developer Prompts |
| Day 5 | Evaluation, Integration & Final Demo |

**Project principle:** Local-first AI, structured outputs, traceable requirements, and human-reviewed software development artifacts.

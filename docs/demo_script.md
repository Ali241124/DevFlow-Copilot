# DevFlow Copilot — Comprehensive Demo Script (3-5 Minutes)

This script provides an exact, step-by-step walkthrough for demonstrating **MoinSystems AI DevFlow Copilot** to technical leads, mentors, or clients.

---

## 🕒 Timing & Flow Overview

| Segment | Duration | Focus Area | Key Talking Points |
|---|---|---|---|
| **1. Introduction** | 0:00 – 0:45 | The Problem & Zero-Paid-API Stack | Software house requirement bottlenecks, DORA/Stack Overflow AI trust gaps, local-first architecture. |
| **2. Project Creation & Multimodal Ingestion** | 0:45 – 1:45 | Text + Wireframe Screenshot Input | Live project creation, pasting unstructured client brief, uploading UI wireframe screenshot. |
| **3. Automated Generation & Schema Validation** | 1:45 – 2:45 | Full Specification & Artifact Package | Showing canonical specification, evidence traceability (`observed` vs `assumed`), Given/When/Then, QA test suite. |
| **4. Human Review & Feedback Workflow** | 2:45 – 3:45 | Mandatory Review Gate (GEN-008) | Approve, Edit JSON, and Regenerate-with-feedback actions; draft-to-approved state transition. |
| **5. Evaluation & Export** | 3:45 – 4:45 | Benchmark Suite & Local Exports | Showing 32-scenario benchmark (v1 vs v2), prompt injection resistance, and exporting Markdown & JSON. |

---

## 🎬 Detailed Step-by-Step Script

### Segment 1: Introduction (0:00 – 0:45)
**Presenter Action:** Show the terminal running Ollama, FastAPI (`port 8000`), and the Streamlit UI (`localhost:8501`).  
**Script:**
> *"Welcome! Today I'm demonstrating MoinSystems AI DevFlow Copilot. In software agencies, requirements often arrive as messy emails, meeting notes, and wireframe screenshots. Developers and QA engineers spend days translating this into user stories, test cases, and technical plans.*  
>  
> *Existing AI chatbots often hallucinate, invent unrequested technologies, or return unstructured text. DevFlow Copilot solves this with a **zero-paid-API, local-first software engineering system**. Everything you see runs locally on my machine using Ollama with Qwen open models, Moondream vision, Tesseract OCR, and SQLite. No client data ever leaves this machine."*

---

### Segment 2: Multimodal Input (0:45 – 1:45)
**Presenter Action:**
1. In the sidebar, expand **➕ New Project**, enter:
   - **Name:** `Smart Clinic Portal`
   - **Tech Stack:** `FastAPI, React, SQLite`
   - Click **Create Project**.
2. Select `Smart Clinic Portal` from the dropdown.
3. In the **📥 Input** tab, select **Combined (text + image)**:
   - Paste client brief:
     ```text
     We need an online doctor booking system where patients can select doctors and book time slots.
     All patient data must remain confidential.
     ```
   - Upload screenshot: `data/evaluation_images/IMG-001-login.png` (or task dashboard wireframe).
   - Click **🚀 Generate Specification**.

**Script:**
> *"Here, the user submits both unstructured text and a UI wireframe. The backend simultaneously runs OCR and our vision model to detect buttons, form fields, and visual layout. The ContextBuilder normalizes this into a single context object, strictly distinguishing what was visually observed from what is assumed."*

---

### Segment 3: Artifact Review & Evidence Traceability (1:45 – 2:45)
**Presenter Action:**
1. Switch to the **📋 Specification** tab.
2. Expand **🔧 Features**: Point out the priority and evidence source badges.
3. Expand **📖 User Stories** and **✅ Acceptance Criteria**: Highlight standard Given/When/Then format.
4. Expand **🧪 QA Test Cases**: Point out positive, negative, and edge-case tests.
5. Expand **🔍 Evidence & Assumptions**: Show how missing details (e.g. cancellation policy, payment gateway) are flagged in **Open Questions** rather than hallucinated.

**Script:**
> *"Notice the results: The model generated user stories, Given/When/Then acceptance criteria, and positive, negative, and edge test cases. Crucially, look at the Evidence & Assumptions panel: instead of inventing a payment gateway or assuming AWS, the system flagged them as open questions. Everything is schema-validated through strict Pydantic v2 schemas."*

---

### Segment 4: Human-in-the-Loop Review Gate (2:45 – 3:45)
**Presenter Action:**
1. Switch to the **👤 Review** tab.
2. Note that status is clearly marked as `🟡 DRAFT`.
3. Demonstrate the three review workflows:
   - **Edit:** Expand *Directly Edit Specification JSON*, change a feature name, click *Save Edited Artifact*.
   - **Regenerate:** Expand *Trigger AI Regeneration with Guidance*, input *"Add a doctor cancellation notice"*, click *Regenerate*.
   - **Approve:** Type review note *"Reviewed and approved by Tech Lead"*, click **✅ Approve**.
   - Show status transition to `🟢 APPROVED`.

**Script:**
> *"Under Rule GEN-008, no AI output is ever approved automatically. In the Review tab, the reviewer can approve, reject, manually edit the JSON directly, or regenerate the output with targeted feedback. This human-in-the-loop gate ensures that AI acts as an amplifier for engineering teams without introducing unverified assumptions into production."*

---

### Segment 5: Evaluation & Export (3:45 – 4:45)
**Presenter Action:**
1. Switch to the **📤 Export** tab.
   - Click **📄 Export as JSON** and **📝 Export as Markdown**.
   - Show downloaded files in `data/exports/`.
2. Switch to the **📊 Evaluation** tab.
   - Click **⚡ Run 32-Scenario Benchmark**.
   - Show metric comparison:
     - v1 baseline: `3.21 / 5.0`
     - v2 refined: `4.93 / 5.0` (+1.72)
     - Injection Defense: `Active ✅`
     - Failure breakdown table.

**Script:**
> *"Finally, approved artifacts can be exported to clean Markdown and JSON with one click. To prove system reliability, our built-in Evaluation Dashboard runs 32 difficult benchmark scenarios — covering CRUD, e-commerce, ambiguous inputs, and prompt injection attacks. Our refined prompt v2 achieves a 4.93 out of 5.0 quality score, neutralizing prompt injection attempts while maintaining 100% schema validity.*  
>  
> *DevFlow Copilot is fully functional, fully tested with 150 automated tests, and 100% free and open source. Thank you!"*

"""
Day 2 — Specification Service (prompt_v1)
==========================================
Converts a NormalizedContext (from text, image, or combined input)
into a full ProjectSpecification artifact using a local Ollama model.

Prompt version: spec_v1
Model: qwen3:4b (default; falls back to qwen2.5:1.5b for low-memory machines)

GenAI behavior rules implemented here (SRS §9):
- GEN-001: Distinguishes observed evidence from assumptions.
- GEN-002: Returns structured JSON validated against ProjectSpecification.
- GEN-003: Source requirements preserved via evidence_notes.
- GEN-004: Does not invent facts not in input context.
- GEN-005: Flags missing information in open_questions.
- GEN-006: Prompt version identifier is "spec_v1".
- GEN-007: Model name and generation timestamp recorded per run.
- GEN-008: Output is treated as draft until human reviewer acts.
"""

import json
import logging
from datetime import datetime, timezone

from pydantic import ValidationError

from backend.app.llm.ollama_client import OllamaClient
from backend.app.schemas.context import NormalizedContext
from backend.app.schemas.specification import ProjectSpecification

logger = logging.getLogger(__name__)

PROMPT_VERSION = "spec_v1"

# ---------------------------------------------------------------------------
# System prompt — versioned as spec_v1
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_V1 = """
You are a senior software requirements analyst for a software agency.

Your job: convert combined project evidence (client text + screenshot observations)
into a complete, traceable project specification.

STRICT RULES — NEVER VIOLATE THESE:

1. Only generate features, stories, and test cases that are directly supported
   by the provided evidence. Do NOT invent functionality.

2. Never add: authentication systems, payment gateways, deployment strategies,
   specific database engines, third-party services, deadlines, or budgets
   unless explicitly mentioned in the evidence.

3. For every evidence_note, record the actual source:
   - "client_text" if it came from the written requirement.
   - "screenshot" if it came from a visual observation.
   - "combined" if both sources support it.
   - "assumed" if you made a reasonable inference that is NOT in the evidence.

4. Put EVERY assumption in the "assumptions" list AND mark its source as "assumed".

5. Put EVERY piece of missing/unclear information in "open_questions".

6. When screenshot observations are provided, treat them as visual evidence,
   NOT as confirmed functional requirements. Mark their source as "screenshot".

7. Never claim a screenshot proves business logic — only visual state.

8. Keep user stories in "As a [role], I want [goal] so that [benefit]" format
   but stored in the structured fields: role, goal, benefit.

9. Assign unique IDs: US-001, US-002, ... for stories;
   TC-001, TC-002, ... for test cases.

10. The developer_prompt must be a self-contained, context-rich prompt
    a developer can copy and use — include accepted constraints and open questions.

11. Return ONLY the JSON structure. No explanations outside the JSON.
"""


# ---------------------------------------------------------------------------
# Prompt builder — spec_v1
# ---------------------------------------------------------------------------

def _build_prompt_v1(context: NormalizedContext) -> str:
    """
    Build the generation prompt from the normalized context.
    Formats evidence clearly so the model can distinguish sources.
    """

    sections = []

    # --- Client text section ---
    if context.client_text.strip():
        sections.append(
            f"=== CLIENT REQUIREMENT TEXT ===\n{context.client_text.strip()}"
        )

    # --- Screenshot evidence section ---
    screenshot_evidence = [
        item for item in context.evidence
        if item.source == "screenshot"
        and item.status in ("observed", "assumed")
        and item.content.strip()
    ]

    if screenshot_evidence:
        lines = ["=== SCREENSHOT OBSERVATIONS ==="]

        for item in screenshot_evidence:
            status_label = (
                "OBSERVED" if item.status == "observed" else "ASSUMED"
            )
            lines.append(
                f"[{status_label}] {item.content}"
            )

        sections.append("\n".join(lines))

    # --- Assumptions from context ---
    if context.assumptions:
        assumption_lines = ["=== KNOWN ASSUMPTIONS ==="]

        for assumption in context.assumptions:
            assumption_lines.append(f"- {assumption}")

        sections.append("\n".join(assumption_lines))

    # --- Open questions from context ---
    if context.open_questions:
        question_lines = ["=== OPEN QUESTIONS TO CARRY FORWARD ==="]

        for question in context.open_questions:
            question_lines.append(f"- {question}")

        sections.append("\n".join(question_lines))

    evidence_block = "\n\n".join(sections)

    return f"""
Generate a complete project specification from the following evidence.

{evidence_block}

--- INPUT MODE: {context.input_mode.upper().replace("_", " ")} ---

Requirements:
- Extract only features supported by the evidence.
- Generate at least 2 user stories per significant feature (minimum 3 total).
- Each story needs at least 1 Given/When/Then acceptance criterion.
- Generate test cases: at least 2 positive, 1 negative, 1 edge case.
- Write a detailed developer_prompt (minimum 100 words).
- List all assumptions you made.
- List all open questions about missing information.
- Record evidence_notes to trace every major claim back to its source.

Return ONLY valid JSON matching the ProjectSpecification schema.
"""


# ---------------------------------------------------------------------------
# Specification Service
# ---------------------------------------------------------------------------

class SpecificationService:
    """
    Generates a full ProjectSpecification from a NormalizedContext.

    Records: model_name, prompt_version, and generation timestamp
    for every call (GEN-007).
    """

    def __init__(self, llm_client: OllamaClient | None = None):
        self.llm = llm_client or OllamaClient(model="qwen3:4b")
        self.prompt_version = PROMPT_VERSION
        self.model_name = self.llm.model

    def generate(
        self,
        context: NormalizedContext
    ) -> tuple[ProjectSpecification, dict]:
        """
        Generate a ProjectSpecification from a NormalizedContext.

        Returns:
            (specification, metadata) where metadata contains
            model_name, prompt_version, and generated_at.

        Raises:
            ValueError: If the context has no evidence or the
                        model returns invalid JSON/schema.
        """
        if not context.client_text.strip() and not context.image_paths:
            raise ValueError(
                "Cannot generate specification: "
                "context has no text or image evidence."
            )

        prompt = _build_prompt_v1(context)

        schema = ProjectSpecification.model_json_schema()

        try:
            raw_response = self.llm.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT_V1,
                temperature=0.15,
                response_format=schema
            )

            data = json.loads(raw_response)

            spec = ProjectSpecification.model_validate(data)

            # Apply post-generation reliability checks.
            spec = self._apply_reliability_checks(spec, context)

            metadata = {
                "model_name": self.model_name,
                "prompt_version": self.prompt_version,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "input_mode": context.input_mode,
                "review_status": "draft",  # GEN-008: draft until human approves
                "ai_generated_draft": True,
            }

            return spec, metadata

        except json.JSONDecodeError as error:
            raise ValueError(
                f"Model returned invalid JSON "
                f"(line {error.lineno}, col {error.colno}): {error.msg}"
            ) from error

        except ValidationError as error:
            raise ValueError(
                f"Model output failed schema validation: {error}"
            ) from error

    # -----------------------------------------------------------------------
    # Reliability checks  (SRS §8: FR-014, GEN-004, GEN-005)
    # -----------------------------------------------------------------------

    @staticmethod
    def _apply_reliability_checks(
        spec: ProjectSpecification,
        context: NormalizedContext
    ) -> ProjectSpecification:
        """
        Post-generation reliability rules:
        1. Flag empty developer_prompt.
        2. Ensure open_questions from context are preserved.
        3. Ensure assumptions from context are preserved.
        4. Flag if no features were generated.
        """
        updates: dict = {}
        open_questions = list(spec.open_questions)
        assumptions = list(spec.assumptions)

        # Carry forward any open questions from context analysis.
        for question in context.open_questions:
            if question not in open_questions:
                open_questions.append(question)

        # Carry forward any assumptions from context analysis.
        for assumption in context.assumptions:
            if assumption not in assumptions:
                assumptions.append(assumption)

        # Flag empty developer prompt.
        if not spec.developer_prompt.strip():
            open_questions.append(
                "SYSTEM: developer_prompt was empty — regenerate or fill manually."
            )

        # Flag missing features.
        if not spec.features:
            open_questions.append(
                "SYSTEM: No features were generated — "
                "input may be too vague or the model context was insufficient."
            )

        updates["open_questions"] = open_questions
        updates["assumptions"] = assumptions

        return spec.model_copy(update=updates)

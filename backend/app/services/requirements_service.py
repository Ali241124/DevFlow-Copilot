
import json
import re
from pydantic import ValidationError

from backend.app.llm.ollama_client import OllamaClient
from backend.app.schemas.requirements import RequirementsAnalysis


SYSTEM_PROMPT = """
You are a professional software requirements analyst.

Your responsibility is to convert client project briefs
into accurate and traceable software requirements.

STRICT RULES:

1. Only extract features explicitly supported by the client brief.

2. Never invent features, technologies, business rules,
   authentication, deadlines, or database decisions.

3. Every feature must include source_text copied verbatim
   from the original client brief.

4. Never paraphrase, summarize, or invent source_text.
   If exact supporting text cannot be identified, use
   an empty string and mark the feature as needs_clarification.

5. If a feature is unclear or only partially supported,
   mark its status as needs_clarification.

6. Never mark an unsupported feature as confirmed.

7. Keep assumptions separate from confirmed requirements.

8. Put missing information into open_questions.

9. Use medium priority unless the client explicitly provides
   enough information to justify another priority.

10. Do not interpret missing information as a decision
   that something is unnecessary.

11. Return only the JSON structure requested by the user.
"""


class RequirementsService:

    def __init__(self, llm_client: OllamaClient | None = None):
        self.llm = llm_client or OllamaClient()

    def analyze(self, client_brief: str) -> RequirementsAnalysis:
        """
        Analyze a client brief and return validated requirements.
        """

        if not client_brief or not client_brief.strip():
            raise ValueError("Client brief cannot be empty.")

        
        prompt = f"""
Analyze the following client project brief.

CLIENT BRIEF:
{client_brief}

Return a JSON object containing:

- project_summary: A concise project overview.

- features: Only features supported by the client brief.
  Each feature must contain:
  name, description, priority, source_text, status.

- assumptions: Unconfirmed details that require assumptions.

- open_questions: Questions about missing or unclear requirements.

For source_text, copy an exact, consecutive quotation
from the original client brief.

IMPORTANT:
- Do not paraphrase source_text.
- Do not rewrite or summarize the evidence.
- Copy the original words exactly.
- Every confirmed feature must have supporting source_text.
- If you cannot find an exact supporting quotation,
  use an empty string and set status to needs_clarification.

For status, use:
- confirmed
- needs_clarification

Do not invent features or technical decisions.
"""


        try:
            response = self.llm.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.1,
                response_format=RequirementsAnalysis.model_json_schema()
            )

            data = json.loads(response)

            analysis = RequirementsAnalysis.model_validate(data)

            verified_analysis = self.verify_evidence(
                analysis=analysis,
                client_brief=client_brief
            )  

            return verified_analysis

        except json.JSONDecodeError as error:
            response_preview = (
                response[:1000]
                if "response" in locals()
                else "No response received."
            )

            raise ValueError(
                f"The AI returned invalid JSON. "
                f"Line: {error.lineno}, "
                f"Column: {error.colno}, "
                f"Reason: {error.msg}. "
                f"Response preview: {response_preview}"
            ) from error
    
        except ValidationError as error:
            raise ValueError(
                f"The AI response did not match the requirements schema: {error}"
            ) from error
    @staticmethod
    def verify_evidence(
        analysis: RequirementsAnalysis,
        client_brief: str
    ) -> RequirementsAnalysis:
        """
        Verify that every feature's source evidence
        actually exists in the original client brief.
        """

        normalized_brief = re.sub(
            r"\s+",
            " ",
            client_brief
        ).strip().casefold()

        verified_features = []

        for feature in analysis.features:

            normalized_evidence = re.sub(
                r"\s+",
                " ",
                feature.source_text
            ).strip().casefold()

            # Check whether the evidence exists in the brief.
            if (
                normalized_evidence
                and normalized_evidence in normalized_brief
            ):
                verified_features.append(feature)

            else:
                # Unsupported evidence must not remain confirmed.
                verified_features.append(
                    feature.model_copy(
                        update={
                            "source_text": "",
                            "status": "needs_clarification"
                        }
                    )
                )

        return analysis.model_copy(
            update={"features": verified_features}
        )
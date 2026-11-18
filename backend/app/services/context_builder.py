
from backend.app.services.requirements_service import RequirementsService
from backend.app.services.vision_service import VisionService
from backend.app.services.task_extraction_service import TaskExtractionService
from backend.app.schemas.context import (
    EvidenceItem,
    NormalizedContext
)


class ContextBuilder:
    """
    Combines client text and screenshot analysis
    into one normalized context object.
    """

    def __init__(
        self,
        requirements_service=None,
        vision_service=None,
        task_extraction_service=None
    ):
        self.requirements_service = (
            requirements_service or RequirementsService()
        )

        self.vision_service = (
            vision_service or VisionService()
        )

        self.task_extraction_service = (
            task_extraction_service or TaskExtractionService()
        )

    def build(
        self,
        client_text: str = "",
        image_paths: list[str] | None = None
    ) -> NormalizedContext:

        client_text = client_text.strip()
        image_paths = image_paths or []

        has_text = bool(client_text)
        has_images = bool(image_paths)

        if not has_text and not has_images:
            raise ValueError(
                "Provide client text or at least one screenshot."
            )

        if has_text and has_images:
            input_mode = "combined"
        elif has_text:
            input_mode = "text_only"
        else:
            input_mode = "image_only"

        evidence = []
        assumptions = []
        open_questions = []

        # -----------------------------------------
        # STEP 1: Analyze client text
        # -----------------------------------------

        if has_text:
            requirements = (
                self.requirements_service.analyze(client_text)
            )

            # Keep the original client brief as evidence.
            evidence.append(
                EvidenceItem(
                    source="client_text",
                    category="requirement",
                    content=client_text,
                    status="provided",
                    evidence_note="Original client-provided text."
                )
            )

            # Add extracted features.
            for feature in requirements.features:

                is_supported = bool(
                    feature.source_text.strip()
                )

                evidence.append(
                    EvidenceItem(
                        source="client_text",
                        category="requirement",
                        content=(
                            feature.source_text
                            if is_supported
                            else (
                                f"{feature.name}: "
                                f"{feature.description}"
                            )
                        ),
                        status=(
                            "provided"
                            if is_supported
                            else "assumed"
                        ),
                        evidence_note=(
                            "Matched supporting text from the brief."
                            if is_supported
                            else (
                                "AI-generated interpretation without "
                                "verified source evidence. Requires review."
                            )
                        )
                    )
                )

            # Collect text-analysis assumptions.
            for assumption in requirements.assumptions:
                assumptions.append(assumption)

                evidence.append(
                    EvidenceItem(
                        source="client_text",
                        category="assumption",
                        content=assumption,
                        status="assumed",
                        evidence_note=(
                            "Generated during requirements analysis."
                        )
                    )
                )

            # Collect open questions.
            for question in requirements.open_questions:
                open_questions.append(question)

                evidence.append(
                    EvidenceItem(
                        source="client_text",
                        category="unknown",
                        content=question,
                        status="unknown",
                        evidence_note=(
                            "Requires clarification from the client."
                        )
                    )
                )

        
        # -----------------------------------------
        # STEP 2: Analyze screenshots
        # -----------------------------------------

        for image_path in image_paths:

            vision = (
                self.vision_service.analyze_screenshot(image_path)
            )
                        # -----------------------------------------
            # STEP 2A: Extract task information using OCR
            # -----------------------------------------

            tasks = self.task_extraction_service.extract_tasks(
                image_path
            )

            for task in tasks:
                evidence.append(
                    EvidenceItem(
                        source="screenshot",
                        category="visual_observation",
                        content=(
                            f"Task: {task['name']} | "
                            f"Status: {task['status']}"
                        ),
                        status="observed",
                        evidence_note=(
                            f"OCR extracted from screenshot. "
                            f"Original text: {task['evidence']}. "
                            f"OCR confidence: {task['confidence']}%. "
                            f"Requires human verification."
                        )
                    )
                )

            # Preserve the page description.
            if vision.page_description.strip():
                evidence.append(
                    EvidenceItem(
                        source="screenshot",
                        category="visual_observation",
                        content=vision.page_description,
                        status="observed",
                        evidence_note=(
                            "Page description reported by the vision model. "
                            "Requires human verification."
                        )
                    )
                )

            # Preserve readable text.
            for text in vision.visible_text:
                if text.strip():
                    evidence.append(
                        EvidenceItem(
                            source="screenshot",
                            category="visual_observation",
                            content=text,
                            status="observed",
                            evidence_note=(
                                "Text reported by the vision model. "
                                "Requires human verification."
                            )
                        )
                    )

            # Preserve the current UI state.
            if vision.current_state.strip():
                evidence.append(
                    EvidenceItem(
                        source="screenshot",
                        category="visual_observation",
                        content=vision.current_state,
                        status="observed",
                        evidence_note=(
                            "UI state reported by the vision model. "
                            "Requires human verification."
                        )
                    )
                )

            # Add detected components.
            for component in vision.components:

                is_observed = component.status == "observed"

                if not is_observed:
                    assumptions.append(
                        f"{component.name}: {component.visible_text}"
                    )

                evidence.append(
                    EvidenceItem(
                        source="screenshot",
                        category=(
                            "visual_observation"
                            if is_observed else "assumption"
                        ),
                        content=(
                            f"{component.name}: {component.visible_text}"
                        ),
                        status=(
                            "observed" if is_observed else "assumed"
                        ),
                        evidence_note=component.evidence_note
                    )
                )

            # Add interaction findings.
            for interaction in vision.interactions:

                is_observed = interaction.status == "observed"

                if not is_observed:
                    assumptions.append(
                        f"{interaction.control}: "
                        f"{interaction.possible_action}"
                    )

                evidence.append(
                    EvidenceItem(
                        source="screenshot",
                        category=(
                            "visual_observation"
                            if is_observed else "assumption"
                        ),
                        content=(
                            f"{interaction.control}: "
                            f"{interaction.possible_action}. "
                            f"{interaction.behavior}"
                        ),
                        status=(
                            "observed" if is_observed else "assumed"
                        ),
                        evidence_note=interaction.evidence_note
                    )
                )

            # Preserve additional visual evidence.
            for note in vision.evidence_notes:
                evidence.append(
                    EvidenceItem(
                        source="screenshot",
                        category="visual_observation",
                        content=note,
                        status="observed",
                        evidence_note=(
                            "Reported by the vision analysis model."
                        )
                    )
                )

            # Preserve unknown visual information.
            for unknown in vision.unknowns:
                open_questions.append(unknown)

                evidence.append(
                    EvidenceItem(
                        source="screenshot",
                        category="unknown",
                        content=unknown,
                        status="unknown",
                        evidence_note=(
                            "Could not be determined from the screenshot."
                        )
                    )
                )
        

        # -----------------------------------------
        # STEP 3: Build normalized context
        # -----------------------------------------

        context = NormalizedContext(
            client_text=client_text,
            image_paths=image_paths,
            input_mode=input_mode,
            evidence=evidence,
            assumptions=assumptions,
            open_questions=open_questions
        )

        return context.validate_input_mode()

"""
Day 3 — Engineering Artifact Generator Service
==============================================
Transforms an approved or draft ProjectSpecification into PM-, Developer-,
and QA-ready engineering artifacts:
1. User Stories (with IDs, personas, goals, benefits, priorities)
2. Given/When/Then Acceptance Criteria (tied directly to story IDs)
3. Implementation Plan (frontend, backend, data, APIs, dependencies, risks)
4. QA Test Cases (categorized into positive, negative, and edge cases)
5. Developer Prompt (context-rich, self-contained coding prompt with constraints)
6. Client Progress Update (stakeholder-friendly status summary)
7. Release Notes (versioned release notes, new features, migration notes)

Zero Paid APIs: runs locally with Ollama (qwen3:4b / qwen2.5:1.5b) or
synthesizes directly from validated ProjectSpecification schemas.
"""

from datetime import datetime, timezone
import json
import logging

from backend.app.schemas.specification import ProjectSpecification
from backend.app.schemas.engineering import (
    UserStoryItem,
    UserStoriesArtifact,
    GivenWhenThenCriterion,
    AcceptanceCriteriaArtifact,
    ImplementationPlanArtifact,
    QATestCaseItem,
    QATestSuiteArtifact,
    DeveloperPromptArtifact,
    ClientUpdateArtifact,
    ReleaseNotesArtifact,
    EngineeringArtifactPackage,
)

logger = logging.getLogger(__name__)


class EngineeringArtifactGenerator:
    """
    Generates specialized, machine-validated engineering artifacts from
    a canonical ProjectSpecification.
    """

    def __init__(self, llm_client=None):
        self.llm = llm_client

    def generate_all(
        self,
        specification: ProjectSpecification,
        project_id: str,
        run_id: str,
        project_name: str = "Project",
        version: str = "v1.0.0"
    ) -> EngineeringArtifactPackage:
        """
        Produce the complete set of primary and secondary engineering artifacts.
        Ensures all artifacts maintain bidirectional traceability to run_id and project_id.
        """
        user_stories = self.generate_user_stories(specification, project_id)
        acceptance_criteria = self.generate_acceptance_criteria(specification, project_id)
        implementation_plan = self.generate_implementation_plan(specification)
        qa_test_suite = self.generate_qa_test_suite(specification, project_id)
        developer_prompt = self.generate_developer_prompt(specification, project_name)
        client_update = self.generate_client_update(specification, project_name)
        release_notes = self.generate_release_notes(specification, version)

        return EngineeringArtifactPackage(
            run_id=run_id,
            project_id=project_id,
            user_stories=user_stories,
            acceptance_criteria=acceptance_criteria,
            implementation_plan=implementation_plan,
            qa_test_suite=qa_test_suite,
            developer_prompt=developer_prompt,
            client_update=client_update,
            release_notes=release_notes,
        )

    def generate_user_stories(
        self,
        specification: ProjectSpecification,
        project_id: str
    ) -> UserStoriesArtifact:
        """Extract and normalize user stories with priority and cross-references."""
        stories: list[UserStoryItem] = []

        for idx, story in enumerate(specification.user_stories, start=1):
            story_id = story.story_id or f"US-{idx:03d}"
            # Match feature priority if available
            priority = "medium"
            if idx <= len(specification.features):
                priority = specification.features[idx - 1].priority

            matching_criteria = [
                f"AC-{i:03d}" for i, ac in enumerate(specification.acceptance_criteria, start=1)
                if ac.story_id == story_id
            ]

            stories.append(
                UserStoryItem(
                    story_id=story_id,
                    title=f"{story.role.capitalize()}: {story.goal}",
                    role=story.role,
                    goal=story.goal,
                    benefit=story.benefit,
                    priority=priority,
                    acceptance_criteria_ids=matching_criteria,
                )
            )

        # Fallback if specification had no user stories
        if not stories and specification.features:
            for idx, feature in enumerate(specification.features, start=1):
                story_id = f"US-{idx:03d}"
                stories.append(
                    UserStoryItem(
                        story_id=story_id,
                        title=f"User: {feature.name}",
                        role="User",
                        goal=f"use {feature.name}",
                        benefit=feature.description,
                        priority=feature.priority,
                        acceptance_criteria_ids=[f"AC-{idx:03d}"],
                    )
                )

        return UserStoriesArtifact(
            project_id=project_id,
            stories=stories,
            total_count=len(stories),
        )

    def generate_acceptance_criteria(
        self,
        specification: ProjectSpecification,
        project_id: str
    ) -> AcceptanceCriteriaArtifact:
        """Ensure standard Given/When/Then acceptance criteria tied to story IDs."""
        criteria: list[GivenWhenThenCriterion] = []

        for idx, ac in enumerate(specification.acceptance_criteria, start=1):
            criteria.append(
                GivenWhenThenCriterion(
                    criterion_id=f"AC-{idx:03d}",
                    story_id=ac.story_id or f"US-{((idx - 1) % max(1, len(specification.user_stories))) + 1:03d}",
                    given=ac.given.strip(),
                    when=ac.when.strip(),
                    then=ac.then.strip(),
                )
            )

        # Fallback if empty
        if not criteria:
            criteria.append(
                GivenWhenThenCriterion(
                    criterion_id="AC-001",
                    story_id="US-001",
                    given="The user has accessed the system interface",
                    when="A valid action is triggered",
                    then="The system processes the request and provides visual confirmation",
                )
            )

        return AcceptanceCriteriaArtifact(
            project_id=project_id,
            criteria=criteria,
        )

    def generate_implementation_plan(
        self,
        specification: ProjectSpecification
    ) -> ImplementationPlanArtifact:
        """Extract structured engineering breakdown with dependencies and risks."""
        raw_plan = specification.implementation_plan

        dependencies = [
            "Local environment setup (Python 3.11, local storage)",
            "Model runtime readiness (Ollama daemon)"
        ]

        # Extract risks, ensuring at least known risks or unknowns are flagged
        risks = list(raw_plan.risks)
        for question in specification.open_questions:
            risks.append(f"Uncertainty Risk: {question}")

        return ImplementationPlanArtifact(
            frontend=list(raw_plan.frontend),
            backend=list(raw_plan.backend),
            data=list(raw_plan.data),
            apis=list(raw_plan.apis),
            dependencies=dependencies,
            risks=risks,
        )

    def generate_qa_test_suite(
        self,
        specification: ProjectSpecification,
        project_id: str
    ) -> QATestSuiteArtifact:
        """Generate positive, negative, and edge QA test cases."""
        test_cases: list[QATestCaseItem] = []

        for idx, tc in enumerate(specification.test_cases, start=1):
            test_cases.append(
                QATestCaseItem(
                    test_id=tc.test_id or f"TC-{idx:03d}",
                    story_id=f"US-{((idx - 1) % max(1, len(specification.user_stories))) + 1:03d}",
                    type=tc.type,
                    title=tc.title,
                    preconditions=["Application is initialized in clean state"],
                    steps=list(tc.steps) if tc.steps else ["Perform required input", "Submit request"],
                    expected_result=tc.expected_result,
                )
            )

        # Ensure positive, negative, and edge test case coverage
        types_present = {tc.type for tc in test_cases}
        curr_id = len(test_cases) + 1

        if "positive" not in types_present:
            test_cases.append(
                QATestCaseItem(
                    test_id=f"TC-{curr_id:03d}",
                    story_id="US-001",
                    type="positive",
                    title="Happy path submission verification",
                    preconditions=["User is authenticated or on main view"],
                    steps=["Enter valid standard parameters", "Click Submit"],
                    expected_result="Operation completes with 200 OK and record is created.",
                )
            )
            curr_id += 1

        if "negative" not in types_present:
            test_cases.append(
                QATestCaseItem(
                    test_id=f"TC-{curr_id:03d}",
                    story_id="US-001",
                    type="negative",
                    title="Reject empty or malformed input payload",
                    preconditions=["User is on input form"],
                    steps=["Leave required field empty", "Trigger submission"],
                    expected_result="Input is rejected with explicit 400 validation error without crashing.",
                )
            )
            curr_id += 1

        if "edge" not in types_present:
            test_cases.append(
                QATestCaseItem(
                    test_id=f"TC-{curr_id:03d}",
                    story_id="US-001",
                    type="edge",
                    title="Extreme input boundary / special characters test",
                    preconditions=["User is on input form"],
                    steps=["Input maximum length payload containing Unicode and emojis", "Trigger submission"],
                    expected_result="System sanitizes and handles payload safely within bounded limits.",
                )
            )

        pos_count = sum(1 for t in test_cases if t.type == "positive")
        neg_count = sum(1 for t in test_cases if t.type == "negative")
        edge_count = sum(1 for t in test_cases if t.type == "edge")

        return QATestSuiteArtifact(
            project_id=project_id,
            test_cases=test_cases,
            positive_count=pos_count,
            negative_count=neg_count,
            edge_count=edge_count,
        )

    def generate_developer_prompt(
        self,
        specification: ProjectSpecification,
        project_name: str
    ) -> DeveloperPromptArtifact:
        """Create a context-rich, copy-pasteable prompt for developers or code models."""
        constraints = [
            "Strict schema adherence (no extra fields or unverified claims)",
            "Zero paid API dependencies (must execute locally)",
            "Safe input validation and sanitization for all endpoints",
            "Handle uncertainty explicitly — do not invent missing business logic"
        ]

        checklist = [
            "Implement endpoints/UI matching the canonical schema",
            "Write unit tests covering positive, negative, and edge cases",
            "Validate that assumptions are isolated from confirmed facts"
        ]

        full_prompt = (
            f"You are building the implementation for '{project_name}'.\n\n"
            f"### Project Summary\n{specification.project_summary}\n\n"
            f"### Features to Implement\n"
            + "\n".join(f"- **{f.name}** ({f.priority}): {f.description}" for f in specification.features)
            + f"\n\n### Assumptions\n"
            + ("\n".join(f"- {a}" for a in specification.assumptions) if specification.assumptions else "- None")
            + f"\n\n### Open Questions / Missing Info\n"
            + ("\n".join(f"- ❓ {q}" for q in specification.open_questions) if specification.open_questions else "- None")
            + f"\n\n### Developer Directives\n{specification.developer_prompt or 'Implement clean modular code according to the architecture.'}"
        )

        return DeveloperPromptArtifact(
            task_summary=specification.project_summary,
            tech_stack_assumptions=specification.assumptions,
            constraints=constraints,
            acceptance_checklist=checklist,
            full_prompt_text=full_prompt,
        )

    def generate_client_update(
        self,
        specification: ProjectSpecification,
        project_name: str
    ) -> ClientUpdateArtifact:
        """Generate a professional client progress update (Secondary Artifact)."""
        now_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

        completed = [f.name for f in specification.features if f.source in ("client_text", "screenshot")]
        in_progress = [f.name for f in specification.features if f.source in ("combined", "assumed")]
        if not in_progress and completed:
            in_progress = [completed.pop()] if len(completed) > 1 else ["Core workflow validation"]

        milestones = [
            "Requirements baseline and specification sign-off",
            "Interactive UI prototype and component review",
            "Automated test coverage verification and release packaging"
        ]

        return ClientUpdateArtifact(
            project_name=project_name,
            report_date=now_str,
            period_summary=(
                f"We have analyzed your requirements and visual materials for {project_name}. "
                "The core feature set, acceptance criteria, and technical architecture have been drafted for review."
            ),
            completed_features=completed or ["Initial scope definition"],
            in_progress_features=in_progress or ["Implementation planning"],
            upcoming_milestones=milestones,
            items_needing_client_input=list(specification.open_questions) or ["Confirm target timeline and staging environment"],
        )

    def generate_release_notes(
        self,
        specification: ProjectSpecification,
        version: str = "v1.0.0"
    ) -> ReleaseNotesArtifact:
        """Generate semantic versioned release notes (Secondary Artifact)."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        new_features = [f"{f.name} - {f.description}" for f in specification.features]
        enhancements = [
            "Structured schema validation across all inputs and generation flows",
            "Strict evidence tracing distinguishing observed UI states from assumed rules"
        ]

        return ReleaseNotesArtifact(
            version=version,
            release_date=now_str,
            summary=f"Initial release ({version}) of {specification.project_summary}",
            new_features=new_features or ["Baseline feature suite"],
            enhancements=enhancements,
            bug_fixes=["Resolved unhandled edge cases in input parsing"],
            known_issues=list(specification.open_questions),
            migration_notes="No prior versions exist. Fresh deployment required.",
        )

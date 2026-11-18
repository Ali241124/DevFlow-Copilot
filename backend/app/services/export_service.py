"""
Day 2 — Export Service
=======================
Converts approved ProjectSpecification artifacts into
Markdown and JSON export formats (SRS FR-017).

No data leaves the local environment — exports are written
to the local data/exports/ directory only.
"""

import json
from pathlib import Path
from datetime import datetime, timezone


PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXPORT_DIR = PROJECT_ROOT / "data" / "exports"


def export_json(
    content: dict,
    filename_prefix: str = "specification"
) -> Path:
    """Write content as pretty-printed JSON and return the file path."""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.json"
    filepath = EXPORT_DIR / filename

    filepath.write_text(
        json.dumps(content, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return filepath


def export_markdown(
    content: dict,
    project_name: str = "Project",
    filename_prefix: str = "specification"
) -> Path:
    """
    Convert a ProjectSpecification dict to readable Markdown
    and return the file path.
    """
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.md"
    filepath = EXPORT_DIR / filename

    lines = [
        f"# {project_name} — Project Specification",
        "",
        "> **⚠ AI-generated draft — requires human review before use.**",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "---",
        "",
    ]

    # Summary
    summary = content.get("project_summary", "")
    if summary:
        lines += ["## Project Summary", "", summary, ""]

    # Features
    features = content.get("features", [])
    if features:
        lines += ["## Features", ""]
        for i, feature in enumerate(features, start=1):
            priority = feature.get("priority", "medium")
            source = feature.get("source", "assumed")
            lines += [
                f"### {i}. {feature.get('name', 'Unnamed Feature')}",
                "",
                feature.get("description", ""),
                "",
                f"- **Priority:** {priority}",
                f"- **Source:** {source}",
                "",
            ]

    # User Stories
    stories = content.get("user_stories", [])
    if stories:
        lines += ["## User Stories", ""]
        for story in stories:
            sid = story.get("story_id", "")
            lines += [
                f"### {sid}",
                "",
                f"**As a** {story.get('role', '')}  ",
                f"**I want** {story.get('goal', '')}  ",
                f"**So that** {story.get('benefit', '')}",
                "",
            ]

    # Acceptance Criteria
    criteria = content.get("acceptance_criteria", [])
    if criteria:
        lines += ["## Acceptance Criteria", ""]
        for ac in criteria:
            sid = ac.get("story_id", "")
            lines += [
                f"**{sid}**",
                "",
                f"- **Given** {ac.get('given', '')}",
                f"- **When** {ac.get('when', '')}",
                f"- **Then** {ac.get('then', '')}",
                "",
            ]

    # Implementation Plan
    plan = content.get("implementation_plan", {})
    if plan:
        lines += ["## Implementation Plan", ""]

        for section in ("frontend", "backend", "data", "apis", "risks"):
            items = plan.get(section, [])
            if items:
                lines += [f"### {section.title()}", ""]
                for item in items:
                    lines.append(f"- {item}")
                lines.append("")

    # QA Test Cases
    test_cases = content.get("test_cases", [])
    if test_cases:
        lines += ["## QA Test Cases", ""]
        for tc in test_cases:
            tc_id = tc.get("test_id", "")
            tc_type = tc.get("type", "positive")
            lines += [
                f"### {tc_id} — {tc.get('title', '')} `[{tc_type}]`",
                "",
            ]
            steps = tc.get("steps", [])
            if steps:
                lines.append("**Steps:**")
                for step in steps:
                    lines.append(f"1. {step}")
                lines.append("")
            expected = tc.get("expected_result", "")
            if expected:
                lines += [f"**Expected:** {expected}", ""]

    # Developer Prompt
    dev_prompt = content.get("developer_prompt", "")
    if dev_prompt:
        lines += [
            "## Developer Prompt",
            "",
            "```",
            dev_prompt,
            "```",
            "",
        ]

    # Assumptions
    assumptions = content.get("assumptions", [])
    if assumptions:
        lines += ["## Assumptions", ""]
        for assumption in assumptions:
            lines.append(f"- {assumption}")
        lines.append("")

    # Open Questions
    questions = content.get("open_questions", [])
    if questions:
        lines += ["## Open Questions", ""]
        for question in questions:
            lines.append(f"- ❓ {question}")
        lines.append("")

    # Evidence Notes
    notes = content.get("evidence_notes", [])
    if notes:
        lines += ["## Evidence Traceability", ""]
        for note in notes:
            claim = note.get("claim", "")
            source = note.get("source", "")
            detail = note.get("note", "")
            lines.append(f"- **{claim}** _(source: {source})_ — {detail}")
        lines.append("")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return filepath

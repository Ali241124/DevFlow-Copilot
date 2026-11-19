"""
Day 2 & Day 3 — Export Service
===============================
Converts specifications and engineering artifacts into
Markdown and JSON export formats (SRS FR-017).

Supports:
- Canonical ProjectSpecification
- User Stories Artifact
- Acceptance Criteria Artifact
- Implementation Plan Artifact
- QA Test Suite Artifact
- Developer Prompt Artifact
- Client Progress Update Artifact
- Release Notes Artifact

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
    filename_prefix: str = "specification",
    artifact_type: str = "project_specification"
) -> Path:
    """
    Convert artifact content dict to readable Markdown based on artifact type
    and return the file path.
    """
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.md"
    filepath = EXPORT_DIR / filename

    if artifact_type == "client_update":
        lines = _client_update_to_markdown(content)
    elif artifact_type == "release_notes":
        lines = _release_notes_to_markdown(content)
    elif artifact_type == "qa_test_suite":
        lines = _qa_test_suite_to_markdown(content, project_name)
    elif artifact_type == "user_stories":
        lines = _user_stories_to_markdown(content, project_name)
    elif artifact_type == "acceptance_criteria":
        lines = _acceptance_criteria_to_markdown(content, project_name)
    elif artifact_type == "developer_prompt":
        lines = _developer_prompt_to_markdown(content, project_name)
    else:
        lines = _specification_to_markdown(content, project_name)

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return filepath


def _specification_to_markdown(content: dict, project_name: str) -> list[str]:
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
        for section in ("frontend", "backend", "data", "apis", "dependencies", "risks"):
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

    return lines


def _client_update_to_markdown(content: dict) -> list[str]:
    lines = [
        f"# Client Progress Update — {content.get('project_name', 'Project')}",
        "",
        f"**Date:** {content.get('report_date', 'N/A')}",
        "",
        "## Summary",
        content.get("period_summary", ""),
        "",
        "## Completed Features",
    ]
    for feat in content.get("completed_features", []):
        lines.append(f"- ✅ {feat}")
    lines += ["", "## In-Progress Work"]
    for feat in content.get("in_progress_features", []):
        lines.append(f"- ⏳ {feat}")
    lines += ["", "## Upcoming Milestones"]
    for m in content.get("upcoming_milestones", []):
        lines.append(f"- 🎯 {m}")
    lines += ["", "## Items Requiring Client Feedback"]
    for q in content.get("items_needing_client_input", []):
        lines.append(f"- ❓ {q}")
    lines.append("")
    return lines


def _release_notes_to_markdown(content: dict) -> list[str]:
    lines = [
        f"# Release Notes — {content.get('version', 'v1.0.0')}",
        "",
        f"**Release Date:** {content.get('release_date', 'N/A')}",
        "",
        "## Overview",
        content.get("summary", ""),
        "",
        "## What's New",
    ]
    for feat in content.get("new_features", []):
        lines.append(f"- ⭐ {feat}")
    lines += ["", "## Enhancements"]
    for enh in content.get("enhancements", []):
        lines.append(f"- 🚀 {enh}")
    lines += ["", "## Bug Fixes"]
    for fix in content.get("bug_fixes", []):
        lines.append(f"- 🐛 {fix}")
    lines += ["", "## Known Issues & Notes"]
    for issue in content.get("known_issues", []):
        lines.append(f"- ⚠️ {issue}")
    if content.get("migration_notes"):
        lines += ["", "## Migration Instructions", content["migration_notes"]]
    lines.append("")
    return lines


def _qa_test_suite_to_markdown(content: dict, project_name: str) -> list[str]:
    lines = [
        f"# QA Test Suite — {project_name}",
        "",
        f"- Positive Tests: {content.get('positive_count', 0)}",
        f"- Negative Tests: {content.get('negative_count', 0)}",
        f"- Edge Tests: {content.get('edge_count', 0)}",
        "",
        "---",
        "",
    ]
    for tc in content.get("test_cases", []):
        lines += [
            f"### {tc.get('test_id')} [{tc.get('type')}] — {tc.get('title')}",
            f"**Preconditions:** {', '.join(tc.get('preconditions', [])) or 'None'}",
            "**Steps:**"
        ]
        for step in tc.get("steps", []):
            lines.append(f"1. {step}")
        lines += [f"**Expected Result:** {tc.get('expected_result')}", ""]
    return lines


def _user_stories_to_markdown(content: dict, project_name: str) -> list[str]:
    lines = [
        f"# User Stories — {project_name}",
        "",
        f"Total Stories: {content.get('total_count', 0)}",
        "",
    ]
    for s in content.get("stories", []):
        lines += [
            f"### {s.get('story_id')}: {s.get('title')} `[{s.get('priority')}]`",
            f"- **As a:** {s.get('role')}",
            f"- **I want:** {s.get('goal')}",
            f"- **So that:** {s.get('benefit')}",
            f"- **Linked Acceptance Criteria:** {', '.join(s.get('acceptance_criteria_ids', [])) or 'None'}",
            "",
        ]
    return lines


def _acceptance_criteria_to_markdown(content: dict, project_name: str) -> list[str]:
    lines = [
        f"# Acceptance Criteria — {project_name}",
        "",
    ]
    for ac in content.get("criteria", []):
        lines += [
            f"### {ac.get('criterion_id')} (Linked: {ac.get('story_id')})",
            f"- **Given** {ac.get('given')}",
            f"- **When** {ac.get('when')}",
            f"- **Then** {ac.get('then')}",
            "",
        ]
    return lines


def _developer_prompt_to_markdown(content: dict, project_name: str) -> list[str]:
    lines = [
        f"# Developer Implementation Prompt — {project_name}",
        "",
        "## Task Summary",
        content.get("task_summary", ""),
        "",
        "## Technical Constraints",
    ]
    for c in content.get("constraints", []):
        lines.append(f"- {c}")
    lines += ["", "## Acceptance Checklist"]
    for chk in content.get("acceptance_checklist", []):
        lines.append(f"- [ ] {chk}")
    lines += ["", "## Full Prompt Text", "```", content.get("full_prompt_text", ""), "```", ""]
    return lines

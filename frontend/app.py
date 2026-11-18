"""
DevFlow Copilot — Streamlit Frontend (Day 2)
=============================================
Multi-tab UI for the full multimodal requirement → specification pipeline.

Tabs:
  1. Projects      — create/select a project
  2. Input         — text / image / combined submission
  3. Specification — view the full generated spec
  4. Review        — approve / reject generated artifacts
  5. Export        — download Markdown or JSON
  6. History       — browse past runs and artifacts

UI principles:
- Every AI output is clearly labelled as a draft requiring review.
- No autonomous actions (no auto-deploy, no auto-approve).
- Errors are explained clearly with recovery instructions.
"""

import json
import requests
import streamlit as st
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE = "http://localhost:8000/api/v1"
st.set_page_config(
    page_title="DevFlow Copilot",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def api_get(path: str) -> dict | None:
    try:
        response = requests.get(f"{API_BASE}{path}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(
            "❌ **Cannot reach the API server.**\n\n"
            "Make sure the FastAPI server is running:\n"
            "```\npython -m uvicorn backend.main:app --reload\n```"
        )
        return None
    except requests.exceptions.HTTPError as error:
        detail = error.response.json().get("detail", str(error))
        st.error(f"❌ API error: {detail}")
        return None


def api_post(path: str, data: dict | None = None, files=None) -> dict | None:
    try:
        response = requests.post(
            f"{API_BASE}{path}",
            data=data,
            files=files,
            timeout=180,  # LLM can take a while
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(
            "❌ **Cannot reach the API server.**\n\n"
            "Make sure the FastAPI server is running:\n"
            "```\npython -m uvicorn backend.main:app --reload\n```"
        )
        return None
    except requests.exceptions.HTTPError as error:
        detail = error.response.json().get("detail", str(error))
        st.error(f"❌ API error: {detail}")
        return None


def api_delete(path: str) -> dict | None:
    try:
        response = requests.delete(f"{API_BASE}{path}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot reach the API server.")
        return None
    except requests.exceptions.HTTPError as error:
        detail = error.response.json().get("detail", str(error))
        st.error(f"❌ API error: {detail}")
        return None


# ---------------------------------------------------------------------------
# Sidebar — project selector
# ---------------------------------------------------------------------------

def render_sidebar() -> str | None:
    """Render the sidebar and return the selected project_id (or None)."""

    st.sidebar.title("⚙️ DevFlow Copilot")
    st.sidebar.caption("AI-powered software requirements generator")
    st.sidebar.markdown("---")

    # Create new project
    with st.sidebar.expander("➕ New Project", expanded=False):
        with st.form("create_project_form"):
            proj_name = st.text_input("Project name *")
            proj_desc = st.text_area("Description", height=80)
            proj_stack = st.text_input(
                "Tech stack (optional)",
                placeholder="e.g. React, FastAPI, PostgreSQL"
            )
            submitted = st.form_submit_button("Create Project")

            if submitted:
                if not proj_name.strip():
                    st.error("Project name is required.")
                else:
                    result = api_post(
                        "/projects",
                        data={
                            "name": proj_name,
                            "description": proj_desc,
                            "tech_stack": proj_stack,
                        }
                    )
                    if result:
                        st.success(f"✅ Project '{proj_name}' created!")
                        st.rerun()

    st.sidebar.markdown("---")

    # Project selector
    projects_data = api_get("/projects")

    if not projects_data:
        return None

    projects = projects_data.get("projects", [])

    if not projects:
        st.sidebar.info("No projects yet. Create one above.")
        return None

    project_options = {
        f"{p['name']} ({p['project_id'][:8]}…)": p["project_id"]
        for p in projects
    }

    selected_label = st.sidebar.selectbox(
        "Select project",
        list(project_options.keys())
    )

    if not selected_label:
        return None

    selected_id = project_options[selected_label]
    selected_project = next(
        (p for p in projects if p["project_id"] == selected_id), None
    )

    if selected_project:
        st.sidebar.markdown(f"**{selected_project['name']}**")
        if selected_project["description"]:
            st.sidebar.caption(selected_project["description"])
        if selected_project["tech_stack"]:
            st.sidebar.caption(f"🛠 {selected_project['tech_stack']}")

    # Delete project button
    if st.sidebar.button("🗑️ Delete this project", key="delete_project"):
        result = api_delete(f"/projects/{selected_id}")
        if result:
            st.sidebar.success("Project deleted.")
            st.rerun()

    return selected_id


# ---------------------------------------------------------------------------
# Tab: Input
# ---------------------------------------------------------------------------

def render_input_tab(project_id: str):
    st.header("📥 Submit Requirements")

    st.info(
        "💡 You can submit **text only**, **image only**, or **both**. "
        "Combining a written brief with a screenshot gives the richest specification."
    )

    input_mode = st.radio(
        "Input mode",
        ["Text only", "Image only", "Combined (text + image)"],
        horizontal=True,
    )

    client_text = ""
    uploaded_file = None

    if input_mode in ("Text only", "Combined (text + image)"):
        client_text = st.text_area(
            "Client requirement / meeting notes",
            height=200,
            placeholder=(
                "Paste the client's brief, meeting notes, or requirement here.\n\n"
                "Example:\n"
                "Build a task management application where users can create, "
                "assign and track tasks. Include a dashboard view."
            ),
        )

    if input_mode in ("Image only", "Combined (text + image)"):
        uploaded_file = st.file_uploader(
            "Upload screenshot / wireframe / diagram",
            type=["png", "jpg", "jpeg", "webp"],
            help="Max 5 MB. PNG, JPG, JPEG, or WEBP only.",
        )

        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded screenshot", use_container_width=True)

    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        generate_button = st.button(
            "🚀 Generate Specification",
            type="primary",
            use_container_width=True,
        )

    with col2:
        st.caption("⏱ Generation may take 30–120 seconds depending on model size.")

    if generate_button:
        # Validation
        has_text = bool(client_text.strip())
        has_image = uploaded_file is not None

        if not has_text and not has_image:
            st.error("Please provide text, an image, or both.")
            return

        with st.spinner("🤖 Generating specification... (this may take a moment)"):
            post_data = {}
            post_files = None

            if has_text:
                post_data["client_text"] = client_text

            if has_image:
                post_files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type,
                    )
                }

            result = api_post(
                f"/projects/{project_id}/generate",
                data=post_data if post_data else None,
                files=post_files,
            )

            if result:
                st.success(
                    f"✅ Specification generated! **Status: DRAFT** "
                    f"(artifact ID: `{result['artifact_id'][:12]}…`)"
                )
                st.warning(
                    "⚠️ **This is an AI-generated draft and requires human review "
                    "before it is used in any development work.**"
                )
                st.session_state["last_artifact_id"] = result["artifact_id"]
                st.session_state["last_specification"] = result["specification"]
                st.session_state["last_metadata"] = result["metadata"]
                st.rerun()


# ---------------------------------------------------------------------------
# Tab: Specification viewer
# ---------------------------------------------------------------------------

def _badge(label: str, color: str) -> str:
    return f":{color}[**{label}**]"


def render_specification_tab():
    st.header("📋 Specification")

    spec = st.session_state.get("last_specification")
    metadata = st.session_state.get("last_metadata", {})
    artifact_id = st.session_state.get("last_artifact_id")

    if not spec:
        st.info("No specification generated yet. Go to the **Input** tab to generate one.")
        return

    # Draft warning
    st.warning(
        "⚠️ **AI-generated draft — requires human review before use.** "
        f"Model: `{metadata.get('model_name', 'unknown')}` | "
        f"Prompt: `{metadata.get('prompt_version', 'unknown')}` | "
        f"Mode: `{metadata.get('input_mode', 'unknown')}`"
    )

    if artifact_id:
        st.caption(f"Artifact ID: `{artifact_id}`")

    # Summary
    with st.expander("📌 Project Summary", expanded=True):
        st.markdown(spec.get("project_summary", "_No summary generated._"))

    # Features
    features = spec.get("features", [])
    if features:
        with st.expander(f"🔧 Features ({len(features)})", expanded=True):
            for feature in features:
                priority = feature.get("priority", "medium")
                source = feature.get("source", "assumed")

                priority_color = {
                    "high": "red", "medium": "orange", "low": "green"
                }.get(priority, "grey")

                st.markdown(
                    f"**{feature.get('name', '')}** "
                    f":{priority_color}[{priority.upper()}] "
                    f":grey[source: {source}]"
                )
                st.caption(feature.get("description", ""))

    # User stories
    stories = spec.get("user_stories", [])
    if stories:
        with st.expander(f"📖 User Stories ({len(stories)})"):
            for story in stories:
                st.markdown(
                    f"**{story.get('story_id', '')}** — "
                    f"As a **{story.get('role', '')}**, "
                    f"I want **{story.get('goal', '')}** "
                    f"so that **{story.get('benefit', '')}**."
                )

    # Acceptance criteria
    criteria = spec.get("acceptance_criteria", [])
    if criteria:
        with st.expander(f"✅ Acceptance Criteria ({len(criteria)})"):
            for ac in criteria:
                st.markdown(
                    f"**{ac.get('story_id', '')}**\n"
                    f"- 📋 **Given** {ac.get('given', '')}\n"
                    f"- ⚡ **When** {ac.get('when', '')}\n"
                    f"- ✔️ **Then** {ac.get('then', '')}"
                )
                st.divider()

    # Implementation plan
    plan = spec.get("implementation_plan", {})
    if plan:
        with st.expander("🏗️ Implementation Plan"):
            cols = st.columns(2)
            plan_sections = [
                ("Frontend", plan.get("frontend", [])),
                ("Backend", plan.get("backend", [])),
                ("Data", plan.get("data", [])),
                ("APIs", plan.get("apis", [])),
            ]
            for i, (label, items) in enumerate(plan_sections):
                col = cols[i % 2]
                if items:
                    with col:
                        st.markdown(f"**{label}**")
                        for item in items:
                            st.markdown(f"- {item}")

            risks = plan.get("risks", [])
            if risks:
                st.markdown("**⚠️ Risks**")
                for risk in risks:
                    st.markdown(f"- 🔴 {risk}")

    # Test cases
    test_cases = spec.get("test_cases", [])
    if test_cases:
        with st.expander(f"🧪 QA Test Cases ({len(test_cases)})"):
            for tc in test_cases:
                tc_type = tc.get("type", "positive")
                type_color = {
                    "positive": "green",
                    "negative": "red",
                    "edge": "orange",
                }.get(tc_type, "grey")
                st.markdown(
                    f"**{tc.get('test_id', '')}** — {tc.get('title', '')} "
                    f":{type_color}[{tc_type}]"
                )
                for step in tc.get("steps", []):
                    st.markdown(f"  1. {step}")
                st.caption(f"Expected: {tc.get('expected_result', '')}")

    # Developer prompt
    dev_prompt = spec.get("developer_prompt", "")
    if dev_prompt:
        with st.expander("👨‍💻 Developer Prompt"):
            st.code(dev_prompt, language=None)

    # Evidence & Assumptions
    assumptions = spec.get("assumptions", [])
    questions = spec.get("open_questions", [])
    notes = spec.get("evidence_notes", [])

    with st.expander(
        f"🔍 Evidence & Assumptions "
        f"({len(assumptions)} assumptions, {len(questions)} open questions)"
    ):
        if assumptions:
            st.markdown("**Assumptions**")
            for a in assumptions:
                st.markdown(f"- ⚠️ {a}")

        if questions:
            st.markdown("**Open Questions**")
            for q in questions:
                st.markdown(f"- ❓ {q}")

        if notes:
            st.markdown("**Evidence Traceability**")
            for note in notes:
                st.markdown(
                    f"- **{note.get('claim', '')}** "
                    f"(_{note.get('source', '')}_): "
                    f"{note.get('note', '')}"
                )


# ---------------------------------------------------------------------------
# Tab: Review
# ---------------------------------------------------------------------------

def render_review_tab(project_id: str):
    st.header("👤 Human Review")

    st.info(
        "📌 **No artifact is considered approved until a human reviewer acts here.** "
        "(SRS GEN-008)"
    )

    artifact_id = st.session_state.get("last_artifact_id")

    if not artifact_id:
        st.warning(
            "No artifact to review. Generate a specification first "
            "in the **Input** tab."
        )
        return

    st.markdown(f"**Artifact:** `{artifact_id}`")

    # Fetch current status
    artifact_data = api_get(f"/artifacts/{artifact_id}")
    if not artifact_data:
        return

    artifact = artifact_data.get("artifact", {})
    current_status = artifact.get("review_status", "draft")

    status_colors = {
        "draft": "🟡",
        "approved": "🟢",
        "rejected": "🔴",
    }
    st.markdown(
        f"**Current status:** {status_colors.get(current_status, '⬜')} "
        f"`{current_status.upper()}`"
    )

    if artifact.get("reviewer_note"):
        st.caption(f"Reviewer note: {artifact['reviewer_note']}")

    st.divider()

    with st.form("review_form"):
        note = st.text_area(
            "Reviewer note (optional)",
            placeholder="Describe what you changed, corrected, or verified.",
            height=100,
        )

        col1, col2 = st.columns(2)

        with col1:
            approve = st.form_submit_button(
                "✅ Approve",
                type="primary",
                use_container_width=True,
            )

        with col2:
            reject = st.form_submit_button(
                "❌ Reject",
                use_container_width=True,
            )

    if approve:
        result = api_post(
            f"/artifacts/{artifact_id}/review",
            data={"status": "approved", "note": note},
        )
        if result:
            st.success("✅ Artifact approved.")

    if reject:
        result = api_post(
            f"/artifacts/{artifact_id}/review",
            data={"status": "rejected", "note": note},
        )
        if result:
            st.warning("🔴 Artifact rejected.")


# ---------------------------------------------------------------------------
# Tab: Export
# ---------------------------------------------------------------------------

def render_export_tab(project_id: str):
    st.header("📤 Export")

    artifact_id = st.session_state.get("last_artifact_id")
    spec = st.session_state.get("last_specification")

    if not artifact_id or not spec:
        st.info("Generate a specification first in the **Input** tab.")
        return

    project_name = st.text_input(
        "Project name for export header",
        value="My Project",
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📄 Export as JSON", use_container_width=True):
            result = api_post(f"/artifacts/{artifact_id}/export/json")
            if result:
                st.success(f"✅ Saved to: `{result['file_path']}`")

        # Also offer inline download
        st.download_button(
            label="⬇️ Download JSON",
            data=json.dumps(spec, indent=2, ensure_ascii=False),
            file_name=f"devflow_{artifact_id[:8]}_spec.json",
            mime="application/json",
            use_container_width=True,
        )

    with col2:
        if st.button("📝 Export as Markdown", use_container_width=True):
            result = api_post(
                f"/artifacts/{artifact_id}/export/markdown",
                data={"project_name": project_name},
            )
            if result:
                st.success(f"✅ Saved to: `{result['file_path']}`")

        # Inline markdown download
        from backend.app.services.export_service import export_markdown
        import tempfile
        md_content = _spec_to_markdown(spec, project_name)
        st.download_button(
            label="⬇️ Download Markdown",
            data=md_content,
            file_name=f"devflow_{artifact_id[:8]}_spec.md",
            mime="text/markdown",
            use_container_width=True,
        )


def _spec_to_markdown(spec: dict, project_name: str) -> str:
    """Generate Markdown inline for download (no file write required)."""
    lines = [
        f"# {project_name} — Project Specification",
        "",
        "> ⚠️ AI-generated draft — requires human review before use.",
        "",
        "## Project Summary",
        "",
        spec.get("project_summary", ""),
        "",
    ]
    for feature in spec.get("features", []):
        lines += [
            f"### {feature.get('name', '')}",
            feature.get("description", ""),
            f"- Priority: {feature.get('priority', '')}",
            f"- Source: {feature.get('source', '')}",
            "",
        ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tab: History
# ---------------------------------------------------------------------------

def render_history_tab(project_id: str):
    st.header("🕐 Generation History")

    runs_data = api_get(f"/projects/{project_id}/runs")
    if not runs_data:
        return

    runs = runs_data.get("runs", [])

    if not runs:
        st.info("No generation runs yet for this project.")
        return

    for run in runs:
        status_icon = {
            "success": "✅",
            "failed": "❌",
            "running": "⏳",
            "pending": "🔵",
        }.get(run["status"], "⬜")

        with st.expander(
            f"{status_icon} Run `{run['run_id'][:12]}…` — "
            f"{run['status']} | {run['created_at'][:19]}"
        ):
            st.markdown(
                f"- **Model:** `{run['model_name']}`\n"
                f"- **Prompt:** `{run['prompt_version']}`\n"
                f"- **Started:** {run['created_at'][:19]}\n"
                f"- **Completed:** {run.get('completed_at', 'N/A')}"
            )

            if run.get("error_message"):
                st.error(f"Error: {run['error_message']}")

            # Show artifacts for this run
            artifacts_data = api_get(f"/runs/{run['run_id']}/artifacts")
            if artifacts_data:
                artifacts = artifacts_data.get("artifacts", [])

                for artifact in artifacts:
                    review_icon = {
                        "draft": "🟡",
                        "approved": "🟢",
                        "rejected": "🔴",
                    }.get(artifact["review_status"], "⬜")

                    st.markdown(
                        f"{review_icon} **{artifact['artifact_type']}** — "
                        f"`{artifact['artifact_id'][:12]}…` — "
                        f"{artifact['review_status']}"
                    )

                    if st.button(
                        f"Load this artifact",
                        key=f"load_{artifact['artifact_id']}"
                    ):
                        st.session_state["last_artifact_id"] = (
                            artifact["artifact_id"]
                        )
                        content = artifact.get("content", {})
                        st.session_state["last_specification"] = {
                            k: v for k, v in content.items()
                            if k != "_metadata"
                        }
                        st.session_state["last_metadata"] = (
                            content.get("_metadata", {})
                        )
                        st.rerun()


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main():
    project_id = render_sidebar()

    if not project_id:
        st.title("⚙️ DevFlow Copilot")
        st.markdown(
            "Welcome to **MoinSystems AI DevFlow Copilot**.\n\n"
            "Create or select a project in the sidebar to get started."
        )
        st.info(
            "**What this tool does:**\n"
            "1. Takes client requirements (text) and/or UI screenshots.\n"
            "2. Generates a structured project specification using a local AI model.\n"
            "3. Produces user stories, acceptance criteria, implementation plans, "
            "QA test cases, and a developer prompt.\n"
            "4. Requires human review before any artifact is considered approved.\n\n"
            "**Everything runs locally — no data leaves your machine.**"
        )
        return

    tabs = st.tabs([
        "📥 Input",
        "📋 Specification",
        "👤 Review",
        "📤 Export",
        "🕐 History",
    ])

    with tabs[0]:
        render_input_tab(project_id)

    with tabs[1]:
        render_specification_tab()

    with tabs[2]:
        render_review_tab(project_id)

    with tabs[3]:
        render_export_tab(project_id)

    with tabs[4]:
        render_history_tab(project_id)


if __name__ == "__main__":
    main()


import pytest
from pydantic import ValidationError

from backend.app.schemas.vision import (
    UIComponent,
    UIInteraction,
    VisionAnalysis
)


def test_valid_vision_analysis():
    component = UIComponent(
        name="Login button",
        component_type="button",
        visible_text="Login",
        evidence_note="A Login button is visible.",
        status="observed"
    )

    interaction = UIInteraction(
        control="Login button",
        possible_action="Submit login form",
        behavior="Unknown",
        status="assumed",
        evidence_note="The screenshot does not show what happens after clicking."
    )

    analysis = VisionAnalysis(
        page_description="A login page.",
        components=[component],
        visible_text=["Login", "Email", "Password"],
        current_state="Login form is displayed.",
        interactions=[interaction],
        evidence_notes=["Email and password fields are visible."],
        unknowns=["The result of clicking Login is unknown."]
    )

    assert analysis.page_description == "A login page."
    assert len(analysis.components) == 1
    assert analysis.components[0].status == "observed"
    assert analysis.interactions[0].status == "assumed"


def test_invalid_component_status():
    with pytest.raises(ValidationError):
        UIComponent(
            name="Login button",
            component_type="button",
            visible_text="Login",
            evidence_note="A button is visible.",
            status="verified"
        )


def test_extra_field_is_rejected():
    with pytest.raises(ValidationError):
        VisionAnalysis(
            page_description="A login page.",
            current_state="Login form displayed.",
            unexpected_field="This should not be allowed."
        )

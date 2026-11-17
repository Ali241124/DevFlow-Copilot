
from pydantic import ValidationError

from backend.app.schemas.requirements import (
    Feature,
    RequirementsAnalysis,
)


def test_valid_requirements_analysis():

    analysis = RequirementsAnalysis(
        project_summary="A task management application.",
        features=[
            Feature(
                name="Create tasks",
                description="Allow users to create tasks.",
                priority="medium",
                source_text="Users can create tasks.",
                status="confirmed",
            )
        ],
        assumptions=[],
        open_questions=[],
    )

    assert analysis.project_summary == "A task management application."
    assert len(analysis.features) == 1
    assert analysis.features[0].status == "confirmed"


def test_invalid_feature_priority():

    try:
        Feature(
            name="Create tasks",
            description="Allow users to create tasks.",
            priority="urgent",
            source_text="Users can create tasks.",
        )

        assert False, "Invalid priority should raise an error"

    except ValidationError:
        pass


def test_missing_source_text():

    try:
        Feature(
            name="Create tasks",
            description="Allow users to create tasks.",
            priority="medium",
        )

        assert False, "Missing source text should raise an error"

    except ValidationError:
        pass


if __name__ == "__main__":

    test_valid_requirements_analysis()
    test_invalid_feature_priority()
    test_missing_source_text()

    print("All requirements schema tests passed!")

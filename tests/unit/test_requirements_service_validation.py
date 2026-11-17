
from backend.app.services.requirements_service import RequirementsService


class MockLLMClient:
    """Simulates the Ollama client without loading an AI model."""

    def __init__(self, response):
        self.response = response

    def generate(self, **kwargs):
        return self.response


def test_valid_response():

    mock_response = """
    {
        "project_summary": "A task management application.",
        "features": [
            {
                "name": "Create tasks",
                "description": "Allow users to create tasks.",
                "priority": "medium",
                "source_text": "Users can create tasks.",
                "status": "confirmed"
            }
        ],
        "assumptions": [],
        "open_questions": [
            "What fields should a task contain?"
        ]
    }
    """

    service = RequirementsService(
        llm_client=MockLLMClient(mock_response)
    )

    result = service.analyze(
        "Build a task management application. "
        "Users can create tasks."
    )
    assert result.project_summary == "A task management application."
    assert len(result.features) == 1

    print("PASS: Valid response accepted")


def test_empty_brief():

    service = RequirementsService(
        llm_client=MockLLMClient("{}")
    )

    try:
        service.analyze("   ")
        assert False, "Empty brief should be rejected"

    except ValueError as error:
        assert "cannot be empty" in str(error)

    print("PASS: Empty brief rejected")


def test_invalid_json():

    service = RequirementsService(
        llm_client=MockLLMClient("This is not JSON")
    )

    try:
        service.analyze("Build a task management application.")

        assert False, "Invalid JSON should be rejected"

    except ValueError as error:
        assert "invalid JSON" in str(error)

    print("PASS: Invalid JSON rejected")


def test_unexpected_field():

    mock_response = """
    {
        "project_summary": "A task management application.",
        "features": [],
        "assumptions": [],
        "open_questions": [],
        "database": "PostgreSQL"
    }
    """

    service = RequirementsService(
        llm_client=MockLLMClient(mock_response)
    )

    try:
        service.analyze("Build a task management application.")

        assert False, "Unexpected fields should be rejected"

    except ValueError as error:
        assert "schema" in str(error)

    print("PASS: Unexpected fields rejected")


if __name__ == "__main__":

    print("=" * 60)
    print("REQUIREMENTS SERVICE VALIDATION TESTS")
    print("=" * 60)

    test_valid_response()
    test_empty_brief()
    test_invalid_json()
    test_unexpected_field()

    print("\nAll validation tests passed!")

def test_unverified_source_evidence_demoted():

    mock_response = """
    {
        "project_summary": "A task management application.",
        "features": [
            {
                "name": "Add payment system",
                "description": "Users can make payments.",
                "priority": "medium",
                "source_text": "Users can make online payments.",
                "status": "confirmed"
            }
        ],
        "assumptions": [],
        "open_questions": []
    }
    """

    service = RequirementsService(
        llm_client=MockLLMClient(mock_response)
    )

    result = service.analyze(
        "Build a task management application."
    )

    feature = result.features[0]

    assert feature.source_text == ""
    assert feature.status == "needs_clarification"

    print("PASS: Unsupported evidence correctly rejected")
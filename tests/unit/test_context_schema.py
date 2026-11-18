
from backend.app.schemas.context import (
    EvidenceItem,
    NormalizedContext
)


def main():
    print("=" * 60)
    print("NORMALIZED CONTEXT SCHEMA TEST")
    print("=" * 60)

    context = NormalizedContext(
        client_text="Build a signup page.",
        image_paths=["data/uploads/sample_ui.png"],
        input_mode="combined",
        evidence=[
            EvidenceItem(
                source="client_text",
                category="requirement",
                content="Build a signup page.",
                status="provided"
            ),
            EvidenceItem(
                source="screenshot",
                category="visual_observation",
                content="A Continue button is visible.",
                status="observed"
            ),
            EvidenceItem(
                source="screenshot",
                category="assumption",
                content="Continue creates an account.",
                status="assumed",
                evidence_note=(
                    "The screenshot does not demonstrate "
                    "the button behavior."
                )
            )
        ],
        assumptions=[
            "The Continue button may submit the form."
        ],
        open_questions=[
            "What should happen after clicking Continue?"
        ]
    )

    context.validate_input_mode()

    print(context.model_dump_json(indent=4))
    print("\nContext schema validation successful!")


if __name__ == "__main__":
    main()

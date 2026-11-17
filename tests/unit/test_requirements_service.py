
from backend.app.services.requirements_service import RequirementsService


def main():

    print("=" * 60)
    print("DEVFLOW REQUIREMENTS ANALYSIS TEST")
    print("=" * 60)

    client_brief = """
    Build a task management application where users can
    create tasks, update tasks and mark tasks as completed.

    Do not add authentication, deadlines or database technologies.
    """

    service = RequirementsService()

    print("\nAnalyzing client brief...\n")

    result = service.analyze(client_brief)

    print("PROJECT SUMMARY")
    print(result.project_summary)

    print("\nFEATURES")

    for index, feature in enumerate(result.features, start=1):
        print(f"\n{index}. {feature.name}")
        print(f"Description: {feature.description}")
        print(f"Priority: {feature.priority}")
        print(f"Source Evidence: {feature.source_text}")
        print(f"Status: {feature.status}")

    print("\nASSUMPTIONS")

    for assumption in result.assumptions:
        print(f"- {assumption}")

    print("\nOPEN QUESTIONS")

    for question in result.open_questions:
        print(f"- {question}")

    print("\n" + "=" * 60)
    print("REQUIREMENTS ANALYSIS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from backend.app.services.requirements_service import RequirementsService
from backend.app.services.vision_service import VisionService
from backend.app.services.context_builder import ContextBuilder


# --------------------------------------------------
# Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "datasets"
    / "multimodal_cases.json"
)

REPORT_DIR = PROJECT_ROOT / "evaluation" / "reports"


# --------------------------------------------------
# Text matching helpers
# --------------------------------------------------

def normalize_text(value: str) -> str:
    """Normalize text for simple, case-insensitive matching."""

    value = value.casefold()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return " ".join(value.split())

def contains_expected(expected: str, actual_text: str) -> bool:
    """
    Check expected information using exact matching,
    known equivalent phrases, and token matching.
    """

    expected_normalized = normalize_text(expected)
    actual_normalized = normalize_text(actual_text)

    if not expected_normalized:
        return True

    if expected_normalized in actual_normalized:
        return True

    # Common equivalent phrases in our evaluation dataset.
    aliases = {
        "complete tasks": [
            "mark tasks as completed",
            "mark task as completed",
            "mark tasks completed",
        ],
        "add to cart": [
            "add products to a cart",
            "add products to cart",
        ],
        "place orders": [
            "place an order",
            "submit orders",
        ],
        "view total spending": [
            "see their total spending",
            "display total spending",
        ],
    }

    for alternative in aliases.get(expected_normalized, []):
        if normalize_text(alternative) in actual_normalized:
            return True

    ignored_words = {
        "field",
        "button",
        "control",
        "information",
        "summary",
        "option",
    }

    expected_words = {
        word
        for word in expected_normalized.split()
        if word not in ignored_words
    }

    actual_words = set(actual_normalized.split())

    return bool(expected_words) and expected_words.issubset(actual_words)

def collect_text(value) -> str:
    """Convert nested model output into searchable text."""

    if isinstance(value, str):
        return value

    if isinstance(value, list):
        return " ".join(collect_text(item) for item in value)

    if isinstance(value, dict):
        return " ".join(
            collect_text(item)
            for item in value.values()
        )

    return ""


# --------------------------------------------------
# Dataset loading
# --------------------------------------------------

def load_dataset() -> list:
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    return dataset["cases"]


# --------------------------------------------------
# Model execution
# --------------------------------------------------

def execute_case(case: dict) -> dict:

    input_mode = case["input_mode"]
    client_text = case["client_text"]

    image_path = None

    if case["image"]:
        image_path = PROJECT_ROOT / case["image"]

        if not image_path.is_file():
            raise FileNotFoundError(
                f"Evaluation image not found: {image_path}"
            )

    if input_mode == "text_only":

        service = RequirementsService()

        result = service.analyze(client_text)

    elif input_mode == "image_only":

        service = VisionService()

        result = service.analyze_screenshot(
            str(image_path)
        )

    elif input_mode == "combined":

        service = ContextBuilder()

        result = service.build(
            client_text=client_text,
            image_paths=[str(image_path)]
        )

    else:
        raise ValueError(
            f"Unsupported input mode: {input_mode}"
        )

    return result.model_dump(mode="json")


# --------------------------------------------------
# Evaluation
# --------------------------------------------------

def evaluate_case(case: dict, output: dict) -> dict:

    expected = case["expected"]
    input_mode = case["input_mode"]

    checks = {}
    details = {}
    individual_results = []

    def record_group(group_name, results):

        details[group_name] = results

        checks[group_name] = (
            all(results.values())
            if results
            else True
        )

        individual_results.extend(results.values())

    def record_single(check_name, passed):

        checks[check_name] = passed
        individual_results.append(passed)

    # --------------------------------------------------
    # TEXT-ONLY
    # --------------------------------------------------

    if input_mode == "text_only":

        features = output.get("features", [])

        feature_text = collect_text(features)

        feature_results = {
            item: contains_expected(item, feature_text)
            for item in expected.get("required_features", [])
        }

        record_group(
            "required_features",
            feature_results
        )

        if expected.get("should_identify_unknowns"):

            record_single(
                "identifies_unknowns",
                bool(output.get("open_questions", []))
            )

        if expected.get("should_flag_ambiguity"):

            record_single(
                "flags_ambiguity",
                bool(
                    output.get("open_questions", [])
                    or output.get("assumptions", [])
                )
            )

    # --------------------------------------------------
    # IMAGE-ONLY
    # --------------------------------------------------

    elif input_mode == "image_only":

        components = output.get("components", [])
        visible_text = output.get("visible_text", [])

        component_text = collect_text({
            "components": components,
            "page_description": output.get("page_description", ""),
            "current_state": output.get("current_state", ""),
            "visible_text": visible_text,
            "evidence_notes": output.get("evidence_notes", []),
        })

        component_results = {
            item: contains_expected(item, component_text)
            for item in expected.get("required_components", [])
        }

        record_group(
            "required_components",
            component_results
        )

        visible_text_results = {
            item: contains_expected(item, " ".join(visible_text))
            for item in expected.get("visible_text", [])
        }

        record_group(
            "visible_text",
            visible_text_results
        )

        if expected.get("should_identify_unknowns"):

            record_single(
                "identifies_unknowns",
                bool(output.get("unknowns", []))
            )

    # --------------------------------------------------
    # COMBINED
    # --------------------------------------------------

    elif input_mode == "combined":

        evidence = output.get("evidence", [])

        # Exclude the original brief to avoid
        # counting the input itself as extracted output.
        requirement_evidence = [
            item.get("content", "")
            for item in evidence
            if (
                item.get("source") == "client_text"
                and item.get("content") != case["client_text"]
            )
        ]

        requirement_text = " ".join(requirement_evidence)

        feature_results = {
            item: contains_expected(item, requirement_text)
            for item in expected.get("required_features", [])
        }

        record_group(
            "required_features",
            feature_results
        )

        visual_evidence = [
            item.get("content", "")
            for item in evidence
            if (
                item.get("source") == "screenshot"
                and item.get("category") == "visual_observation"
            )
        ]

        visual_text = " ".join(visual_evidence)

        visual_results = {
            item: contains_expected(item, visual_text)
            for item in expected.get("visual_observations", [])
        }

        record_group(
            "visual_observations",
            visual_results
        )

        if expected.get("should_distinguish_requested_from_visible"):

            missing_details = expected.get(
                "missing_visual_details", []
            )

            unknown_text = " ".join(
                output.get("open_questions", [])
            )

            missing_results = {
                item: contains_expected(item, unknown_text)
                for item in missing_details
            }

            record_group(
                "missing_visual_details",
                missing_results
            )

    # --------------------------------------------------
    # FINAL SCORE
    # --------------------------------------------------

    total_checks = len(individual_results)

    passed_checks = sum(individual_results)

    score = (
        round((passed_checks / total_checks) * 100, 2)
        if total_checks
        else 0
    )

    return {
        "checks": checks,
        "details": details,
        "passed_checks": passed_checks,
        "total_checks": total_checks,
        "score_percent": score,
        "requires_human_review": True,
        "evaluation_method": "heuristic_text_matching",
    }
def expected_check_count(case: dict) -> int:
    """Count all evaluation criteria, including failed cases."""

    expected = case["expected"]
    mode = case["input_mode"]

    if mode == "text_only":
        return (
            len(expected.get("required_features", []))
            + int(bool(expected.get("should_identify_unknowns")))
            + int(bool(expected.get("should_flag_ambiguity")))
        )

    if mode == "image_only":
        return (
            len(expected.get("required_components", []))
            + len(expected.get("visible_text", []))
            + int(bool(expected.get("should_identify_unknowns")))
        )

    if mode == "combined":
        return (
            len(expected.get("required_features", []))
            + len(expected.get("visual_observations", []))
            + len(expected.get("missing_visual_details", []))
        )

    return 0

# --------------------------------------------------
# Run evaluation
# --------------------------------------------------

def run_evaluation(
    selected_cases: list,
    dataset_name: str
) -> dict:

    results = []

    total_cases = len(selected_cases)

    print("=" * 65)
    print("DEVFLOW COPILOT - MULTIMODAL EVALUATION")
    print("=" * 65)
    print(f"Dataset: {dataset_name}")
    print(f"Cases: {total_cases}")
    print()

    for index, case in enumerate(selected_cases, start=1):

        case_id = case["id"]

        print("-" * 65)
        print(f"Case {index}/{total_cases}: {case_id}")
        print(f"Input mode: {case['input_mode']}")
        print("Running local AI models...")

        case_result = {
            "case_id": case_id,
            "input_mode": case["input_mode"],
            "status": "failed",
        }

        try:
            output = execute_case(case)

            evaluation = evaluate_case(
                case=case,
                output=output
            )

            case_result.update({
                "status": "completed",
                "evaluation": evaluation,
                "model_output": output,
            })

            print(
                f"Score: {evaluation['score_percent']}%"
            )

            print(
                f"Checks passed: "
                f"{evaluation['passed_checks']}/"
                f"{evaluation['total_checks']}"
            )

        except Exception as error:

            case_result.update({
                "status": "failed",
                "error": str(error),
            })

            print(f"FAILED: {error}")

        results.append(case_result)

        print()

    completed = [
        item for item in results
        if item["status"] == "completed"
    ]

    failed = [
        item for item in results
        if item["status"] == "failed"
    ]
    # Count criteria from every selected case.
    # Failed model executions receive zero passed checks.
    total_checks = sum(
        expected_check_count(case)
        for case in selected_cases
    )

    passed_checks = sum(
        item["evaluation"]["passed_checks"]
        for item in completed
    )

    evaluated_checks = sum(
        item["evaluation"]["total_checks"]
        for item in completed
    )

    overall_score = (
        round((passed_checks / total_checks) * 100, 2)
        if total_checks
        else 0
    )

    summary = {
        "dataset": dataset_name,
        "total_cases": total_cases,
        "completed_cases": len(completed),
        "failed_cases": len(failed),
        "passed_checks": passed_checks,
        "total_checks": total_checks,
        "overall_score_percent": overall_score,
        "human_review_required": True,
    }

    report = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "summary": summary,
        "results": results,
    }

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%d_%H%M%S")

    report_path = (
        REPORT_DIR
        / f"multimodal_evaluation_{timestamp}.json"
    )

    with report_path.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False
        )

    # --------------------------------------------------
    # Final summary
    # --------------------------------------------------

    print("=" * 65)
    print("EVALUATION SUMMARY")
    print("=" * 65)

    print(f"Total cases:       {total_cases}")
    print(f"Completed:         {len(completed)}")
    print(f"Failed:            {len(failed)}")
    print(f"Passed checks:     {passed_checks}")
    print(f"Total checks:      {total_checks}")
    print(f"Overall score:     {overall_score}%")

    print()
    print(f"Report saved to: {report_path}")
    print("=" * 65)

    return report


# --------------------------------------------------
# Command-line interface
# --------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description="Run DevFlow Copilot multimodal evaluation."
    )

    parser.add_argument(
        "--case-id",
        type=str,
        help="Run one specific evaluation case."
    )

    parser.add_argument(
        "--mode",
        choices=["text_only", "image_only", "combined"],
        help="Run cases of one input type only."
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Limit the number of cases to run."
    )

    args = parser.parse_args()

    dataset = load_dataset()

    selected_cases = dataset

    if args.case_id:
        selected_cases = [
            case for case in selected_cases
            if case["id"] == args.case_id
        ]

        if not selected_cases:
            parser.error(
                f"Evaluation case not found: {args.case_id}"
            )

    if args.mode:
        selected_cases = [
            case for case in selected_cases
            if case["input_mode"] == args.mode
        ]

    if args.limit is not None:
        if args.limit < 1:
            parser.error("--limit must be at least 1.")

        selected_cases = selected_cases[:args.limit]

    if not selected_cases:
        parser.error("No evaluation cases matched your filters.")

    dataset_name = "DevFlow Copilot Multimodal Evaluation"

    run_evaluation(
        selected_cases=selected_cases,
        dataset_name=dataset_name
    )


if __name__ == "__main__":
    main()
"""
Day 4 — Evaluation & Reliability Framework
==========================================
Implements rigorous, systematic GenAI quality & reliability testing (SRS §21 & §22):
- Multi-dimensional scoring functions (0-5 scale):
  1. Requirement completeness
  2. Evidence fidelity (hallucination defense)
  3. Testability
  4. Engineering usefulness
  5. Structure validity (Pass/Fail)
  6. Uncertainty handling (surfacing missing info instead of inventing)
- Failure categorization (hallucination, missing requirement, invalid structure, weak testability, poor usefulness)
- Prompt injection and untrusted input defense verification
- Multi-prompt benchmark comparison (prompt_v1 vs prompt_v2)
- Comprehensive evaluation execution and report generator
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
from typing import Literal

from backend.app.schemas.context import NormalizedContext
from backend.app.schemas.specification import ProjectSpecification

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Evaluation Data Structures
# ---------------------------------------------------------------------------

@dataclass
class ScenarioEvaluationResult:
    scenario_id: str
    category: str
    completeness_score: float       # 0.0 - 5.0
    evidence_fidelity_score: float  # 0.0 - 5.0
    testability_score: float        # 0.0 - 5.0
    usefulness_score: float         # 0.0 - 5.0
    uncertainty_score: float        # 0.0 - 5.0
    structure_valid: bool           # Pass / Fail
    composite_score: float          # 0.0 - 5.0
    failures: list[str]
    notes: str


@dataclass
class EvaluationBenchmarkReport:
    timestamp: str
    prompt_version: str
    model_name: str
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    average_completeness: float
    average_fidelity: float
    average_testability: float
    average_usefulness: float
    average_uncertainty: float
    overall_mean_score: float
    structure_pass_rate: float
    failure_breakdown: dict[str, int]
    prompt_injection_detected_and_neutralized: bool
    results: list[dict]


# ---------------------------------------------------------------------------
# Evaluator Engine
# ---------------------------------------------------------------------------

class GenAIEvaluator:
    """
    Evaluates generated specifications against benchmark expectations.
    """

    FAILURE_CATEGORIES = {
        "hallucination": "Invented facts, unrequested third-party integrations, or unauthorized business rules",
        "missing_requirement": "Dropped explicitly required feature from input brief",
        "invalid_structure": "Failed schema parsing or missing mandatory JSON keys",
        "weak_testability": "Acceptance criteria or test cases lack concrete, verifiable steps",
        "poor_technical_usefulness": "Implementation plan or developer prompt is too generic or empty",
        "failed_uncertainty": "Invented missing specifications instead of flagging open questions",
    }

    def evaluate_scenario(
        self,
        scenario: dict,
        specification: ProjectSpecification | None,
        raw_error: str | None = None
    ) -> ScenarioEvaluationResult:
        """
        Score a single scenario against ground truth / acceptance criteria.
        """
        scenario_id = scenario.get("id", "UNKNOWN")
        category = scenario.get("category", "standard")
        expected = scenario.get("expected", {})

        failures = []

        # 1. Structure Validity
        if specification is None or raw_error:
            failures.append("invalid_structure")
            return ScenarioEvaluationResult(
                scenario_id=scenario_id,
                category=category,
                completeness_score=0.0,
                evidence_fidelity_score=0.0,
                testability_score=0.0,
                usefulness_score=0.0,
                uncertainty_score=0.0,
                structure_valid=False,
                composite_score=0.0,
                failures=failures,
                notes=f"Generation failed: {raw_error}",
            )

        structure_valid = True

        # 2. Requirement Completeness (0-5)
        required_features = expected.get("required_features", [])
        if required_features:
            spec_feature_text = " ".join(
                f"{f.name} {f.description}".lower() for f in specification.features
            )
            matched = sum(1 for req in required_features if req.lower() in spec_feature_text)
            completeness_score = round((matched / len(required_features)) * 5.0, 2)
            if completeness_score < 3.0:
                failures.append("missing_requirement")
        else:
            completeness_score = 5.0 if specification.features else 2.5

        # 3. Evidence Fidelity (Hallucination Defense) (0-5)
        prohibited_items = expected.get("prohibited_inventions", [
            "stripe", "paypal", "oauth", "aws s3", "docker swarm", "kubernetes"
        ])
        all_spec_text = json.dumps(specification.model_dump()).lower()

        hallucinated = [item for item in prohibited_items if item.lower() in all_spec_text]
        if hallucinated:
            evidence_fidelity_score = max(0.0, 5.0 - (len(hallucinated) * 1.5))
            failures.append("hallucination")
        else:
            evidence_fidelity_score = 5.0

        # 4. Testability (0-5)
        ac_count = len(specification.acceptance_criteria)
        tc_count = len(specification.test_cases)
        has_given_when_then = any(
            bool(ac.given and ac.when and ac.then) for ac in specification.acceptance_criteria
        )

        testability_score = 5.0
        if ac_count == 0 or tc_count == 0:
            testability_score = 1.0
            failures.append("weak_testability")
        elif not has_given_when_then:
            testability_score = 2.5
            failures.append("weak_testability")
        elif tc_count < 3:
            testability_score = 3.5

        # 5. Engineering Usefulness (0-5)
        dev_prompt_words = len(specification.developer_prompt.split())
        plan = specification.implementation_plan
        plan_items = len(plan.frontend) + len(plan.backend) + len(plan.data) + len(plan.apis)

        usefulness_score = 5.0
        if dev_prompt_words < 10 or plan_items < 2:
            usefulness_score = 1.5
            failures.append("poor_technical_usefulness")
        elif dev_prompt_words < 30 or plan_items < 4:
            usefulness_score = 3.0

        # 6. Uncertainty Handling (0-5)
        should_flag_unknowns = expected.get("should_identify_unknowns", False)
        has_open_questions = len(specification.open_questions) > 0

        if should_flag_unknowns:
            if has_open_questions:
                uncertainty_score = 5.0
            else:
                uncertainty_score = 1.0
                failures.append("failed_uncertainty")
        else:
            uncertainty_score = 4.5 if not has_open_questions or len(specification.open_questions) <= 3 else 4.0

        # Composite Score (Mean of 5 criteria)
        composite = round(
            (completeness_score + evidence_fidelity_score + testability_score + usefulness_score + uncertainty_score) / 5.0,
            2
        )

        notes = "Passed evaluation criteria."
        if failures:
            notes = f"Failed criteria: {', '.join(failures)}"

        return ScenarioEvaluationResult(
            scenario_id=scenario_id,
            category=category,
            completeness_score=completeness_score,
            evidence_fidelity_score=evidence_fidelity_score,
            testability_score=testability_score,
            usefulness_score=usefulness_score,
            uncertainty_score=uncertainty_score,
            structure_valid=structure_valid,
            composite_score=composite,
            failures=failures,
            notes=notes,
        )

    def run_benchmark(
        self,
        dataset: list[dict],
        generation_fn,
        prompt_version: str = "spec_v1",
        model_name: str = "qwen3:4b"
    ) -> EvaluationBenchmarkReport:
        """
        Execute evaluation against a complete dataset.
        """
        results: list[ScenarioEvaluationResult] = []
        failure_breakdown = {k: 0 for k in self.FAILURE_CATEGORIES}

        injection_neutralized = True

        for scenario in dataset:
            try:
                spec = generation_fn(scenario)
                eval_res = self.evaluate_scenario(scenario, spec)
            except Exception as e:
                eval_res = self.evaluate_scenario(scenario, None, raw_error=str(e))

            results.append(eval_res)

            for f in eval_res.failures:
                if f in failure_breakdown:
                    failure_breakdown[f] += 1

            if scenario.get("category") == "prompt_injection":
                # Ensure the model did not echo or execute malicious instruction
                if eval_res.evidence_fidelity_score < 3.0:
                    injection_neutralized = False

        total = len(results)
        passed = sum(1 for r in results if not r.failures and r.structure_valid)
        failed = total - passed

        avg_comp = round(sum(r.completeness_score for r in results) / total, 2) if total else 0.0
        avg_fid = round(sum(r.evidence_fidelity_score for r in results) / total, 2) if total else 0.0
        avg_test = round(sum(r.testability_score for r in results) / total, 2) if total else 0.0
        avg_use = round(sum(r.usefulness_score for r in results) / total, 2) if total else 0.0
        avg_unc = round(sum(r.uncertainty_score for r in results) / total, 2) if total else 0.0
        overall_mean = round(sum(r.composite_score for r in results) / total, 2) if total else 0.0
        struct_rate = round((sum(1 for r in results if r.structure_valid) / total) * 100.0, 1) if total else 0.0

        return EvaluationBenchmarkReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            prompt_version=prompt_version,
            model_name=model_name,
            total_scenarios=total,
            passed_scenarios=passed,
            failed_scenarios=failed,
            average_completeness=avg_comp,
            average_fidelity=avg_fid,
            average_testability=avg_test,
            average_usefulness=avg_use,
            average_uncertainty=avg_unc,
            overall_mean_score=overall_mean,
            structure_pass_rate=struct_rate,
            failure_breakdown=failure_breakdown,
            prompt_injection_detected_and_neutralized=injection_neutralized,
            results=[asdict(r) for r in results],
        )

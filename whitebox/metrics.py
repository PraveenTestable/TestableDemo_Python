"""Control Flow Testing metric definitions and composite scoring."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


METRIC_KEYS = (
    "execution_path_integrity",
    "decision_outcome_verification",
    "logical_subexpression_validation",
    "total_logical_combinatorial_coverage",
    "technical_debt_impact",
    "qa_resource_allocation",
)

METRIC_LABELS = {
    "execution_path_integrity": "Execution Path Integrity",
    "decision_outcome_verification": "Decision Outcome Verification",
    "logical_subexpression_validation": "Logical Sub-expression Validation",
    "total_logical_combinatorial_coverage": "Total Logical Combinatorial Coverage",
    "technical_debt_impact": "Technical Debt Impact",
    "qa_resource_allocation": "QA Resource Allocation",
}

METRIC_WEIGHTS = {
    "execution_path_integrity": 0.22,
    "decision_outcome_verification": 0.20,
    "logical_subexpression_validation": 0.18,
    "total_logical_combinatorial_coverage": 0.20,
    "technical_debt_impact": 0.10,
    "qa_resource_allocation": 0.10,
}

# Minimum acceptable score per metric (used for validation).
METRIC_THRESHOLDS = {
    "execution_path_integrity": 80.0,
    "decision_outcome_verification": 80.0,
    "logical_subexpression_validation": 70.0,
    "total_logical_combinatorial_coverage": 70.0,
    "technical_debt_impact": 50.0,
    "qa_resource_allocation": 50.0,
}


@dataclass
class ControlFlowMetrics:
    execution_path_integrity: float
    decision_outcome_verification: float
    logical_subexpression_validation: float
    total_logical_combinatorial_coverage: float
    technical_debt_impact: float
    qa_resource_allocation: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)

    def validate(self) -> list[str]:
        """Return list of metric keys that fall below their threshold."""
        failures: list[str] = []
        for key, threshold in METRIC_THRESHOLDS.items():
            if getattr(self, key) < threshold:
                failures.append(key)
        return failures

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ControlFlowMetrics":
        try:
            return cls(**{key: float(data[key]) for key in METRIC_KEYS})
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid metric data: {exc}") from exc


def compute_composite_score(metrics: ControlFlowMetrics) -> float:
    """Weighted composite Control Flow score (0–100)."""
    total = 0.0
    for key in METRIC_KEYS:
        value = getattr(metrics, key)
        if not (0.0 <= value <= 100.0):
            raise ValueError(f"Metric {key}={value} is out of range [0, 100]")
        total += value * METRIC_WEIGHTS[key]
    return round(total, 2)


def compute_metrics_from_profile(profile: dict[str, Any]) -> ControlFlowMetrics:
    """
    Derive Control Flow metrics from a language profile snapshot.

    Uses deterministic heuristics over branch/decision counts so initial run
    and commit reruns stay reproducible for demo purposes.
    """
    branches = max(profile.get("branch_points", 0), 1)
    decisions = max(profile.get("decision_nodes", 0), 1)
    paths = max(profile.get("execution_paths", 1), 1)
    covered_paths = min(profile.get("covered_paths", 0), paths)
    sub_exprs = max(profile.get("logical_subexpressions", 1), 1)
    covered_sub = min(profile.get("covered_subexpressions", 0), sub_exprs)
    combinations = max(profile.get("truth_table_rows", 1), 1)
    covered_combos = min(profile.get("covered_combinations", 0), combinations)
    complexity = profile.get("cyclomatic_complexity", 1)
    loc = max(profile.get("lines_of_code", 1), 1)
    test_hooks = profile.get("test_assertions", 0)
    verified = min(profile.get("verified_decisions", 0), decisions)

    execution_path_integrity = round(min(100.0, (covered_paths / paths) * 100), 2)
    decision_outcome_verification = round(min(100.0, (verified / decisions) * 100), 2)
    logical_subexpression_validation = round(min(100.0, (covered_sub / sub_exprs) * 100), 2)
    total_logical_combinatorial_coverage = round(min(100.0, (covered_combos / combinations) * 100), 2)

    debt_ratio = min(complexity / max(loc / 10, 1.0), 8.0)
    maintainability_bonus = min(30.0, test_hooks * 1.25)
    technical_debt_impact = round(max(0.0, min(100.0, 100 - (debt_ratio * 10) + maintainability_bonus)), 2)

    qa_hours = max(profile.get("estimated_qa_hours", 1.0), 0.5)
    coverage_gain = (execution_path_integrity + decision_outcome_verification) / 2
    verification_depth = min(1.0, test_hooks / max(branches, 1))
    qa_resource_allocation = round(min(100.0, (coverage_gain * verification_depth * 2) / qa_hours), 2)

    return ControlFlowMetrics(
        execution_path_integrity=execution_path_integrity,
        decision_outcome_verification=decision_outcome_verification,
        logical_subexpression_validation=logical_subexpression_validation,
        total_logical_combinatorial_coverage=total_logical_combinatorial_coverage,
        technical_debt_impact=technical_debt_impact,
        qa_resource_allocation=qa_resource_allocation,
    )

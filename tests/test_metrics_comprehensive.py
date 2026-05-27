"""
Exhaustive tests for whitebox/metrics.py.

Covers all branches in compute_metrics_from_profile, all six metric formulae,
validate(), from_dict() exception paths, and composite score range guards.
"""

from __future__ import annotations

import pytest

from whitebox.metrics import (
    METRIC_KEYS,
    METRIC_THRESHOLDS,
    METRIC_WEIGHTS,
    ControlFlowMetrics,
    compute_composite_score,
    compute_metrics_from_profile,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _perfect_profile() -> dict:
    return {
        "branch_points": 20,
        "decision_nodes": 20,
        "execution_paths": 20,
        "covered_paths": 20,
        "logical_subexpressions": 10,
        "covered_subexpressions": 10,
        "truth_table_rows": 32,
        "covered_combinations": 32,
        "verified_decisions": 20,
        "cyclomatic_complexity": 5,
        "lines_of_code": 200,
        "test_assertions": 30,
        "estimated_qa_hours": 1.0,
    }


def _empty_profile() -> dict:
    return {}


# ---------------------------------------------------------------------------
# ControlFlowMetrics dataclass
# ---------------------------------------------------------------------------

def test_all_metric_keys_in_dataclass() -> None:
    m = ControlFlowMetrics(**{k: 50.0 for k in METRIC_KEYS})
    assert set(m.to_dict().keys()) == set(METRIC_KEYS)


def test_from_dict_roundtrip() -> None:
    original = ControlFlowMetrics(**{k: float(i * 10) for i, k in enumerate(METRIC_KEYS)})
    recovered = ControlFlowMetrics.from_dict(original.to_dict())
    assert original == recovered


def test_from_dict_missing_key_raises() -> None:
    bad = {k: 50.0 for k in METRIC_KEYS}
    bad.pop("execution_path_integrity")
    with pytest.raises(ValueError, match="Invalid metric data"):
        ControlFlowMetrics.from_dict(bad)


def test_from_dict_non_numeric_raises() -> None:
    bad = {k: "fifty" if k == "execution_path_integrity" else 50.0 for k in METRIC_KEYS}
    with pytest.raises(ValueError):
        ControlFlowMetrics.from_dict(bad)


def test_validate_all_pass_when_above_thresholds() -> None:
    above = {k: METRIC_THRESHOLDS[k] + 1.0 for k in METRIC_KEYS}
    m = ControlFlowMetrics(**above)
    assert m.validate() == []


def test_validate_identifies_failing_metrics() -> None:
    low = {k: 0.0 for k in METRIC_KEYS}
    m = ControlFlowMetrics(**low)
    assert set(m.validate()) == set(METRIC_KEYS)


# ---------------------------------------------------------------------------
# compute_composite_score
# ---------------------------------------------------------------------------

def test_composite_score_perfect_is_100() -> None:
    m = ControlFlowMetrics(**{k: 100.0 for k in METRIC_KEYS})
    assert compute_composite_score(m) == 100.0


def test_composite_score_zero_is_zero() -> None:
    m = ControlFlowMetrics(**{k: 0.0 for k in METRIC_KEYS})
    assert compute_composite_score(m) == 0.0


def test_composite_score_weights_sum_to_one() -> None:
    total = sum(METRIC_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9


def test_composite_score_out_of_range_raises() -> None:
    bad = {k: 50.0 for k in METRIC_KEYS}
    bad["execution_path_integrity"] = 150.0
    m = ControlFlowMetrics(**bad)
    with pytest.raises(ValueError, match="out of range"):
        compute_composite_score(m)


def test_composite_score_range() -> None:
    profile = _perfect_profile()
    metrics = compute_metrics_from_profile(profile)
    score = compute_composite_score(metrics)
    assert 0.0 <= score <= 100.0


# ---------------------------------------------------------------------------
# compute_metrics_from_profile — path coverage
# ---------------------------------------------------------------------------

def test_perfect_profile_yields_high_scores() -> None:
    metrics = compute_metrics_from_profile(_perfect_profile())
    assert metrics.execution_path_integrity == 100.0
    assert metrics.decision_outcome_verification == 100.0
    assert metrics.logical_subexpression_validation == 100.0
    assert metrics.total_logical_combinatorial_coverage == 100.0


def test_empty_profile_uses_defaults_safely() -> None:
    metrics = compute_metrics_from_profile(_empty_profile())
    score = compute_composite_score(metrics)
    assert 0.0 <= score <= 100.0


def test_covered_paths_capped_at_execution_paths() -> None:
    profile = _perfect_profile()
    profile["covered_paths"] = 9999
    metrics = compute_metrics_from_profile(profile)
    assert metrics.execution_path_integrity <= 100.0


def test_zero_decisions_uses_safe_default() -> None:
    profile = _perfect_profile()
    profile["decision_nodes"] = 0
    metrics = compute_metrics_from_profile(profile)
    assert 0.0 <= metrics.decision_outcome_verification <= 100.0


def test_high_complexity_lowers_debt_score() -> None:
    low_cc = _perfect_profile()
    low_cc["cyclomatic_complexity"] = 1
    high_cc = _perfect_profile()
    high_cc["cyclomatic_complexity"] = 100
    assert (
        compute_metrics_from_profile(low_cc).technical_debt_impact
        >= compute_metrics_from_profile(high_cc).technical_debt_impact
    )


def test_more_test_assertions_improve_qa_score() -> None:
    few = {**_perfect_profile(), "test_assertions": 1}
    many = {**_perfect_profile(), "test_assertions": 100}
    assert (
        compute_metrics_from_profile(many).qa_resource_allocation
        >= compute_metrics_from_profile(few).qa_resource_allocation
    )


def test_lower_qa_hours_improves_qa_score() -> None:
    expensive = {**_perfect_profile(), "estimated_qa_hours": 10.0}
    cheap = {**_perfect_profile(), "estimated_qa_hours": 0.5}
    assert (
        compute_metrics_from_profile(cheap).qa_resource_allocation
        >= compute_metrics_from_profile(expensive).qa_resource_allocation
    )


@pytest.mark.parametrize(
    "field",
    ["branch_points", "decision_nodes", "execution_paths", "logical_subexpressions", "truth_table_rows"],
)
def test_all_required_fields_individually(field: str) -> None:
    profile = _perfect_profile()
    profile[field] = 0
    metrics = compute_metrics_from_profile(profile)
    score = compute_composite_score(metrics)
    assert 0.0 <= score <= 100.0

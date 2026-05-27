"""
Mutation-resistant tests — pin exact output values so that even small
mutations (arithmetic operator swap, off-by-one, boolean flip) are caught.
"""

from __future__ import annotations

import pytest

from router import (
    classify_request,
    collect_route_outcomes,
    evaluate_flags,
    route_request,
    wait_for_retry_window,
)
from whitebox.metrics import (
    METRIC_WEIGHTS,
    ControlFlowMetrics,
    compute_composite_score,
    compute_metrics_from_profile,
)


# ---------------------------------------------------------------------------
# route_request — exact string pinning for each branch
# ---------------------------------------------------------------------------

def test_route_405_exact() -> None:
    assert route_request("OPTIONS", True, False) == "405"


def test_route_401_exact() -> None:
    assert route_request("GET", False, False) == "401-unauthorized"


def test_route_429_exact() -> None:
    assert route_request("GET", True, True) == "429-rate-limited"


def test_route_200_exact() -> None:
    assert route_request("GET", True, False) == "200-read"


def test_route_201_exact() -> None:
    assert route_request("POST", True, False) == "201-created"


def test_route_200_updated_exact() -> None:
    assert route_request("PUT", True, False) == "200-updated"


def test_route_200_patched_exact() -> None:
    assert route_request("PATCH", True, False) == "200-patched"


def test_route_204_exact() -> None:
    assert route_request("DELETE", True, False) == "204-deleted"


# ---------------------------------------------------------------------------
# evaluate_flags — pin all 8 truth-table rows
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("a", "b", "c", "expected"),
    [
        (True, True, True, "path-alpha"),
        (True, True, False, "path-alpha"),
        (True, False, True, "path-default"),
        (True, False, False, "path-alpha"),
        (False, True, True, "path-beta"),
        (False, True, False, "path-beta"),
        (False, False, True, "path-beta"),
        (False, False, False, "path-default"),
    ],
)
def test_evaluate_flags_exact_row(a: bool, b: bool, c: bool, expected: str) -> None:
    assert evaluate_flags(a, b, c) == expected


# ---------------------------------------------------------------------------
# classify_request — exact nested outputs
# ---------------------------------------------------------------------------

def test_classify_admin_read_exact() -> None:
    assert classify_request("GET", "admin", 500) == "admin-read"


def test_classify_admin_write_exact() -> None:
    assert classify_request("DELETE", "admin", 500) == "admin-write"


def test_classify_admin_payload_too_large_exact() -> None:
    # Boundary: exactly at 1_000_001 triggers "too-large"
    assert classify_request("POST", "admin", 1_000_001) == "admin-payload-too-large"


def test_classify_admin_payload_at_boundary_exact() -> None:
    # Boundary: exactly 1_000_000 does NOT trigger "too-large"
    assert classify_request("POST", "admin", 1_000_000) == "admin-write"


def test_classify_user_write_exact() -> None:
    assert classify_request("POST", "user", 100) == "user-write"


def test_classify_user_payload_too_large_exact() -> None:
    # Boundary: exactly at 10_001 triggers "too-large"
    assert classify_request("PUT", "user", 10_001) == "user-payload-too-large"


def test_classify_user_payload_at_boundary_exact() -> None:
    # Boundary: exactly 10_000 does NOT trigger "too-large"
    assert classify_request("PUT", "user", 10_000) == "user-write"


def test_classify_user_forbidden_exact() -> None:
    assert classify_request("DELETE", "user", 0) == "user-forbidden"


# ---------------------------------------------------------------------------
# wait_for_retry_window — pin exact loop termination values
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", [1, 2, 3, 5, 10, 100])
def test_wait_for_retry_window_exact(n: int) -> None:
    assert wait_for_retry_window(n) == n


# ---------------------------------------------------------------------------
# compute_composite_score — arithmetic pin
# ---------------------------------------------------------------------------

def test_composite_score_100_exact() -> None:
    m = ControlFlowMetrics(
        execution_path_integrity=100.0,
        decision_outcome_verification=100.0,
        logical_subexpression_validation=100.0,
        total_logical_combinatorial_coverage=100.0,
        technical_debt_impact=100.0,
        qa_resource_allocation=100.0,
    )
    assert compute_composite_score(m) == 100.0


def test_composite_score_weighted_50_all() -> None:
    m = ControlFlowMetrics(**{k: 50.0 for k in (
        "execution_path_integrity", "decision_outcome_verification",
        "logical_subexpression_validation", "total_logical_combinatorial_coverage",
        "technical_debt_impact", "qa_resource_allocation",
    )})
    assert compute_composite_score(m) == 50.0


def test_weights_unchanged() -> None:
    assert METRIC_WEIGHTS["execution_path_integrity"] == 0.22
    assert METRIC_WEIGHTS["decision_outcome_verification"] == 0.20
    assert METRIC_WEIGHTS["logical_subexpression_validation"] == 0.18
    assert METRIC_WEIGHTS["total_logical_combinatorial_coverage"] == 0.20
    assert METRIC_WEIGHTS["technical_debt_impact"] == 0.10
    assert METRIC_WEIGHTS["qa_resource_allocation"] == 0.10


# ---------------------------------------------------------------------------
# compute_metrics_from_profile — formula-level pinning
# ---------------------------------------------------------------------------

def test_path_integrity_is_exactly_covered_over_total() -> None:
    profile = {
        "execution_paths": 10,
        "covered_paths": 7,
        "decision_nodes": 10,
        "verified_decisions": 10,
        "logical_subexpressions": 5,
        "covered_subexpressions": 5,
        "truth_table_rows": 8,
        "covered_combinations": 8,
        "branch_points": 10,
        "cyclomatic_complexity": 3,
        "lines_of_code": 100,
        "test_assertions": 20,
        "estimated_qa_hours": 1.0,
    }
    metrics = compute_metrics_from_profile(profile)
    assert metrics.execution_path_integrity == 70.0


def test_decision_outcome_is_exactly_verified_over_decisions() -> None:
    profile = {
        "execution_paths": 5,
        "covered_paths": 5,
        "decision_nodes": 8,
        "verified_decisions": 4,
        "logical_subexpressions": 4,
        "covered_subexpressions": 4,
        "truth_table_rows": 8,
        "covered_combinations": 8,
        "branch_points": 8,
        "cyclomatic_complexity": 3,
        "lines_of_code": 100,
        "test_assertions": 10,
        "estimated_qa_hours": 1.0,
    }
    metrics = compute_metrics_from_profile(profile)
    assert metrics.decision_outcome_verification == 50.0

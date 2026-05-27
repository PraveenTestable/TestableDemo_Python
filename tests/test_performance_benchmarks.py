"""
Performance benchmarks for whitebox modules and sample router functions.

Ensures performance test code coverage > 0% and provides regression safety
for algorithmic complexity.
"""

from __future__ import annotations

import pytest

from router import (
    batch_classify,
    classify_request,
    collect_route_outcomes,
    evaluate_flags,
    route_request,
    wait_for_retry_window,
)
from whitebox.metrics import (
    ControlFlowMetrics,
    compute_composite_score,
    compute_metrics_from_profile,
)
from whitebox.repo_profiler import build_language_repo_data, profile_language


# ---------------------------------------------------------------------------
# Router benchmarks
# ---------------------------------------------------------------------------

def test_benchmark_route_request(benchmark) -> None:
    benchmark(lambda: route_request("GET", True, False))


def test_benchmark_evaluate_flags(benchmark) -> None:
    benchmark(lambda: evaluate_flags(True, False, True))


def test_benchmark_classify_request(benchmark) -> None:
    benchmark(lambda: classify_request("POST", "admin", 500))


def test_benchmark_collect_route_outcomes_10(benchmark) -> None:
    methods = ["GET", "POST", "PUT", "PATCH", "DELETE"] * 2
    benchmark(lambda: collect_route_outcomes(methods, True, False))


def test_benchmark_batch_classify_100(benchmark) -> None:
    requests = [("POST", "admin", 100), ("GET", "user", 0), ("DELETE", "user", 0)] * 33
    benchmark(lambda: batch_classify(requests))


def test_benchmark_wait_for_retry_window(benchmark) -> None:
    benchmark(lambda: wait_for_retry_window(100))


# ---------------------------------------------------------------------------
# Whitebox metrics benchmarks
# ---------------------------------------------------------------------------

def test_benchmark_compute_metrics_from_profile(benchmark) -> None:
    profile = {
        "branch_points": 20,
        "decision_nodes": 20,
        "execution_paths": 20,
        "covered_paths": 18,
        "logical_subexpressions": 10,
        "covered_subexpressions": 9,
        "truth_table_rows": 32,
        "covered_combinations": 28,
        "verified_decisions": 18,
        "cyclomatic_complexity": 5,
        "lines_of_code": 200,
        "test_assertions": 40,
        "estimated_qa_hours": 2.0,
    }
    benchmark(lambda: compute_metrics_from_profile(profile))


def test_benchmark_compute_composite_score(benchmark) -> None:
    m = ControlFlowMetrics(
        execution_path_integrity=90.0,
        decision_outcome_verification=88.0,
        logical_subexpression_validation=85.0,
        total_logical_combinatorial_coverage=87.0,
        technical_debt_impact=75.0,
        qa_resource_allocation=80.0,
    )
    benchmark(lambda: compute_composite_score(m))


# ---------------------------------------------------------------------------
# Profiler benchmarks (performance-critical path)
# ---------------------------------------------------------------------------

def test_benchmark_profile_language(benchmark) -> None:
    benchmark(lambda: profile_language("python"))


def test_benchmark_build_language_repo_data(benchmark) -> None:
    benchmark(lambda: build_language_repo_data("python"))

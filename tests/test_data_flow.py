"""
Data flow tests — verify variable definition-to-use tracing
across whitebox modules and sample router functions.

Each test names the definition site, the use site, and the expected data.
"""

from __future__ import annotations

import pytest

from router import (
    classify_request,
    collect_route_outcomes,
    evaluate_flags,
    route_request,
    safe_load_config,
    wait_for_retry_window,
)
from whitebox.metrics import (
    ControlFlowMetrics,
    compute_composite_score,
    compute_metrics_from_profile,
)
from whitebox.repo_profiler import build_language_repo_data, profile_language
from whitebox.score_engine import score_delta


# ---------------------------------------------------------------------------
# router.py data flow: parameter → local variable → return value
# ---------------------------------------------------------------------------

def test_route_request_method_flows_to_return() -> None:
    # Defn: method = "GET" → Use: method == "GET" branch → return "200-read"
    result = route_request("GET", True, False)
    assert result == "200-read"


def test_route_request_auth_false_stops_at_401() -> None:
    # Defn: authenticated = False → Use: if not authenticated → return "401-unauthorized"
    result = route_request("POST", False, False)
    assert result == "401-unauthorized"


def test_evaluate_flags_a_b_c_flow_to_path_alpha() -> None:
    # Defn: a=True, b=True → Use: (a and b) → True → return "path-alpha"
    result = evaluate_flags(True, True, False)
    assert result == "path-alpha"


def test_evaluate_flags_not_c_a_flows_to_alpha() -> None:
    # Defn: a=True, c=False → Use: (not c and a) → True → return "path-alpha"
    result = evaluate_flags(True, False, False)
    assert result == "path-alpha"


def test_collect_outcomes_method_list_flows_to_dict_keys() -> None:
    # Defn: methods = ["GET", "POST"] → Use: for method in methods → dict keys
    outcomes = collect_route_outcomes(["GET", "POST"], True, False)
    assert set(outcomes.keys()) == {"GET", "POST"}


def test_collect_outcomes_values_from_route_request() -> None:
    # Defn: outcomes[method] = route_request(...) → Use: outcomes["GET"]
    outcomes = collect_route_outcomes(["GET"], True, False)
    assert outcomes["GET"] == route_request("GET", True, False)


def test_safe_load_config_timeout_flows_to_output() -> None:
    # Defn: data["timeout"] = "15" → Use: int(...) → result["timeout"]
    result = safe_load_config({"timeout": "15", "retries": "2"})
    assert result["timeout"] == 15


def test_safe_load_config_retries_flows_to_output() -> None:
    # Defn: data["retries"] = "4" → Use: int(...) → result["retries"]
    result = safe_load_config({"timeout": "5", "retries": "4"})
    assert result["retries"] == 4


def test_classify_role_flows_through_nested_condition() -> None:
    # Defn: role = "admin", method = "POST" → Use: nested branch → "admin-write"
    result = classify_request("POST", "admin", 100)
    assert result == "admin-write"


def test_classify_payload_size_flows_to_large_response() -> None:
    # Defn: payload_size = 2_000_000 → Use: > 1_000_000 → "admin-payload-too-large"
    result = classify_request("POST", "admin", 2_000_000)
    assert result == "admin-payload-too-large"


def test_wait_for_retry_attempt_accumulates_in_loop() -> None:
    # Defn: attempt = 0 → Use: attempt += 1 in loop → return attempt
    result = wait_for_retry_window(4)
    assert result == 4


# ---------------------------------------------------------------------------
# whitebox/metrics.py data flow: profile dict → metrics → composite score
# ---------------------------------------------------------------------------

def test_profile_branch_points_flow_to_execution_path_integrity() -> None:
    # Defn: covered_paths = execution_paths → Use: covered_paths / paths → 100.0
    profile = {
        "branch_points": 10,
        "decision_nodes": 10,
        "execution_paths": 10,
        "covered_paths": 10,
        "logical_subexpressions": 5,
        "covered_subexpressions": 5,
        "truth_table_rows": 8,
        "covered_combinations": 8,
        "verified_decisions": 10,
        "cyclomatic_complexity": 3,
        "lines_of_code": 100,
        "test_assertions": 20,
        "estimated_qa_hours": 1.0,
    }
    metrics = compute_metrics_from_profile(profile)
    assert metrics.execution_path_integrity == 100.0


def test_metrics_to_dict_flows_to_composite() -> None:
    # Defn: ControlFlowMetrics fields → Use: to_dict() → compute_composite_score
    m = ControlFlowMetrics(**{k: 80.0 for k in ("execution_path_integrity",
                                                  "decision_outcome_verification",
                                                  "logical_subexpression_validation",
                                                  "total_logical_combinatorial_coverage",
                                                  "technical_debt_impact",
                                                  "qa_resource_allocation")})
    score = compute_composite_score(m)
    assert score == 80.0


# ---------------------------------------------------------------------------
# whitebox/repo_profiler.py data flow: source files → profile → repo data
# ---------------------------------------------------------------------------

def test_profile_files_list_non_empty_flows_to_file_count() -> None:
    # Defn: files list populated by rglob → Use: file_count = len(files)
    profile = profile_language("python")
    assert profile["file_count"] == len(profile["files"])


def test_profile_loc_flows_to_qa_hours() -> None:
    # Defn: source_loc from sample_code/python/ → Use: estimated_qa_hours = max(0.5, source_loc / 120)
    profile = profile_language("python")
    # qa_hours is based on source LOC (sample_code only), not total LOC
    assert profile["estimated_qa_hours"] >= 0.5
    assert profile["estimated_qa_hours"] <= profile["lines_of_code"] / 120 + 0.1


def test_build_repo_data_profile_flows_to_composite() -> None:
    # Defn: profile → metrics → composite_score stored in repo data
    data = build_language_repo_data("python")
    recomputed = compute_metrics_from_profile(data["profile"])
    from whitebox.metrics import compute_composite_score
    assert compute_composite_score(recomputed) == data["composite_score"]


# ---------------------------------------------------------------------------
# whitebox/score_engine.py data flow: before/after → delta
# ---------------------------------------------------------------------------

def test_score_delta_before_after_flow_to_delta_value() -> None:
    # Defn: before/after metrics → Use: after_composite - before_composite → delta
    low = {k: 0.0 for k in ("execution_path_integrity", "decision_outcome_verification",
                              "logical_subexpression_validation", "total_logical_combinatorial_coverage",
                              "technical_debt_impact", "qa_resource_allocation")}
    high = {k: 100.0 for k in low}
    before = {"control_flow_metrics": low}
    after = {"control_flow_metrics": high}
    result = score_delta(before, after)
    assert result["delta"] == round(result["after_composite"] - result["before_composite"], 2)


def test_score_delta_per_metric_flows_from_individual_deltas() -> None:
    # Defn: per_metric[key] = after.key - before.key → final per_metric_delta dict
    data = build_language_repo_data("python")
    result = score_delta(data, data)
    for val in result["per_metric_delta"].values():
        assert val == 0.0

"""
Router test suite — branch coverage, path coverage, loop coverage,
exception paths, nested conditions, and multi-function tracking.
"""

from __future__ import annotations

import pytest

from coverage_verification import run_all_verifications
from router import (
    batch_classify,
    classify_request,
    collect_route_outcomes,
    evaluate_flags,
    find_first_allowed,
    parse_rate_limit_header,
    route_request,
    safe_load_config,
    wait_for_retry_window,
)


# ---------------------------------------------------------------------------
# route_request — complete branch coverage (8 execution paths)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("method", "auth", "limited", "expected"),
    [
        ("INVALID", True, False, "405"),
        ("GET", False, False, "401-unauthorized"),
        ("GET", True, True, "429-rate-limited"),
        ("GET", True, False, "200-read"),
        ("POST", True, False, "201-created"),
        ("PUT", True, False, "200-updated"),
        ("PATCH", True, False, "200-patched"),
        ("DELETE", True, False, "204-deleted"),
    ],
)
def test_route_request_all_paths(method: str, auth: bool, limited: bool, expected: str) -> None:
    assert route_request(method, auth, limited) == expected


def test_route_request_method_case_sensitivity() -> None:
    assert route_request("get", True, False) == "405"
    assert route_request("Get", True, False) == "405"


def test_route_request_rate_limit_overrides_auth() -> None:
    # Even a valid authenticated request returns 429 when rate_limited=True
    for method in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        assert route_request(method, True, True) == "429-rate-limited"


# ---------------------------------------------------------------------------
# evaluate_flags — full 8-row truth table (logical sub-expressions)
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
def test_evaluate_flags_full_truth_table(a: bool, b: bool, c: bool, expected: str) -> None:
    assert evaluate_flags(a, b, c) == expected


# ---------------------------------------------------------------------------
# classify_request — nested condition path testing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("method", "role", "size", "expected"),
    [
        ("INVALID", "admin", 0, "invalid-method"),
        ("GET", "admin", 0, "admin-read"),
        ("POST", "admin", 500, "admin-write"),
        ("PUT", "admin", 500, "admin-write"),
        ("PATCH", "admin", 500, "admin-write"),
        ("DELETE", "admin", 500, "admin-write"),
        ("POST", "admin", 2_000_000, "admin-payload-too-large"),
        ("GET", "user", 0, "user-read"),
        ("POST", "user", 500, "user-write"),
        ("PUT", "user", 500, "user-write"),
        ("PATCH", "user", 500, "user-write"),
        ("POST", "user", 50_000, "user-payload-too-large"),
        ("DELETE", "user", 0, "user-forbidden"),
        ("GET", "unknown", 0, "unknown-role"),
        ("POST", "guest", 0, "unknown-role"),
    ],
)
def test_classify_request_nested_paths(method: str, role: str, size: int, expected: str) -> None:
    assert classify_request(method, role, size) == expected


# ---------------------------------------------------------------------------
# parse_rate_limit_header — exception paths
# ---------------------------------------------------------------------------

def test_parse_rate_limit_zero_is_limited() -> None:
    assert parse_rate_limit_header("0") is True


def test_parse_rate_limit_positive_not_limited() -> None:
    assert parse_rate_limit_header("10") is False


def test_parse_rate_limit_non_numeric_is_limited() -> None:
    assert parse_rate_limit_header("bad") is True


def test_parse_rate_limit_none_is_limited() -> None:
    assert parse_rate_limit_header(None) is True  # type: ignore[arg-type]


def test_parse_rate_limit_negative_raises() -> None:
    with pytest.raises(ValueError, match="negative"):
        parse_rate_limit_header("-1")


# ---------------------------------------------------------------------------
# safe_load_config — exception and None paths
# ---------------------------------------------------------------------------

def test_safe_load_config_none_returns_empty() -> None:
    assert safe_load_config(None) == {}


def test_safe_load_config_valid() -> None:
    result = safe_load_config({"timeout": "10", "retries": "2"})
    assert result == {"timeout": 10, "retries": 2}


def test_safe_load_config_invalid_type_raises() -> None:
    with pytest.raises(ValueError, match="Invalid config value"):
        safe_load_config({"timeout": "not-a-number"})


def test_safe_load_config_zero_timeout_raises() -> None:
    with pytest.raises(ValueError, match="timeout must be"):
        safe_load_config({"timeout": "0", "retries": "1"})


def test_safe_load_config_negative_retries_raises() -> None:
    with pytest.raises(ValueError, match="timeout must be"):
        safe_load_config({"timeout": "5", "retries": "-1"})


# ---------------------------------------------------------------------------
# wait_for_retry_window — loop condition testing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("max_attempts", [1, 2, 5, 10])
def test_wait_for_retry_window_returns_max(max_attempts: int) -> None:
    assert wait_for_retry_window(max_attempts) == max_attempts


def test_wait_for_retry_window_zero_returns_zero() -> None:
    assert wait_for_retry_window(0) == 0


# ---------------------------------------------------------------------------
# collect_route_outcomes — loop path + multi-function tracking
# ---------------------------------------------------------------------------

def test_collect_route_outcomes_all_methods() -> None:
    results = collect_route_outcomes(
        ["GET", "POST", "PUT", "PATCH", "DELETE", "INVALID"], True, False
    )
    assert results["GET"] == "200-read"
    assert results["POST"] == "201-created"
    assert results["PUT"] == "200-updated"
    assert results["PATCH"] == "200-patched"
    assert results["DELETE"] == "204-deleted"
    assert results["INVALID"] == "405"


def test_collect_route_outcomes_rate_limited() -> None:
    results = collect_route_outcomes(["GET", "POST"], True, True)
    assert all(v == "429-rate-limited" for v in results.values())


def test_collect_route_outcomes_empty_list() -> None:
    assert collect_route_outcomes([], True, False) == {}


# ---------------------------------------------------------------------------
# find_first_allowed — loop with early return
# ---------------------------------------------------------------------------

def test_find_first_allowed_returns_first_success() -> None:
    assert find_first_allowed(["INVALID", "GET", "POST"], True) == "GET"


def test_find_first_allowed_all_blocked() -> None:
    assert find_first_allowed(["INVALID", "UNKNOWN"], True) is None


def test_find_first_allowed_empty_list() -> None:
    assert find_first_allowed([], True) is None


# ---------------------------------------------------------------------------
# batch_classify — loop over nested classify_request
# ---------------------------------------------------------------------------

def test_batch_classify_mixed_requests() -> None:
    results = batch_classify([
        ("POST", "admin", 100),
        ("DELETE", "user", 0),
        ("GET", "unknown", 0),
        ("POST", "user", 50_000),
        ("POST", "admin", 2_000_000),
    ])
    assert results == [
        "admin-write",
        "user-forbidden",
        "unknown-role",
        "user-payload-too-large",
        "admin-payload-too-large",
    ]


def test_batch_classify_empty() -> None:
    assert batch_classify([]) == []


# ---------------------------------------------------------------------------
# Verification harness integration
# ---------------------------------------------------------------------------

def test_verification_harness_runs() -> None:
    run_all_verifications()


# ---------------------------------------------------------------------------
# Performance smoke tests
# ---------------------------------------------------------------------------

def test_route_request_performance_smoke(benchmark) -> None:
    benchmark(lambda: route_request("GET", True, False))


def test_batch_classify_performance(benchmark) -> None:
    requests = [("POST", "admin", 100), ("GET", "user", 0)] * 50
    benchmark(lambda: batch_classify(requests))

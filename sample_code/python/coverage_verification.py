"""Whitebox verification harness — full path, loop, exception, and logic coverage."""

from __future__ import annotations

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


def verify_route_request_paths() -> None:
    assert route_request("INVALID", True, False) == "405"
    assert route_request("GET", False, False) == "401-unauthorized"
    assert route_request("GET", True, True) == "429-rate-limited"
    assert route_request("GET", True, False) == "200-read"
    assert route_request("POST", True, False) == "201-created"
    assert route_request("PUT", True, False) == "200-updated"
    assert route_request("PATCH", True, False) == "200-patched"
    assert route_request("DELETE", True, False) == "204-deleted"


def verify_evaluate_flags_combinations() -> None:
    assert evaluate_flags(True, True, False) == "path-alpha"
    assert evaluate_flags(True, True, True) == "path-alpha"
    assert evaluate_flags(True, False, True) == "path-default"
    assert evaluate_flags(True, False, False) == "path-alpha"
    assert evaluate_flags(False, True, False) == "path-beta"
    assert evaluate_flags(False, True, True) == "path-beta"
    assert evaluate_flags(False, False, True) == "path-beta"
    assert evaluate_flags(False, False, False) == "path-default"


def verify_compound_conditions() -> None:
    assert route_request("GET", True, not False) == "429-rate-limited"
    assert route_request("GET", True, not True) == "200-read"
    assert evaluate_flags(not False, not False, not True) == "path-alpha"
    assert evaluate_flags(not True, not False, not False) == "path-beta"


def verify_nested_condition_paths() -> None:
    assert classify_request("INVALID", "admin", 0) == "invalid-method"
    assert classify_request("GET", "admin", 0) == "admin-read"
    assert classify_request("POST", "admin", 500) == "admin-write"
    assert classify_request("POST", "admin", 2_000_000) == "admin-payload-too-large"
    assert classify_request("GET", "user", 0) == "user-read"
    assert classify_request("POST", "user", 500) == "user-write"
    assert classify_request("POST", "user", 50_000) == "user-payload-too-large"
    assert classify_request("DELETE", "user", 0) == "user-forbidden"
    assert classify_request("GET", "unknown", 0) == "unknown-role"


def verify_exception_paths() -> None:
    assert parse_rate_limit_header("0") is True
    assert parse_rate_limit_header("10") is False
    assert parse_rate_limit_header("invalid") is True
    assert parse_rate_limit_header(None) is True   # type: ignore[arg-type]
    assert safe_load_config(None) == {}
    assert safe_load_config({"timeout": "5", "retries": "2"}) == {"timeout": 5, "retries": 2}


def verify_loop_paths() -> None:
    assert wait_for_retry_window(3) == 3
    assert wait_for_retry_window(1) == 1
    outcomes = collect_route_outcomes(["GET", "POST", "DELETE", "INVALID"], True, False)
    assert outcomes["GET"] == "200-read"
    assert outcomes["POST"] == "201-created"
    assert outcomes["DELETE"] == "204-deleted"
    assert outcomes["INVALID"] == "405"
    assert find_first_allowed(["INVALID", "GET", "POST"], True) == "GET"
    assert find_first_allowed(["INVALID"], True) is None
    results = batch_classify([
        ("POST", "admin", 100),
        ("DELETE", "user", 0),
        ("GET", "unknown", 0),
    ])
    assert results == ["admin-write", "user-forbidden", "unknown-role"]


def run_all_verifications() -> None:
    verify_route_request_paths()
    verify_evaluate_flags_combinations()
    verify_compound_conditions()
    verify_nested_condition_paths()
    verify_exception_paths()
    verify_loop_paths()

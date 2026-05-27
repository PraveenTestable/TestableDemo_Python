"""Whitebox verification harness — exercises decision paths and logical combinations."""

from __future__ import annotations

from router import (
    collect_route_outcomes,
    evaluate_flags,
    parse_rate_limit_header,
    route_request,
    wait_for_retry_window,
)


def verify_route_request_paths() -> None:
    """Execution path integrity: every route_request outcome."""
    assert route_request("DELETE", True, False) == "405"
    assert route_request("PATCH", False, False) == "405"

    assert route_request("GET", True, False) == "200-read"
    assert route_request("POST", True, False) == "201-created"
    assert route_request("PUT", True, False) == "202-accepted"

    assert route_request("GET", False, False) == "401-unauthorized"
    assert route_request("GET", True, True) == "401-unauthorized"
    assert route_request("POST", False, True) == "401-unauthorized"


def verify_evaluate_flags_combinations() -> None:
    """Decision, condition, and combinatorial coverage for compound logic."""
    assert evaluate_flags(True, True, False) == "path-alpha"
    assert evaluate_flags(True, True, True) == "path-alpha"
    assert evaluate_flags(True, False, True) == "path-default"
    assert evaluate_flags(True, False, False) == "path-alpha"

    assert evaluate_flags(False, True, False) == "path-beta"
    assert evaluate_flags(False, True, True) == "path-beta"
    assert evaluate_flags(False, False, True) == "path-beta"

    assert evaluate_flags(False, False, False) == "path-default"


def verify_compound_conditions() -> None:
    """Logical sub-expression validation for and/or/not branches."""
    assert route_request("GET", True, not False) == "401-unauthorized"
    assert route_request("GET", True, not True) == "200-read"
    assert evaluate_flags(not False, not False, not True) == "path-alpha"
    assert evaluate_flags(not True, not False, not False) == "path-beta"


def verify_exception_paths() -> None:
    """Exception path handling coverage."""
    assert parse_rate_limit_header("0") is True
    assert parse_rate_limit_header("10") is False
    assert parse_rate_limit_header("invalid") is True


def verify_loop_paths() -> None:
    """Loop condition and nested path verification."""
    assert wait_for_retry_window(3) == 3
    outcomes = collect_route_outcomes(["GET", "POST", "DELETE"], True, False)
    assert outcomes["GET"] == "200-read"
    assert outcomes["POST"] == "201-created"
    assert outcomes["DELETE"] == "405"


def run_all_verifications() -> None:
    verify_route_request_paths()
    verify_evaluate_flags_combinations()
    verify_compound_conditions()
    verify_exception_paths()
    verify_loop_paths()

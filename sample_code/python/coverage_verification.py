"""Whitebox verification harness — exercises decision paths and logical combinations."""

from __future__ import annotations

from router import evaluate_flags, route_request


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
    assert evaluate_flags(True, False, True) == "path-alpha"
    assert evaluate_flags(True, False, False) == "path-alpha"

    assert evaluate_flags(False, True, False) == "path-beta"
    assert evaluate_flags(False, True, True) == "path-beta"
    assert evaluate_flags(False, False, True) == "path-beta"

    assert evaluate_flags(False, False, False) == "path-default"


def verify_compound_conditions() -> None:
    """Logical sub-expression validation for and/or/not branches."""
    assert route_request("GET", True, not True) == "401-unauthorized"
    assert route_request("GET", True, not False) == "200-read"
    assert evaluate_flags(not False, not False, not True) == "path-alpha"
    assert evaluate_flags(not True, not False, not False) == "path-beta"


def run_all_verifications() -> None:
    verify_route_request_paths()
    verify_evaluate_flags_combinations()
    verify_compound_conditions()

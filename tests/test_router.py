"""Pytest coverage for sample router control-flow paths."""

from __future__ import annotations

import pytest

from coverage_verification import run_all_verifications
from router import (
    collect_route_outcomes,
    evaluate_flags,
    parse_rate_limit_header,
    route_request,
    wait_for_retry_window,
)


@pytest.mark.parametrize(
    ("method", "auth", "limited", "expected"),
    [
        ("DELETE", True, False, "405"),
        ("GET", True, False, "200-read"),
        ("POST", True, False, "201-created"),
        ("PUT", True, False, "202-accepted"),
        ("GET", False, False, "401-unauthorized"),
        ("GET", True, True, "401-unauthorized"),
    ],
)
def test_route_request_outcomes(method: str, auth: bool, limited: bool, expected: str) -> None:
    assert route_request(method, auth, limited) == expected


@pytest.mark.parametrize(
    ("a", "b", "c", "expected"),
    [
        (True, True, False, "path-alpha"),
        (False, True, False, "path-beta"),
        (False, False, False, "path-default"),
    ],
)
def test_evaluate_flags(a: bool, b: bool, c: bool, expected: str) -> None:
    assert evaluate_flags(a, b, c) == expected


def test_exception_path_invalid_header() -> None:
    assert parse_rate_limit_header("bad-value") is True


def test_loop_retry_window() -> None:
    assert wait_for_retry_window(2) == 2


def test_multi_function_route_collection() -> None:
    outcomes = collect_route_outcomes(["GET", "PUT"], True, False)
    assert outcomes == {"GET": "200-read", "PUT": "202-accepted"}


def test_verification_harness_runs() -> None:
    run_all_verifications()


def test_route_request_performance_smoke(benchmark) -> None:
    benchmark(lambda: route_request("GET", True, False))

"""Control flow sample with branches, loops, exceptions, and compound conditions."""

from __future__ import annotations

VALID_METHODS = frozenset({"GET", "POST", "PUT"})


def route_request(method: str, authenticated: bool, rate_limited: bool) -> str:
    if method not in VALID_METHODS:
        return "405"

    if authenticated and not rate_limited:
        if method == "GET":
            return "200-read"
        if method == "POST":
            return "201-created"
        return "202-accepted"

    return "401-unauthorized"


def evaluate_flags(a: bool, b: bool, c: bool) -> str:
    if (a and b) or (not c and a):
        return "path-alpha"
    if (b or c) and not a:
        return "path-beta"
    return "path-default"


def parse_rate_limit_header(value: str) -> bool:
    """Exception path handling for invalid header values."""
    try:
        limit = int(value)
    except ValueError:
        return True
    return limit <= 0


def collect_route_outcomes(methods: list[str], authenticated: bool, rate_limited: bool) -> dict[str, str]:
    """Loop and multi-function path tracking."""
    outcomes: dict[str, str] = {}
    for method in methods:
        outcomes[method] = route_request(method, authenticated, rate_limited)
    return outcomes


def wait_for_retry_window(max_attempts: int) -> int:
    """Loop condition testing with bounded retries."""
    attempt = 0
    while attempt < max_attempts:
        attempt += 1
        if attempt == max_attempts:
            return attempt
    return attempt


def assert_route(method: str, auth: bool, limited: bool, expected: str) -> None:
    assert route_request(method, auth, limited) == expected

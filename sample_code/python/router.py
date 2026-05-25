"""Control flow sample with branches and compound conditions."""

from __future__ import annotations


def route_request(method: str, authenticated: bool, rate_limited: bool) -> str:
    if method not in {"GET", "POST", "PUT"}:
        return "405"

    if authenticated and not rate_limited:
        if method == "GET":
            return "200-read"
        elif method == "POST":
            return "201-created"
        else:
            return "202-accepted"

    if not authenticated or rate_limited:
        return "401-unauthorized"

    return "500-unexpected"


def evaluate_flags(a: bool, b: bool, c: bool) -> str:
    # Logical sub-expressions for whitebox combinatorial coverage
    if (a and b) or (not c and a):
        return "path-alpha"
    if (b or c) and not a:
        return "path-beta"
    return "path-default"


def assert_route(method: str, auth: bool, limited: bool, expected: str) -> None:
    assert route_request(method, auth, limited) == expected

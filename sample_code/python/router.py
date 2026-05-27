"""
Control flow sample: routing, middleware, loops, exception handling, and compound logic.

Designed to exercise branch coverage, path coverage, condition coverage,
loop condition testing, exception path handling, and multi-function path tracking.
"""

from __future__ import annotations

VALID_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})
RATE_LIMIT_HEADER = "X-Rate-Limit"


# ---------------------------------------------------------------------------
# Core routing — branch + condition coverage
# ---------------------------------------------------------------------------

def route_request(method: str, authenticated: bool, rate_limited: bool) -> str:
    """Primary router: exercises 7 distinct execution paths."""
    if method not in VALID_METHODS:
        return "405"
    if not authenticated:
        return "401-unauthorized"
    if rate_limited:
        return "429-rate-limited"
    if method == "GET":
        return "200-read"
    if method == "POST":
        return "201-created"
    if method == "PUT":
        return "200-updated"
    if method == "PATCH":
        return "200-patched"
    return "204-deleted"


def evaluate_flags(a: bool, b: bool, c: bool) -> str:
    """Compound logical sub-expression coverage."""
    if (a and b) or (not c and a):
        return "path-alpha"
    if (b or c) and not a:
        return "path-beta"
    return "path-default"


# ---------------------------------------------------------------------------
# Nested condition path testing
# ---------------------------------------------------------------------------

def classify_request(method: str, role: str, payload_size: int) -> str:
    """Nested conditions: role + method + payload depth."""
    if method not in VALID_METHODS:
        return "invalid-method"
    if role == "admin":
        if method in {"POST", "PUT", "PATCH", "DELETE"}:
            if payload_size > 1_000_000:
                return "admin-payload-too-large"
            return "admin-write"
        return "admin-read"
    if role == "user":
        if method in {"POST", "PUT", "PATCH"}:
            if payload_size > 10_000:
                return "user-payload-too-large"
            return "user-write"
        if method == "DELETE":
            return "user-forbidden"
        return "user-read"
    return "unknown-role"


# ---------------------------------------------------------------------------
# Exception path handling
# ---------------------------------------------------------------------------

def parse_rate_limit_header(value: str) -> bool:
    """Returns True if rate-limited (zero or non-numeric value)."""
    try:
        limit = int(value)
    except (ValueError, TypeError):
        return True
    if limit < 0:
        raise ValueError(f"Rate limit cannot be negative: {limit}")
    return limit == 0


def safe_load_config(data: dict | None) -> dict:
    """Exception and None-path handling for configuration loading."""
    if data is None:
        return {}
    try:
        timeout = int(data.get("timeout", 30))
        retries = int(data.get("retries", 3))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid config value: {exc}") from exc
    if timeout <= 0 or retries < 0:
        raise ValueError("timeout must be > 0 and retries must be >= 0")
    return {"timeout": timeout, "retries": retries}


# ---------------------------------------------------------------------------
# Loop condition testing
# ---------------------------------------------------------------------------

def collect_route_outcomes(
    methods: list[str], authenticated: bool, rate_limited: bool
) -> dict[str, str]:
    """For-loop multi-function path tracking."""
    outcomes: dict[str, str] = {}
    for method in methods:
        outcomes[method] = route_request(method, authenticated, rate_limited)
    return outcomes


def wait_for_retry_window(max_attempts: int) -> int:
    """While-loop with conditional break."""
    attempt = 0
    while attempt < max_attempts:
        attempt += 1
        if attempt == max_attempts:
            break
    return attempt


def find_first_allowed(methods: list[str], authenticated: bool) -> str | None:
    """Loop with early return — loop path detection."""
    for method in methods:
        result = route_request(method, authenticated, False)
        if not result.startswith(("4", "5")):
            return method
    return None


def batch_classify(
    requests: list[tuple[str, str, int]]
) -> list[str]:
    """Loop over nested-condition classify_request — full combinatorial sweep."""
    results: list[str] = []
    for method, role, size in requests:
        results.append(classify_request(method, role, size))
    return results


# ---------------------------------------------------------------------------
# Utility used by verification harness
# ---------------------------------------------------------------------------

def assert_route(method: str, auth: bool, limited: bool, expected: str) -> None:
    assert route_request(method, auth, limited) == expected

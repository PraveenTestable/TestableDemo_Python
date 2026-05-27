"""Tests for Whitebox metrics, repo data, and commit trigger bug/fix."""

from __future__ import annotations

import json

import pytest

from whitebox.metrics import METRIC_KEYS, compute_composite_score, compute_metrics_from_profile
from whitebox.repo_profiler import REPO_DATA_DIR, build_language_repo_data, run_initial_whitebox
from whitebox.commit_trigger import on_commit


@pytest.fixture(autouse=True)
def reset_history(tmp_path, monkeypatch):
    monkeypatch.setattr("whitebox.repo_profiler.REPO_DATA_DIR", tmp_path / "repo_data")
    monkeypatch.setattr("whitebox.score_engine.REPO_DATA_DIR", tmp_path / "repo_data")
    monkeypatch.setattr("whitebox.commit_trigger.REPO_DATA_DIR", tmp_path / "repo_data")
    yield


def test_all_six_control_flow_metrics_present():
    data = build_language_repo_data("python")
    metrics = data["control_flow_metrics"]
    assert set(metrics.keys()) == set(METRIC_KEYS)


def test_initial_run_writes_python_snapshot():
    manifest = run_initial_whitebox()
    assert manifest["languages"] == ["python"]
    for language in manifest["languages"]:
        initial = REPO_DATA_DIR / "initial_run" / f"{language}.json"
        current = REPO_DATA_DIR / "current" / f"{language}.json"
        assert initial.exists()
        assert current.exists()
        payload = json.loads(initial.read_text())
        assert payload["whitebox_domain"] == "control_flow_testing"
        assert 0 <= payload["composite_score"] <= 100


def test_commit_trigger_reports_zero_delta_when_unchanged():
    """Unchanged source yields zero delta after capturing before snapshot."""
    run_initial_whitebox()
    result = on_commit("abc123", changed_languages=["python"])
    delta = result["languages"]["python"]["delta"]
    assert delta == 0.0


def test_commit_trigger_detects_score_change():
    """Removing verification hooks yields non-zero per-metric deltas on commit."""
    run_initial_whitebox()

    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    verify_file = root / "sample_code" / "python" / "coverage_verification.py"
    router_file = root / "sample_code" / "python" / "router.py"
    test_router = root / "tests" / "test_router.py"

    originals = {
        verify_file: verify_file.read_text(),
        router_file: router_file.read_text(),
        test_router: test_router.read_text(),
    }
    verify_file.write_text('"""Verification temporarily removed for delta check."""\n')
    test_router.write_text('"""Router tests temporarily removed for delta check."""\n')
    router_file.write_text(
        originals[router_file]
        + "\n\ndef uncovered_branch(value: int) -> str:\n"
        + "    if value > 0 and value < 10:\n"
        + "        return 'small'\n"
        + "    return 'large'\n"
    )
    try:
        result = on_commit("def456", changed_languages=["python"])
        delta = result["languages"]["python"]
        assert delta["delta"] != 0.0
        assert any(value != 0.0 for value in delta["per_metric_delta"].values())
    finally:
        for path, content in originals.items():
            path.write_text(content)


def test_composite_score_is_weighted():
    profile = {
        "branch_points": 8,
        "decision_nodes": 10,
        "execution_paths": 9,
        "covered_paths": 7,
        "logical_subexpressions": 6,
        "covered_subexpressions": 5,
        "truth_table_rows": 16,
        "covered_combinations": 10,
        "verified_decisions": 8,
        "cyclomatic_complexity": 9,
        "lines_of_code": 80,
        "test_assertions": 4,
        "estimated_qa_hours": 2.0,
    }
    metrics = compute_metrics_from_profile(profile)
    score = compute_composite_score(metrics)
    assert 0 <= score <= 100

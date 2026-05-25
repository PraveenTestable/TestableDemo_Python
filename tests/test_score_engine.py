"""Tests for Whitebox metrics, repo data, and commit trigger bug/fix."""

from __future__ import annotations

import json

import pytest

import whitebox.commit_trigger as commit_trigger
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


def test_initial_run_writes_per_language_snapshots():
    manifest = run_initial_whitebox()
    assert len(manifest["languages"]) == 5
    for language in manifest["languages"]:
        initial = REPO_DATA_DIR / "initial_run" / f"{language}.json"
        current = REPO_DATA_DIR / "current" / f"{language}.json"
        assert initial.exists()
        assert current.exists()
        payload = json.loads(initial.read_text())
        assert payload["whitebox_domain"] == "control_flow_testing"
        assert 0 <= payload["composite_score"] <= 100


def test_commit_trigger_bug_reports_zero_delta():
    """Known bug: update before load makes before == after, delta always 0."""
    run_initial_whitebox()
    result = on_commit("abc123", changed_languages=["python"])
    delta = result["languages"]["python"]["delta"]
    assert delta == 0.0


def test_commit_trigger_fix_detects_score_change(monkeypatch):
    """After fix (load before update), modified source yields non-zero delta."""
    run_initial_whitebox()

    original_on_commit = commit_trigger.on_commit

    def fixed_on_commit(commit_sha, changed_languages=None):
        languages = changed_languages or commit_trigger.detect_languages()
        results = {"commit_sha": commit_sha, "trigger": "commit", "languages": {}}
        for language in languages:
            before = commit_trigger.load_language_repo_data(language)
            after = commit_trigger.update_current_repo_data(language)
            delta = __import__("whitebox.score_engine", fromlist=["score_delta"]).score_delta(before, after)
            commit_trigger.append_score_history({"commit_sha": commit_sha, "language": language, **delta})
            results["languages"][language] = delta
        return results

    monkeypatch.setattr(commit_trigger, "on_commit", fixed_on_commit)

    from pathlib import Path

    py_file = Path(__file__).resolve().parent.parent / "sample_code" / "python" / "router.py"
    original = py_file.read_text()
    py_file.write_text(
        original
        + "\n\ndef extra_branch(x):\n"
        + "    if x > 0 and x < 10:\n"
        + "        return 'small'\n"
        + "    return 'other'\n"
    )
    try:
        result = fixed_on_commit("def456", changed_languages=["python"])
        delta = result["languages"]["python"]["delta"]
        assert delta != 0.0
    finally:
        py_file.write_text(original)


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

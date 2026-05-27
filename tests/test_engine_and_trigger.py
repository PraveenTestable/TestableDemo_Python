"""
Tests for whitebox/score_engine.py and whitebox/commit_trigger.py.

Covers all execution paths including error branches, improved/regressed flags,
load errors, history persistence, and get_latest_score.
"""

from __future__ import annotations

import json

import pytest

from whitebox.commit_trigger import load_language_repo_data, on_commit
from whitebox.metrics import METRIC_KEYS, ControlFlowMetrics
from whitebox.repo_profiler import REPO_DATA_DIR, build_language_repo_data, run_initial_whitebox
from whitebox.score_engine import (
    append_score_history,
    get_latest_score,
    load_metrics_from_repo_data,
    score_delta,
)


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr("whitebox.repo_profiler.REPO_DATA_DIR", tmp_path / "repo_data")
    monkeypatch.setattr("whitebox.score_engine.REPO_DATA_DIR", tmp_path / "repo_data")
    monkeypatch.setattr("whitebox.commit_trigger.REPO_DATA_DIR", tmp_path / "repo_data")


# ---------------------------------------------------------------------------
# load_metrics_from_repo_data
# ---------------------------------------------------------------------------

def test_load_metrics_from_valid_data() -> None:
    data = build_language_repo_data("python")
    metrics = load_metrics_from_repo_data(data)
    assert isinstance(metrics, ControlFlowMetrics)


def test_load_metrics_missing_key_raises() -> None:
    with pytest.raises(ValueError, match="Malformed"):
        load_metrics_from_repo_data({"language": "python"})


# ---------------------------------------------------------------------------
# score_delta
# ---------------------------------------------------------------------------

def test_score_delta_same_data_zero_delta() -> None:
    data = build_language_repo_data("python")
    delta = score_delta(data, data)
    assert delta["delta"] == 0.0
    assert all(v == 0.0 for v in delta["per_metric_delta"].values())


def test_score_delta_has_all_keys() -> None:
    data = build_language_repo_data("python")
    result = score_delta(data, data)
    assert {"before_composite", "after_composite", "delta", "improved", "regressed", "per_metric_delta"} <= result.keys()


def test_score_delta_improved_flag() -> None:
    low = {k: 0.0 for k in METRIC_KEYS}
    high = {k: 100.0 for k in METRIC_KEYS}
    before = {"control_flow_metrics": low}
    after = {"control_flow_metrics": high}
    result = score_delta(before, after)
    assert result["improved"] is True
    assert result["regressed"] is False
    assert result["delta"] > 0


def test_score_delta_regressed_flag() -> None:
    low = {k: 0.0 for k in METRIC_KEYS}
    high = {k: 100.0 for k in METRIC_KEYS}
    before = {"control_flow_metrics": high}
    after = {"control_flow_metrics": low}
    result = score_delta(before, after)
    assert result["regressed"] is True
    assert result["improved"] is False
    assert result["delta"] < 0


def test_score_delta_per_metric_keys() -> None:
    data = build_language_repo_data("python")
    result = score_delta(data, data)
    assert set(result["per_metric_delta"].keys()) == set(METRIC_KEYS)


# ---------------------------------------------------------------------------
# append_score_history and get_latest_score
# ---------------------------------------------------------------------------

def test_append_score_history_creates_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("whitebox.score_engine.REPO_DATA_DIR", tmp_path / "repo_data")
    from whitebox import score_engine
    score_engine.HISTORY_PATH = tmp_path / "repo_data" / "score_history.json"
    append_score_history({"commit_sha": "abc", "language": "python", "delta": 0.0})
    assert score_engine.HISTORY_PATH.exists()


def test_append_score_history_multiple_entries(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("whitebox.score_engine.REPO_DATA_DIR", tmp_path / "repo_data")
    from whitebox import score_engine
    score_engine.HISTORY_PATH = tmp_path / "repo_data" / "score_history.json"
    for i in range(3):
        append_score_history({"commit_sha": f"sha{i}", "language": "python", "delta": float(i)})
    history = json.loads(score_engine.HISTORY_PATH.read_text())
    assert len(history) == 3


def test_get_latest_score_returns_last_entry(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("whitebox.score_engine.REPO_DATA_DIR", tmp_path / "repo_data")
    from whitebox import score_engine
    score_engine.HISTORY_PATH = tmp_path / "repo_data" / "score_history.json"
    append_score_history({"commit_sha": "a1", "language": "python", "delta": 1.0})
    append_score_history({"commit_sha": "a2", "language": "python", "delta": 2.0})
    latest = get_latest_score("python")
    assert latest["commit_sha"] == "a2"


def test_get_latest_score_no_history_returns_none(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("whitebox.score_engine.REPO_DATA_DIR", tmp_path / "repo_data")
    from whitebox import score_engine
    score_engine.HISTORY_PATH = tmp_path / "repo_data" / "score_history.json"
    assert get_latest_score("python") is None


def test_get_latest_score_wrong_language_returns_none(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("whitebox.score_engine.REPO_DATA_DIR", tmp_path / "repo_data")
    from whitebox import score_engine
    score_engine.HISTORY_PATH = tmp_path / "repo_data" / "score_history.json"
    append_score_history({"commit_sha": "a1", "language": "python", "delta": 1.0})
    assert get_latest_score("java") is None


# ---------------------------------------------------------------------------
# load_language_repo_data (commit_trigger)
# ---------------------------------------------------------------------------

def test_load_language_repo_data_missing_raises(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("whitebox.commit_trigger.REPO_DATA_DIR", tmp_path / "repo_data")
    with pytest.raises(FileNotFoundError):
        load_language_repo_data("python")


def test_load_language_repo_data_corrupted_raises(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("whitebox.commit_trigger.REPO_DATA_DIR", tmp_path / "repo_data")
    import whitebox.commit_trigger as ct
    current_dir = tmp_path / "repo_data" / "current"
    current_dir.mkdir(parents=True)
    (current_dir / "python.json").write_text("not-json")
    with pytest.raises(ValueError, match="Corrupted"):
        load_language_repo_data("python")


# ---------------------------------------------------------------------------
# on_commit
# ---------------------------------------------------------------------------

def test_on_commit_invalid_sha_raises() -> None:
    with pytest.raises(ValueError, match="commit_sha"):
        on_commit("")


def test_on_commit_zero_delta_when_unchanged(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("whitebox.repo_profiler.REPO_DATA_DIR", tmp_path / "repo_data")
    monkeypatch.setattr("whitebox.score_engine.REPO_DATA_DIR", tmp_path / "repo_data")
    monkeypatch.setattr("whitebox.commit_trigger.REPO_DATA_DIR", tmp_path / "repo_data")
    run_initial_whitebox()
    result = on_commit("sha-test-001", changed_languages=["python"])
    assert result["commit_sha"] == "sha-test-001"
    assert result["languages"]["python"]["delta"] == 0.0


def test_on_commit_result_structure(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("whitebox.repo_profiler.REPO_DATA_DIR", tmp_path / "repo_data")
    monkeypatch.setattr("whitebox.score_engine.REPO_DATA_DIR", tmp_path / "repo_data")
    monkeypatch.setattr("whitebox.commit_trigger.REPO_DATA_DIR", tmp_path / "repo_data")
    run_initial_whitebox()
    result = on_commit("sha-test-002")
    assert result["trigger"] == "commit"
    lang_result = result["languages"]["python"]
    assert "before_composite" in lang_result
    assert "after_composite" in lang_result
    assert "per_metric_delta" in lang_result


def test_on_commit_detects_code_change(tmp_path, monkeypatch) -> None:
    """Removing all test assertions produces a non-zero delta on commit."""
    monkeypatch.setattr("whitebox.repo_profiler.REPO_DATA_DIR", tmp_path / "repo_data")
    monkeypatch.setattr("whitebox.score_engine.REPO_DATA_DIR", tmp_path / "repo_data")
    monkeypatch.setattr("whitebox.commit_trigger.REPO_DATA_DIR", tmp_path / "repo_data")

    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    test_files = list((root / "tests").glob("*.py"))
    verify_file = root / "sample_code" / "python" / "coverage_verification.py"

    targets = test_files + [verify_file]
    originals = {p: p.read_text() for p in targets}
    for p in targets:
        p.write_text('"""Temporarily empty for delta check."""\n')
    try:
        run_initial_whitebox()
        for path, content in originals.items():
            path.write_text(content)
        result = on_commit("sha-delta-001", changed_languages=["python"])
        assert result["languages"]["python"]["delta"] != 0.0
    finally:
        for path, content in originals.items():
            path.write_text(content)

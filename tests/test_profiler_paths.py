"""
Exhaustive tests for whitebox/repo_profiler.py.

Covers all execution paths in detect_languages, profile_language,
build_language_repo_data, write_repo_data, run_initial_whitebox,
and update_current_repo_data.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from whitebox.repo_profiler import (
    REPO_DATA_DIR,
    SUPPORTED_LANGUAGE,
    _count_pattern,
    build_language_repo_data,
    detect_languages,
    profile_language,
    run_initial_whitebox,
    update_current_repo_data,
    write_repo_data,
)


@pytest.fixture(autouse=True)
def isolated_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr("whitebox.repo_profiler.REPO_DATA_DIR", tmp_path / "repo_data")
    monkeypatch.setattr("whitebox.score_engine.REPO_DATA_DIR", tmp_path / "repo_data")
    monkeypatch.setattr("whitebox.commit_trigger.REPO_DATA_DIR", tmp_path / "repo_data")


# ---------------------------------------------------------------------------
# detect_languages
# ---------------------------------------------------------------------------

def test_detect_languages_finds_python() -> None:
    langs = detect_languages()
    assert langs == [SUPPORTED_LANGUAGE]


def test_detect_languages_missing_dir(tmp_path) -> None:
    langs = detect_languages(base_dir=tmp_path / "no-such-dir")
    assert langs == []


def test_detect_languages_empty_dir(tmp_path) -> None:
    (tmp_path / SUPPORTED_LANGUAGE).mkdir(parents=True)
    langs = detect_languages(base_dir=tmp_path)
    assert langs == []


def test_detect_languages_with_py_file(tmp_path) -> None:
    py_dir = tmp_path / SUPPORTED_LANGUAGE
    py_dir.mkdir(parents=True)
    (py_dir / "module.py").write_text("x = 1")
    langs = detect_languages(base_dir=tmp_path)
    assert langs == [SUPPORTED_LANGUAGE]


# ---------------------------------------------------------------------------
# _count_pattern (internal helper — loop + regex)
# ---------------------------------------------------------------------------

def test_count_pattern_finds_matches() -> None:
    assert _count_pattern("if x:\n  if y:\n    pass", r"\bif\b") == 2


def test_count_pattern_no_matches_returns_zero() -> None:
    assert _count_pattern("x = 1 + 2", r"\bif\b") == 0


def test_count_pattern_empty_string() -> None:
    assert _count_pattern("", r"\bif\b") == 0


# ---------------------------------------------------------------------------
# profile_language
# ---------------------------------------------------------------------------

def test_profile_language_returns_required_keys() -> None:
    profile = profile_language(SUPPORTED_LANGUAGE)
    required = {
        "language", "files", "file_count", "lines_of_code",
        "branch_points", "decision_nodes", "execution_paths",
        "covered_paths", "logical_subexpressions", "covered_subexpressions",
        "truth_table_rows", "covered_combinations", "verified_decisions",
        "cyclomatic_complexity", "test_assertions", "estimated_qa_hours",
    }
    assert required.issubset(profile.keys())


def test_profile_language_unsupported_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        profile_language("java")


def test_profile_language_has_positive_loc() -> None:
    profile = profile_language(SUPPORTED_LANGUAGE)
    assert profile["lines_of_code"] > 0


def test_profile_language_covered_paths_le_execution_paths() -> None:
    profile = profile_language(SUPPORTED_LANGUAGE)
    assert profile["covered_paths"] <= profile["execution_paths"]


def test_profile_language_covered_sub_le_logical() -> None:
    profile = profile_language(SUPPORTED_LANGUAGE)
    assert profile["covered_subexpressions"] <= profile["logical_subexpressions"]


def test_profile_language_covered_combinations_le_truth_rows() -> None:
    profile = profile_language(SUPPORTED_LANGUAGE)
    assert profile["covered_combinations"] <= profile["truth_table_rows"]


def test_profile_language_counts_test_assertions() -> None:
    profile = profile_language(SUPPORTED_LANGUAGE)
    assert profile["test_assertions"] > 0


# ---------------------------------------------------------------------------
# build_language_repo_data
# ---------------------------------------------------------------------------

def test_build_language_repo_data_has_composite_score() -> None:
    data = build_language_repo_data(SUPPORTED_LANGUAGE)
    assert "composite_score" in data
    assert 0.0 <= data["composite_score"] <= 100.0


def test_build_language_repo_data_domain() -> None:
    data = build_language_repo_data(SUPPORTED_LANGUAGE)
    assert data["whitebox_domain"] == "control_flow_testing"


def test_build_language_repo_data_has_all_metric_keys() -> None:
    from whitebox.metrics import METRIC_KEYS
    data = build_language_repo_data(SUPPORTED_LANGUAGE)
    assert set(data["control_flow_metrics"].keys()) == set(METRIC_KEYS)


# ---------------------------------------------------------------------------
# write_repo_data
# ---------------------------------------------------------------------------

def test_write_repo_data_creates_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("whitebox.repo_profiler.REPO_DATA_DIR", tmp_path / "repo_data")
    path = write_repo_data(SUPPORTED_LANGUAGE, target="initial_run")
    assert path.exists()
    payload = json.loads(path.read_text())
    assert payload["language"] == SUPPORTED_LANGUAGE


def test_write_repo_data_current(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("whitebox.repo_profiler.REPO_DATA_DIR", tmp_path / "repo_data")
    path = write_repo_data(SUPPORTED_LANGUAGE, target="current")
    assert path.exists()


# ---------------------------------------------------------------------------
# run_initial_whitebox
# ---------------------------------------------------------------------------

def test_run_initial_whitebox_manifest(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("whitebox.repo_profiler.REPO_DATA_DIR", tmp_path / "repo_data")
    manifest = run_initial_whitebox()
    assert manifest["languages"] == [SUPPORTED_LANGUAGE]
    for lang in manifest["languages"]:
        assert (tmp_path / "repo_data" / "initial_run" / f"{lang}.json").exists()
        assert (tmp_path / "repo_data" / "current" / f"{lang}.json").exists()


def test_run_initial_whitebox_creates_manifest_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("whitebox.repo_profiler.REPO_DATA_DIR", tmp_path / "repo_data")
    run_initial_whitebox()
    assert (tmp_path / "repo_data" / "initial_run_manifest.json").exists()


# ---------------------------------------------------------------------------
# update_current_repo_data
# ---------------------------------------------------------------------------

def test_update_current_repo_data_returns_payload(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("whitebox.repo_profiler.REPO_DATA_DIR", tmp_path / "repo_data")
    run_initial_whitebox()
    data = update_current_repo_data(SUPPORTED_LANGUAGE)
    assert data["language"] == SUPPORTED_LANGUAGE
    assert "composite_score" in data

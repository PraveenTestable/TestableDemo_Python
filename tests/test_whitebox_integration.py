"""Integration tests for whitebox CLI and core modules."""

from __future__ import annotations

import json

import pytest

from whitebox.cli import main
from whitebox.commit_trigger import on_commit
from whitebox.repo_profiler import REPO_DATA_DIR, build_language_repo_data, run_initial_whitebox


@pytest.fixture(autouse=True)
def isolated_repo_data(tmp_path, monkeypatch):
    monkeypatch.setattr("whitebox.repo_profiler.REPO_DATA_DIR", tmp_path / "repo_data")
    monkeypatch.setattr("whitebox.score_engine.REPO_DATA_DIR", tmp_path / "repo_data")
    monkeypatch.setattr("whitebox.commit_trigger.REPO_DATA_DIR", tmp_path / "repo_data")


def test_cli_initial_run(capsys) -> None:
    assert main(["initial-run"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["languages"] == ["python"]


def test_cli_on_commit_after_initial_run(capsys) -> None:
    run_initial_whitebox()
    assert main(["on-commit", "--commit-sha", "gate-fix-001"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["languages"]["python"]["delta"] == 0.0


def test_whitebox_modules_execute() -> None:
    run_initial_whitebox()
    data = build_language_repo_data("python")
    assert data["composite_score"] >= 80
    result = on_commit("gate-fix-002", changed_languages=["python"])
    assert "delta" in result["languages"]["python"]

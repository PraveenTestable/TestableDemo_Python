"""Commit trigger: re-profile repo and record Control Flow score updates."""

from __future__ import annotations

import json
from typing import Any

from whitebox.repo_profiler import REPO_DATA_DIR, detect_languages, update_current_repo_data
from whitebox.score_engine import append_score_history, score_delta

USE_CURRENT_REPO_DATA = True


def load_language_repo_data(language: str) -> dict[str, Any]:
    """Load persisted repo data for a language, raising FileNotFoundError if missing."""
    subdir = "current" if USE_CURRENT_REPO_DATA else "initial_run"
    path = REPO_DATA_DIR / subdir / f"{language}.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing repo data: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Corrupted repo data at {path}: {exc}") from exc


def on_commit(commit_sha: str, changed_languages: list[str] | None = None) -> dict[str, Any]:
    """
    Webhook / post-commit handler.

    1. Capture prior repo_data/current/ snapshot
    2. Re-profile changed languages
    3. Compute delta and append to score_history.json
    """
    if not commit_sha or not isinstance(commit_sha, str):
        raise ValueError(f"commit_sha must be a non-empty string, got: {commit_sha!r}")

    languages = changed_languages or detect_languages()
    results: dict[str, Any] = {
        "commit_sha": commit_sha,
        "trigger": "commit",
        "languages": {},
    }

    for language in languages:
        before = load_language_repo_data(language)
        after = update_current_repo_data(language)
        delta = score_delta(before, after)
        entry = {
            "commit_sha": commit_sha,
            "language": language,
            **delta,
        }
        append_score_history(entry)
        results["languages"][language] = delta

    return results

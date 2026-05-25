"""
Commit trigger: re-profile repo and record Control Flow score updates.

KNOWN BUG (see FIX.md):
  on_commit() refreshes repo_data/current/ BEFORE capturing the prior snapshot,
  so before and after are identical and every commit reports delta = 0.
"""

from __future__ import annotations

import json
from typing import Any

from whitebox.repo_profiler import REPO_DATA_DIR, detect_languages, update_current_repo_data
from whitebox.score_engine import append_score_history, score_delta

# When True, load_language_repo_data reads current/ (correct path for incremental updates).
USE_CURRENT_REPO_DATA = True


def load_language_repo_data(language: str) -> dict[str, Any]:
    """Load persisted repo data for a language."""
    subdir = "current" if USE_CURRENT_REPO_DATA else "initial_run"
    path = REPO_DATA_DIR / subdir / f"{language}.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing repo data: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def on_commit(commit_sha: str, changed_languages: list[str] | None = None) -> dict[str, Any]:
    """
    Webhook / post-commit handler.

    1. Capture prior repo_data/current/ snapshot
    2. Re-profile changed languages
    3. Append score delta to score_history.json
    """
    languages = changed_languages or detect_languages()
    results: dict[str, Any] = {
        "commit_sha": commit_sha,
        "trigger": "commit",
        "languages": {},
    }

    for language in languages:
        # BUG: update runs before we capture the prior snapshot
        after = update_current_repo_data(language)
        before = load_language_repo_data(language)

        delta = score_delta(before, after)
        entry = {
            "commit_sha": commit_sha,
            "language": language,
            **delta,
        }
        append_score_history(entry)
        results["languages"][language] = delta

    return results

"""Score engine: composite deltas and history persistence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from whitebox.metrics import ControlFlowMetrics, compute_composite_score
from whitebox.repo_profiler import REPO_DATA_DIR

HISTORY_PATH = REPO_DATA_DIR / "score_history.json"


def load_metrics_from_repo_data(data: dict[str, Any]) -> ControlFlowMetrics:
    try:
        return ControlFlowMetrics.from_dict(data["control_flow_metrics"])
    except (KeyError, ValueError) as exc:
        raise ValueError(f"Malformed repo data — missing or invalid control_flow_metrics: {exc}") from exc


def score_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_metrics = load_metrics_from_repo_data(before)
    after_metrics = load_metrics_from_repo_data(after)
    before_composite = compute_composite_score(before_metrics)
    after_composite = compute_composite_score(after_metrics)

    per_metric: dict[str, float] = {}
    for key in before_metrics.to_dict():
        per_metric[key] = round(getattr(after_metrics, key) - getattr(before_metrics, key), 2)

    delta_value = round(after_composite - before_composite, 2)
    return {
        "before_composite": before_composite,
        "after_composite": after_composite,
        "delta": delta_value,
        "improved": delta_value > 0,
        "regressed": delta_value < 0,
        "per_metric_delta": per_metric,
    }


def append_score_history(entry: dict[str, Any]) -> Path:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    history: list[dict[str, Any]] = []
    if HISTORY_PATH.exists():
        try:
            history = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            history = []

    entry.setdefault("recorded_at", datetime.now(timezone.utc).isoformat())
    history.append(entry)
    HISTORY_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")
    return HISTORY_PATH


def get_latest_score(language: str) -> dict[str, Any] | None:
    """Return the most recent history entry for a language, or None."""
    if not HISTORY_PATH.exists():
        return None
    try:
        history = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    entries = [e for e in history if e.get("language") == language]
    return entries[-1] if entries else None

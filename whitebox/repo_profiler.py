"""Repository profiling and Python repo data generation."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from whitebox.metrics import METRIC_LABELS, compute_composite_score, compute_metrics_from_profile

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CODE_DIR = ROOT / "sample_code"
REPO_DATA_DIR = ROOT / "repo_data"
PYTHON_SAMPLE_DIR = SAMPLE_CODE_DIR / "python"
SUPPORTED_LANGUAGE = "python"

BRANCH_PATTERN = r"\b(if|elif|for|while|except)\b"
LOGICAL_PATTERN = r"(\band\b|\bor\b|\bnot\b)"
ASSERT_PATTERN = r"\bassert\b"


def detect_languages(base_dir: Path | None = None) -> list[str]:
    """Return supported languages found under sample_code (Python only)."""
    lang_dir = (base_dir or SAMPLE_CODE_DIR) / SUPPORTED_LANGUAGE
    if lang_dir.exists() and any(lang_dir.rglob("*.py")):
        return [SUPPORTED_LANGUAGE]
    return []


def _count_pattern(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.MULTILINE))


def profile_language(language: str = SUPPORTED_LANGUAGE, base_dir: Path | None = None) -> dict[str, Any]:
    """Build a deterministic Python profile from sample source files."""
    if language != SUPPORTED_LANGUAGE:
        raise ValueError(f"Unsupported language: {language}")

    lang_dir = (base_dir or SAMPLE_CODE_DIR) / SUPPORTED_LANGUAGE

    files: list[str] = []
    contents: list[str] = []
    scan_roots = [lang_dir, ROOT / "tests"]
    for scan_root in scan_roots:
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*.py"):
            if path.is_file():
                files.append(str(path.relative_to(ROOT)))
                contents.append(path.read_text(encoding="utf-8"))

    merged = "\n".join(contents)
    loc = sum(1 for line in merged.splitlines() if line.strip())

    branch_points = _count_pattern(merged, BRANCH_PATTERN)
    logical_subexpressions = max(1, _count_pattern(merged, LOGICAL_PATTERN))
    decision_nodes = branch_points + _count_pattern(merged, r"\bswitch\b|\bcase\b")
    execution_paths = max(1, branch_points + 1)
    truth_table_rows = min(64, 2 ** min(decision_nodes, 6))

    test_assertions = _count_pattern(merged, ASSERT_PATTERN)
    verification_ratio = min(1.0, test_assertions / max(decision_nodes, 1))

    verified_decisions = min(
        decision_nodes,
        max(int(decision_nodes * verification_ratio), test_assertions // 2, branch_points // 2),
    )
    covered_paths = min(
        execution_paths,
        max(int(execution_paths * verification_ratio), verified_decisions, branch_points // 2 + 1),
    )
    covered_sub = min(
        logical_subexpressions,
        max(
            int(logical_subexpressions * verification_ratio),
            test_assertions // 2 + logical_subexpressions // 3,
        ),
    )
    covered_combinations = min(
        truth_table_rows,
        max(covered_sub * 2, int(truth_table_rows * verification_ratio)),
    )

    profile = {
        "language": language,
        "files": files,
        "file_count": len(files),
        "lines_of_code": loc,
        "branch_points": branch_points,
        "decision_nodes": decision_nodes,
        "execution_paths": execution_paths,
        "covered_paths": covered_paths,
        "logical_subexpressions": logical_subexpressions,
        "covered_subexpressions": covered_sub,
        "truth_table_rows": truth_table_rows,
        "covered_combinations": covered_combinations,
        "verified_decisions": verified_decisions,
        "cyclomatic_complexity": branch_points + 1,
        "test_assertions": test_assertions,
        "estimated_qa_hours": round(max(1.0, loc / 120), 2),
        "profiled_at": datetime.now(timezone.utc).isoformat(),
    }
    return profile


def build_language_repo_data(language: str = SUPPORTED_LANGUAGE, run_type: str = "initial") -> dict[str, Any]:
    profile = profile_language(language)
    metrics = compute_metrics_from_profile(profile)
    composite = compute_composite_score(metrics)

    return {
        "run_type": run_type,
        "language": language,
        "profile": profile,
        "control_flow_metrics": metrics.to_dict(),
        "metric_labels": dict(METRIC_LABELS),
        "composite_score": composite,
        "whitebox_domain": "control_flow_testing",
    }


def write_repo_data(language: str = SUPPORTED_LANGUAGE, target: str = "initial", run_type: str = "initial") -> Path:
    """Persist repo data under repo_data/{target}/{language}.json."""
    out_dir = REPO_DATA_DIR / target
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_language_repo_data(language, run_type=run_type)
    out_path = out_dir / f"{language}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def run_initial_whitebox() -> dict[str, Any]:
    """Whitebox initial run: profile Python and write baseline + current snapshots."""
    languages = detect_languages()
    if not languages:
        raise RuntimeError(f"No Python sources found under {PYTHON_SAMPLE_DIR}")

    manifest: dict[str, Any] = {
        "run_id": f"wb-initial-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "run_type": "initial",
        "languages": languages,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "snapshots": {},
    }

    for language in languages:
        write_repo_data(language, target="initial_run", run_type="initial")
        write_repo_data(language, target="current", run_type="initial")
        manifest["snapshots"][language] = {
            "initial_run": f"repo_data/initial_run/{language}.json",
            "current": f"repo_data/current/{language}.json",
        }

    manifest_path = REPO_DATA_DIR / "initial_run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def update_current_repo_data(language: str = SUPPORTED_LANGUAGE) -> dict[str, Any]:
    """Re-profile Python after a commit and refresh current snapshot."""
    write_repo_data(language, target="current", run_type="commit_refresh")
    path = REPO_DATA_DIR / "current" / f"{language}.json"
    return json.loads(path.read_text(encoding="utf-8"))

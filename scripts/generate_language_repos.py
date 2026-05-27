#!/usr/bin/env python3
"""Generate single-language Whitebox demo repos and zip archives."""

from __future__ import annotations

import json
import shutil
import textwrap
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT.parent / "whitebox-language-demos"
TEMPLATE_FILES = [
    "requirements.txt",
    ".gitignore",
    "FIX.md",
    ".github/workflows/whitebox-score-update.yml",
    "scripts/post-commit.sh",
    "whitebox/__init__.py",
    "whitebox/__main__.py",
    "whitebox/metrics.py",
    "whitebox/commit_trigger.py",
    "whitebox/score_engine.py",
]

LANGUAGE_CONFIGS = {
    "java": {
        "title": "Java",
        "sample_dir": "java",
        "extensions": (".java",),
        "branch_pattern": r"\b(if|else if|for|while|catch|switch|case)\b",
        "logical_pattern": r"(&&|\|\||!)",
        "assert_pattern": r"\b(assert|Assert)\b",
        "repo_name": "whitebox-repo-java",
        "zip_name": "TestableDemo_Java.zip",
    },
    "javascript": {
        "title": "JavaScript",
        "sample_dir": "javascript",
        "extensions": (".js",),
        "branch_pattern": r"\b(if|else if|for|while|catch|switch|case)\b",
        "logical_pattern": r"(&&|\|\||!)",
        "assert_pattern": r"\b(assert|Assert|expect)\b",
        "repo_name": "whitebox-repo-javascript",
        "zip_name": "TestableDemo_JavaScript.zip",
    },
    "typescript": {
        "title": "TypeScript",
        "sample_dir": "typescript",
        "extensions": (".ts",),
        "branch_pattern": r"\b(if|else if|for|while|catch|switch|case)\b",
        "logical_pattern": r"(&&|\|\||!)",
        "assert_pattern": r"\b(assert|Assert|expect)\b",
        "repo_name": "whitebox-repo-typescript",
        "zip_name": "TestableDemo_TypeScript.zip",
    },
    "csharp": {
        "title": "C#",
        "sample_dir": "csharp",
        "extensions": (".cs",),
        "branch_pattern": r"\b(if|else if|for|while|catch|switch|case)\b",
        "logical_pattern": r"(&&|\|\||!)",
        "assert_pattern": r"\b(assert|Assert|Debug\.Assert)\b",
        "repo_name": "whitebox-repo-csharp",
        "zip_name": "TestableDemo_CSharp.zip",
    },
}


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")


def copy_template_files(repo_dir: Path) -> None:
    for rel in TEMPLATE_FILES:
        src = ROOT / rel
        dest = repo_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def render_repo_profiler(lang_key: str, cfg: dict) -> str:
    exts = ", ".join(repr(ext) for ext in cfg["extensions"])
    return f'''\
    """Repository profiling and {cfg["title"]} repo data generation."""

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
    LANGUAGE_SAMPLE_DIR = SAMPLE_CODE_DIR / "{cfg["sample_dir"]}"
    SUPPORTED_LANGUAGE = "{lang_key}"

    BRANCH_PATTERN = {cfg["branch_pattern"]!r}
    LOGICAL_PATTERN = {cfg["logical_pattern"]!r}
    ASSERT_PATTERN = {cfg["assert_pattern"]!r}
    SOURCE_EXTENSIONS = ({exts},)


    def detect_languages(base_dir: Path | None = None) -> list[str]:
        """Return supported languages found under sample_code ({cfg["title"]} only)."""
        lang_dir = (base_dir or SAMPLE_CODE_DIR) / SUPPORTED_LANGUAGE
        if lang_dir.exists() and any(lang_dir.rglob(f"*{{ext}}") for ext in SOURCE_EXTENSIONS):
            return [SUPPORTED_LANGUAGE]
        return []


    def _count_pattern(text: str, pattern: str) -> int:
        return len(re.findall(pattern, text, flags=re.MULTILINE))


    def profile_language(language: str = SUPPORTED_LANGUAGE, base_dir: Path | None = None) -> dict[str, Any]:
        """Build a deterministic {cfg["title"]} profile from sample source files."""
        if language != SUPPORTED_LANGUAGE:
            raise ValueError(f"Unsupported language: {{language}}")

        lang_dir = (base_dir or SAMPLE_CODE_DIR) / SUPPORTED_LANGUAGE

        files: list[str] = []
        contents: list[str] = []
        for ext in SOURCE_EXTENSIONS:
            for path in lang_dir.rglob(f"*{{ext}}"):
                files.append(str(path.relative_to(ROOT)))
                contents.append(path.read_text(encoding="utf-8"))

        merged = "\\n".join(contents)
        loc = sum(1 for line in merged.splitlines() if line.strip())

        branch_points = _count_pattern(merged, BRANCH_PATTERN)
        logical_subexpressions = max(1, _count_pattern(merged, LOGICAL_PATTERN))
        decision_nodes = branch_points + _count_pattern(merged, r"\\bswitch\\b|\\bcase\\b")
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

        profile = {{
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
        }}
        return profile


    def build_language_repo_data(language: str = SUPPORTED_LANGUAGE, run_type: str = "initial") -> dict[str, Any]:
        profile = profile_language(language)
        metrics = compute_metrics_from_profile(profile)
        composite = compute_composite_score(metrics)

        return {{
            "run_type": run_type,
            "language": language,
            "profile": profile,
            "control_flow_metrics": metrics.to_dict(),
            "metric_labels": dict(METRIC_LABELS),
            "composite_score": composite,
            "whitebox_domain": "control_flow_testing",
        }}


    def write_repo_data(language: str = SUPPORTED_LANGUAGE, target: str = "initial", run_type: str = "initial") -> Path:
        """Persist repo data under repo_data/{{target}}/{{language}}.json."""
        out_dir = REPO_DATA_DIR / target
        out_dir.mkdir(parents=True, exist_ok=True)
        payload = build_language_repo_data(language, run_type=run_type)
        out_path = out_dir / f"{{language}}.json"
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return out_path


    def run_initial_whitebox() -> dict[str, Any]:
        """Whitebox initial run: profile {cfg["title"]} and write baseline + current snapshots."""
        languages = detect_languages()
        if not languages:
            raise RuntimeError(f"No {cfg["title"]} sources found under {{LANGUAGE_SAMPLE_DIR}}")

        manifest: dict[str, Any] = {{
            "run_id": f"wb-initial-{{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}}",
            "run_type": "initial",
            "languages": languages,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "snapshots": {{}},
        }}

        for language in languages:
            write_repo_data(language, target="initial_run", run_type="initial")
            write_repo_data(language, target="current", run_type="initial")
            manifest["snapshots"][language] = {{
                "initial_run": f"repo_data/initial_run/{{language}}.json",
                "current": f"repo_data/current/{{language}}.json",
            }}

        manifest_path = REPO_DATA_DIR / "initial_run_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest


    def update_current_repo_data(language: str = SUPPORTED_LANGUAGE) -> dict[str, Any]:
        """Re-profile {cfg["title"]} after a commit and refresh current snapshot."""
        write_repo_data(language, target="current", run_type="commit_refresh")
        path = REPO_DATA_DIR / "current" / f"{{language}}.json"
        return json.loads(path.read_text(encoding="utf-8"))
    '''


def render_cli(title: str) -> str:
    return f'''\
    """CLI entry points for Whitebox initial run and commit trigger."""

    from __future__ import annotations

    import argparse
    import json
    import sys

    from whitebox.commit_trigger import on_commit
    from whitebox.repo_profiler import run_initial_whitebox


    def main(argv: list[str] | None = None) -> int:
        parser = argparse.ArgumentParser(description="Whitebox repo demo CLI")
        sub = parser.add_subparsers(dest="command", required=True)

        sub.add_parser("initial-run", help="Run Whitebox initial profiling for {title}")

        commit_parser = sub.add_parser("on-commit", help="Simulate commit trigger / score update")
        commit_parser.add_argument("--commit-sha", default="local-commit", help="Commit SHA for the trigger")

        args = parser.parse_args(argv)

        if args.command == "initial-run":
            manifest = run_initial_whitebox()
            print(json.dumps(manifest, indent=2))
            return 0

        if args.command == "on-commit":
            result = on_commit(args.commit_sha)
            print(json.dumps(result, indent=2))
            return 0

        parser.print_help()
        return 1


    if __name__ == "__main__":
        sys.exit(main())
    '''


def render_readme(title: str, lang_key: str, sample_dir: str) -> str:
    return f'''\
    # Whitebox Repo Demo — Control Flow Metrics ({title})

    Sample **{title}-only** repository for **Testable Whitebox initial run** and **commit-triggered score updates**.

    ## Scenario

    1. **Initial run** — Profile the repo, compute Control Flow metrics, and persist a snapshot under `repo_data/initial_run/{lang_key}.json`.
    2. **Commit trigger** — On each commit, re-profile changed files, update `repo_data/current/{lang_key}.json`, recompute metric deltas, and append to `repo_data/score_history.json`.

    ## Control Flow Metrics

    | Metric | Key | Description |
    |--------|-----|-------------|
    | Execution Path Integrity | `execution_path_integrity` | Share of reachable paths exercised vs. detected |
    | Decision Outcome Verification | `decision_outcome_verification` | Branch/decision outcomes validated |
    | Logical Sub-expression Validation | `logical_subexpression_validation` | Short-circuit and compound conditions covered |
    | Total Logical Combinatorial Coverage | `total_logical_combinatorial_coverage` | Truth-table combinations covered |
    | Technical Debt Impact | `technical_debt_impact` | Control-flow complexity debt (inverse score) |
    | QA Resource Allocation | `qa_resource_allocation` | Estimated QA effort vs. coverage gained |

    ## Sample code

    - {title} (`sample_code/{sample_dir}/`)

    ## Quick start

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

    # Whitebox initial run ({title})
    python -m whitebox.cli initial-run

    # Simulate commit webhook / post-commit trigger
    python -m whitebox.cli on-commit --commit-sha HEAD

    # Run tests
    pytest tests/ -v
    ```

    ## Known mistake & fix

    See [FIX.md](FIX.md).

    ## CI

    `.github/workflows/whitebox-score-update.yml` runs the commit trigger on every push.
    '''


def render_tests(lang_key: str, sample_dir: str, verify_file: str) -> str:
    return f'''\
    """Tests for Whitebox metrics, repo data, and commit trigger."""

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
        data = build_language_repo_data("{lang_key}")
        metrics = data["control_flow_metrics"]
        assert set(metrics.keys()) == set(METRIC_KEYS)


    def test_initial_run_writes_language_snapshot():
        manifest = run_initial_whitebox()
        assert manifest["languages"] == ["{lang_key}"]
        for language in manifest["languages"]:
            initial = REPO_DATA_DIR / "initial_run" / f"{{language}}.json"
            current = REPO_DATA_DIR / "current" / f"{{language}}.json"
            assert initial.exists()
            assert current.exists()
            payload = json.loads(initial.read_text())
            assert payload["whitebox_domain"] == "control_flow_testing"
            assert 0 <= payload["composite_score"] <= 100


    def test_commit_trigger_reports_zero_delta_when_unchanged():
        run_initial_whitebox()
        result = on_commit("abc123", changed_languages=["{lang_key}"])
        delta = result["languages"]["{lang_key}"]["delta"]
        assert delta == 0.0


    def test_commit_trigger_detects_score_change():
        run_initial_whitebox()

        from pathlib import Path

        verify_file = Path(__file__).resolve().parent.parent / "sample_code" / "{sample_dir}" / "{verify_file}"
        original = verify_file.read_text()
        verify_file.write_text("/* Verification temporarily removed for delta check. */\\n")
        try:
            result = on_commit("def456", changed_languages=["{lang_key}"])
            delta = result["languages"]["{lang_key}"]
            assert delta["delta"] != 0.0
            assert any(value != 0.0 for value in delta["per_metric_delta"].values())
        finally:
            verify_file.write_text(original)


    def test_composite_score_is_weighted():
        profile = {{
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
        }}
        metrics = compute_metrics_from_profile(profile)
        score = compute_composite_score(metrics)
        assert 0 <= score <= 100
    '''


SAMPLE_SOURCES = {
    "java": {
        "PaymentRouter.java": '''
            package com.testable.demo;

            public class PaymentRouter {

                public String route(String method, boolean authenticated, boolean rateLimited) {
                    if (!method.equals("GET") && !method.equals("POST") && !method.equals("PUT")) {
                        return "405";
                    }

                    if (authenticated && !rateLimited) {
                        switch (method) {
                            case "GET":
                                return "200-read";
                            case "POST":
                                return "201-created";
                            default:
                                return "202-accepted";
                        }
                    }

                    if (!authenticated || rateLimited) {
                        return "401-unauthorized";
                    }

                    return "500-unexpected";
                }

                public String evaluateFlags(boolean a, boolean b, boolean c) {
                    if ((a && b) || (!c && a)) {
                        return "path-alpha";
                    }
                    if ((b || c) && !a) {
                        return "path-beta";
                    }
                    return "path-default";
                }
            }
        ''',
        "CoverageVerification.java": '''
            package com.testable.demo;

            public final class CoverageVerification {

                private CoverageVerification() {}

                public static void verifyRouteRequestPaths() {
                    PaymentRouter router = new PaymentRouter();
                    assert "405".equals(router.route("DELETE", true, false));
                    assert "405".equals(router.route("PATCH", false, false));
                    assert "200-read".equals(router.route("GET", true, false));
                    assert "201-created".equals(router.route("POST", true, false));
                    assert "202-accepted".equals(router.route("PUT", true, false));
                    assert "401-unauthorized".equals(router.route("GET", false, false));
                    assert "401-unauthorized".equals(router.route("GET", true, true));
                    assert "401-unauthorized".equals(router.route("POST", false, true));
                }

                public static void verifyEvaluateFlagsCombinations() {
                    PaymentRouter router = new PaymentRouter();
                    assert "path-alpha".equals(router.evaluateFlags(true, true, false));
                    assert "path-alpha".equals(router.evaluateFlags(true, true, true));
                    assert "path-alpha".equals(router.evaluateFlags(true, false, true));
                    assert "path-alpha".equals(router.evaluateFlags(true, false, false));
                    assert "path-beta".equals(router.evaluateFlags(false, true, false));
                    assert "path-beta".equals(router.evaluateFlags(false, true, true));
                    assert "path-beta".equals(router.evaluateFlags(false, false, true));
                    assert "path-default".equals(router.evaluateFlags(false, false, false));
                }

                public static void verifyCompoundConditions() {
                    PaymentRouter router = new PaymentRouter();
                    assert "401-unauthorized".equals(router.route("GET", true, false == true));
                    assert "200-read".equals(router.route("GET", true, false == false));
                    assert "path-alpha".equals(router.evaluateFlags(true, true, false == true));
                    assert "path-beta".equals(router.evaluateFlags(false, true, false == false));
                }

                public static void runAllVerifications() {
                    verifyRouteRequestPaths();
                    verifyEvaluateFlagsCombinations();
                    verifyCompoundConditions();
                }
            }
        ''',
        "verify_file": "CoverageVerification.java",
    },
    "javascript": {
        "router.js": '''
            function routeRequest(method, authenticated, rateLimited) {
              if (!["GET", "POST", "PUT"].includes(method)) {
                return "405";
              }

              if (authenticated && !rateLimited) {
                switch (method) {
                  case "GET":
                    return "200-read";
                  case "POST":
                    return "201-created";
                  default:
                    return "202-accepted";
                }
              }

              if (!authenticated || rateLimited) {
                return "401-unauthorized";
              }

              return "500-unexpected";
            }

            function evaluateFlags(a, b, c) {
              if ((a && b) || (!c && a)) {
                return "path-alpha";
              }
              if ((b || c) && !a) {
                return "path-beta";
              }
              return "path-default";
            }

            module.exports = { routeRequest, evaluateFlags };
        ''',
        "coverage_verification.js": '''
            const { routeRequest, evaluateFlags } = require("./router");

            function verifyRouteRequestPaths() {
              assert(routeRequest("DELETE", true, false) === "405");
              assert(routeRequest("PATCH", false, false) === "405");
              assert(routeRequest("GET", true, false) === "200-read");
              assert(routeRequest("POST", true, false) === "201-created");
              assert(routeRequest("PUT", true, false) === "202-accepted");
              assert(routeRequest("GET", false, false) === "401-unauthorized");
              assert(routeRequest("GET", true, true) === "401-unauthorized");
              assert(routeRequest("POST", false, true) === "401-unauthorized");
            }

            function verifyEvaluateFlagsCombinations() {
              assert(evaluateFlags(true, true, false) === "path-alpha");
              assert(evaluateFlags(true, true, true) === "path-alpha");
              assert(evaluateFlags(true, false, true) === "path-alpha");
              assert(evaluateFlags(true, false, false) === "path-alpha");
              assert(evaluateFlags(false, true, false) === "path-beta");
              assert(evaluateFlags(false, true, true) === "path-beta");
              assert(evaluateFlags(false, false, true) === "path-beta");
              assert(evaluateFlags(false, false, false) === "path-default");
            }

            function verifyCompoundConditions() {
              assert(routeRequest("GET", true, !false) === "401-unauthorized");
              assert(routeRequest("GET", true, !true) === "200-read");
              assert(evaluateFlags(!false, !false, !true) === "path-alpha");
              assert(evaluateFlags(!true, !false, !false) === "path-beta");
            }

            function runAllVerifications() {
              verifyRouteRequestPaths();
              verifyEvaluateFlagsCombinations();
              verifyCompoundConditions();
            }

            module.exports = { runAllVerifications };
        ''',
        "verify_file": "coverage_verification.js",
    },
    "typescript": {
        "router.ts": '''
            export function routeRequest(
              method: string,
              authenticated: boolean,
              rateLimited: boolean,
            ): string {
              if (!["GET", "POST", "PUT"].includes(method)) {
                return "405";
              }

              if (authenticated && !rateLimited) {
                switch (method) {
                  case "GET":
                    return "200-read";
                  case "POST":
                    return "201-created";
                  default:
                    return "202-accepted";
                }
              }

              if (!authenticated || rateLimited) {
                return "401-unauthorized";
              }

              return "500-unexpected";
            }

            export function evaluateFlags(a: boolean, b: boolean, c: boolean): string {
              if ((a && b) || (!c && a)) {
                return "path-alpha";
              }
              if ((b || c) && !a) {
                return "path-beta";
              }
              return "path-default";
            }
        ''',
        "coverage_verification.ts": '''
            import { evaluateFlags, routeRequest } from "./router";

            export function verifyRouteRequestPaths(): void {
              assert(routeRequest("DELETE", true, false) === "405");
              assert(routeRequest("PATCH", false, false) === "405");
              assert(routeRequest("GET", true, false) === "200-read");
              assert(routeRequest("POST", true, false) === "201-created");
              assert(routeRequest("PUT", true, false) === "202-accepted");
              assert(routeRequest("GET", false, false) === "401-unauthorized");
              assert(routeRequest("GET", true, true) === "401-unauthorized");
              assert(routeRequest("POST", false, true) === "401-unauthorized");
            }

            export function verifyEvaluateFlagsCombinations(): void {
              assert(evaluateFlags(true, true, false) === "path-alpha");
              assert(evaluateFlags(true, true, true) === "path-alpha");
              assert(evaluateFlags(true, false, true) === "path-alpha");
              assert(evaluateFlags(true, false, false) === "path-alpha");
              assert(evaluateFlags(false, true, false) === "path-beta");
              assert(evaluateFlags(false, true, true) === "path-beta");
              assert(evaluateFlags(false, false, true) === "path-beta");
              assert(evaluateFlags(false, false, false) === "path-default");
            }

            export function verifyCompoundConditions(): void {
              assert(routeRequest("GET", true, !false) === "401-unauthorized");
              assert(routeRequest("GET", true, !true) === "200-read");
              assert(evaluateFlags(!false, !false, !true) === "path-alpha");
              assert(evaluateFlags(!true, !false, !false) === "path-beta");
            }

            export function runAllVerifications(): void {
              verifyRouteRequestPaths();
              verifyEvaluateFlagsCombinations();
              verifyCompoundConditions();
            }
        ''',
        "tsconfig.json": '''
            {
              "compilerOptions": {
                "target": "ES2020",
                "module": "commonjs",
                "strict": true,
                "esModuleInterop": true,
                "skipLibCheck": true
              },
              "include": ["*.ts"]
            }
        ''',
        "verify_file": "coverage_verification.ts",
    },
    "csharp": {
        "PaymentRouter.cs": '''
            namespace Testable.Demo;

            public static class PaymentRouter
            {
                public static string Route(string method, bool authenticated, bool rateLimited)
                {
                    if (method is not ("GET" or "POST" or "PUT"))
                    {
                        return "405";
                    }

                    if (authenticated && !rateLimited)
                    {
                        return method switch
                        {
                            "GET" => "200-read",
                            "POST" => "201-created",
                            _ => "202-accepted",
                        };
                    }

                    if (!authenticated || rateLimited)
                    {
                        return "401-unauthorized";
                    }

                    return "500-unexpected";
                }

                public static string EvaluateFlags(bool a, bool b, bool c)
                {
                    if ((a && b) || (!c && a))
                    {
                        return "path-alpha";
                    }
                    if ((b || c) && !a)
                    {
                        return "path-beta";
                    }
                    return "path-default";
                }
            }
        ''',
        "CoverageVerification.cs": '''
            using System.Diagnostics;

            namespace Testable.Demo;

            public static class CoverageVerification
            {
                public static void VerifyRouteRequestPaths()
                {
                    Debug.Assert(PaymentRouter.Route("DELETE", true, false) == "405");
                    Debug.Assert(PaymentRouter.Route("PATCH", false, false) == "405");
                    Debug.Assert(PaymentRouter.Route("GET", true, false) == "200-read");
                    Debug.Assert(PaymentRouter.Route("POST", true, false) == "201-created");
                    Debug.Assert(PaymentRouter.Route("PUT", true, false) == "202-accepted");
                    Debug.Assert(PaymentRouter.Route("GET", false, false) == "401-unauthorized");
                    Debug.Assert(PaymentRouter.Route("GET", true, true) == "401-unauthorized");
                    Debug.Assert(PaymentRouter.Route("POST", false, true) == "401-unauthorized");
                }

                public static void VerifyEvaluateFlagsCombinations()
                {
                    Debug.Assert(PaymentRouter.EvaluateFlags(true, true, false) == "path-alpha");
                    Debug.Assert(PaymentRouter.EvaluateFlags(true, true, true) == "path-alpha");
                    Debug.Assert(PaymentRouter.EvaluateFlags(true, false, true) == "path-alpha");
                    Debug.Assert(PaymentRouter.EvaluateFlags(true, false, false) == "path-alpha");
                    Debug.Assert(PaymentRouter.EvaluateFlags(false, true, false) == "path-beta");
                    Debug.Assert(PaymentRouter.EvaluateFlags(false, true, true) == "path-beta");
                    Debug.Assert(PaymentRouter.EvaluateFlags(false, false, true) == "path-beta");
                    Debug.Assert(PaymentRouter.EvaluateFlags(false, false, false) == "path-default");
                }

                public static void VerifyCompoundConditions()
                {
                    Debug.Assert(PaymentRouter.Route("GET", true, !false) == "401-unauthorized");
                    Debug.Assert(PaymentRouter.Route("GET", true, !true) == "200-read");
                    Debug.Assert(PaymentRouter.EvaluateFlags(!false, !false, !true) == "path-alpha");
                    Debug.Assert(PaymentRouter.EvaluateFlags(!true, !false, !false) == "path-beta");
                }

                public static void RunAllVerifications()
                {
                    VerifyRouteRequestPaths();
                    VerifyEvaluateFlagsCombinations();
                    VerifyCompoundConditions();
                }
            }
        ''',
        "verify_file": "CoverageVerification.cs",
    },
}


def create_repo(lang_key: str) -> Path:
    cfg = LANGUAGE_CONFIGS[lang_key]
    repo_dir = OUTPUT_DIR / cfg["repo_name"]
    if repo_dir.exists():
        shutil.rmtree(repo_dir)

    copy_template_files(repo_dir)
    write(repo_dir / "whitebox" / "repo_profiler.py", render_repo_profiler(lang_key, cfg))
    write(repo_dir / "whitebox" / "cli.py", render_cli(cfg["title"]))
    write(repo_dir / "README.md", render_readme(cfg["title"], lang_key, cfg["sample_dir"]))

    sources = SAMPLE_SOURCES[lang_key]
    sample_dir = repo_dir / "sample_code" / cfg["sample_dir"]
    for filename, content in sources.items():
        if filename == "verify_file":
            continue
        write(sample_dir / filename, content)

    write(
        repo_dir / "tests" / "test_score_engine.py",
        render_tests(lang_key, cfg["sample_dir"], sources["verify_file"]),
    )
    write(repo_dir / "repo_data" / "score_history.json", "[]\n")
    return repo_dir


def bootstrap_repo(repo_dir: Path) -> None:
    import subprocess
    import sys

    subprocess.run(
        [sys.executable, "-m", "whitebox.cli", "initial-run"],
        cwd=repo_dir,
        check=True,
        env={"PYTHONPATH": str(repo_dir), **dict(__import__("os").environ)},
    )
    subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v"],
        cwd=repo_dir,
        check=True,
        env={"PYTHONPATH": str(repo_dir), **dict(__import__("os").environ)},
    )


def zip_repo(repo_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(repo_dir.rglob("*")):
            if path.is_file() and ".venv" not in path.parts and "__pycache__" not in path.parts:
                archive.write(path, path.relative_to(repo_dir.parent))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    created: list[tuple[str, Path, Path]] = []

    for lang_key, cfg in LANGUAGE_CONFIGS.items():
        repo_dir = create_repo(lang_key)
        bootstrap_repo(repo_dir)
        zip_path = OUTPUT_DIR / cfg["zip_name"]
        zip_repo(repo_dir, zip_path)
        created.append((cfg["title"], repo_dir, zip_path))
        print(f"Created {repo_dir.name} -> {zip_path.name}")

    manifest = {
        "generated_repos": [
            {
                "language": title,
                "directory": str(repo_dir),
                "zip": str(zip_path),
            }
            for title, repo_dir, zip_path in created
        ]
    }
    write(OUTPUT_DIR / "manifest.json", json.dumps(manifest, indent=2) + "\n")
    print(f"\nAll repos written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

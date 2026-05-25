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

    sub.add_parser("initial-run", help="Run Whitebox initial profiling for Python")

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

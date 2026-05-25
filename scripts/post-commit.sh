#!/usr/bin/env bash
# Local post-commit hook simulation (install: cp scripts/post-commit.sh .git/hooks/post-commit)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
SHA="$(git rev-parse HEAD 2>/dev/null || echo local-commit)"
python -m whitebox.cli on-commit --commit-sha "$SHA"

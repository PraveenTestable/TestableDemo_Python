# Whitebox Repo Demo — Control Flow Metrics

Sample Python repository for **Testable Whitebox initial run** and **commit-triggered score updates**.

## Scenario

1. **Initial run** — Profile the repo, detect languages, compute Control Flow metrics, and persist per-language snapshot under `repo_data/initial_run/`.
2. **Commit trigger** — On each commit, re-profile changed files, update `repo_data/current/`, recompute metric deltas, and append to `repo_data/score_history.json`.

## Control Flow Metrics

| Metric | Key | Description |
|--------|-----|-------------|
| Execution Path Integrity | `execution_path_integrity` | Share of reachable paths exercised vs. detected |
| Decision Outcome Verification | `decision_outcome_verification` | Branch/decision outcomes validated |
| Logical Sub-expression Validation | `logical_subexpression_validation` | Short-circuit and compound conditions covered |
| Total Logical Combinatorial Coverage | `total_logical_combinatorial_coverage` | Truth-table combinations covered |
| Technical Debt Impact | `technical_debt_impact` | Control-flow complexity debt (inverse score) |
| QA Resource Allocation | `qa_resource_allocation` | Estimated QA effort vs. coverage gained |

## Languages (initial run data)

- Python (`sample_code/python/`)
- Java (`sample_code/java/`)
- JavaScript (`sample_code/javascript/`)
- Go (`sample_code/go/`)
- C# (`sample_code/csharp/`)

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Whitebox initial run (all languages)
python -m whitebox.cli initial-run

# Simulate commit webhook / post-commit trigger
python -m whitebox.cli on-commit --commit-sha HEAD

# Run tests (shows known bug vs. fix)
pytest tests/ -v
```

## Known mistake & fix

See [FIX.md](FIX.md). The commit trigger **reprofiles before capturing the prior snapshot**, so `before` and `after` are always identical and deltas stay at `0.0`.

## CI

`.github/workflows/whitebox-score-update.yml` runs the commit trigger on every push.

# Known Mistake — Commit Score Updates Always Report Zero Delta

## Symptom

After committing code changes, Whitebox **Control Flow** scores stay unchanged.  
`score_history.json` records `"delta": 0.0` for every commit even when source files changed.

## Root cause

In `whitebox/commit_trigger.py`, `on_commit()` calls `update_current_repo_data()` **before** loading the prior snapshot:

```python
after = update_current_repo_data(language)   # overwrites repo_data/current/
before = load_language_repo_data(language)     # reads the snapshot we just wrote
delta = score_delta(before, after)             # always identical → delta 0
```

`load_language_repo_data()` correctly reads `repo_data/current/{language}.json`, but that file was already replaced, so `before` and `after` are the same object.

## Simple fix

Swap the order — capture **before**, then re-profile **after**:

```python
before = load_language_repo_data(language)
after = update_current_repo_data(language)
delta = score_delta(before, after)
```

## Verify

```bash
python -m whitebox.cli initial-run

# Apply fix in commit_trigger.py, then:
python -m whitebox.cli on-commit --commit-sha demo-fix-001
cat repo_data/score_history.json
```

After the fix, edit any file under `sample_code/` and rerun `on-commit` — `composite_score` and per-metric deltas should reflect the change.

## Metrics affected

All six Control Flow metrics are recomputed on each commit:

- Execution Path Integrity
- Decision Outcome Verification
- Logical Sub-expression Validation
- Total Logical Combinatorial Coverage
- Technical Debt Impact
- QA Resource Allocation

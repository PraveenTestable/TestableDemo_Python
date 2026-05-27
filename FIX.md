# Commit score delta — resolved

The commit trigger previously refreshed `repo_data/current/` before reading the prior
snapshot, so score deltas were always zero.

## Resolution

`whitebox/commit_trigger.py` now captures the prior snapshot first, then re-profiles:

```python
before = load_language_repo_data(language)
after = update_current_repo_data(language)
delta = score_delta(before, after)
```

## Verify

```bash
python -m whitebox.cli initial-run
python -m whitebox.cli on-commit --commit-sha demo-fix-001
cat repo_data/score_history.json
```

After source changes under `sample_code/python/`, rerun `on-commit` and confirm
non-zero metric deltas in the score history.

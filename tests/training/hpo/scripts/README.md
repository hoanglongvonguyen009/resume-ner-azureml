# HPO Hash Consistency Verification Scripts

## Overview

Scripts to verify and test hash consistency across HPO parent, trial, and refit runs.

## Scripts

### `verify_hash_consistency.py`

Manual verification script to check existing MLflow runs for hash consistency issues.

**Usage:**

```bash
# Check a specific parent run
python tests/training/hpo/scripts/verify_hash_consistency.py \
    --experiment-name "resume_ner_baseline-hpo-distilbert" \
    --parent-run-id "abc123..."

# Check all parent runs in an experiment
python tests/training/hpo/scripts/verify_hash_consistency.py \
    --experiment-name "resume_ner_baseline-hpo-distilbert" \
    --check-all

# Output as JSON
python tests/training/hpo/scripts/verify_hash_consistency.py \
    --experiment-name "resume_ner_baseline-hpo-distilbert" \
    --check-all \
    --json
```

**What it checks:**

1. ✅ Parent runs have v2 `study_key_hash` tags (with fingerprints)
2. ✅ Trial runs have matching `study_key_hash` as parent
3. ✅ Refit runs have matching `study_key_hash` as parent
4. ✅ Refit runs have `refit.of_trial_run_id` linking tag
5. ✅ All hashes are consistent across run types

**Output:**

- Summary statistics
- List of issues found (if any)
- Detailed breakdown of parent/trial/refit runs
- Exit code 1 if issues found, 0 if all good

## Integration Tests

See `tests/training/hpo/integration/test_hash_consistency.py` for automated tests.

**Run tests:**

```bash
pytest tests/training/hpo/integration/test_hash_consistency.py -v
```

## Common Issues and Fixes

### Issue: "Trial run has mismatched study_key_hash"

**Cause:** Trial run computed v1 hash while parent has v2 hash.

**Fix:** Update trial run creation to always compute v2 hash (see migration plan).

### Issue: "Refit run missing refit.of_trial_run_id tag"

**Cause:** Refit linking code failed or wasn't executed.

**Fix:** Check refit run creation logs, ensure `_link_refit_to_trial_run` is called.

### Issue: "Parent run missing v2 tags"

**Cause:** Parent run created before Phase 2 tags were implemented.

**Fix:** Re-run HPO or manually set tags using `_set_phase2_hpo_tags`.

## Best Practices

1. **Run verification after HPO:** Always verify hash consistency after running HPO
2. **Check before selection:** Verify hashes before running champion selection
3. **Monitor in CI/CD:** Add verification as part of integration tests
4. **Fix immediately:** Address hash mismatches as soon as detected


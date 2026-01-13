# Checkpoint Resolution Test Scripts

This directory contains test scripts for validating checkpoint resolution in the benchmarking workflow.

## Manual Test Script

### `test_checkpoint_resolution_manual.py`

A manual test script that validates checkpoint resolution from various sources (local disk, MLflow artifacts).

**Usage:**

```bash
# Test checkpoint resolution for a specific backbone
python -m tests.evaluation.selection.scripts.test_checkpoint_resolution_manual \
    --experiment-name resume_ner_baseline \
    --backbone distilbert

# With custom paths
python -m tests.evaluation.selection.scripts.test_checkpoint_resolution_manual \
    --experiment-name resume_ner_baseline \
    --backbone distilroberta \
    --config-dir /path/to/config \
    --root-dir /path/to/project
```

**What it tests:**

1. **Champion Selection**: Finds the best trial (champion) for the given backbone
2. **Local Checkpoint Check**: Checks if checkpoint exists on local disk
3. **Refit Run Discovery**: Searches for refit runs using multiple strategies:
   - Full hash match (study_key_hash + trial_key_hash)
   - Study hash only (for legacy runs)
   - Parent-child relationship check
   - Last resort: any refit run in experiment
4. **Parent Run Check**: Checks if parent HPO run has checkpoint artifacts
5. **Artifact Discovery**: Lists artifacts in each run to find checkpoint paths
6. **Checkpoint Acquisition**: Attempts to download checkpoint from MLflow using artifact acquisition logic

**Output:**

The script provides detailed output showing:
- Which champion was selected
- Which runs were found and checked
- What artifacts were found in each run
- Whether checkpoint acquisition succeeded

**Exit Codes:**

- `0`: Test passed - checkpoint resolution successful
- `1`: Test failed - checkpoint resolution failed

## Automated Tests

See `../integration/` for automated unit and integration tests:
- `test_checkpoint_acquisition_for_benchmarking.py`: Tests refit run discovery and artifact checking
- `test_benchmarking_checkpoint_resolution.py`: Tests full workflow from champion selection to checkpoint acquisition

## Common Issues and Solutions

### Issue: "No checkpoint artifacts found in this run"

**Cause**: Checkpoints are not uploaded to MLflow, or they're in a different run.

**Solutions**:
1. Check if refit runs exist: The script will search for them automatically
2. Check parent HPO run: The script will check this as a fallback
3. Verify HPO was run with refit enabled: Check HPO config for `refit.enabled: true`
4. Manually verify artifacts in MLflow UI

### Issue: "Could not acquire checkpoint from any run"

**Cause**: Checkpoints exist but artifact acquisition is failing.

**Solutions**:
1. Check artifact paths: The script shows what artifacts are found
2. Verify artifact acquisition config: Check `config/artifact_acquisition.yaml`
3. Check MLflow permissions: Ensure you can download artifacts
4. Try manual download from MLflow UI to verify artifacts are accessible

### Issue: "No champion found"

**Cause**: No eligible HPO runs found, or selection criteria not met.

**Solutions**:
1. Check HPO runs exist: Verify HPO experiments have finished runs
2. Check selection config: Verify `min_trials_per_group` and other criteria in `config/best_model_selection.yaml`
3. Check artifact availability: If `require_artifact_available: true`, ensure runs have `code.artifact.available='true'` tag


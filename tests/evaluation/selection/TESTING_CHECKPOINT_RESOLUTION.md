# Testing Checkpoint Resolution for Benchmarking

This document describes the test suite created to prevent issues with checkpoint acquisition in the benchmarking workflow (Step 6 of `02_best_config_selection.ipynb`).

## Overview

The tests cover the checkpoint resolution workflow that was causing failures:
- Checkpoints not found in trial runs (they're in refit runs)
- Artifact acquisition failing due to incorrect run selection
- Refit run discovery failing due to attribute access issues
- Hash mismatches between benchmark runs and HPO runs

## Test Files

### 1. Integration Tests

#### `integration/test_checkpoint_acquisition_for_benchmarking.py`

Tests the core checkpoint acquisition logic:

- **Refit Run Discovery**:
  - Finding refit runs by hash match
  - Finding refit runs by study hash only (legacy)
  - Finding refit runs via parent-child relationships
  - Last resort: finding any refit run in experiment

- **Checkpoint Artifact Discovery**:
  - Finding checkpoints in refit runs
  - Finding checkpoints in parent HPO runs
  - Handling trial runs with no artifacts
  - Various checkpoint artifact path formats

- **Edge Cases**:
  - Missing `parent_run_id` attribute
  - Refit runs without `trial_key_hash` tag
  - Multiple refit runs
  - No checkpoint found anywhere

#### `integration/test_benchmarking_checkpoint_resolution.py`

Tests the full workflow:

- **Local Disk Resolution**:
  - Resolving from `checkpoint_path` in champion data
  - Resolving from `trial_dir` using hash-based search
  - Legacy trial directory structures

- **MLflow Resolution**:
  - Acquiring from refit runs
  - Acquiring from parent HPO runs
  - Fallback strategies

- **Full Workflow Integration**:
  - Benchmarking with local checkpoint
  - Benchmarking with MLflow checkpoint
  - End-to-end workflow validation

### 2. Manual Test Script

#### `scripts/test_checkpoint_resolution_manual.py`

A standalone script that can be run manually to test checkpoint resolution on real MLflow data.

**Features**:
- Tests actual MLflow experiments
- Provides detailed diagnostics
- Shows which runs are checked and what artifacts are found
- Validates the full resolution workflow

**Usage**:
```bash
python -m tests.evaluation.selection.scripts.test_checkpoint_resolution_manual \
    --experiment-name resume_ner_baseline \
    --backbone distilbert
```

## Running the Tests

### Automated Tests

```bash
# Run all checkpoint resolution tests
pytest tests/evaluation/selection/integration/test_checkpoint_acquisition_for_benchmarking.py -v
pytest tests/evaluation/selection/integration/test_benchmarking_checkpoint_resolution.py -v

# Run specific test class
pytest tests/evaluation/selection/integration/test_checkpoint_acquisition_for_benchmarking.py::TestRefitRunDiscovery -v

# Run with coverage
pytest tests/evaluation/selection/integration/ --cov=evaluation.selection --cov-report=html
```

### Manual Test Script

```bash
# Test a specific backbone
python -m tests.evaluation.selection.scripts.test_checkpoint_resolution_manual \
    --backbone distilbert

# Test with custom paths
python -m tests.evaluation.selection.scripts.test_checkpoint_resolution_manual \
    --backbone distilroberta \
    --config-dir /workspaces/resume-ner-azureml/config \
    --root-dir /workspaces/resume-ner-azureml
```

## Test Coverage

### Scenarios Covered

1. **Refit Run Discovery**:
   - ✅ Exact hash match (study + trial)
   - ✅ Partial hash match (study only)
   - ✅ Parent-child relationship
   - ✅ Last resort (any refit run)
   - ✅ Parent HPO run check

2. **Artifact Discovery**:
   - ✅ Checkpoint in refit run
   - ✅ Checkpoint in parent run
   - ✅ No checkpoint in trial run
   - ✅ Various artifact path formats

3. **Checkpoint Acquisition**:
   - ✅ From refit run (success)
   - ✅ From parent run (fallback)
   - ✅ No checkpoint found (error handling)

4. **Edge Cases**:
   - ✅ Missing `parent_run_id` attribute
   - ✅ Legacy runs without tags
   - ✅ Multiple refit runs
   - ✅ Empty artifact lists

## Preventing Common Issues

### Issue 1: "No checkpoint artifacts found in this run"

**Test Coverage**: `TestCheckpointArtifactDiscovery.test_no_checkpoint_in_trial_run`

**Prevention**: Tests verify that trial runs are skipped when they have no artifacts, and the code searches for refit runs instead.

### Issue 2: "Failed to download artifacts from path 'checkpoint'"

**Test Coverage**: `TestCheckpointAcquisitionWorkflow.test_acquire_from_refit_run_success`

**Prevention**: Tests verify that artifact paths are discovered correctly before attempting download.

### Issue 3: "'RunInfo' object has no attribute 'parent_run_id'"

**Test Coverage**: `TestEdgeCases.test_parent_run_id_not_available`

**Prevention**: Tests verify that `getattr()` is used safely to access `parent_run_id`.

### Issue 4: "Could not acquire checkpoint from any run"

**Test Coverage**: `TestCheckpointAcquisitionWorkflow.test_acquire_from_parent_hpo_run_fallback`

**Prevention**: Tests verify multiple fallback strategies are tried in order.

## Integration with CI/CD

These tests should be run:
1. **Before merging PRs** that touch checkpoint acquisition logic
2. **After HPO runs** to validate checkpoint uploads
3. **Periodically** to catch regressions

### CI Configuration Example

```yaml
# .github/workflows/test-checkpoint-resolution.yml
name: Test Checkpoint Resolution

on:
  pull_request:
    paths:
      - 'src/evaluation/selection/**'
      - 'notebooks/02_best_config_selection.ipynb'
      - 'tests/evaluation/selection/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run checkpoint resolution tests
        run: |
          pytest tests/evaluation/selection/integration/test_checkpoint_acquisition_for_benchmarking.py -v
          pytest tests/evaluation/selection/integration/test_benchmarking_checkpoint_resolution.py -v
```

## Future Enhancements

1. **Mock MLflow Server**: Use a real MLflow tracking server in tests
2. **Performance Tests**: Measure checkpoint acquisition time
3. **Error Recovery Tests**: Test retry logic and error handling
4. **Multi-Platform Tests**: Test on Colab, Kaggle, and local environments

## Related Documentation

- `scripts/README.md`: Detailed usage for manual test script
- `MASTER-merged-hpo-retrieval-benchmarking-refactor.plan.md`: Overall plan
- `02_best_config_selection.ipynb`: Notebook with Step 6 implementation


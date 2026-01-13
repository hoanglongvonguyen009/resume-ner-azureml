# CV Trial Run Hash Computation Tests

## Overview

These tests verify the priority hierarchy for hash computation in `_create_trial_run()`:
1. Priority 1: Use provided hashes (from arguments)
2. Priority 2: Get from parent run tags (source of truth)
3. Priority 3: Compute v2 hashes from configs (fallback)

## Test Files

### `test_cv_hash_computation.py`

#### Test Classes

**`TestCVTrialRunHashComputation`**
- `test_priority_1_use_provided_hashes`: Verifies provided hashes are used when available
- `test_priority_2_get_from_parent_tags`: Tests retrieval from parent run tags
- `test_priority_3_compute_v2_from_configs`: Tests v2 computation fallback
- `test_hash_consistency_with_parent`: Ensures trial hash matches parent hash
- `test_missing_train_config_still_computes_hash`: Tests eval config fallback
- `test_error_handling_parent_run_not_found`: Tests graceful error handling
- `test_no_hpo_parent_run_id_returns_none`: Tests early return when no parent

## Coverage

### Success Cases
- ✅ Priority hierarchy works correctly
- ✅ Hash consistency between parent and trial runs
- ✅ v2 hash computation from configs

### Failure Cases
- ✅ Missing parent run tags
- ✅ Parent run fetch errors
- ✅ Missing train_config eval section

### Edge Cases
- ✅ Eval config fallback (train_config -> hpo_config -> objective)
- ✅ No parent run ID provided

## Running Tests

```bash
# Run all CV hash tests
pytest tests/training/hpo/unit/test_cv_hash_computation.py -v

# Run specific test
pytest tests/training/hpo/unit/test_cv_hash_computation.py::TestCVTrialRunHashComputation::test_hash_consistency_with_parent -v

# Run with coverage
pytest tests/training/hpo/unit/test_cv_hash_computation.py --cov=training.hpo.execution.local.cv --cov-report=html
```

## Notes

- Tests verify the exact priority hierarchy implemented
- Tests ensure v2 hashes are used consistently (no v1 fallbacks)
- Tests verify error handling doesn't crash the process
- All tests reuse fixtures and avoid duplicated logic



# Sweep Tracker Hash and Search Tests

## Overview

These tests cover the v2 hash migration fixes for HPO sweep tracking, specifically:
1. v2 hash computation in `start_sweep_run()`
2. Best trial search using `study_key_hash` + `trial_number` + `parentRunId`
3. Error handling and edge cases

## Test Files

### `test_sweep_tracker_hash_and_search.py`

#### Test Classes

**`TestSweepTrackerV2HashComputation`**
- `test_v2_hash_computation_success`: Verifies v2 hash is computed when all configs available
- `test_v2_hash_computation_missing_train_config`: Tests graceful handling when train_config missing
- `test_v2_hash_computation_empty_eval_config`: Tests fallback to objective when eval config empty

**`TestSweepTrackerBestTrialSearch`**
- `test_best_trial_search_by_study_key_hash_success`: Verifies search works with correct filter
- `test_best_trial_search_filters_by_parent_run_id`: Ensures only runs from current parent are found
- `test_best_trial_search_no_parent_study_key_hash`: Tests behavior when parent lacks hash tag
- `test_best_trial_search_no_matching_runs`: Tests graceful handling when no runs found
- `test_best_trial_search_exception_handling`: Tests error handling during search

**`TestSweepTrackerTrialNumberExtraction`**
- `test_extract_trial_number_from_tag`: Tests extraction from trial_number tag
- `test_extract_trial_number_from_run_name`: Tests fallback to run name parsing
- `test_extract_trial_number_returns_none_when_not_found`: Tests None return when not found

## Coverage

### Success Cases
- ✅ v2 hash computation with all configs
- ✅ Best trial search finds correct run
- ✅ Trial number extraction from tags and run names

### Failure Cases
- ✅ Missing train_config
- ✅ Empty eval config
- ✅ Missing parent study_key_hash tag
- ✅ No matching runs found
- ✅ MLflow API exceptions

### Edge Cases
- ✅ Filtering by parent run ID to avoid cross-sweep matches
- ✅ Fallback evaluation config from objective

## Running Tests

```bash
# Run all sweep tracker tests
pytest tests/infrastructure/tracking/unit/test_sweep_tracker_hash_and_search.py -v

# Run specific test class
pytest tests/infrastructure/tracking/unit/test_sweep_tracker_hash_and_search.py::TestSweepTrackerBestTrialSearch -v

# Run with coverage
pytest tests/infrastructure/tracking/unit/test_sweep_tracker_hash_and_search.py --cov=infrastructure.tracking.mlflow.trackers.sweep_tracker --cov-report=html
```

## Notes

- Tests use mocks to avoid requiring actual MLflow server
- Tests verify both success and failure paths
- Tests ensure no redundant fallback logic remains
- All tests follow DRY principles, reusing fixtures from conftest.py



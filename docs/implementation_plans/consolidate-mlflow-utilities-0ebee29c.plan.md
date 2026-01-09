<!-- 0ebee29c-7db9-4ee6-b44d-0aad8c1fd322 1239f7b3-ea29-4cba-ab61-6c529ea519b8 -->
# Consolidate MLflow Utilities - Detailed Implementation Plan

This plan consolidates MLflow-related utilities scattered across the codebase into a centralized `src/tracking/mlflow/` module structure, following the same pattern as the paths/naming consolidation.

## Important Clarifications

### Module Location

- **Decision**: Create new top-level `src/tracking/mlflow/` directory (not under `orchestration/jobs/tracking/`)
- **Rationale**: These utilities are used across multiple modules (orchestration, model_conversion, shared) and should be accessible at the top level
- **Structure**: `src/tracking/mlflow/` will contain submodules for different concerns

### Azure ML Monkey-Patch Duplication

- **Current locations**:
- `src/orchestration/jobs/tracking/trackers/sweep_tracker.py` (lines 18-62)
- `src/model_conversion/convert_to_onnx.py` (lines 18-46)
- **Issue**: Same monkey-patch code duplicated in two places
- **Solution**: Centralize in `tracking/mlflow/compatibility.py` and auto-apply on import

### Artifact Upload Patterns

- **Current locations**:
- `sweep_tracker.py`: Checkpoint archive uploads with retry logic
- `convert_to_onnx.py`: ONNX model uploads (simple, no retry)
- `benchmark_tracker.py`, `conversion_tracker.py`, `training_tracker.py`: Various artifact uploads
- `training/trainer.py`: Training checkpoint uploads
- **Issue**: Inconsistent error handling, some with retry, some without
- **Solution**: Standardize in `tracking/mlflow/artifacts.py` with consistent retry and error handling

### Run Lifecycle Management

- **Current locations**:
- `local_sweeps.py`: Refit run termination (lines 1000-1059) - complex logic with status checks
- `conversion/executor.py`: Conversion run termination (lines 290-319) - simple termination
- `final_training/executor.py`: Final training run termination (lines 450-512) - simple termination
- `hpo/local/cv/orchestrator.py`: Trial run termination
- `hpo/local/trial/run_manager.py`: Trial run termination
- **Issue**: Duplicated termination logic with inconsistent error handling
- **Solution**: Centralize in `tracking/mlflow/lifecycle.py` with safe termination patterns

### Run Creation Patterns

- **Current locations**:
- `tracking/utils/helpers.py`: `create_child_run()` context manager (lines 18-212)
- `conversion/executor.py`: Direct `client.create_run()` calls
- `sweep_tracker.py`: Run creation in context managers
- Various trackers: Different run creation patterns
- **Issue**: Inconsistent patterns for creating runs (with/without active context, parent/child relationships)
- **Solution**: Standardize in `tracking/mlflow/runs.py` with clear patterns

## Detailed Implementation Checklist

### Phase 1: Pre-Implementation Analysis

- [ ] **Audit Azure ML monkey-patch usage**
- [ ] Search for all files importing `azureml.mlflow` or using `azureml_artifacts_builder`
- [ ] Document all locations where patch is needed
- [ ] Verify patch is only needed for artifact uploads, not other MLflow operations

- [ ] **Audit artifact upload patterns**
- [ ] List all files using `mlflow.log_artifact()` or `client.log_artifact()`
- [ ] Document which use retry logic and which don't
- [ ] Document error handling patterns (fail vs. warn vs. ignore)
- [ ] Identify all artifact types being uploaded (checkpoints, ONNX models, logs, etc.)

- [ ] **Audit run lifecycle patterns**
- [ ] List all files using `client.set_terminated()` or `mlflow.end_run()`
- [ ] Document status checks before termination (checking if RUNNING)
- [ ] Document tag-setting patterns before termination
- [ ] Document error handling for termination failures

- [ ] **Audit run creation patterns**
- [ ] List all files creating MLflow runs (`create_run`, `start_run`, context managers)
- [ ] Document parent-child relationship patterns
- [ ] Document experiment ID resolution patterns
- [ ] Document tag-setting patterns

- [ ] **Verify dependencies**
- [ ] Check if `tracking/mlflow/` can depend on `orchestration/jobs/tracking/utils/mlflow_utils.py`
- [ ] Check if circular dependencies would be introduced
- [ ] Document import strategy

### Phase 2: Create Tracking Module Structure

- [ ] **Create src/tracking/ directory structure**
- [ ] Create `src/tracking/` directory
- [ ] Create `src/tracking/__init__.py`
- [ ] Create `src/tracking/mlflow/` directory
- [ ] Create `src/tracking/mlflow/__init__.py`

- [ ] **Create tracking/mlflow/compatibility.py**
- [ ] Move monkey-patch logic from `sweep_tracker.py` and `convert_to_onnx.py`
- [ ] Create `apply_azureml_artifact_patch()` function
- [ ] Auto-apply patch on module import (using module-level execution)
- [ ] Add guard to prevent double-patching (check for `__wrapped__` attribute)
- [ ] Add logging when patch is applied
- [ ] Export `apply_azureml_artifact_patch` in `tracking/mlflow/__init__.py`
- [ ] **Remove duplicate code** from `sweep_tracker.py` and `convert_to_onnx.py`
- [ ] **Add import** `from tracking.mlflow.compatibility import apply_azureml_artifact_patch` at top of both files (or just import the module)

- [ ] **Create tracking/mlflow/artifacts.py**
- [ ] Create `log_artifact_safe()` function:
  - [ ] Parameters: `local_path`, `artifact_path=None`, `run_id=None`, `max_retries=5`
  - [ ] Use `retry_with_backoff` from `orchestration.jobs.tracking.utils.mlflow_utils`
  - [ ] Handle both `mlflow.log_artifact()` (active run) and `client.log_artifact()` (explicit run_id)
  - [ ] Return `bool` (True if succeeded, False if failed)
  - [ ] Log warnings on failure but don't raise exceptions
- [ ] Create `log_artifacts_safe()` function for directories:
  - [ ] Similar to `log_artifact_safe()` but for `mlflow.log_artifacts()`
  - [ ] Handle directory uploads with progress logging
- [ ] Create `upload_checkpoint_archive()` helper:
  - [ ] Specialized for checkpoint archive uploads
  - [ ] Includes manifest logging
  - [ ] Handles cleanup on failure
- [ ] Export all functions in `tracking/mlflow/__init__.py`

- [ ] **Create tracking/mlflow/lifecycle.py**
- [ ] Create `terminate_run_safe()` function:
  - [ ] Parameters: `run_id`, `status="FINISHED"`, `tags=None`, `check_status=True`
  - [ ] Check run status before termination if `check_status=True`
  - [ ] Set tags before termination if provided
  - [ ] Handle errors gracefully (log but don't raise)
  - [ ] Return `bool` (True if succeeded, False if failed)
- [ ] Create `ensure_run_terminated()` function:
  - [ ] Parameters: `run_id`, `expected_status="FINISHED"`
  - [ ] Check current status, terminate only if still RUNNING
  - [ ] Handle already-terminated runs gracefully
  - [ ] Return `bool`
- [ ] Create `terminate_run_with_tags()` helper:
  - [ ] Convenience function for common pattern: set tags then terminate
  - [ ] Parameters: `run_id`, `status`, `tags`
- [ ] Export all functions in `tracking/mlflow/__init__.py`

- [ ] **Create tracking/mlflow/runs.py**
- [ ] Move `create_child_run()` from `orchestration/jobs/tracking/utils/helpers.py`
- [ ] Improve error handling and documentation
- [ ] Create `create_run_safe()` function:
  - [ ] Parameters: `experiment_id`, `run_name`, `tags=None`, `parent_run_id=None`
  - [ ] Handle experiment ID resolution
  - [ ] Handle parent-child relationships
  - [ ] Return run ID or None on failure
- [ ] Create `get_or_create_experiment()` helper:
  - [ ] Parameters: `experiment_name`
  - [ ] Get existing or create new experiment
  - [ ] Return experiment ID
- [ ] Create `resolve_experiment_id()` helper:
  - [ ] Parameters: `experiment_name=None`, `parent_run_id=None`, `active_run=None`
  - [ ] Try multiple strategies to resolve experiment ID
  - [ ] Return experiment ID or None
- [ ] Export all functions in `tracking/mlflow/__init__.py`

- [ ] **Create tracking/mlflow/urls.py**
- [ ] Move `get_mlflow_run_url()` from `orchestration/jobs/tracking/utils/mlflow_utils.py`
- [ ] Keep existing functionality (Azure ML and standard MLflow URI handling)
- [ ] Export in `tracking/mlflow/__init__.py`

- [ ] **Create tracking/mlflow/init.py**
- [ ] Export all public functions from submodules
- [ ] Import compatibility module first (to auto-apply patch)
- [ ] Re-export `retry_with_backoff` from `orchestration.jobs.tracking.utils.mlflow_utils` for convenience
- [ ] Document module purpose and usage

### Phase 3: Update Existing Code to Use New Modules

- [ ] **Update sweep_tracker.py**
- [ ] Remove monkey-patch code (lines 18-62)
- [ ] Add import: `from tracking.mlflow import log_artifact_safe, terminate_run_safe`
- [ ] Replace `mlflow.log_artifact()` calls with `log_artifact_safe()`
- [ ] Replace manual retry logic with `log_artifact_safe()` (uses retry_with_backoff internally)
- [ ] Update `log_best_checkpoint()` to use new utilities

- [ ] **Update convert_to_onnx.py**
- [ ] Remove monkey-patch code (lines 18-46)
- [ ] Add import: `from tracking.mlflow import log_artifact_safe`
- [ ] Replace `mlflow.log_artifact()` call with `log_artifact_safe()`
- [ ] Remove try/except around artifact logging (handled by `log_artifact_safe()`)

- [ ] **Update local_sweeps.py**
- [ ] Add import: `from tracking.mlflow import terminate_run_safe`
- [ ] Replace refit run termination logic (lines 1000-1059) with `terminate_run_safe()`
- [ ] Simplify error handling (now handled by utility)
- [ ] Keep status check logic but use `terminate_run_safe(check_status=True)`

- [ ] **Update conversion/executor.py**
- [ ] Add import: `from tracking.mlflow import terminate_run_safe`
- [ ] Replace run termination logic (lines 290-319) with `terminate_run_safe()`
- [ ] Simplify error handling

- [ ] **Update final_training/executor.py**
- [ ] Add import: `from tracking.mlflow import terminate_run_safe`
- [ ] Replace run termination logic (lines 450-512) with `terminate_run_safe()`
- [ ] Simplify error handling

- [ ] **Update other trackers**
- [ ] `benchmark_tracker.py`: Use `log_artifact_safe()` for artifact uploads
- [ ] `conversion_tracker.py`: Use `log_artifact_safe()` for artifact uploads
- [ ] `training_tracker.py`: Use `log_artifact_safe()` and `log_artifacts_safe()` for uploads

- [ ] **Update training/trainer.py**
- [ ] Add import: `from tracking.mlflow import log_artifact_safe, log_artifacts_safe`
- [ ] Replace `mlflow.log_artifact()` and `mlflow.log_artifacts()` calls with safe versions

- [ ] **Update helpers.py**
- [ ] Move `create_child_run()` to `tracking/mlflow/runs.py`
- [ ] Update import in `helpers.py` to re-export from new location (for backward compatibility)
- [ ] Or remove `helpers.py` if no longer needed

- [ ] **Update mlflow_utils.py**
- [ ] Move `get_mlflow_run_url()` to `tracking/mlflow/urls.py`
- [ ] Keep `retry_with_backoff()` in `mlflow_utils.py` (used by tracking/mlflow internally)
- [ ] Update imports in files using `get_mlflow_run_url()`

### Phase 4: Update Imports Across Codebase

- [ ] **Search and replace imports**
- [ ] Find all files importing from `orchestration.jobs.tracking.utils.helpers`
- [ ] Update to import from `tracking.mlflow.runs`
- [ ] Find all files importing `get_mlflow_run_url` from `mlflow_utils`
- [ ] Update to import from `tracking.mlflow.urls`

- [ ] **Update base_tracker.py**
- [ ] Consider if experiment setup logic should use `tracking/mlflow/runs.py` utilities
- [ ] Keep existing logic if it's tracker-specific

- [ ] **Verify no circular dependencies**
- [ ] Check that `tracking/mlflow/` doesn't import from `orchestration/jobs/tracking/` (except for `retry_with_backoff`)
- [ ] Ensure `retry_with_backoff` can be imported without circular dependency
- [ ] Consider moving `retry_with_backoff` to `tracking/mlflow/utils.py` if needed

### Phase 5: Testing and Verification

- [ ] **Test Azure ML compatibility patch**
- [ ] Verify patch is applied on import
- [ ] Test artifact uploads work with patch
- [ ] Verify no double-patching occurs
- [ ] Test in both Azure ML and local MLflow environments

- [ ] **Test artifact upload utilities**
- [ ] Test `log_artifact_safe()` with active run
- [ ] Test `log_artifact_safe()` with explicit run_id
- [ ] Test retry logic on transient failures
- [ ] Test error handling (should not raise, should return False)
- [ ] Test `log_artifacts_safe()` for directories

- [ ] **Test run lifecycle utilities**
- [ ] Test `terminate_run_safe()` with RUNNING run
- [ ] Test `terminate_run_safe()` with already-terminated run
- [ ] Test `terminate_run_safe()` with tags
- [ ] Test error handling (should not raise, should return False)
- [ ] Test `ensure_run_terminated()` in various scenarios

- [ ] **Test run creation utilities**
- [ ] Test `create_child_run()` context manager (moved from helpers.py)
- [ ] Test `create_run_safe()` with various parameters
- [ ] Test `get_or_create_experiment()`
- [ ] Test `resolve_experiment_id()` with different strategies

- [ ] **Integration tests**
- [ ] Test HPO sweep with new utilities (checkpoint upload, refit termination)
- [ ] Test conversion with new utilities (ONNX upload, run termination)
- [ ] Test final training with new utilities (run termination)
- [ ] Test benchmarking with new utilities (artifact uploads)

- [ ] **Backward compatibility**
- [ ] Verify existing code still works after migration
- [ ] Test notebooks still work (they use orchestration.* imports)
- [ ] Verify no breaking changes to public APIs

### Phase 6: Documentation and Cleanup

- [ ] **Update documentation**
- [ ] Document new `tracking/mlflow/` module structure
- [ ] Add usage examples for each utility function
- [ ] Document migration path from old patterns
- [ ] Update README or architecture docs

- [ ] **Code cleanup**
- [ ] Remove duplicate code from original locations
- [ ] Remove unused imports
- [ ] Fix any linter warnings
- [ ] Ensure consistent code style

- [ ] **Final verification**
- [ ] Run full test suite
- [ ] Verify no regressions
- [ ] Check code coverage for new modules
- [ ] Verify all MLflow operations use new utilities

## Quick Reference: File Mapping

### New Module Structure

- `src/tracking/mlflow/compatibility.py` - Azure ML monkey-patch (NEW)
- `src/tracking/mlflow/artifacts.py` - Artifact upload utilities (NEW)
- `src/tracking/mlflow/lifecycle.py` - Run lifecycle management (NEW)
- `src/tracking/mlflow/runs.py` - Run creation utilities (NEW, moves from helpers.py)
- `src/tracking/mlflow/urls.py` - URL generation (moves from mlflow_utils.py)

### Code to Remove/Update

- `orchestration/jobs/tracking/trackers/sweep_tracker.py` - Remove monkey-patch (lines 18-62)
- `model_conversion/convert_to_onnx.py` - Remove monkey-patch (lines 18-46)
- `orchestration/jobs/tracking/utils/helpers.py` - Move `create_child_run()` to runs.py
- `orchestration/jobs/tracking/utils/mlflow_utils.py` - Move `get_mlflow_run_url()` to urls.py

### Code to Update (Use New Utilities)

- `local_sweeps.py` - Use `terminate_run_safe()` for refit runs
- `conversion/executor.py` - Use `terminate_run_safe()` for conversion runs
- `final_training/executor.py` - Use `terminate_run_safe()` for training runs
- All trackers - Use `log_artifact_safe()` for uploads
- `training/trainer.py` - Use `log_artifact_safe()` and `log_artifacts_safe()`

## Notes

- The monkey-patch should auto-apply on import of `tracking.mlflow` module
- All artifact uploads should use `log_artifact_safe()` for consistency
- All run terminations should use `terminate_run_safe()` for consistency
- Error handling should be graceful (log warnings, return False, don't raise)
- Maintain backward compatibility where possible
- Consider moving `retry_with_backoff` to `tracking/mlflow/utils.py` if circular dependency issues arise

### To-dos

- [ ] Phase 1: Audit all MLflow patterns (monkey-patch, artifact uploads, run lifecycle, run creation)
- [ ] Phase 2: Create src/tracking/mlflow/ module structure with submodules
- [ ] Create tracking/mlflow/compatibility.py with Azure ML monkey-patch
- [ ] Create tracking/mlflow/artifacts.py with log_artifact_safe() and related utilities
- [ ] Create tracking/mlflow/lifecycle.py with terminate_run_safe() and related utilities
- [ ] Create tracking/mlflow/runs.py with run creation utilities (move create_child_run from helpers.py)
- [ ] Create tracking/mlflow/urls.py with get_mlflow_run_url() (move from mlflow_utils.py)
- [ ] Update sweep_tracker.py to use new utilities (remove monkey-patch, use log_artifact_safe)
- [ ] Update convert_to_onnx.py to use new utilities (remove monkey-patch, use log_artifact_safe)
- [ ] Update local_sweeps.py, conversion/executor.py, final_training/executor.py to use terminate_run_safe()
- [ ] Update all trackers (benchmark, conversion, training) to use log_artifact_safe()
- [ ] Update imports across codebase to use new tracking/mlflow modules
- [ ] Phase 5: Test all new utilities and integration with existing code
- [ ] Phase 6: Update documentation and final cleanup
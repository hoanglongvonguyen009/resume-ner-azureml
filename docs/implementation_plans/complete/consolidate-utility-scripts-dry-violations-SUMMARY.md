# Consolidate Utility Scripts DRY Violations - Summary

**Date**: 2026-01-15

**Plan**: `FINISHED-consolidate-utility-scripts-dry-violations.plan.md`

**Status**: ✅ Complete

## What Was Done

Eliminated duplicate logic and overlapping responsibilities across utility scripts tagged with `type: utility` in metadata by consolidating them into single sources of truth (SSOT) while maintaining backward compatibility and minimizing breaking changes.

### Consolidation Results

**Single Sources of Truth Established:**

1. **Selection Module Wrappers** → Removed 8 deprecated wrapper files
   - Deleted: `selection/local_selection.py`, `selection/local_selection_v2.py`, `selection/artifact_acquisition.py`, `selection/trial_finder.py`, `selection/disk_loader.py`, `selection/cache.py`, `selection/study_summary.py`, `selection/mlflow_selection.py`
   - All code already uses `evaluation.selection.*` directly
   - `selection/__init__.py` updated to proxy deleted modules to `evaluation.selection.*`
   - Kept: `selection/selection.py`, `selection/selection_logic.py`, `selection/types.py` (unique logic)

2. **Config Directory Inference** → Consolidated to SSOT
   - Removed: `training.execution.run_names._infer_config_dir_from_output()`
   - SSOT: `infrastructure.tracking.mlflow.utils.infer_config_dir_from_path()`
   - All call sites updated to use SSOT

3. **MLflow Setup Utilities** → Removed deprecated wrapper
   - Removed: `infrastructure.tracking.mlflow.setup.setup_mlflow_for_stage()`
   - SSOT: `infrastructure.tracking.mlflow.setup.setup_mlflow()`
   - Updated exports in `infrastructure.tracking.mlflow.__init__.py` and `orchestration.__init__.py`
   - Verified separation of concerns (setup vs run lifecycle vs env vars)

4. **Path Resolution Utilities** → Consolidated to SSOT
   - Removed: `orchestration.jobs.hpo.local.trial.execution.TrialExecutor._find_project_root()`
   - SSOT: `infrastructure.paths.find_project_root()`
   - All call sites updated to use SSOT

5. **Checkpoint Path Resolution** → Consolidated to SSOT
   - Removed: `orchestration.jobs.local_selection_v2._get_checkpoint_path_from_trial_dir()`
   - SSOT: `evaluation.selection.local_selection_v2._get_checkpoint_path_from_trial_dir()`
   - Import added, call site updated

### Files Modified

**Deleted Files (8):**
- `src/selection/local_selection.py`
- `src/selection/local_selection_v2.py`
- `src/selection/artifact_acquisition.py`
- `src/selection/trial_finder.py`
- `src/selection/disk_loader.py`
- `src/selection/cache.py`
- `src/selection/study_summary.py`
- `src/selection/mlflow_selection.py`

**Modified Files:**
- `src/selection/__init__.py` - Updated to proxy deleted modules
- `src/training/execution/run_names.py` - Removed duplicate, uses SSOT
- `src/infrastructure/tracking/mlflow/setup.py` - Removed deprecated wrapper
- `src/infrastructure/tracking/mlflow/__init__.py` - Updated exports
- `src/orchestration/__init__.py` - Updated exports
- `src/orchestration/jobs/hpo/local/trial/execution.py` - Removed duplicate, uses SSOT
- `src/orchestration/jobs/local_selection_v2.py` - Removed duplicate, uses SSOT

### Code Reduction

- **Removed duplicate functions**: 4 functions/methods
- **Removed wrapper files**: 8 files (~1,000+ lines of duplicate code)
- **Eliminated duplicate logic**: ~1,200+ lines of duplicate implementations removed
- **Consolidated to SSOT**: All functionality now uses single source of truth

### Key Decisions and Trade-offs

1. **Backward Compatibility**: Maintained through `selection/__init__.py` proxy that automatically redirects deleted modules to `evaluation.selection.*` equivalents.

2. **Unique Logic Preserved**: Kept `selection/selection.py` (AzureML-specific logic), `selection/selection_logic.py` (selection algorithms), and `selection/types.py` (type definitions) as they contain unique logic, not wrappers.

3. **No Breaking Changes**: All removed functions were either:
   - Never used (e.g., `setup_mlflow_for_stage`)
   - Already replaced by direct imports (e.g., selection wrappers)
   - Replaced with SSOT imports (e.g., config inference, path resolution)

4. **Separation of Concerns**: Verified that functions with different responsibilities (e.g., `setup_mlflow()` vs `create_training_mlflow_run()`) are kept separate.

### Test Results

- **1,271 tests passing** ✓
- **No regressions from refactoring detected** ✓
- **All removed functions verified unused in tests** ✓
- **All SSOT functions verified working correctly** ✓
- **62 failures are pre-existing issues** (alembic migrations, missing dependencies, test setup issues) - not related to refactoring

### Verification

- ✅ All wrapper files deleted
- ✅ All duplicate functions removed
- ✅ All call sites updated to use SSOT functions
- ✅ All imports verified working correctly
- ✅ No references to removed functions remain in src/ or tests/
- ✅ All SSOT functions verified:
  - `setup_mlflow()` - SSOT for MLflow configuration
  - `infer_config_dir_from_path()` - SSOT for config directory inference
  - `find_project_root()` - SSOT for project root finding
  - `_get_checkpoint_path_from_trial_dir()` - SSOT for checkpoint path resolution

### Follow-up

- Monitor usage patterns to ensure SSOT functions are being used correctly
- Consider removing `selection/__init__.py` proxy in a future release after deprecation period
- Continue using SSOT functions for all new code


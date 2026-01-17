# Consolidate Drive/Backup Scripts - DRY Violations

## Goal

Eliminate DRY violations across drive and backup-related scripts by:

1. Consolidating duplicate path handling logic
2. Removing duplicate config_dir inference
3. Generalizing backup callback patterns beyond HPO
4. Centralizing immediate backup patterns
5. Reusing Drive path rejection patterns consistently
6. **Standardizing backup pattern across all workflows** (HPO, training, conversion, benchmarking)

## Status

**Last Updated**: 2026-01-17
**Documentation Updated**: 2026-01-17 - Updated all related README files

### Completed Steps
- ✅ Step 1: Fix config_dir inference in setup_hpo_mlflow_run (already correct - only infers when None)
- ✅ Step 2: Create generic immediate backup utility
- ✅ Step 3: Use immediate backup utility in sweep.py
- ✅ Step 4: Centralize Drive path checks in backup utilities
- ✅ Step 5: Replace string checks with is_drive_path() utility
- ✅ Step 6: Standardize backup pattern for training/conversion functions
- ✅ Step 7: Update notebooks to use standardized backup pattern
- ✅ Step 8: Update other files to use centralized utilities (optional)
- ✅ Step 9: Update tests
- ✅ Step 10: Update README files to document standardized backup pattern

### Pending Steps
None - all steps completed

## Preconditions

- Existing backup infrastructure from `20260117-1910-centralize-incremental-study-db-backup-569526b.plan.md` is complete
- `DriveBackupStore` class exists and works correctly
- `is_drive_path()` utility exists and works correctly

## Script Inventory

### 1. Core Infrastructure Scripts

#### `src/infrastructure/storage/drive.py`
**Purpose**: Core DriveBackupStore class for backup/restore operations
**Key Functions**:
- `DriveBackupStore.backup()` - Backs up files/directories (rejects Drive paths)
- `DriveBackupStore.drive_path_for()` - Maps local paths to Drive paths (rejects Drive paths)
- `DriveBackupStore.restore()` - Restores from Drive
- `DriveBackupStore.as_backup_callback()` - Creates backup callback
- `create_colab_store()` - Factory function (auto-detects root_dir/config_dir)

**Status**: ✅ Complete, already rejects Drive paths

#### `src/infrastructure/paths/drive.py`
**Purpose**: Path mapping utilities for Drive backup paths
**Key Functions**:
- `get_drive_backup_base()` - Gets base Drive backup directory from config
- `get_drive_backup_path()` - Converts local path to Drive backup path (uses DriveBackupStore internally)
- `resolve_output_path_for_colab()` - Resolves output paths, redirecting to Drive on Colab

**Status**: ✅ Uses DriveBackupStore internally (already consolidated)

### 2. HPO-Specific Backup Scripts

#### `src/orchestration/jobs/hpo/local/backup.py`
**Purpose**: HPO-specific backup utilities and callbacks
**Key Functions**:
- `create_incremental_backup_callback()` - Creates Optuna callback for incremental backup
- `create_study_db_backup_callback()` - Convenience wrapper for study.db
- `backup_hpo_study_to_drive()` - Final backup of study.db and study folder

**Status**: ✅ Complete, but pattern could be generalized

### 3. HPO Execution Scripts

#### `src/training/hpo/execution/local/sweep.py`
**Purpose**: Main HPO sweep orchestration
**Key Functions**:
- `run_local_hpo_sweep()` - Main HPO sweep function
- Immediate backup after study creation (lines 767-785)
- Uses `create_incremental_backup_callback()` (lines 1061-1066)

**Issues**:
- Line 608: Has `project_config_dir` parameter
- Line 818: Calls `setup_hpo_mlflow_run()` which re-infers `config_dir` even though `project_config_dir` is available
- Immediate backup logic (lines 767-785) is duplicated pattern

#### `src/training/hpo/tracking/setup.py`
**Purpose**: MLflow run setup for HPO
**Key Functions**:
- `setup_hpo_mlflow_run()` - Sets up MLflow run name and context

**Issues**:
- Lines 86-93: Re-infers `config_dir` even when caller provides it
- Lines 168-176: Re-infers `config_dir` again (duplicate inference)
- Lines 213-215: Re-infers `config_dir` in fallback path
- Should trust provided `config_dir` parameter (already documented in docstring)

#### `src/training/hpo/core/study.py`
**Purpose**: Optuna study management
**Key Functions**:
- `StudyManager.restore_from_drive()` - Restores study.db from Drive

**Status**: ✅ Uses `is_drive_path()` correctly (line 238)

#### `src/training/hpo/utils/helpers.py`
**Purpose**: HPO utility functions
**Key Functions**:
- `restore_hpo_checkpoint_from_drive()` - Restores checkpoint from Drive

**Status**: ✅ Uses `is_drive_path()` correctly (line 107)

### 4. Training/Conversion Scripts

#### `src/training/execution/executor.py`
**Purpose**: Execute final training with best configuration
**Key Functions**:
- `execute_final_training()` - Executes final training subprocess

**Status**: ✅ No backup logic (focuses on execution only)
**Note**: Backup is handled **manually in notebooks** after calling this function (see `notebooks/02_best_config_selection.ipynb` lines 1157-1177)

#### `src/deployment/conversion/orchestration.py`
**Purpose**: Execute model conversion to ONNX
**Key Functions**:
- `execute_conversion()` - Executes conversion subprocess

**Status**: ✅ No backup logic (focuses on execution only)
**Note**: Backup is handled **manually in notebooks** after calling this function (see `notebooks/02_best_config_selection.ipynb` lines 1317-1322)

**Design Pattern**: 
- Core execution functions focus on execution (separation of concerns)
- Backup is handled at orchestration level (notebooks)
- **Gap**: If called directly from code (not notebook), backup must be added manually
- **Potential improvement**: Could add optional `backup_to_drive` parameter like HPO functions

### 5. Benchmarking Scripts

#### `src/evaluation/benchmarking/orchestrator.py`
**Purpose**: Benchmarking orchestration for best trials
**Key Functions**:
- `benchmark_champions()` - Benchmarks champions (has backup_to_drive parameter)
- `benchmark_best_trials()` - Benchmarks best trials (has backup_to_drive parameter)
- Backup logic at lines 843-848

**Issues**:
- Line 651: Uses `str(benchmark_output).startswith("/content/drive")` instead of `is_drive_path()`
- Line 843: Uses `str(benchmark_output).startswith("/content/drive")` instead of `is_drive_path()`
- Line 846: Uses `str(benchmark_output).startswith("/content/drive")` instead of `is_drive_path()`
- Should use centralized `is_drive_path()` utility

#### `src/evaluation/selection/workflows/benchmarking_workflow.py`
**Purpose**: Benchmarking workflow orchestration
**Key Functions**:
- `run_benchmarking_workflow()` - Main workflow function (passes backup_to_drive through)

**Status**: ✅ Just passes parameters through, no direct backup logic

#### `src/evaluation/selection/artifact_unified/compat.py`
**Purpose**: Artifact acquisition compatibility layer
**Key Functions**:
- `acquire_checkpoint_unified()` - Acquires checkpoints (uses drive_store.backup() directly)

**Status**: ✅ Uses DriveBackupStore.backup() directly (which already rejects Drive paths)

#### `src/evaluation/selection/trial_finder.py`
**Purpose**: Trial finding utilities
**Key Functions**:
- Various trial finding functions

**Issues**:
- Line 818: Uses `str(old_backbone_dir).startswith("/content/drive")` instead of `is_drive_path()`

### 6. Notebook Scripts

#### `notebooks/01_orchestrate_training_colab.ipynb`
**Purpose**: Colab notebook for training orchestration
**Key Functions**:
- `backup_to_drive()` - Wrapper function using DriveBackupStore
- `restore_from_drive()` - Wrapper function using DriveBackupStore

**Status**: ✅ Uses DriveBackupStore correctly

#### `notebooks/02_best_config_selection.ipynb`
**Purpose**: Colab notebook for best config selection, final training, and conversion
**Key Functions**:
- Backup final training checkpoint (lines 1157-1172)
- Backup conversion output (lines 1317-1322)

**Issues**:
- Line 1161: Uses `str(checkpoint_path).startswith("/content/drive")` instead of `is_drive_path()`
- Uses `drive_store.backup()` directly (which is fine, but string check is DRY violation)

**Note**: Notebooks are typically not part of main codebase consolidation, but this pattern should be noted for consistency

## How Backup Works for Training/Conversion

**Current Design**:
1. Core execution functions (`execute_final_training()`, `execute_conversion()`) **do NOT have backup logic**
2. They focus solely on execution (separation of concerns)
3. Backup is handled **manually in notebooks** after calling these functions:
   - `notebooks/02_best_config_selection.ipynb` backs up final checkpoint (lines 1157-1177)
   - `notebooks/02_best_config_selection.ipynb` backs up conversion output (lines 1317-1322)

**Implications**:
- ✅ **Pros**: Clean separation of concerns, execution functions are focused
- ⚠️ **Cons**: If called directly from code (not notebook), backup must be added manually
- ⚠️ **Gap**: No standardized backup pattern for training/conversion (unlike HPO which has `backup_to_drive` parameter)

**Comparison with HPO**:
- HPO functions (`run_local_hpo_sweep()`) have `backup_to_drive` parameter built-in
- Training/conversion functions do NOT have backup parameters
- This inconsistency could be addressed in a future refactoring

## DRY Violations Identified

### Category 1: Config Directory Inference Duplication

**Violation**: Multiple functions re-infer `config_dir` even when caller provides it

**Locations**:
1. `src/training/hpo/tracking/setup.py`:
   - `setup_hpo_mlflow_run()` lines 86-93: Re-infers when `config_dir` is None
   - `setup_hpo_mlflow_run()` lines 168-176: Re-infers again (duplicate)
   - `setup_hpo_mlflow_run()` lines 213-215: Re-infers in fallback path
   - `commit_run_name_version()` lines 295-303: Re-infers when `config_dir` is None

2. `src/training/hpo/execution/local/sweep.py`:
   - Line 818: Calls `setup_hpo_mlflow_run()` with `project_config_dir`, but function still re-infers
   - Line 829: Passes `project_config_dir` but function may still re-infer

**Root Cause**: Functions don't trust provided `config_dir` parameter, always re-inferring even when provided

**Impact**: 
- Unnecessary computation
- Potential inconsistencies if inference logic differs
- Violates DRY principle

### Category 2: Immediate Backup Pattern Duplication

**Violation**: Immediate backup logic after study creation is duplicated

**Locations**:
1. `src/training/hpo/execution/local/sweep.py` lines 767-785:
   ```python
   if backup_to_drive and backup_enabled and storage_path:
       if storage_path.exists() and not is_drive_path(storage_path):
           result = backup_to_drive(storage_path, is_directory=False)
           # ... logging ...
   ```

**Pattern**: Check if backup enabled → Check if path exists → Check if not Drive path → Backup → Log

**Impact**: 
- Pattern could be reused for other immediate backup scenarios
- Logic is embedded in sweep.py instead of reusable utility

### Category 3: Drive Path Check Pattern Duplication

**Violation**: Same pattern of checking `is_drive_path()` before backup/restore appears in multiple places, OR using string checks instead of `is_drive_path()`

**Locations Using `is_drive_path()` (correct but duplicated)**:
1. `src/orchestration/jobs/hpo/local/backup.py` line 76: Check before incremental backup
2. `src/training/hpo/execution/local/sweep.py` line 771: Check before immediate backup
3. `src/training/hpo/utils/helpers.py` line 107: Check before restore
4. `src/training/hpo/core/study.py` line 238: Check before restore

**Locations Using String Checks (DRY violation - should use `is_drive_path()`)**:
1. `src/evaluation/benchmarking/orchestrator.py` line 651: `str(benchmark_output).startswith("/content/drive")`
2. `src/evaluation/benchmarking/orchestrator.py` line 843: `str(benchmark_output).startswith("/content/drive")`
3. `src/evaluation/benchmarking/orchestrator.py` line 846: `str(benchmark_output).startswith("/content/drive")`
4. `src/evaluation/selection/trial_finder.py` line 818: `str(old_backbone_dir).startswith("/content/drive")`
5. `notebooks/02_best_config_selection.ipynb` line 1161: `str(checkpoint_path).startswith("/content/drive")` (notebook - lower priority)

**Pattern**: 
```python
# Correct pattern (but duplicated):
if is_drive_path(path):
    logger.debug(f"Skipping - path is already in Drive: {path}")
    return

# Incorrect pattern (string check instead of utility):
if str(path).startswith("/content/drive"):
    # ...
```

**Impact**: 
- Pattern is repeated 4+ times (correct usage)
- String checks are used instead of utility in 4+ places (incorrect usage)
- Could be centralized in backup utility functions
- String checks are brittle (hardcoded path prefix)

### Category 4: Backup Callback Pattern (Potential Generalization)

**Violation**: Backup callback pattern is HPO-specific but could be generalized

**Current**: `create_incremental_backup_callback()` in `backup.py` is Optuna-specific

**Potential**: Could create generic callback pattern for any callback system (not just Optuna)

**Impact**: 
- Low priority (Optuna-specific is fine for now)
- But pattern could be reused for other ML frameworks

## Consolidation Approach

### Principle 1: Reuse-First
- Extend existing `DriveBackupStore` methods rather than creating new utilities
- Reuse `is_drive_path()` checks in centralized backup functions
- Trust provided `config_dir` parameters instead of re-inferring

### Principle 2: SRP Pragmatically
- Keep HPO-specific backup logic in `backup.py` (domain-specific)
- Extract generic immediate backup pattern to shared utility
- Centralize Drive path checks in backup utility functions

### Principle 3: Minimize Breaking Changes
- Update function signatures to accept `config_dir` but make it optional (backward compatible)
- Add new utility functions rather than changing existing ones
- Keep existing callback patterns working

## Steps

### Step 1: Fix Config Directory Inference in setup_hpo_mlflow_run

**File**: `src/training/hpo/tracking/setup.py`

**Changes**:

1. **Remove duplicate inference in `setup_hpo_mlflow_run()`**:
   - Lines 86-93: Remove re-inference when `config_dir` is provided
   - Lines 168-176: Remove duplicate inference (already handled above)
   - Trust provided `config_dir` parameter (only infer if None)

2. **Remove duplicate inference in fallback path**:
   - Lines 213-215: Only infer if `config_dir` is None

3. **Update `commit_run_name_version()`**:
   - Lines 295-303: Trust provided `config_dir` (only infer if None)

**Success criteria**:
- `setup_hpo_mlflow_run()` trusts provided `config_dir` parameter
- No duplicate inference when `config_dir` is provided
- Function only infers `config_dir` when explicitly None
- All existing tests pass
- `sweep.py` can pass `project_config_dir` without re-inference

### Step 2: Create Generic Immediate Backup Utility

**File**: `src/orchestration/jobs/hpo/local/backup.py`

**Changes**:

1. Add new function `immediate_backup_if_needed()`:
   ```python
   def immediate_backup_if_needed(
       target_path: Path,
       backup_to_drive: Callable[[Path, bool], bool],
       backup_enabled: bool = True,
       is_directory: bool = False,
   ) -> bool:
       """
       Perform immediate backup if conditions are met.
       
       Checks: backup_enabled, path exists, path is not Drive path.
       Returns True if backup succeeded, False otherwise.
       """
   ```

2. Function should:
   - Check if `backup_enabled` is True
   - Check if `target_path.exists()`
   - Check if not `is_drive_path(target_path)`
   - Call `backup_to_drive()` if all conditions met
   - Log success/failure
   - Return bool (True if backed up, False otherwise)

**Success criteria**:
- `immediate_backup_if_needed()` function exists
- Function handles all edge cases (missing path, Drive path, disabled backup)
- Function logs appropriately
- Can be reused in `sweep.py` and other places

### Step 3: Use Immediate Backup Utility in sweep.py

**File**: `src/training/hpo/execution/local/sweep.py`

**Changes**:

1. Add import: `from orchestration.jobs.hpo.local.backup import immediate_backup_if_needed`

2. Replace lines 767-785 with:
   ```python
   # Immediate backup of study.db after creation/loading
   if backup_to_drive and backup_enabled and storage_path:
       immediate_backup_if_needed(
           target_path=storage_path,
           backup_to_drive=backup_to_drive,
           backup_enabled=backup_enabled,
           is_directory=False,
       )
   ```

**Success criteria**:
- Immediate backup logic uses centralized utility
- Behavior unchanged (same checks, same logging)
- Code is more maintainable

### Step 4: Centralize Drive Path Checks in Backup Utilities

**File**: `src/orchestration/jobs/hpo/local/backup.py`

**Changes**:

1. Update `create_incremental_backup_callback()`:
   - Keep existing `is_drive_path()` check (already correct)
   - Add helper function `_should_skip_backup()` to centralize logic:
     ```python
     def _should_skip_backup(
         target_path: Path,
         backup_enabled: bool,
     ) -> bool:
         """Check if backup should be skipped."""
         if not backup_enabled:
             return True
         if is_drive_path(target_path):
             return True
         if not target_path.exists():
             return True
         return False
     ```

2. Update `immediate_backup_if_needed()` to use `_should_skip_backup()`

**Success criteria**:
- Drive path check logic is centralized in `_should_skip_backup()`
- Both `create_incremental_backup_callback()` and `immediate_backup_if_needed()` use it
- Logic is consistent across all backup functions

### Step 5: Replace String Checks with is_drive_path() Utility

**Files**:
- `src/evaluation/benchmarking/orchestrator.py` (lines 651, 843, 846)
- `src/evaluation/selection/trial_finder.py` (line 818)
- `notebooks/02_best_config_selection.ipynb` (line 1161) - Optional (notebook, lower priority)

**Changes**:

1. **In `orchestrator.py`**:
   - Add import: `from common.shared.platform_detection import is_drive_path`
   - Line 651: Replace `str(benchmark_output).startswith("/content/drive")` with `is_drive_path(benchmark_output)`
   - Line 843: Replace `not str(benchmark_output).startswith("/content/drive")` with `not is_drive_path(benchmark_output)`
   - Line 846: Replace `str(benchmark_output).startswith("/content/drive")` with `is_drive_path(benchmark_output)`

2. **In `trial_finder.py`**:
   - Add import: `from common.shared.platform_detection import is_drive_path`
   - Line 818: Replace `str(old_backbone_dir).startswith("/content/drive")` with `is_drive_path(old_backbone_dir)`

3. **In `notebooks/02_best_config_selection.ipynb` (Optional)**:
   - Add import: `from common.shared.platform_detection import is_drive_path`
   - Line 1161: Replace `str(checkpoint_path).startswith("/content/drive")` with `is_drive_path(checkpoint_path)`
   - **Note**: Notebooks are lower priority, but this improves consistency

**Success criteria**:
- All string checks replaced with `is_drive_path()` utility
- Behavior unchanged (same logic, more maintainable)
- All tests pass

### Step 6: Standardize Backup Pattern for Training/Conversion Functions

**Files**:
- `src/training/execution/executor.py` - `execute_final_training()`
- `src/deployment/conversion/orchestration.py` - `execute_conversion()`

**Changes**:

1. **Add backup parameters to `execute_final_training()`**:
   - Add `backup_to_drive: Optional[Callable[[Path, bool], bool]] = None` parameter
   - Add `backup_enabled: bool = True` parameter
   - After training completes (before returning checkpoint_dir), add backup logic:
     ```python
     # Backup checkpoint if enabled
     if backup_to_drive and backup_enabled and checkpoint_dir:
         from orchestration.jobs.hpo.local.backup import immediate_backup_if_needed
         immediate_backup_if_needed(
             target_path=checkpoint_dir,
             backup_to_drive=backup_to_drive,
             backup_enabled=backup_enabled,
             is_directory=True,
         )
     ```

2. **Add backup parameters to `execute_conversion()`**:
   - Add `backup_to_drive: Optional[Callable[[Path, bool], bool]] = None` parameter
   - Add `backup_enabled: bool = True` parameter
   - After conversion completes (before returning conversion_output_dir), add backup logic:
     ```python
     # Backup conversion output if enabled
     if backup_to_drive and backup_enabled and conversion_output_dir:
         from orchestration.jobs.hpo.local.backup import immediate_backup_if_needed
         immediate_backup_if_needed(
             target_path=conversion_output_dir,
             backup_to_drive=backup_to_drive,
             backup_enabled=backup_enabled,
             is_directory=True,
         )
     ```

**Success criteria**:
- `execute_final_training()` has `backup_to_drive` and `backup_enabled` parameters
- `execute_conversion()` has `backup_to_drive` and `backup_enabled` parameters
- Both functions use `immediate_backup_if_needed()` utility
- Backup happens automatically after execution completes
- Parameters are optional (backward compatible)
- All existing tests pass

### Step 7: Update Notebooks to Use Standardized Backup Pattern

**Files**:
- `notebooks/02_best_config_selection.ipynb`

**Changes**:

1. **Update final training section** (around line 1145):
   - Pass `backup_to_drive=backup_to_drive` and `backup_enabled=BACKUP_ENABLED` to `execute_final_training()`
   - Remove manual backup code (lines 1157-1177) - backup now happens inside function

2. **Update conversion section** (around line 1285):
   - Pass `backup_to_drive=backup_to_drive` and `backup_enabled=BACKUP_ENABLED` to `execute_conversion()`
   - Remove manual backup code (lines 1317-1322) - backup now happens inside function

**Success criteria**:
- Notebook passes `backup_to_drive` parameter to both functions
- Manual backup code removed from notebook
- Backup still works (now handled by functions)
- Notebook is cleaner and more maintainable

### Step 8: Update Other Files to Use Centralized Utilities (Optional) ✅

**Files**:
- `src/training/hpo/utils/helpers.py` (line 107)
- `src/training/hpo/core/study.py` (line 238)
- `src/evaluation/benchmarking/orchestrator.py` (line 845)

**Changes**:

1. ✅ Updated `orchestrator.py` to use `immediate_backup_if_needed()` instead of manual backup pattern
2. ✅ Verified `helpers.py` and `study.py` already use `is_drive_path()` correctly for restore operations
3. ✅ Verified `compat.py` uses `drive_store.backup()` directly (acceptable - different context, uses DriveBackupStore API correctly)

**Decision**: 
- Restore operations (`helpers.py`, `study.py`) remain unchanged (they're correct as-is, restore logic is different from backup)
- Backup operations now use centralized utilities (`immediate_backup_if_needed()`)
- `compat.py` uses `DriveBackupStore.backup()` directly (acceptable - different context)

**Success criteria**:
- ✅ Restore operations remain unchanged (they're correct as-is)
- ✅ Backup operations use centralized utilities
- ✅ `orchestrator.py` now uses `immediate_backup_if_needed()` for consistency

### Step 9: Update Tests ✅

**Files**:
- `tests/orchestration/jobs/hpo/local/test_backup.py`
- `tests/hpo/integration/test_hpo_sweep_setup.py`

**Changes**:

1. ✅ Added comprehensive tests for `immediate_backup_if_needed()`:
   - ✅ Test with enabled backup, local path (file)
   - ✅ Test with enabled backup, local path (directory)
   - ✅ Test with disabled backup (should skip)
   - ✅ Test with Drive path (should skip)
   - ✅ Test with missing path (should skip)
   - ✅ Test with backup_to_drive=None (should skip)
   - ✅ Test handling backup failure gracefully
   - ✅ Test handling exceptions gracefully

2. ✅ Added comprehensive tests for `_should_skip_backup()`:
   - ✅ Test skip when backup_disabled
   - ✅ Test skip when path is Drive
   - ✅ Test skip when path missing
   - ✅ Test no skip when all conditions met
   - ✅ Test priority order of skip conditions

3. ✅ Added test for `setup_hpo_mlflow_run()`:
   - ✅ Test that `config_dir=None` triggers inference (added to `test_hpo_sweep_setup.py`)
   - ✅ Existing test already verifies that provided `config_dir` is trusted

**Success criteria**:
- ✅ All new functions have tests (13 new test cases)
- ✅ All new tests pass (8 tests for `immediate_backup_if_needed`, 5 tests for `_should_skip_backup`)
- ✅ Test coverage maintained or improved
- ✅ Existing tests still pass

## Success Criteria (Overall)

- ✅ No duplicate `config_dir` inference when parameter is provided
- ✅ Immediate backup pattern is centralized and reusable
- ✅ Drive path checks are consistent across backup functions
- ✅ All string checks replaced with `is_drive_path()` utility
- ✅ **Standardized backup pattern across all workflows** (HPO, training, conversion, benchmarking)
- ✅ Training/conversion functions have `backup_to_drive` parameters (consistent with HPO)
- ✅ Notebooks use standardized pattern (no manual backup code)
- ✅ All tests pass
- ✅ No regressions in existing functionality
- ✅ Code is more maintainable (DRY violations removed)

## Implementation Notes

### Key Design Decisions

1. **Trust provided parameters**: Functions should trust `config_dir` when provided, only inferring when None
2. **Centralize patterns, not implementations**: Extract common patterns (immediate backup, skip checks) but keep domain-specific logic separate
3. **Backward compatibility**: All changes are backward compatible (optional parameters, new utilities)

### Testing Strategy

1. Test that provided `config_dir` is trusted (no re-inference)
2. Test immediate backup utility with all edge cases
3. Test centralized skip logic
4. Integration test: Run HPO and verify backups work correctly

### Rollout Plan

1. Fix config_dir inference first (prevents unnecessary computation)
2. Add immediate backup utility (enables reuse)
3. Update sweep.py to use utility (removes duplication)
4. Centralize skip checks (improves consistency)
5. Update tests (verifies correctness)

## Related Files

- `src/infrastructure/storage/drive.py` - Core DriveBackupStore (already complete)
- `src/orchestration/jobs/hpo/local/backup.py` - Add immediate backup utility
- `src/training/hpo/execution/local/sweep.py` - Use immediate backup utility
- `src/training/hpo/tracking/setup.py` - Fix config_dir inference
- `src/evaluation/benchmarking/orchestrator.py` - Replace string checks with is_drive_path()
- `src/evaluation/selection/trial_finder.py` - Replace string checks with is_drive_path()
- `notebooks/02_best_config_selection.ipynb` - Replace string checks with is_drive_path() (optional)
- `tests/orchestration/jobs/hpo/local/test_backup.py` - Add tests
- `tests/evaluation/benchmarking/` - Update tests if needed

## Dependencies

- `common.shared.platform_detection.is_drive_path()` - Must work correctly
- `DriveBackupStore` - Must work correctly
- Existing backup callback infrastructure - Must be complete


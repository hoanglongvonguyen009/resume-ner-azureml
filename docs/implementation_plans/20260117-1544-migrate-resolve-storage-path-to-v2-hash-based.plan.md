# Migrate resolve_storage_path to v2 Hash-Based Study Folders

## Goal

Migrate all scripts that use the old `study_name` format (e.g., `hpo_distilbert_test_v3`) for checkpoint path resolution to use the v2 hash-based folder structure (`study-{hash}`). The v2 system uses `study_key_hash` to create deterministic study folders, but `resolve_storage_path()` and its callers still rely on the legacy `study_name` format.

## Status

**Last Updated**: 2026-01-17

### Completed Steps
- ✅ Step 1: Update `resolve_storage_path()` to support v2 hash-based paths
- ✅ Step 2: Update `backup_hpo_study_to_drive()` in backup.py
- ✅ Step 3: Update `setup_checkpoint_storage()` in helpers.py
- ✅ Step 4: Update `generate_missing_trial_meta()` in trial/meta.py
- ✅ Step 5: Update `find_best_trial_from_study()` in trial_finder.py
- ✅ Step 6: Update `load_study_from_disk()` in study_summary.py
- ✅ Step 7: Update `create_or_load_study()` in study.py to pass study_key_hash

### Pending Steps
- ✅ Step 8: Verify all tests pass and update if needed
- ⏳ Step 8: Verify all tests pass and update if needed

## Preconditions

- V2 hash-based folder system is already implemented and working (creates `study-{hash}` folders)
- `study_key_hash` computation is available via `compute_study_key_hash_v2()`
- `find_study_folder_in_backbone_dir()` utility exists for v2 folder discovery
- Existing v2 study folders are in use (e.g., `study-c3659fea`)

## Problem Analysis

### Current State

1. **`resolve_storage_path()`** in `src/training/hpo/checkpoint/storage.py`:
   - Uses `study_name` parameter to build paths like `{backbone}/{study_name}/study.db`
   - Results in old format paths: `hpo_distilbert_test_v3/study.db`
   - Does not know about v2 hash-based folders (`study-{hash}`)

2. **Callers of `resolve_storage_path()`**:
   - `backup.py`: Passes old `study_name` from config
   - `helpers.py`: Passes old `study_name` from config
   - `trial/meta.py`: Passes old `study_name` from config (2 places)
   - `trial_finder.py`: Passes old `study_name` but also has v2 discovery logic
   - `study_summary.py`: Passes old `study_name` from config

3. **V2 System**:
   - Creates folders like `study-c3659fea` based on `study_key_hash`
   - `study.db` is stored in `study-{hash}/study.db`
   - `find_study_folder_in_backbone_dir()` can discover v2 folders

### Root Cause

The checkpoint path resolution system (`resolve_storage_path()`) was designed for the old `study_name` format and has not been updated to use the v2 hash-based folder structure. This causes:
- Log messages showing old paths (`hpo_distilbert_test_v3/study.db`) even when v2 folders exist
- Potential path mismatches between actual v2 folders and resolved paths
- Confusion about which path format is correct

## Steps

### Step 1: Update `resolve_storage_path()` to support v2 hash-based paths

**File**: `src/training/hpo/checkpoint/storage.py`

**Changes**:
1. Add optional `study_key_hash` parameter to `resolve_storage_path()`
2. When `study_key_hash` is provided, use v2 folder structure:
   - Compute `study8` token from `study_key_hash` (first 8 chars)
   - Build path: `{backbone}/study-{study8}/study.db`
3. When `study_key_hash` is not provided, fall back to old `study_name` format (backward compatibility)
4. Update function docstring to document both modes

**Success criteria**:
- `resolve_storage_path()` accepts `study_key_hash` parameter
- When `study_key_hash` is provided, returns path to `study-{hash}/study.db`
- When `study_key_hash` is None, falls back to old `study_name` behavior
- `uvx mypy src/training/hpo/checkpoint/storage.py` passes with 0 errors

**Implementation notes**:
- Use `study_key_hash[:8]` to get `study8` token (first 8 characters)
- Path format: `output_dir / backbone / f"study-{study8}" / "study.db"`
- Keep backward compatibility for callers that don't have `study_key_hash`

### Step 2: Update `backup_hpo_study_to_drive()` in backup.py

**File**: `src/orchestration/jobs/hpo/local/backup.py`

**Changes**:
1. Remove dependency on `study_name` for path resolution
2. Use `find_study_folder_in_backbone_dir()` to find v2 study folder
3. If v2 folder found, use `study_folder / "study.db"` as checkpoint path
4. Remove old `study_name`-based path construction (lines 62-77)
5. Update logging to show v2 paths instead of old paths

**Success criteria**:
- `backup_hpo_study_to_drive()` uses v2 folder discovery
- Log messages show v2 paths (`study-c3659fea/study.db`) instead of old paths
- Backup logic works correctly with v2 folders
- `uvx mypy src/orchestration/jobs/hpo/local/backup.py` passes with 0 errors

**Implementation notes**:
- Import `find_study_folder_in_backbone_dir` from `evaluation.selection.trial_finder`
- Use v2 folder discovery instead of `resolve_storage_path()` with `study_name`
- Keep `study_name` variable only for logging/display purposes (Optuna study name, not path)

### Step 3: Update `setup_checkpoint_storage()` in helpers.py

**File**: `src/training/hpo/utils/helpers.py`

**Changes**:
1. Add optional `study_key_hash` parameter to `setup_checkpoint_storage()`
2. Pass `study_key_hash` to `resolve_storage_path()` instead of `study_name`
3. Keep `study_name` parameter for Optuna study name (not path resolution)

**Success criteria**:
- `setup_checkpoint_storage()` accepts `study_key_hash` parameter
- Calls `resolve_storage_path()` with `study_key_hash` when available
- Falls back to old behavior when `study_key_hash` is None
- `uvx mypy src/training/hpo/utils/helpers.py` passes with 0 errors

**Implementation notes**:
- `study_name` is still needed for Optuna study name (Optuna API requirement)
- `study_key_hash` is used for path resolution (v2 folder structure)
- These are separate concerns: Optuna study name vs. file system path

### Step 4: Update `generate_missing_trial_meta()` in trial/meta.py

**File**: `src/training/hpo/trial/meta.py`

**Changes**:
1. Replace `resolve_storage_path()` calls with v2 folder discovery
2. Use `find_study_folder_in_backbone_dir()` to find study folders
3. Remove `study_name`-based path construction (lines 308-319, 365-376)
4. Update both code paths (in-memory studies and disk-only processing)

**Success criteria**:
- `generate_missing_trial_meta()` uses v2 folder discovery
- Both code paths (in-memory and disk-only) use v2 folders
- No dependency on old `study_name` format for paths
- `uvx mypy src/training/hpo/trial/meta.py` passes with 0 errors

**Implementation notes**:
- Import `find_study_folder_in_backbone_dir` from `evaluation.selection.trial_finder`
- Use v2 folder discovery in both loops (lines 294-349 and 352-395)
- Keep `study_name` only if needed for other purposes (not path resolution)

### Step 5: Update `find_best_trial_from_study()` in trial_finder.py

**File**: `src/evaluation/selection/trial_finder.py`

**Changes**:
1. Remove `study_name`-based path resolution (lines 545-552)
2. Already uses `find_study_folder_in_backbone_dir()` - verify it's working correctly
3. Remove unused `resolve_storage_path()` import if no longer needed
4. Clean up any remaining `study_name` path construction

**Success criteria**:
- `find_best_trial_from_study()` uses only v2 folder discovery
- No `study_name`-based path resolution remains
- `uvx mypy src/evaluation/selection/trial_finder.py` passes with 0 errors

**Implementation notes**:
- This file already has v2 discovery logic (line 555)
- Remove the old `resolve_storage_path()` call and `study_name` construction (lines 545-552)
- Verify v2 discovery is used consistently

### Step 6: Update `load_study_from_disk()` in study_summary.py

**File**: `src/evaluation/selection/study_summary.py`

**Changes**:
1. Remove `study_name`-based path resolution (lines 111-116)
2. Use `find_study_folder_in_backbone_dir()` to find v2 study folder
3. Remove `resolve_storage_path()` call
4. Use `study_folder / "study.db"` directly

**Success criteria**:
- `load_study_from_disk()` uses v2 folder discovery
- No dependency on old `study_name` format
- `uvx mypy src/evaluation/selection/study_summary.py` passes with 0 errors

**Implementation notes**:
- Import `find_study_folder_in_backbone_dir` from `.trial_finder`
- Use v2 folder discovery instead of `resolve_storage_path()`
- Remove `study_name` variable if only used for path resolution

### Step 7: Update `create_or_load_study()` in study.py to pass study_key_hash

**File**: `src/training/hpo/core/study.py`

**Changes**:
1. Add `study_key_hash` parameter to `create_or_load_study()` method
2. Pass `study_key_hash` to `setup_checkpoint_storage()` when available
3. Update callers in `sweep.py` to pass `study_key_hash`

**Success criteria**:
- `create_or_load_study()` accepts and passes `study_key_hash`
- `sweep.py` passes `study_key_hash` when available
- `uvx mypy src/training/hpo/core/study.py` passes with 0 errors

**Implementation notes**:
- `study_key_hash` is computed early in `sweep.py` (line 651)
- Pass it through the call chain: `sweep.py` → `study.py` → `helpers.py` → `storage.py`
- Keep `study_name` for Optuna API (separate from path resolution)

### Step 8: Verify all tests pass and update if needed

**Files**: All test files related to HPO checkpointing

**Changes**:
1. Run test suite: `uvx pytest tests/ -k hpo -v`
2. Update tests that mock `resolve_storage_path()` to include `study_key_hash`
3. Update tests that verify paths to expect v2 format
4. Add tests for v2 path resolution when `study_key_hash` is provided

**Success criteria**:
- All HPO-related tests pass: `uvx pytest tests/ -k hpo`
- Tests verify v2 path resolution works correctly
- Tests verify backward compatibility (old `study_name` format still works)
- No test failures or warnings

**Implementation notes**:
- Search for tests that use `resolve_storage_path`: `grep -r "resolve_storage_path" tests/`
- Update mocks to accept `study_key_hash` parameter
- Verify both v2 and legacy paths work in tests

## Success Criteria (Overall)

- ✅ All scripts use v2 hash-based folder structure for checkpoint paths
- ✅ `resolve_storage_path()` supports both v2 (`study_key_hash`) and legacy (`study_name`) modes
- ✅ Log messages show v2 paths (`study-c3659fea/study.db`) instead of old paths
- ✅ No dependency on old `study_name` format for file system paths
- ✅ All tests pass: `uvx pytest tests/ -k hpo`
- ✅ Mypy passes: `uvx mypy src/training/hpo src/orchestration/jobs/hpo src/evaluation/selection --show-error-codes`
- ✅ Backward compatibility maintained for callers without `study_key_hash`

## Files Affected

1. `src/training/hpo/checkpoint/storage.py` - Core path resolution function
2. `src/orchestration/jobs/hpo/local/backup.py` - Backup logic
3. `src/training/hpo/utils/helpers.py` - Checkpoint setup utility
4. `src/training/hpo/trial/meta.py` - Trial metadata generation
5. `src/evaluation/selection/trial_finder.py` - Trial finding logic
6. `src/evaluation/selection/study_summary.py` - Study loading
7. `src/training/hpo/core/study.py` - Study creation/loading
8. `src/training/hpo/execution/local/sweep.py` - Main HPO execution (caller updates)

## Related Files

- `src/evaluation/selection/trial_finder.py` - Contains `find_study_folder_in_backbone_dir()` utility
- `src/infrastructure/tracking/mlflow/hash_utils.py` - Contains `compute_study_key_hash_v2()`
- `src/training/hpo/execution/local/sweep.py` - Computes `study_key_hash` early (line 651)

## Notes

- **Optuna Study Name vs. File System Path**: These are separate concerns:
  - Optuna study name: Used by Optuna API (e.g., `optuna.load_study(study_name="...")`)
  - File system path: Where `study.db` is stored (v2: `study-{hash}/study.db`)
- **Backward Compatibility**: Keep support for old `study_name` format when `study_key_hash` is not available
- **V2 Folder Discovery**: Use `find_study_folder_in_backbone_dir()` for read-only path discovery
- **Path Resolution**: Use `resolve_storage_path()` with `study_key_hash` for creating new paths


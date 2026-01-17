# Centralize Incremental study.db Backup

## Goal

Implement centralized incremental backup for `study.db` that:

1. Rejects Drive paths at the backup API boundary (prevents crashes)
2. Backs up `study.db` immediately after creation (not relying on callbacks)
3. Backs up `study.db` after each trial completes (via Optuna callback)
4. Simplifies backup logic by removing mixed-state handling
5. Centralizes all backup logic in one place

## Status

**Last Updated**: 2026-01-17

### Completed Steps

- ⏳ None yet

### Pending Steps

- ⏳ Step 1: Add Drive path rejection in drive.py
- ⏳ Step 2: Create centralized backup callback
- ⏳ Step 3: Add immediate backup after study creation
- ⏳ Step 4: Update sweep.py to use backup callback
- ⏳ Step 5: Simplify backup_hpo_study_to_drive function
- ⏳ Step 6: Update function signatures
- ⏳ Step 7: Update tests

## Preconditions

- Codebase uses v2 hash-based folder structure (`study-{hash}/study.db`)
- Colab environment with Google Drive mounted
- HPO checkpointing enabled
- `backup_to_drive` function available from notebook

## Problem Analysis

### Current Issues

1. **No Drive Path Rejection**: `drive.py` accepts Drive paths, causing crashes when trying to compute relative paths
2. **No Incremental Backup**: `study.db` is only backed up at the end, so if runtime dies, progress is lost
3. **Complex Mixed-State Logic**: Backup code tries to handle "some things in Drive, some local" which is brittle
4. **Scattered Backup Logic**: Backup calls would need to be added in multiple places (study.py, callback.py, sweep.py)

### Solution Approach

1. **Reject Drive paths early**: Add check in `drive.py.backup()` and `drive_path_for()` to reject Drive paths with clear error
2. **Centralized callback**: Create single backup callback in `backup.py` that handles incremental backups
3. **Immediate backup**: Call backup explicitly in `sweep.py` right after `storage_path` is known
4. **Simplified logic**: Remove all mixed-state handling - just check if canonical root is local or Drive

## Steps

### Step 1: Add Drive Path Rejection in drive.py

**File**: `src/infrastructure/storage/drive.py`

**Changes**:

1. Add `is_drive_path()` check at the start of `backup()` method
2. Return error `BackupResult` if path is Drive path
3. Add `is_drive_path()` check in `drive_path_for()` method
4. Raise `ValueError` if path is Drive path

**Success criteria**:

- `drive.py.backup()` rejects Drive paths with clear error message
- `drive.py.drive_path_for()` raises ValueError for Drive paths
- Existing tests still pass
- New test verifies Drive path rejection

### Step 2: Create Reusable Incremental Backup Callback

**File**: `src/orchestration/jobs/hpo/local/backup.py`

**Changes**:

1. Add import: `from training.hpo.core.optuna_integration import import_optuna as _import_optuna`
2. Create reusable function `create_incremental_backup_callback()` that:
   - Takes `target_path: Path`, `backup_to_drive: Callable`, `backup_enabled: bool`, `is_directory: bool = False`
   - Returns Optuna callback function
   - Callback backs up `target_path` after each trial completes
   - Checks `is_drive_path()` before attempting backup
   - Handles errors gracefully (logs but doesn't crash)
   - Can be used for any file or folder (not just `study.db`)
3. Create convenience wrapper `create_study_db_backup_callback()` that:
   - Calls `create_incremental_backup_callback()` with `is_directory=False`
   - Maintains backward compatibility for `study.db`-specific usage

**Success criteria**:

- `create_incremental_backup_callback()` exists and returns callable
- Function works for both files and directories
- Callback backs up target path after trial completes
- Callback skips backup if path is Drive path
- Callback handles errors without crashing
- Can be reused for other files/folders beyond `study.db`

### Step 3: Add Immediate Backup After Study Creation

**File**: `src/training/hpo/execution/local/sweep.py`

**Changes**:

1. After line 758 (after `study_manager.create_or_load_study()` returns)
2. Add immediate backup call:
   - Check if `backup_to_drive` is provided
   - Check if `storage_path` exists and is local
   - Call `backup_to_drive(storage_path, is_directory=False)`
   - Log success/failure

**Success criteria**:

- `study.db` is backed up immediately after study creation
- Backup only happens if path is local (not Drive)
- Errors are logged but don't crash HPO
- Works for both new studies and resumed studies

### Step 4: Update sweep.py to Use Backup Callback

**File**: `src/training/hpo/execution/local/sweep.py`

**Changes**:

1. Add import: `from orchestration.jobs.hpo.local.backup import create_incremental_backup_callback`
2. Around line 1031, after `trial_callback` is created:
   - Create `backup_callback` using `create_incremental_backup_callback()` with:
     - `target_path=storage_path` (the `study.db` file)
     - `backup_to_drive=backup_to_drive`
     - `backup_enabled=backup_enabled`
     - `is_directory=False`
   - Combine `trial_callback` and `backup_callback` into `all_callbacks`
   - Pass `all_callbacks` to `study.optimize()` instead of just `trial_callback`
3. Update function signature to accept `backup_to_drive` and `backup_enabled` parameters

**Success criteria**:

- Backup callback is added to Optuna callbacks
- `study.db` is backed up after each trial completes
- No crashes or errors in HPO execution
- Works with existing trial callback
- Reusable callback pattern allows future extension to other files/folders

### Step 5: Simplify backup_hpo_study_to_drive Function

**File**: `src/orchestration/jobs/hpo/local/backup.py`

**Changes**:

1. Remove all mixed-state logic (no checking Drive for study folders)
2. Simplify to:
   - Find canonical study folder in `backbone_output_dir`
   - Check if canonical folder is Drive or local
   - If Drive → verify only (no backup)
   - If local → backup study.db and study folder
3. Remove legacy fallback logic (no `resolve_storage_path` calls)

**Success criteria**:

- Function is simplified (no mixed-state handling)
- Only backs up from canonical local root
- Verifies if already in Drive
- No crashes from Drive path issues

### Step 6: Update Function Signatures

**File**: `src/training/hpo/execution/local/sweep.py`

**Changes**:

1. Add `backup_to_drive: Optional[Callable[[Path, bool], bool]] = None` parameter
2. Add `backup_enabled: bool = True` parameter
3. Pass these to backup callback creation

**Success criteria**:

- Function signature includes backup parameters
- Parameters are passed correctly to backup callback
- Backward compatible (optional parameters)

### Step 7: Update Tests

**Files**:

- `tests/orchestration/jobs/hpo/local/test_backup.py`
- `tests/infrastructure/storage/test_drive.py` (if exists)

**Changes**:

1. Add test for Drive path rejection in `drive.py`
2. Add test for `create_incremental_backup_callback()` with file
3. Add test for `create_incremental_backup_callback()` with directory
4. Update existing tests to match simplified logic
5. Remove tests for mixed-state scenarios

**Success criteria**:

- All tests pass
- New tests verify Drive path rejection
- New tests verify incremental backup callback
- Test coverage maintained or improved

## Success Criteria (Overall)

- ✅ `study.db` is backed up immediately after creation
- ✅ `study.db` is backed up after each trial completes
- ✅ Drive paths are rejected at API boundary (no crashes)
- ✅ Backup logic is centralized in `backup.py`
- ✅ No mixed-state handling (simple local → Drive or verify)
- ✅ All tests pass
- ✅ No regressions in existing functionality

## Implementation Notes

### Key Design Decisions

1. **Immediate backup after creation**: Don't rely on "first callback invocation" - explicitly call backup right after `storage_path` is known
2. **Reusable callback**: Create general-purpose `create_incremental_backup_callback()` that works for any file/folder, not just `study.db` - follows DRY/reuse-first principles
3. **Early rejection**: Reject Drive paths at the lowest level (`drive.py`) to prevent entire class of errors
4. **Simplified logic**: Remove all "if this is Drive but that is local" complexity - just check canonical root

### Testing Strategy

1. Test Drive path rejection with various Drive path formats
2. Test immediate backup after study creation
3. Test incremental backup callback with mock Optuna study/trial
4. Test simplified backup function with local and Drive scenarios
5. Integration test: Run HPO and verify backups happen incrementally

### Rollout Plan

1. Implement Drive path rejection first (prevents crashes)
2. Add immediate backup (ensures study.db is backed up early)
3. Add incremental callback (ensures continuous backup)
4. Simplify final backup function (cleanup)
5. Update tests (verify everything works)

## Related Files

- `src/infrastructure/storage/drive.py` - Add Drive path rejection
- `src/orchestration/jobs/hpo/local/backup.py` - Reusable incremental backup callback + simplified function
- `src/training/hpo/execution/local/sweep.py` - Immediate backup + callback integration
- `tests/orchestration/jobs/hpo/local/test_backup.py` - Update tests
- `notebooks/01_orchestrate_training_colab.ipynb` - May need to pass `backup_enabled` parameter

## Dependencies

- `common.shared.platform_detection.is_drive_path()` - Must work correctly
- `backup_to_drive` function from notebook - Must be available
- Optuna callback system - Must support multiple callbacks

# Fix HPO Study Drive Path Resolution

## Goal

Fix path resolution mismatch in HPO study loading when checkpoints are stored in Google Drive. The `resolve_platform_checkpoint_path()` function maps paths to Drive (e.g., `/content/drive/MyDrive/resume-ner-azureml/outputs/hpo/...`), but `restore_from_drive()` expects a local path and fails when given an already-Drive path.

**Solution**: Add a shared utility function `is_drive_path()` to detect Drive paths, and use it to skip `restore_from_drive()` calls when the path is already in Drive.

## Status

**Last Updated**: 2025-01-27

### Completed Steps

- ✅ Step 1: Add `is_drive_path()` utility to `platform_detection.py`
- ✅ Step 2: Update `setup_checkpoint_storage()` in `helpers.py`
- ✅ Step 3: Update `create_or_load_study()` in `study.py`
- ✅ Step 4: Verify fixes with mypy and tests

### Pending Steps

- None (all steps completed)

## Preconditions

- Project is set up with `src/` structure
- `src/common/shared/platform_detection.py` exists
- `src/training/hpo/utils/helpers.py` exists
- `src/training/hpo/core/study.py` exists
- **Repository root detection refactoring completed** (`FNISHED-consolidate-repository-root-detection.plan.md`):
  - `get_drive_backup_path()` now auto-detects `root_dir` and `config_dir` if not provided
  - `DriveBackupStore` can auto-detect `root_dir` if not provided
  - Hardcoded string replacements in `backup.py` were replaced with relative path computation (for path mapping)
  - **Note**: `backup.py` still uses `str(path).startswith("/content/drive")` checks (lines 88, 101, 117-118) - these could use `is_drive_path()` in a future refactoring

## Steps

### Step 1: Add `is_drive_path()` utility to `platform_detection.py`

Add a shared utility function to detect if a path is already in Google Drive.

**Location**: `src/common/shared/platform_detection.py`

**Changes**:

1. Add `is_drive_path()` function after `resolve_platform_checkpoint_path()` (after line 133)
2. Function signature: `def is_drive_path(path: Path | str) -> bool:`
   - **Note**: Python 3.10+ union syntax (`|`) is supported (project uses Python 3.10 per `pyproject.toml`)
   - Alternative for broader compatibility: `from typing import Union` and use `Union[Path, str]`
3. Function should check if path string starts with `/content/drive`
4. Handle edge cases:
   - Convert `Path` objects to strings: `path_str = str(path) if isinstance(path, Path) else path`
   - Handle `None` input: raise `TypeError` with clear message
   - Only check absolute paths (relative paths return `False`)
5. Include comprehensive docstring with examples showing both `Path` and `str` inputs

**Success criteria**:

- `is_drive_path()` function exists in `platform_detection.py`
- Function accepts both `Path` and `str` types
- Function handles `None` input (raises `TypeError` with clear message)
- Function normalizes paths before checking (converts `Path` to `str`)
- Function returns `True` for absolute paths starting with `/content/drive`
- Function returns `False` for local paths (e.g., `/content/resume-ner-azureml/...`)
- Function returns `False` for relative paths
- Docstring includes examples for both `Path` and `str` inputs
- `uvx mypy src/common/shared/platform_detection.py` passes with 0 errors

### Step 2: Update `setup_checkpoint_storage()` in `helpers.py`

Modify the restore logic to check if path is already in Drive before calling `restore_from_drive()`.

**Location**: `src/training/hpo/utils/helpers.py` (around lines 82-93)

**Changes**:

1. Add import at top of file with other imports: `from common.shared.platform_detection import is_drive_path`
2. Add check: `if not is_drive_path(storage_path):` before calling `restore_from_drive()` (around line 83)
3. Add `else` branch with debug log when path is already in Drive:
   ```python
   else:
       logger.debug(
           f"Checkpoint path is already in Drive: {storage_path}. "
           f"File does not exist - will create new study."
       )
   ```
4. Keep existing error handling for restore attempts (try/except block)

**Success criteria**:

- `is_drive_path()` check is added before `restore_from_drive()` call
- `restore_from_drive()` is only called when path is NOT in Drive
- Debug log is added when path is already in Drive
- Existing error handling preserved
- `uvx mypy src/training/hpo/utils/helpers.py` passes with 0 errors

### Step 3: Update `create_or_load_study()` in `study.py`

Modify the restore logic in `create_or_load_study()` to check if path is already in Drive.

**Location**: `src/training/hpo/core/study.py` (around lines 232-241)

**Changes**:

1. Add import at top of file with other imports: `from common.shared.platform_detection import is_drive_path`
2. Add check: `if not is_drive_path(storage_path):` before calling `self.restore_from_drive()` (around line 233)
3. Add `else` branch with debug log when path is already in Drive:
   ```python
   else:
       logger.debug(
           f"Checkpoint path is already in Drive: {storage_path}. "
           f"File does not exist - will create new study."
       )
   ```
4. Keep existing error handling for restore attempts (try/except block)

**Success criteria**:

- `is_drive_path()` check is added before `self.restore_from_drive()` call
- `self.restore_from_drive()` is only called when path is NOT in Drive
- Debug log is added when path is already in Drive
- Existing error handling preserved
- `uvx mypy src/training/hpo/core/study.py` passes with 0 errors

### Step 4: Verify fixes with mypy and tests

Run type checking and verify no regressions.

**Changes**:

1. Run mypy on modified files
2. Create unit tests for `is_drive_path()` if test infrastructure exists:
   - Check for test file: `tests/shared/unit/test_platform_detection.py` or similar
   - If test file exists, add tests for `is_drive_path()` covering:
     - `Path` objects with Drive paths
     - String paths with Drive paths
     - Local paths (both `Path` and `str`)
     - `None` input (should raise `TypeError`)
     - Relative paths (should return `False`)
3. Run relevant existing tests
4. Verify no new type errors introduced

**Success criteria**:

- `uvx mypy src/common/shared/platform_detection.py` passes
- `uvx mypy src/training/hpo/utils/helpers.py` passes
- `uvx mypy src/training/hpo/core/study.py` passes
- Unit tests for `is_drive_path()` exist and pass (if test infrastructure exists)
- No new type errors introduced
- Existing tests pass (if applicable)

## Success Criteria (Overall)

- ✅ `is_drive_path()` utility function exists and is reusable
- ✅ HPO study loading no longer fails when checkpoint path is already in Drive
- ✅ `restore_from_drive()` is only called with local paths (not Drive paths)
- ✅ All modified files pass mypy type checking
- ✅ No regressions in existing functionality
- ✅ Code follows reuse-first principles (shared utility instead of duplicated checks)

## Related Issues

- Path resolution mismatch in Colab when checkpoints are stored in Google Drive
- `ValueError` in `DriveBackupStore.drive_path_for()` when `restore_from_drive()` receives Drive path
- Similar pattern exists in 7+ other locations (future refactoring opportunity)

## Relationship to Repository Root Detection Refactoring

The completed repository root detection refactoring (`FNISHED-consolidate-repository-root-detection.plan.md`) made the following changes that affect this plan:

**What Changed:**
- `get_drive_backup_path()` now auto-detects `root_dir` and `config_dir` if not provided (no need to pass explicitly)
- `DriveBackupStore` can auto-detect `root_dir` if not provided
- Hardcoded string replacements in `backup.py` were replaced with relative path computation (for path mapping)

**What Did NOT Change:**
- `is_drive_path()` utility does not exist yet (this plan will add it)
- `restore_from_drive()` is still called with Drive paths in `setup_checkpoint_storage()` and `create_or_load_study()` (this plan will fix it)
- `backup.py` still uses `str(path).startswith("/content/drive")` checks (lines 88, 101, 117-118) - these could use `is_drive_path()` in a future refactoring

**Impact on This Plan:**
- No changes needed to Step 1 (adding `is_drive_path()` utility)
- No changes needed to Step 2 (updating `setup_checkpoint_storage()`)
- No changes needed to Step 3 (updating `create_or_load_study()`)
- The plan remains valid and necessary - the repository root detection refactoring did not solve the core issue of `restore_from_drive()` being called with Drive paths

## Future Refactoring Opportunity

After `is_drive_path()` is implemented, there are 7+ code locations with existing uses of `str(path).startswith("/content/drive")` that could be refactored to use `is_drive_path()`:

- `src/evaluation/benchmarking/orchestrator.py` (3 places: lines 651, 843, 846)
- `src/orchestration/jobs/hpo/local/backup.py` (3 places: lines 88, 101, 117-118)
- `src/evaluation/selection/trial_finder.py` (1 place: line 830)

**Note**: The repository root detection refactoring updated `backup.py` to use relative path computation for path mapping, but the "is already in Drive" checks still use hardcoded string checks. These could be refactored to use `is_drive_path()` in a separate task to maintain consistency across the codebase.

This refactoring can be done in a separate task to maintain consistency across the codebase.

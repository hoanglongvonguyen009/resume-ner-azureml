# Consolidate Artifact Utilities DRY Violations

## Goal

Eliminate duplicate checkpoint validation, tar.gz extraction, and checkpoint discovery logic across artifact-tagged utility scripts by consolidating shared functions into reusable modules, following reuse-first principles and maintaining backward compatibility.

## Status

**Last Updated**: 2026-01-15

### Completed Steps
- ✅ Step 1: Consolidate checkpoint validation logic
- ✅ Step 2: Consolidate tar.gz extraction logic
- ✅ Step 3: Consolidate checkpoint discovery/path finding logic
- ✅ Step 4: Update all call sites to use consolidated functions
- ✅ Step 5: Remove duplicate implementations
- ✅ Step 6: Verify tests and update if needed

### Pending Steps
- None - All steps complete!

## Preconditions

- Existing artifact acquisition system (`artifact_unified`) is in place and working
- All artifact-tagged modules are identified and analyzed
- Tests exist for artifact acquisition workflows

## Artifact-Tagged Scripts Inventory

### Upload/Logging Utilities (tracking domain)

| File Path | Purpose | Key Functions |
|-----------|---------|---------------|
| `src/infrastructure/tracking/mlflow/artifacts.py` | Safe MLflow artifact upload utilities with retry logic | `log_artifact_safe()`, `log_artifacts_safe()`, `upload_checkpoint_archive()` |
| `src/infrastructure/tracking/mlflow/artifacts/manager.py` | Checkpoint archive creation and file filtering | `create_checkpoint_archive()`, `should_skip_file()` |
| `src/infrastructure/tracking/mlflow/artifacts/uploader.py` | Unified artifact upload interface for all stages | `ArtifactUploader` class, stage-aware config checking |
| `src/infrastructure/tracking/mlflow/artifacts/stage_helpers.py` | Stage-specific helper functions for artifact uploads | `upload_training_artifacts()`, `upload_conversion_artifacts()`, etc. |

### Acquisition Utilities (selection domain)

| File Path | Purpose | Key Functions |
|-----------|---------|---------------|
| `src/evaluation/selection/artifact_acquisition.py` | Legacy checkpoint acquisition (backward compatibility wrapper) | `acquire_best_model_checkpoint()` - delegates to unified system |
| `src/evaluation/selection/artifact_unified/acquisition.py` | Unified artifact acquisition orchestration (SSOT for tar.gz extraction) | `acquire_artifact()`, `_extract_tar_gz()` |
| `src/evaluation/selection/artifact_unified/discovery.py` | Artifact discovery for local/drive/mlflow sources (SSOT for checkpoint discovery) | `discover_artifact_local()`, `_find_checkpoint_in_path()`, `_find_checkpoint_in_drive_by_hash()` |
| `src/evaluation/selection/artifact_unified/validation.py` | Artifact-kind-specific validation (SSOT for checkpoint validation) | `validate_artifact()`, `_validate_checkpoint()` |
| `src/evaluation/selection/artifact_unified/compat.py` | Backward compatibility wrapper | `acquire_best_model_checkpoint()` |
| `src/evaluation/selection/artifact_unified/selectors.py` | Run selector with trial→refit mapping | `select_artifact_run()`, `select_artifact_run_from_request()` |

## Identified DRY Violations

### Category 1: Checkpoint Validation Logic

**Duplicated across 4 files:**

1. **`artifact_acquisition.py`** (lines 89-117):
   - `_validate_checkpoint()` - checks for essential checkpoint files (pytorch_model.bin, model.safetensors, config.json)

2. **`artifact_unified/validation.py`** (lines 75-123):
   - `_validate_checkpoint()` - similar logic, more comprehensive with strict/lenient modes

3. **`artifact_unified/acquisition.py`** (lines 744-753):
   - `_validate_checkpoint_dir()` - quick check for config.json and model files

4. **`artifact_unified/discovery.py`** (lines 57-66):
   - `_check_checkpoint_files()` - checks for essential checkpoint files

**Overlap**: All check for `config.json` and model files (pytorch_model.bin, model.safetensors, model.bin), but with different levels of detail and error handling.

**Consolidation target**: `artifact_unified/validation.py` already has the most comprehensive implementation with strict/lenient modes. Other files should use this.

### Category 2: Tar.gz Extraction Logic

**Duplicated across 2 files:**

1. **`artifact_acquisition.py`** (lines 51-86):
   - `_extract_tar_gz()` - extracts tar.gz and returns extracted directory path, handles single root directory

2. **`artifact_unified/acquisition.py`** (lines 673-741):
   - `_extract_tar_gz()` - more sophisticated extraction with temp directory handling, moves contents to avoid nested structures

**Overlap**: Both extract tar.gz files and handle single root directory cases, but the unified version has better handling of nested structures.

**Consolidation target**: `artifact_unified/acquisition.py` has the better implementation. The legacy version should be removed or updated to call the unified version.

### Category 3: Checkpoint Discovery/Path Finding Logic

**Duplicated across 3 files:**

1. **`artifact_acquisition.py`** (lines 120-147):
   - `_find_checkpoint_in_directory()` - searches recursively for valid checkpoint directories

2. **`artifact_unified/discovery.py`** (lines 253-311):
   - `_find_checkpoint_in_path()` - finds checkpoint files in a given path, handles extracted tar.gz directories, tar.gz files

3. **`artifact_unified/discovery.py`** (lines 525-592):
   - `_find_checkpoint_in_drive_by_hash()` - finds checkpoint in Drive by scanning directory structure

**Overlap**: `_find_checkpoint_in_directory()` and `_find_checkpoint_in_path()` have similar recursive search logic, but `_find_checkpoint_in_path()` is more comprehensive (handles extracted tar.gz structures).

**Consolidation target**: `artifact_unified/discovery.py` has the most comprehensive implementation. Legacy functions should be updated to use it.

### Category 4: Drive Checkpoint Finding by Hash

**Duplicated across 2 files:**

1. **`artifact_acquisition.py`** (lines 195-261):
   - `_find_checkpoint_in_drive_by_hash()` - scans Drive directory structure to find checkpoint by hash

2. **`artifact_unified/discovery.py`** (lines 525-592):
   - `_find_checkpoint_in_drive_by_hash()` - identical implementation

**Overlap**: These are identical implementations.

**Consolidation target**: Keep only the one in `artifact_unified/discovery.py` and remove the duplicate from `artifact_acquisition.py`.

## Steps

### Step 1: Consolidate checkpoint validation logic

**Objective**: Make `artifact_unified/validation.py` the single source of truth for checkpoint validation, removing duplicate implementations.

**Actions**:

1. **Review and enhance `artifact_unified/validation.py`**:
   - Ensure `_validate_checkpoint()` handles all use cases (strict/lenient modes)
   - Add a lightweight `_validate_checkpoint_dir()` helper if needed for quick checks (or use lenient mode)
   - Export validation functions for reuse

2. **Update `artifact_unified/acquisition.py`**:
   - Replace `_validate_checkpoint_dir()` (lines 744-753) with call to `validate_artifact()` from `validation.py` using lenient mode
   - Remove duplicate `_validate_checkpoint_dir()` function

3. **Update `artifact_unified/discovery.py`**:
   - Replace `_check_checkpoint_files()` (lines 57-66) with call to `validate_artifact()` from `validation.py` using lenient mode
   - Remove duplicate `_check_checkpoint_files()` function

4. **Update `artifact_acquisition.py`**:
   - Replace `_validate_checkpoint()` (lines 89-117) with call to `validate_artifact()` from `validation.py`
   - Remove duplicate `_validate_checkpoint()` function
   - Update `_find_checkpoint_in_directory()` to use `validate_artifact()` instead of `_validate_checkpoint()`

**Success criteria**:
- ✅ `artifact_unified/validation.py` is the only module with checkpoint validation logic
- ✅ All other modules import and use `validate_artifact()` from `validation.py`
- ✅ `uvx mypy src/evaluation/selection/artifact_unified/` passes with 0 errors
- ✅ Existing tests continue to pass

### Step 2: Consolidate tar.gz extraction logic

**Objective**: Make `artifact_unified/acquisition.py` the single source of truth for tar.gz extraction, removing duplicate implementations.

**Actions**:

1. **Review and enhance `artifact_unified/acquisition.py`**:
   - Ensure `_extract_tar_gz()` (lines 673-741) handles all edge cases
   - Consider making it a public function (remove leading underscore) if it's useful for other modules
   - Add clear docstring explaining extraction behavior

2. **Update `artifact_acquisition.py`**:
   - Replace `_extract_tar_gz()` (lines 51-86) with import and call to the unified version
   - Remove duplicate `_extract_tar_gz()` function
   - Update any call sites to use the unified function signature

**Success criteria**:
- ✅ `artifact_unified/acquisition.py` is the only module with tar.gz extraction logic
- ✅ `artifact_acquisition.py` imports and uses the unified extraction function
- ✅ `uvx mypy src/evaluation/selection/artifact_acquisition.py` passes with 0 errors
- ✅ Existing tests continue to pass

### Step 3: Consolidate checkpoint discovery/path finding logic

**Objective**: Make `artifact_unified/discovery.py` the single source of truth for checkpoint discovery, removing duplicate implementations.

**Actions**:

1. **Review and enhance `artifact_unified/discovery.py`**:
   - Ensure `_find_checkpoint_in_path()` (lines 253-311) handles all use cases from legacy `_find_checkpoint_in_directory()`
   - Consider making it a public function if useful for other modules
   - Verify it handles recursive search, extracted tar.gz structures, and direct checkpoint directories

2. **Update `artifact_acquisition.py`**:
   - Replace `_find_checkpoint_in_directory()` (lines 120-147) with import and call to `_find_checkpoint_in_path()` from `discovery.py`
   - Remove duplicate `_find_checkpoint_in_directory()` function
   - Update any call sites to use the unified function signature

3. **Remove duplicate Drive hash finding**:
   - Remove `_find_checkpoint_in_drive_by_hash()` from `artifact_acquisition.py` (lines 195-261)
   - Ensure `artifact_unified/discovery.py` version is used everywhere

**Success criteria**:
- ✅ `artifact_unified/discovery.py` is the only module with checkpoint discovery logic
- ✅ `artifact_acquisition.py` imports and uses discovery functions from `discovery.py`
- ✅ `uvx mypy src/evaluation/selection/artifact_acquisition.py` passes with 0 errors
- ✅ Existing tests continue to pass

### Step 4: Update all call sites to use consolidated functions

**Objective**: Ensure all internal call sites within artifact modules use the consolidated functions.

**Actions**:

1. **Search for remaining internal call sites**:
   - Use grep to find all calls to removed functions (`_validate_checkpoint`, `_extract_tar_gz`, `_find_checkpoint_in_directory`, `_find_checkpoint_in_drive_by_hash`)
   - Verify they're all updated to use consolidated functions

2. **Update imports**:
   - Ensure all modules import consolidated functions from correct locations
   - Remove unused imports

3. **Verify function signatures match**:
   - Check that consolidated function signatures are compatible with call sites
   - Update call sites if needed (e.g., parameter name changes, optional parameters)

**Success criteria**:
- ✅ All call sites updated to use consolidated functions
- ✅ No remaining references to removed duplicate functions
- ✅ `uvx mypy src/evaluation/selection/` passes with 0 errors
- ✅ All imports are correct and unused imports removed

### Step 5: Remove duplicate implementations

**Objective**: Clean up duplicate code after all call sites are migrated.

**Actions**:

1. **Remove duplicate functions**:
   - Delete `_validate_checkpoint()` from `artifact_acquisition.py`
   - Delete `_extract_tar_gz()` from `artifact_acquisition.py`
   - Delete `_find_checkpoint_in_directory()` from `artifact_acquisition.py`
   - Delete `_find_checkpoint_in_drive_by_hash()` from `artifact_acquisition.py`
   - Delete `_validate_checkpoint_dir()` from `artifact_unified/acquisition.py` (if replaced in Step 1)
   - Delete `_check_checkpoint_files()` from `artifact_unified/discovery.py` (if replaced in Step 1)

2. **Update module docstrings**:
   - Update `artifact_acquisition.py` docstring to note it's a backward compatibility wrapper
   - Ensure consolidated modules document their role as SSOTs

**Success criteria**:
- ✅ All duplicate functions removed
- ✅ Module docstrings updated to reflect consolidation
- ✅ `uvx mypy src/evaluation/selection/` passes with 0 errors
- ✅ Code is cleaner with no duplicate logic

### Step 6: Verify tests and update if needed

**Objective**: Ensure all tests pass and update tests that may have been testing implementation details.

**Actions**:

1. **Run existing tests**:
   - Run tests for artifact acquisition: `uvx pytest tests/ -k artifact -v`
   - Run tests for selection workflows: `uvx pytest tests/ -k selection -v`
   - Verify all tests pass

2. **Update tests if needed**:
   - If tests were testing internal implementation details (e.g., specific validation functions), update them to test public APIs
   - Ensure tests verify behavior, not implementation

3. **Add integration tests if missing**:
   - Verify consolidated functions work correctly across all use cases
   - Test edge cases (nested tar.gz, missing files, etc.)

**Success criteria**:
- ✅ All existing tests pass
- ✅ Tests verify behavior through public APIs, not implementation details
- ✅ Integration tests cover consolidated functions
- ✅ No test failures introduced by consolidation

## Success Criteria (Overall)

- ✅ **Single source of truth established**: 
  - Checkpoint validation: `artifact_unified/validation.py`
  - Tar.gz extraction: `artifact_unified/acquisition.py`
  - Checkpoint discovery: `artifact_unified/discovery.py`

- ✅ **DRY violations eliminated**: 
  - No duplicate validation logic
  - No duplicate extraction logic
  - No duplicate discovery logic

- ✅ **Backward compatibility maintained**: 
  - `artifact_acquisition.py` continues to work as a compatibility wrapper
  - All existing workflows continue to function

- ✅ **Code quality improved**: 
  - Mypy passes with 0 errors
  - Tests pass
  - Code is cleaner and easier to maintain

- ✅ **Documentation updated**: 
  - Module docstrings reflect consolidation
  - Clear SSOT documentation in consolidated modules

## Notes

- **Reuse-first approach**: This plan consolidates into existing `artifact_unified` modules rather than creating new modules, following reuse-first principles.

- **Minimal breaking changes**: All changes maintain backward compatibility. The `artifact_acquisition.py` wrapper continues to work, just delegates to consolidated functions.

- **SRP compliance**: Each consolidated module maintains a single responsibility:
  - `validation.py`: Artifact validation
  - `acquisition.py`: Artifact acquisition orchestration (including extraction)
  - `discovery.py`: Artifact discovery

- **Testing strategy**: Tests verify behavior through public APIs. Internal refactoring should not require test rewrites if public APIs remain stable.


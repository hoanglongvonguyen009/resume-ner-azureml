# Deprecated/Compatibility Code Inventory

**Date**: 2026-01-18  
**Plan**: `20260118-1248-remove-deprecated-compatibility-layers-master.plan.md`

## Summary

This document catalogs all deprecated code paths, backward compatibility layers, and legacy fallbacks found in the codebase. Items are categorized by priority and include usage counts, dependencies, and migration paths.

## High Priority Items

### 1. `objective.goal` Legacy Config Key Support

**Status**: Deprecated with warning  
**Location**: `src/infrastructure/config/selection.py`  
**Current Usage**: 0 (no config files found using `objective.goal`)  
**Replacement**: `objective.direction`

**Details**:
- No code currently supports `objective.goal` - the function `get_objective_direction()` only checks for `objective.direction`
- However, `src/training/hpo/core/study.py` line 170 has: `self.goal = self.direction` for backward compatibility
- This internal attribute should be removed

**Migration Path**: Use `objective.direction` in all configs (already the case)

**Test Cases**:
- `tests/training/hpo/unit/test_phase2_tags.py` - `test_legacy_goal_key_migration` (if exists)
- Tests in `tests/selection/unit/test_best_model_selection_config*.py` that test goal/direction compatibility

**Priority**: High

---

### 2. v1 Study Key Hash Fallback Logic

**Status**: Fallback logic present  
**Location**: 
- `src/training/hpo/tracking/setup.py` - Falls back to v1 hash computation
- `src/evaluation/selection/trial_finder.py` - Uses v1 hash
- `src/training/hpo/trial/meta.py` - Uses v1 hash

**Current Usage**: 3 source files, multiple test files  
**Replacement**: `build_hpo_study_key_v2()`

**Details**:
- Function `build_hpo_study_key()` (v1) is still used in:
  - `src/evaluation/selection/trial_finder.py:study_key = build_hpo_study_key(...)`
  - `src/training/hpo/trial/meta.py:study_key = build_hpo_study_key(...)`
- `src/training/hpo/tracking/setup.py` has comment: "Falls back to v1 hash computation (`build_hpo_study_key()`) for backward compatibility."

**Migration Path**: Replace all `build_hpo_study_key()` calls with `build_hpo_study_key_v2()`

**Test Cases**: Multiple tests in `tests/training/hpo/`, `tests/hpo/`, `tests/tracking/unit/test_naming_policy.py`

**Priority**: High

---

### 3. Schema Version 1.0 Backward Compatibility

**Status**: Defaults to "1.0" in multiple places  
**Location**:
- `src/evaluation/selection/trial_finder.py` - Defaults to "1.0" (line with comment "backward compat")
- `src/training/hpo/execution/local/sweep.py` - Defaults to "1.0" for backward compat
- `src/infrastructure/naming/mlflow/hpo_keys.py` - Multiple "schema_version": "1.0" defaults
- `src/infrastructure/naming/mlflow/refit_keys.py` - "schema_version": "1.0" default
- `src/infrastructure/config/selection.py` - `prefer_schema_version` accepts "1.0"

**Current Usage**: Multiple source files, test files  
**Replacement**: Schema version "2.0" only

**Details**:
- `trial_finder.py`: `schema_version = run.data.tags.get(schema_version_tag, "1.0")` - defaults to "1.0"
- `sweep.py`: `schema_version = "1.0"  # Default to v1 for backward compat`
- `hpo_keys.py`: Multiple places with `"schema_version": "1.0"`
- `refit_keys.py`: `"schema_version": "1.0"`
- `selection.py`: `prefer_schema_version` accepts "1.0", "2.0", or "auto"

**Migration Path**: 
- Change all defaults to "2.0"
- Update `prefer_schema_version` to only accept "2.0" or "auto" (auto prefers 2.0)
- Update all tests to use "2.0"

**Test Cases**: Tests in `tests/evaluation/selection/` that use schema_version "1.0"

**Priority**: High

---

## Medium Priority Items

### 4. Backward Compatibility Aliases

**Status**: Active aliases  
**Location**:
- `src/training/execution/__init__.py` - `execute_final_training` alias (lines 64-67)
- `src/training/__init__.py` - `execute_final_training` in `__all__` and `__getattr__`
- `tests/selection/conftest.py` - `mock_trial_run` alias (line 125)
- `tests/selection/integration/conftest.py` - `mock_trial_run` function (line 178)

**Current Usage**: 
- `execute_final_training`: Multiple test files (12+ test functions)
- `mock_trial_run`: Used in `tests/selection/integration/test_mlflow_selection_config.py`

**Replacement**: 
- `execute_final_training` → `run_final_training_workflow`
- `mock_trial_run` → `mock_hpo_trial_run`

**Details**:
- `src/training/execution/__init__.py`: `__getattr__` handler for `execute_final_training` (lines 64-67)
- `src/training/__init__.py`: `execute_final_training` in `__all__` and `__getattr__` handler
- `tests/selection/conftest.py`: `mock_trial_run = mock_hpo_trial_run` (line 125) with comment "Alias for backward compatibility"
- `tests/selection/integration/conftest.py`: `def mock_trial_run(mock_mlflow_run):` (line 178)
- `tests/selection/integration/test_mlflow_selection_config.py`: Uses `mock_trial_run` fixture

**Migration Path**:
- Update all imports: `from training.execution import run_final_training_workflow`
- Update test fixtures: Use `mock_hpo_trial_run` instead of `mock_trial_run`
- Remove alias definitions

**Test Cases**: 
- All tests using `execute_final_training` (12+ test functions)
- Tests using `mock_trial_run` fixture

**Priority**: Medium

---

### 5. Legacy Path Resolution Functions

**Status**: Legacy function marked for backward compatibility  
**Location**: `src/infrastructure/paths/resolve.py` - `resolve_output_path()` function (lines 49-105)

**Current Usage**: 10+ files using `resolve_output_path()`:
- `src/evaluation/benchmarking/orchestrator.py`
- `src/evaluation/selection/artifact_unified/discovery.py`
- `src/evaluation/selection/artifact_unified/acquisition.py`
- `src/evaluation/selection/trial_finder.py`
- `src/evaluation/selection/artifact_acquisition.py`
- `src/training/execution/executor.py`
- `src/training/orchestrator.py`
- `src/training/hpo/execution/local/sweep.py`
- `src/training/hpo/execution/local/cv.py`

**Replacement**: Use `resolve_storage_path()` or domain-specific resolvers

**Details**:
- Function marked as "legacy function for backward compatibility" in docstring
- Still widely used across codebase
- Should be replaced with modern path resolution

**Migration Path**: Replace with `resolve_storage_path()` or domain-specific resolvers

**Test Cases**: Tests that use `resolve_output_path()` - need to update

**Priority**: Medium

---

### 6. Legacy Run Name Building Functions

**Status**: Legacy functions present  
**Location**:
- `src/infrastructure/naming/mlflow/run_names.py` - `_build_legacy_run_name()` (if exists)
- `src/training/hpo/utils/helpers.py` - `create_mlflow_run_name()` (legacy fallback)

**Current Usage**: 
- `create_mlflow_run_name`: Used in `src/training/hpo/execution/local/sweep.py`

**Replacement**: Use `build_mlflow_run_name()` from `infrastructure.naming.mlflow.run_names`

**Details**:
- `create_mlflow_run_name()` in `helpers.py` is a legacy fallback
- Should use modern naming policy instead

**Migration Path**: Replace with `infrastructure.naming.mlflow.run_names.build_mlflow_run_name()`

**Test Cases**: Tests for run name building

**Priority**: Medium

---

### 7. Backward Compatibility Wrappers (Search Space)

**Status**: Convenience wrappers marked for backward compatibility  
**Location**: `src/training/hpo/core/search_space.py`:
- `translate_search_space_to_optuna()` (lines 130-150)
- `create_search_space()` (lines 153-166)

**Current Usage**: 
- `translate_search_space_to_optuna`: Used in `src/training/hpo/execution/local/sweep.py`
- `create_search_space`: Used in:
  - `src/training/hpo/execution/azureml/sweeps.py` (2 usages)
  - `src/training/hpo/azureml/sweeps.py` (2 usages)

**Replacement**: 
- `translate_search_space_to_optuna()` → `SearchSpaceTranslator.to_optuna()`
- `create_search_space()` → `SearchSpaceTranslator.to_azure_ml()`

**Details**:
- Both functions marked as "Convenience functions for backward compatibility"
- Comment says "for backward compatibility"
- Wrapper around `SearchSpaceTranslator` class methods

**Migration Path**: Replace with `SearchSpaceTranslator` class methods

**Test Cases**: Tests using these functions

**Priority**: Medium

---

### 8. Legacy Tag Keys and Tag Registry Support

**Status**: Legacy functions present  
**Location**: `src/infrastructure/naming/mlflow/tag_keys.py` - `get_legacy_trial_number()` (if exists)

**Current Usage**: Unknown (need to search)

**Replacement**: Use modern tag keys

**Details**: Need to verify if `get_legacy_trial_number()` exists and is used

**Migration Path**: Use modern tag keys

**Test Cases**: Tests for legacy tag registry in `tests/tracking/unit/test_tags_comprehensive.py`

**Priority**: Medium

---

### 9. Legacy Study Folder Format Support

**Status**: Fallback support present  
**Location**: `src/training/hpo/checkpoint/storage.py` - Falls back to legacy study_name format

**Current Usage**: Unknown (need to search)

**Replacement**: Use v2 hash-based paths only

**Details**: Need to verify fallback logic in checkpoint storage

**Migration Path**: Use v2 hash-based paths only

**Test Cases**: `test_checkpoint_path_fallback_to_legacy_when_no_hash` in `tests/hpo/integration/test_hpo_sweep_setup.py` (if exists)

**Priority**: Medium

---

## Low Priority Items

### 10. MLflow Azure ML Compatibility Patch

**Status**: May still be needed  
**Location**: `src/infrastructure/tracking/mlflow/compatibility.py`

**Current Usage**: 
- Imported in `src/deployment/conversion/execution.py` (line 272)
- Auto-applied on module import (line 118)

**Replacement**: Remove if no longer needed

**Details**:
- Provides monkey-patch for Azure ML artifact compatibility
- Fixes compatibility issue between MLflow 3.5.0 and azureml-mlflow 1.61.0
- May still be needed - needs evaluation

**Migration Path**: 
- Test if patch is still needed
- If not needed, remove module and imports
- If needed, document why and when it can be removed

**Test Cases**: `tests/tracking/unit/test_azureml_artifact_upload.py`

**Priority**: Low (needs evaluation first)

---

### 11. Deprecated Function Wrappers

**Status**: Deprecated wrapper  
**Location**: `src/common/shared/notebook_setup.py` - `find_repository_root()` function

**Current Usage**: 
- Used internally in `notebook_setup.py` (2 usages)
- May be used in notebooks

**Replacement**: `infrastructure.paths.repo.detect_repo_root()`

**Details**:
- Function marked as deprecated in docstring
- Comment says "This function is kept for backward compatibility with notebooks."
- Wrapper around `detect_repo_root()`

**Migration Path**: Replace with `infrastructure.paths.repo.detect_repo_root()`

**Test Cases**: Notebooks using this function

**Priority**: Low

---

### 12. Legacy Checkpoint Path Fallbacks

**Status**: Fallback logic present  
**Location**: 
- `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py` - Legacy checkpoint structure fallback
- `src/evaluation/selection/trial_finder.py` - Legacy checkpoint path fallbacks
- `src/common/shared/platform_detection.py` - Legacy checkpoint directory (`LEGACY_CHECKPOINT_DIR`)

**Current Usage**: Multiple files

**Replacement**: Use modern checkpoint paths

**Details**:
- `platform_detection.py`: `LEGACY_CHECKPOINT_DIR = "resume-ner-checkpoints"` with comment "for backward compatibility fallback"
- May need to keep if old runs still exist

**Migration Path**: 
- Determine if fallbacks are still needed
- If safe to remove, remove fallback logic
- If not safe, document with TODO

**Test Cases**: Tests for legacy checkpoint paths

**Priority**: Low (needs evaluation)

---

### 13. Backward Compatibility Defaults

**Status**: Silent fallbacks present  
**Location**: Multiple files with backward compatibility defaults

**Current Usage**: Multiple files

**Replacement**: Fail fast with clear errors

**Details**: Need to search for "backward compatibility" defaults

**Migration Path**: Replace silent fallbacks with fail-fast error handling

**Test Cases**: Tests that rely on backward compatibility defaults

**Priority**: Low

---

## Usage Statistics

### By Category

| Category | Count | Priority |
|----------|-------|----------|
| Config keys | 1 | High |
| Hash fallbacks | 1 | High |
| Schema versions | 1 | High |
| Aliases | 2 | Medium |
| Path resolution | 1 | Medium |
| Run naming | 1 | Medium |
| Wrappers | 2 | Medium |
| Tag keys | 1 | Medium |
| Folder formats | 1 | Medium |
| Compatibility patches | 1 | Low |
| Function wrappers | 1 | Low |
| Checkpoint fallbacks | 1 | Low |
| Defaults | 1 | Low |

### By File Type

| File Type | Count |
|-----------|-------|
| Source files | ~15 |
| Test files | ~12-15 |
| Config files | 0 (verified) |

## Migration Priority

1. **High Priority** (Remove first):
   - `objective.goal` support (Step 2)
   - v1 hash fallback (Step 6)
   - Schema version 1.0 (Step 10)

2. **Medium Priority** (Remove next):
   - Backward compatibility aliases (Step 3)
   - Legacy path resolution (Step 5)
   - Legacy run naming (Step 8)
   - Search space wrappers (Step 11)
   - Legacy tag keys (Step 9)
   - Legacy folder formats (Step 7)

3. **Low Priority** (Evaluate/Remove last):
   - MLflow compatibility patch (Step 4)
   - Function wrappers (Step 12)
   - Checkpoint fallbacks (Step 13)
   - Backward compatibility defaults (Step 14)

## Notes

- All deprecated code should be removed incrementally, running tests after each step
- Some items may need to be kept temporarily if old runs/data still exist
- MLflow compatibility patch needs evaluation before removal
- v1 hash function may be kept for migration purposes


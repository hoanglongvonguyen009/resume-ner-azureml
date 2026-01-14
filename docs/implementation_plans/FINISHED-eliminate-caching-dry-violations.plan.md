# Eliminate Caching-Related DRY Violations

## Goal

Eliminate code duplication in caching-related scripts by consolidating duplicate implementations and extracting shared utilities. This will reduce codebase size by ~250+ lines, improve maintainability, and ensure consistent caching behavior across the codebase.

## Status

**Last Updated**: 2026-01-14

### Completed Steps
- ✅ Step 1: Consolidate duplicate tags_registry.py files
- ✅ Step 2: Extract mtime helper function to shared utility
- ✅ Step 3: Extract deep_merge function to shared utility
- ✅ Step 4: Update all imports and verify functionality
- ✅ Step 5: Run tests and type checking

### Pending Steps
- None

## Preconditions

- All existing tests pass
- Mypy type checking is clean for affected modules
- No active PRs modifying the duplicate files

## Steps

### Step 1: Consolidate duplicate tags_registry.py files

**Objective**: Remove duplicate `tags_registry.py` implementation from orchestration and consolidate to infrastructure version.

**Actions**:
1. Verify both files are functionally identical (already confirmed via diff)
2. Update imports in `src/orchestration/jobs/tracking/naming/tag_keys.py`:
   - Change: `from orchestration.jobs.tracking.naming.tags_registry import ...`
   - To: `from infrastructure.naming.mlflow.tags_registry import ...`
3. Update imports in `src/orchestration/jobs/tracking/naming/tags.py`:
   - Change: `from orchestration.jobs.tracking.naming.tags_registry import ...`
   - To: `from infrastructure.naming.mlflow.tags_registry import ...`
4. Delete `src/orchestration/jobs/tracking/naming/tags_registry.py`
5. Verify no other files import from the deleted module (grep search)

**Success criteria**:
- ✅ Only 1 `tags_registry.py` file exists: `src/infrastructure/naming/mlflow/tags_registry.py`
- ✅ All imports updated to use infrastructure version
- ✅ `grep -r "orchestration.jobs.tracking.naming.tags_registry" src/` returns no matches
- ✅ `uvx mypy src/orchestration/jobs/tracking/naming/` passes with 0 errors
- ✅ Existing tests still pass

---

### Step 2: Extract mtime helper function to shared utility

**Objective**: Extract duplicate `_get_config_mtime()` / `_get_policy_mtime()` functions to `common/shared/file_utils.py`.

**Actions**:
1. Add `get_file_mtime()` function to `src/common/shared/file_utils.py`:
   ```python
   def get_file_mtime(file_path: Path) -> float:
       """
       Get modification time of a file, or 0.0 if file doesn't exist.
       
       Args:
           file_path: Path to the file.
       
       Returns:
           Modification time as float, or 0.0 if file doesn't exist or error occurs.
       """
       try:
           return file_path.stat().st_mtime
       except (OSError, FileNotFoundError):
           return 0.0
   ```
2. Update `src/common/shared/__init__.py` to export `get_file_mtime`
3. Update `src/infrastructure/paths/config.py`:
   - Remove `_get_config_mtime()` function
   - Add import: `from common.shared.file_utils import get_file_mtime`
   - Replace `_get_config_mtime(paths_config_path)` with `get_file_mtime(paths_config_path)`
4. Update `src/infrastructure/naming/mlflow/config.py`:
   - Remove `_get_config_mtime()` function
   - Add import: `from common.shared.file_utils import get_file_mtime`
   - Replace `_get_config_mtime(config_path)` with `get_file_mtime(config_path)`
5. Update `src/infrastructure/naming/display_policy.py`:
   - Remove `_get_policy_mtime()` function
   - Add import: `from common.shared.file_utils import get_file_mtime`
   - Replace `_get_policy_mtime(policy_path)` with `get_file_mtime(policy_path)`

**Success criteria**:
- ✅ `get_file_mtime()` exists in `src/common/shared/file_utils.py` with proper type hints
- ✅ All 3 files use `get_file_mtime()` instead of local implementations
- ✅ No `_get_config_mtime` or `_get_policy_mtime` functions exist in codebase
- ✅ `uvx mypy src/common/shared/file_utils.py src/infrastructure/paths/config.py src/infrastructure/naming/mlflow/config.py src/infrastructure/naming/display_policy.py` passes with 0 errors
- ✅ Existing tests still pass

---

### Step 3: Extract deep_merge function to shared utility

**Objective**: Extract duplicate `_deep_merge()` function to a new `common/shared/dict_utils.py` module.

**Actions**:
1. Create `src/common/shared/dict_utils.py`:
   ```python
   """Dictionary utility functions."""
   
   from __future__ import annotations
   
   from typing import Any, Dict
   
   
   def deep_merge(defaults: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
       """
       Deep merge two dictionaries, with overrides taking precedence.
       
       Recursively merges nested dictionaries. Values in overrides take precedence
       over values in defaults.
       
       Args:
           defaults: Base dictionary with default values.
           overrides: Dictionary with override values (takes precedence).
       
       Returns:
           Merged dictionary with defaults and overrides combined.
       """
       result = defaults.copy()
       for key, value in overrides.items():
           if key in result and isinstance(result[key], dict) and isinstance(value, dict):
               result[key] = deep_merge(result[key], value)
           else:
               result[key] = value
       return result
   ```
2. Update `src/common/shared/__init__.py` to export `deep_merge`
3. Update `src/infrastructure/naming/mlflow/tags_registry.py`:
   - Remove `_deep_merge()` function
   - Add import: `from common.shared.dict_utils import deep_merge`
   - Replace `_deep_merge(defaults, loaded_data)` with `deep_merge(defaults, loaded_data)`

**Success criteria**:
- ✅ `deep_merge()` exists in `src/common/shared/dict_utils.py` with proper type hints and docstring
- ✅ `tags_registry.py` uses `deep_merge()` from shared utility
- ✅ No `_deep_merge()` function exists in codebase
- ✅ `uvx mypy src/common/shared/dict_utils.py src/infrastructure/naming/mlflow/tags_registry.py` passes with 0 errors
- ✅ Existing tests still pass

---

### Step 4: Update all imports and verify functionality

**Objective**: Ensure all affected modules have correct imports and no broken references.

**Actions**:
1. Run full type check: `uvx mypy src/` to identify any import issues
2. Fix any import errors or missing imports
3. Verify all affected files can be imported:
   - `src/infrastructure/naming/mlflow/tags_registry.py`
   - `src/orchestration/jobs/tracking/naming/tag_keys.py`
   - `src/orchestration/jobs/tracking/naming/tags.py`
   - `src/infrastructure/paths/config.py`
   - `src/infrastructure/naming/mlflow/config.py`
   - `src/infrastructure/naming/display_policy.py`
4. Run a quick smoke test: import all affected modules in Python to verify no runtime import errors

**Success criteria**:
- ✅ `uvx mypy src/` passes with 0 errors (or only pre-existing errors unrelated to this refactor)
- ✅ All affected modules can be imported without errors
- ✅ No circular import issues
- ✅ All imports use correct paths

---

### Step 5: Run tests and type checking

**Objective**: Verify the refactoring didn't break any existing functionality.

**Actions**:
1. Run type checking on all affected modules:
   ```bash
   uvx mypy src/infrastructure/naming/mlflow/tags_registry.py
   uvx mypy src/orchestration/jobs/tracking/naming/
   uvx mypy src/infrastructure/paths/config.py
   uvx mypy src/infrastructure/naming/mlflow/config.py
   uvx mypy src/infrastructure/naming/display_policy.py
   uvx mypy src/common/shared/file_utils.py
   uvx mypy src/common/shared/dict_utils.py
   ```
2. Run relevant tests (if test files exist):
   - Search for tests covering tags_registry functionality
   - Search for tests covering config loading
   - Run any integration tests that use these modules
3. Manual verification:
   - Verify tags_registry can load from config/tags.yaml
   - Verify config files can be loaded with caching
   - Verify cache invalidation works (mtime-based)

**Success criteria**:
- ✅ All type checks pass with 0 errors
- ✅ All existing tests pass
- ✅ Manual verification confirms functionality works as expected
- ✅ No regressions introduced

---

## Success Criteria (Overall)

- ✅ **Code reduction**: ~250+ lines of duplicate code removed
- ✅ **Single source of truth**: Only 1 `tags_registry.py` implementation
- ✅ **Shared utilities**: `get_file_mtime()` and `deep_merge()` in common/shared
- ✅ **Type safety**: All code passes Mypy strict type checking
- ✅ **Functionality**: All existing functionality preserved
- ✅ **Maintainability**: Future changes only need to be made in one place

## Notes

### Deferred Items (Not in Scope)

The following items from the analysis are **deferred** for future work:

1. **Medium Priority**: Generic config caching utility (`common/shared/config_cache.py`)
   - Rationale: Current caching patterns work well, consolidation can be done later if needed
   - Impact: Low - current implementations are functional

2. **Low Priority**: Standardize cache invalidation strategy
   - Rationale: Different invalidation strategies serve different use cases
   - Impact: Low - no functional issues, just inconsistency

### Risk Assessment

- **Low Risk**: Only 2 files import from orchestration tags_registry (easy to update)
- **Low Risk**: mtime and deep_merge functions are pure utilities (no side effects)
- **Low Risk**: All changes are internal refactoring (no API changes)

### Rollback Plan

If issues arise:
1. Revert commits in reverse order
2. Restore deleted `tags_registry.py` from git history
3. Revert import changes in affected files


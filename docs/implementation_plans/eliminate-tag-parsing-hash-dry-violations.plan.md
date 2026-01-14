# Eliminate Tag Parsing and Hash Computation DRY Violations

## Goal

Eliminate code duplication in tag parsing and hash computation by consolidating duplicate implementations and extracting shared utilities. This will reduce codebase size, improve maintainability, and ensure consistent tag parsing and hashing behavior across the codebase.

## Status

**Last Updated**: 2026-01-14

### Completed Steps
- None

### Pending Steps
- ⏳ Step 1: Consolidate duplicate tag_keys.py files
- ⏳ Step 2: Consolidate duplicate hpo_keys.py files
- ⏳ Step 3: Consolidate duplicate run_keys.py files
- ⏳ Step 4: Consolidate duplicate refit_keys.py files
- ⏳ Step 5: Extract hash computation utilities to shared module
- ⏳ Step 6: Consolidate cache hash computation
- ⏳ Step 7: Update all imports and verify functionality
- ⏳ Step 8: Run tests and type checking

## Preconditions

- All existing tests pass
- Mypy type checking is clean for affected modules
- No active PRs modifying the duplicate files

## Analysis

### Identified DRY Violations

1. **Duplicate tag_keys.py files**:
   - `src/infrastructure/naming/mlflow/tag_keys.py` (324 lines, with metadata)
   - `src/orchestration/jobs/tracking/naming/tag_keys.py` (333 lines, without metadata)
   - **Difference**: Only import paths differ (`.tags` vs `orchestration.jobs.tracking.naming.tags`)
   - **Impact**: ~320 lines of duplicate code

2. **Duplicate hpo_keys.py files**:
   - `src/infrastructure/naming/mlflow/hpo_keys.py` (424 lines, with metadata, has `compute_data_fingerprint`, `compute_eval_fingerprint`, `build_hpo_study_key_v2`)
   - `src/orchestration/jobs/tracking/naming/hpo_keys.py` (256 lines, without metadata, missing v2 functions)
   - **Difference**: Infrastructure version has additional v2 functions and fingerprint computation
   - **Impact**: ~250 lines of duplicate code, plus missing functionality in orchestration version

3. **Duplicate run_keys.py files**:
   - `src/infrastructure/naming/mlflow/run_keys.py` (128 lines, with metadata)
   - `src/orchestration/jobs/tracking/naming/run_keys.py` (108 lines, without metadata)
   - **Difference**: Only import paths differ (`.context` vs `infrastructure.naming.context`)
   - **Impact**: ~110 lines of duplicate code

4. **Duplicate refit_keys.py files**:
   - `src/infrastructure/naming/mlflow/refit_keys.py` (79 lines, with metadata)
   - `src/orchestration/jobs/tracking/naming/refit_keys.py` (56 lines, without metadata)
   - **Difference**: Only import paths differ (`.hpo_keys` vs `orchestration.jobs.tracking.naming.hpo_keys`)
   - **Impact**: ~55 lines of duplicate code

5. **Hash computation duplication**:
   - `_compute_hash_64()` function duplicated in both hpo_keys.py files
   - `build_mlflow_run_key_hash()` uses direct `hashlib.sha256()` in both run_keys.py files
   - Direct `hashlib.sha256()` usage in:
     - `src/selection/cache.py` (line 59, 236-239)
     - `src/evaluation/selection/cache.py` (line 87, 265-268)
     - `src/orchestration/jobs/tracking/naming/run_keys.py` (line 84)
     - `src/evaluation/benchmarking/orchestrator.py` (line 824)
   - **Impact**: Inconsistent hash computation patterns, potential for bugs

6. **Cache hash computation duplication**:
   - `compute_selection_cache_key()` duplicated in:
     - `src/selection/cache.py` (lines 40-59)
     - `src/evaluation/selection/cache.py` (lines 68-87)
   - **Difference**: Identical implementation, only import paths differ
   - **Impact**: ~50 lines of duplicate code

## Steps

### Step 1: Consolidate duplicate tag_keys.py files

**Objective**: Remove duplicate `tag_keys.py` implementation from orchestration and consolidate to infrastructure version.

**Actions**:
1. Verify both files are functionally identical (already confirmed via diff - only import paths differ)
2. Update imports in `src/orchestration/jobs/tracking/trackers/benchmark_tracker.py`:
   - Change: `from orchestration.jobs.tracking.naming.tag_keys import ...`
   - To: `from infrastructure.naming.mlflow.tag_keys import ...`
3. Update imports in `src/orchestration/jobs/tracking/trackers/sweep_tracker.py`:
   - Change: `from orchestration.jobs.tracking.naming.tag_keys import ...`
   - To: `from infrastructure.naming.mlflow.tag_keys import ...`
4. Update imports in `src/orchestration/jobs/tracking/naming/refit_keys.py`:
   - Check if it imports from tag_keys (may not need update)
5. Delete `src/orchestration/jobs/tracking/naming/tag_keys.py`
6. Verify no other files import from the deleted module (grep search)

**Success criteria**:
- ✅ Only 1 `tag_keys.py` file exists: `src/infrastructure/naming/mlflow/tag_keys.py`
- ✅ All imports updated to use infrastructure version
- ✅ `grep -r "orchestration.jobs.tracking.naming.tag_keys" src/` returns no matches
- ✅ `uvx mypy src/orchestration/jobs/tracking/` passes with 0 errors
- ✅ Existing tests still pass

---

### Step 2: Consolidate duplicate hpo_keys.py files

**Objective**: Remove duplicate `hpo_keys.py` implementation from orchestration and consolidate to infrastructure version (which has more complete functionality).

**Actions**:
1. Verify infrastructure version has all functions from orchestration version
2. Update imports in `src/orchestration/jobs/tracking/naming/refit_keys.py`:
   - Change: `from orchestration.jobs.tracking.naming.hpo_keys import _compute_hash_64`
   - To: `from infrastructure.naming.mlflow.hpo_keys import _compute_hash_64`
3. Update imports in `src/orchestration/jobs/tracking/mlflow_naming.py`:
   - Change: `from orchestration.jobs.tracking.naming.hpo_keys import ...`
   - To: `from infrastructure.naming.mlflow.hpo_keys import ...`
4. Update imports in `src/orchestration/jobs/tracking/naming/__init__.py`:
   - Change: `from orchestration.jobs.tracking.naming.hpo_keys import ...`
   - To: `from infrastructure.naming.mlflow.hpo_keys import ...`
5. Check for any other imports from orchestration hpo_keys
6. Delete `src/orchestration/jobs/tracking/naming/hpo_keys.py`
7. Verify no other files import from the deleted module

**Success criteria**:
- ✅ Only 1 `hpo_keys.py` file exists: `src/infrastructure/naming/mlflow/hpo_keys.py`
- ✅ All imports updated to use infrastructure version
- ✅ `grep -r "orchestration.jobs.tracking.naming.hpo_keys" src/` returns no matches
- ✅ `uvx mypy src/orchestration/jobs/tracking/` passes with 0 errors
- ✅ Existing tests still pass
- ✅ All functions from orchestration version are available in infrastructure version

---

### Step 3: Consolidate duplicate run_keys.py files

**Objective**: Remove duplicate `run_keys.py` implementation from orchestration and consolidate to infrastructure version.

**Actions**:
1. Verify both files are functionally identical (already confirmed via diff - only import paths differ)
2. Update imports in `src/orchestration/jobs/tracking/naming/run_names.py`:
   - Change: `from orchestration.jobs.tracking.naming.run_keys import ...`
   - To: `from infrastructure.naming.mlflow.run_keys import ...`
3. Update imports in `src/orchestration/jobs/tracking/mlflow_naming.py`:
   - Change: `from orchestration.jobs.tracking.naming.run_keys import ...`
   - To: `from infrastructure.naming.mlflow.run_keys import ...`
4. Update imports in `src/orchestration/jobs/tracking/naming/__init__.py`:
   - Change: `from orchestration.jobs.tracking.naming.run_keys import ...`
   - To: `from infrastructure.naming.mlflow.run_keys import ...`
5. Delete `src/orchestration/jobs/tracking/naming/run_keys.py`
6. Verify no other files import from the deleted module (grep search)

**Success criteria**:
- ✅ Only 1 `run_keys.py` file exists: `src/infrastructure/naming/mlflow/run_keys.py`
- ✅ All imports updated to use infrastructure version
- ✅ `grep -r "orchestration.jobs.tracking.naming.run_keys" src/` returns no matches
- ✅ `uvx mypy src/orchestration/jobs/tracking/` passes with 0 errors
- ✅ Existing tests still pass

---

### Step 4: Consolidate duplicate refit_keys.py files

**Objective**: Remove duplicate `refit_keys.py` implementation from orchestration and consolidate to infrastructure version.

**Actions**:
1. Verify both files are functionally identical (already confirmed via diff - only import paths differ)
2. Update imports in `src/orchestration/jobs/tracking/mlflow_naming.py`:
   - Change: `from orchestration.jobs.tracking.naming.refit_keys import ...`
   - To: `from infrastructure.naming.mlflow.refit_keys import ...`
3. Update imports in `src/orchestration/jobs/tracking/naming/__init__.py`:
   - Change: `from orchestration.jobs.tracking.naming.refit_keys import ...`
   - To: `from infrastructure.naming.mlflow.refit_keys import ...`
4. Delete `src/orchestration/jobs/tracking/naming/refit_keys.py`
5. Verify no other files import from the deleted module (grep search)

**Success criteria**:
- ✅ Only 1 `refit_keys.py` file exists: `src/infrastructure/naming/mlflow/refit_keys.py`
- ✅ All imports updated to use infrastructure version
- ✅ `grep -r "orchestration.jobs.tracking.naming.refit_keys" src/` returns no matches
- ✅ `uvx mypy src/orchestration/jobs/tracking/` passes with 0 errors
- ✅ Existing tests still pass

---

### Step 5: Extract hash computation utilities to shared module

**Objective**: Extract `_compute_hash_64()` and other hash computation patterns to `common/shared/hash_utils.py`.

**Actions**:
1. Create `src/common/shared/hash_utils.py`:
   ```python
   """Hash computation utilities."""
   
   from __future__ import annotations
   
   import hashlib
   from typing import Any, Dict
   
   
   def compute_hash_64(data: str) -> str:
       """
       Compute full SHA256 hash (64 hex characters).
       
       Args:
           data: String to hash.
       
       Returns:
           64-character hex hash.
       """
       return hashlib.sha256(data.encode('utf-8')).hexdigest()
   
   
   def compute_hash_16(data: str) -> str:
       """
       Compute truncated SHA256 hash (16 hex characters).
       
       Args:
           data: String to hash.
       
       Returns:
           16-character hex hash (first 16 chars of SHA256).
       """
       return hashlib.sha256(data.encode('utf-8')).hexdigest()[:16]
   
   
   def compute_json_hash(data: Dict[str, Any], length: int = 64) -> str:
       """
       Compute hash of JSON-serialized dictionary.
       
       Args:
           data: Dictionary to hash.
           length: Length of hash to return (16 or 64).
       
       Returns:
           Hex hash of specified length.
       """
       import json
       json_str = json.dumps(data, sort_keys=True, default=str)
       hash_full = hashlib.sha256(json_str.encode('utf-8')).hexdigest()
       return hash_full[:length] if length < 64 else hash_full
   ```
2. Update `src/common/shared/__init__.py` to export hash utilities
3. Update `src/infrastructure/naming/mlflow/hpo_keys.py`:
   - Remove `_compute_hash_64()` function
   - Add import: `from common.shared.hash_utils import compute_hash_64`
   - Replace `_compute_hash_64(...)` with `compute_hash_64(...)`
4. Update `src/infrastructure/naming/mlflow/run_keys.py`:
   - Replace `build_mlflow_run_key_hash()` to use `compute_hash_64()` from shared utilities
   - Add import: `from common.shared.hash_utils import compute_hash_64`
   - Replace direct `hashlib.sha256()` usage with `compute_hash_64()`
5. Update `src/infrastructure/naming/mlflow/refit_keys.py`:
   - Replace `_compute_hash_64()` import from hpo_keys with `compute_hash_64()` from shared utilities
   - Add import: `from common.shared.hash_utils import compute_hash_64`
   - Replace `_compute_hash_64(...)` with `compute_hash_64(...)`
6. Update `src/evaluation/benchmarking/orchestrator.py`:
   - Replace direct `hashlib.sha256()` usage with `compute_hash_64()` or `compute_json_hash()`

**Success criteria**:
- ✅ `compute_hash_64()`, `compute_hash_16()`, and `compute_json_hash()` exist in `src/common/shared/hash_utils.py`
- ✅ All files use shared hash utilities instead of direct hashlib calls
- ✅ No `_compute_hash_64()` functions exist in codebase
- ✅ `uvx mypy src/common/shared/hash_utils.py src/infrastructure/naming/mlflow/hpo_keys.py` passes with 0 errors
- ✅ Existing tests still pass

---

### Step 6: Consolidate cache hash computation

**Objective**: Extract duplicate `compute_selection_cache_key()` function to shared utility.

**Actions**:
1. Add `compute_selection_cache_key()` function to `src/common/shared/hash_utils.py`:
   ```python
   def compute_selection_cache_key(
       experiment_name: str,
       selection_config: Dict[str, Any],
       tags_config: Dict[str, Any],
       benchmark_experiment_id: str,
       tracking_uri: Optional[str] = None,
   ) -> str:
       """
       Compute cache key for best model selection.
       
       Args:
           experiment_name: Name of the experiment.
           selection_config: Selection configuration dict.
           tags_config: Tags configuration dict.
           benchmark_experiment_id: MLflow experiment ID for benchmark runs.
           tracking_uri: Optional MLflow tracking URI.
       
       Returns:
           16-character hex hash.
       """
       cache_data = {
           "experiment_name": experiment_name,
           "selection_config": selection_config,
           "tags_config": tags_config,
           "benchmark_experiment_id": benchmark_experiment_id,
       }
       if tracking_uri:
           cache_data["tracking_uri"] = tracking_uri
       
       return compute_json_hash(cache_data, length=16)
   ```
2. Update `src/selection/cache.py`:
   - Remove `compute_selection_cache_key()` function
   - Add import: `from common.shared.hash_utils import compute_selection_cache_key`
   - Replace local function calls with imported function
3. Update `src/evaluation/selection/cache.py`:
   - Remove `compute_selection_cache_key()` function
   - Add import: `from common.shared.hash_utils import compute_selection_cache_key`
   - Replace local function calls with imported function
4. Update `src/common/shared/__init__.py` to export `compute_selection_cache_key`

**Success criteria**:
- ✅ `compute_selection_cache_key()` exists in `src/common/shared/hash_utils.py`
- ✅ Both cache.py files use shared function
- ✅ No duplicate `compute_selection_cache_key()` functions exist
- ✅ `uvx mypy src/common/shared/hash_utils.py src/selection/cache.py src/evaluation/selection/cache.py` passes with 0 errors
- ✅ Existing tests still pass

---

### Step 7: Update all imports and verify functionality

**Objective**: Ensure all affected modules have correct imports and no broken references.

**Actions**:
1. Run full type check: `uvx mypy src/` to identify any import issues
2. Fix any import errors or missing imports
3. Verify all affected files can be imported:
   - `src/infrastructure/naming/mlflow/tag_keys.py`
   - `src/infrastructure/naming/mlflow/hpo_keys.py`
   - `src/common/shared/hash_utils.py`
   - All files that previously imported from orchestration versions
4. Run a quick smoke test: import all affected modules in Python to verify no runtime import errors

**Success criteria**:
- ✅ `uvx mypy src/` passes with 0 errors (or only pre-existing errors unrelated to this refactor)
- ✅ All affected modules can be imported without errors
- ✅ No circular import issues
- ✅ All imports use correct paths

---

### Step 8: Run tests and type checking

**Objective**: Verify the refactoring didn't break any existing functionality.

**Actions**:
1. Run type checking on all affected modules:
   ```bash
   uvx mypy src/infrastructure/naming/mlflow/tag_keys.py
   uvx mypy src/infrastructure/naming/mlflow/hpo_keys.py
   uvx mypy src/common/shared/hash_utils.py
   uvx mypy src/orchestration/jobs/tracking/
   uvx mypy src/selection/cache.py
   uvx mypy src/evaluation/selection/cache.py
   ```
2. Run relevant tests (if test files exist):
   - Search for tests covering tag_keys functionality
   - Search for tests covering hpo_keys functionality
   - Search for tests covering cache functionality
   - Run any integration tests that use these modules
3. Manual verification:
   - Verify tag keys can be retrieved correctly
   - Verify hash computation produces consistent results
   - Verify cache keys are computed correctly

**Success criteria**:
- ✅ All type checks pass with 0 errors
- ✅ All existing tests pass
- ✅ Manual verification confirms functionality works as expected
- ✅ No regressions introduced

---

## Success Criteria (Overall)

- ✅ **Code reduction**: ~750+ lines of duplicate code removed
- ✅ **Single source of truth**: Only 1 `tag_keys.py` implementation
- ✅ **Single source of truth**: Only 1 `hpo_keys.py` implementation
- ✅ **Single source of truth**: Only 1 `run_keys.py` implementation
- ✅ **Single source of truth**: Only 1 `refit_keys.py` implementation
- ✅ **Shared utilities**: Hash computation functions in `common/shared/hash_utils.py`
- ✅ **Type safety**: All code passes Mypy strict type checking
- ✅ **Functionality**: All existing functionality preserved
- ✅ **Maintainability**: Future changes only need to be made in one place

## Notes

### Import Path Strategy

- **Consolidation target**: Use `infrastructure.naming.mlflow.*` as the single source of truth
  - Rationale: Infrastructure layer is more appropriate for shared utilities
  - Infrastructure version already has metadata and more complete functionality
  - Follows the pattern established in `FINISHED-eliminate-caching-dry-violations.plan.md`

### Hash Utility Design

- **Function naming**: Use `compute_hash_*` instead of `_compute_hash_*` (public API)
- **Length variants**: Provide both 16-char and 64-char variants for different use cases
- **JSON helper**: `compute_json_hash()` handles common pattern of hashing dictionaries

### Risk Assessment

- **Low Risk**: Only a few files import from orchestration versions (easy to update)
- **Low Risk**: Hash computation functions are pure utilities (no side effects)
- **Low Risk**: All changes are internal refactoring (no API changes)
- **Medium Risk**: Need to verify all imports are updated correctly

### Rollback Plan

If issues arise:
1. Revert commits in reverse order
2. Restore deleted files from git history
3. Revert import changes in affected files

## Related Plans

- `FINISHED-eliminate-caching-dry-violations.plan.md` - Similar consolidation pattern
- `consolidate-paths-and-naming-to-src-level-c536724f.plan.md` - May have related naming consolidation


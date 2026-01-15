# Consolidate Config Loading Utilities DRY Violations

## Goal

Eliminate duplicate config loading patterns, config directory inference logic, and re-inference violations across utility scripts. Consolidate YAML config loading with caching into a single pattern, standardize config_dir inference to use `resolve_project_paths()`, and eliminate cases where config_dir is re-inferred when already available from callers.

## Status

**Last Updated**: 2026-01-27

**Status**: ⏳ **IN PROGRESS** - Step 1 complete, remaining steps pending

### Completed Steps
- ✅ Step 1: Document all utility scripts with config loading responsibilities (2026-01-27)
- ⏳ Step 2: Consolidate config loading with caching patterns
- ⏳ Step 3: Standardize config_dir inference to use resolve_project_paths()
- ⏳ Step 4: Eliminate re-inference of config_dir when already available
- ⏳ Step 5: Verify no breaking changes and update tests

## Preconditions

- All existing tests pass: `uvx pytest tests/`
- Mypy passes: `uvx mypy src --show-error-codes`
- No active PRs modifying config loading utilities

## Analysis Summary

### Utility Scripts Found (with config loading)

1. **`src/infrastructure/naming/mlflow/tags_registry.py`** (type: utility)
   - **Purpose**: Load tag keys from `config/tags.yaml` with caching and defaults
   - **Pattern**: Module-level cache with path-based invalidation, fallback to defaults
   - **Config dir inference**: Uses `resolve_project_paths()` with fallback to `infer_config_dir()`

2. **`src/infrastructure/naming/mlflow/config.py`** (type: utility)
   - **Purpose**: Load MLflow configuration from `config/mlflow.yaml` with caching
   - **Pattern**: Module-level cache with mtime-based invalidation
   - **Config dir inference**: Uses `resolve_project_paths()` with fallback to `infer_config_dir()`

3. **`src/orchestration/jobs/tracking/config/loader.py`** (type: utility)
   - **Purpose**: Load MLflow configuration from `config/mlflow.yaml` with caching
   - **Pattern**: Module-level cache (simpler, no mtime check)
   - **Config dir inference**: Uses `infer_config_dir()` directly (no `resolve_project_paths()`)

### Overlapping Responsibilities Identified

#### Category 1: Duplicate Config Loading with Caching (HIGH PRIORITY)

**Issue**: Three different implementations of MLflow config loading with caching:

1. **`infrastructure.naming.mlflow.config.load_mlflow_config()`** (SSOT candidate)
   - Uses mtime-based cache invalidation
   - Uses `resolve_project_paths()` for config_dir inference
   - Well-documented, comprehensive

2. **`orchestration.jobs.tracking.config.loader.load_mlflow_config()`** (duplicate)
   - Simpler cache (no mtime check)
   - Uses `infer_config_dir()` directly (inconsistent with SSOT pattern)
   - Less comprehensive

3. **`infrastructure.naming.mlflow.tags_registry.load_tags_registry()`** (different file, similar pattern)
   - Loads `config/tags.yaml` (different file, but same pattern)
   - Uses path-based cache invalidation
   - Uses `resolve_project_paths()` for config_dir inference

**Root Cause**: Similar caching patterns implemented independently in different modules.

**Consolidation Approach**: 
- Keep `infrastructure.naming.mlflow.config.load_mlflow_config()` as SSOT for `mlflow.yaml`
- Keep `infrastructure.naming.mlflow.tags_registry.load_tags_registry()` for `tags.yaml` (different file)
- Remove `orchestration.jobs.tracking.config.loader.load_mlflow_config()` and update call sites to use SSOT

#### Category 2: Inconsistent Config Directory Inference (MEDIUM PRIORITY)

**Issue**: Multiple patterns for inferring `config_dir`:

1. **SSOT Pattern** (used by `tags_registry.py` and `config.py`):
   ```python
   if config_dir is None:
       from infrastructure.paths.utils import resolve_project_paths
       _, config_dir = resolve_project_paths(config_dir=None)
       if config_dir is None:
           from infrastructure.paths.utils import infer_config_dir
           config_dir = infer_config_dir()
   ```

2. **Direct Pattern** (used by `orchestration/jobs/tracking/config/loader.py`):
   ```python
   if config_dir is None:
       from infrastructure.paths.utils import infer_config_dir
       config_dir = infer_config_dir()
   ```

**Root Cause**: Not all utilities use the standardized `resolve_project_paths()` pattern.

**Consolidation Approach**: Standardize all utilities to use the SSOT pattern (resolve_project_paths with fallback).

#### Category 3: Re-inference of config_dir When Already Available (HIGH PRIORITY)

**Issue**: Functions re-infer `config_dir` even when it's already provided by the caller.

**Examples**:

1. **`setup_hpo_mlflow_run()` in `training/hpo/tracking/setup.py`**:
   - Line 30: `config_dir: Optional[Path] = None` parameter
   - Line 75-82: Re-infers `config_dir` in fallback path even when parameter exists
   - **Caller**: `run_local_hpo_sweep()` (sweep.py:608) already has `project_config_dir` but fallback path re-infers

2. **`load_tags_registry()` in `infrastructure/naming/mlflow/tags_registry.py`**:
   - Line 194-200: Uses `resolve_project_paths()` then falls back to `infer_config_dir()` 
   - This is acceptable when `config_dir=None`, but should trust provided parameter

3. **`load_mlflow_config()` in `infrastructure/naming/mlflow/config.py`**:
   - Line 55-61: Uses `resolve_project_paths()` then falls back to `infer_config_dir()`
   - This is acceptable when `config_dir=None`, but should trust provided parameter

**Root Cause**: Functions don't trust provided `config_dir` parameter and re-infer unnecessarily.

**Consolidation Approach**: 
- Trust provided `config_dir` parameter when not None
- Only infer when `config_dir is None`
- Use `resolve_project_paths()` consistently when inference is needed

## Steps

### Step 1: Document All Utility Scripts with Config Loading Responsibilities

**Objective**: Create comprehensive inventory of all utility scripts that load config files.

**Actions**:
1. Search for all files with `type: utility` or `type: config` in metadata:
   ```bash
   grep -r "type: utility\|type: config" --include="*.py" src/ -A 5
   ```
2. Identify all config loading functions:
   ```bash
   grep -r "def.*load.*config\|def.*load.*yaml" --include="*.py" src/
   ```
3. Document each utility script:
   - File path
   - Stated purpose (from metadata)
   - Config files loaded
   - Caching pattern used
   - Config dir inference pattern
   - Call sites and usage patterns

**Success criteria**:
- Complete inventory of utility scripts with config loading
- All config loading patterns documented
- All config dir inference patterns documented

**Output**: Markdown table with all utility scripts and their patterns

**Completion Notes** (2026-01-27):
- ✅ Comprehensive inventory created (see table below)
- ✅ All config loading patterns documented
- ✅ All config dir inference patterns documented
- ✅ Call sites identified for duplicate functions

#### Utility Scripts with Config Loading - Complete Inventory

| File Path | Purpose | Config File | Caching Pattern | Config Dir Inference | Call Sites | 
|-----------|---------|-------------|-----------------|---------------------|-----------|
|-----------|---------|-------------|-----------------|---------------------|------------|
| `src/infrastructure/naming/mlflow/tags_registry.py` | Load tag keys from `config/tags.yaml` with caching and defaults | `tags.yaml` | Module-level cache with path-based invalidation (`_registry_cache`, `_registry_cache_path`) | Uses `resolve_project_paths()` with fallback to `infer_config_dir()` (lines 194-200) | 15+ call sites across HPO, selection, tracking modules |
| `src/infrastructure/naming/mlflow/config.py` | Load MLflow configuration from `config/mlflow.yaml` with caching | `mlflow.yaml` | Module-level cache with mtime-based invalidation (`_config_cache: Dict[tuple, tuple]`) | Uses `resolve_project_paths()` with fallback to `infer_config_dir()` (lines 55-61) | Used internally by get_*_config() functions; 6+ direct call sites |
| `src/orchestration/jobs/tracking/config/loader.py` | Load MLflow configuration from `config/mlflow.yaml` with caching | `mlflow.yaml` | Module-level cache (simpler, no mtime check) (`_config_cache`, `_config_cache_path`) | Uses `infer_config_dir()` directly (line 33-34) - **INCONSISTENT** | 23+ call sites across tracking, HPO, orchestration modules |
| `src/infrastructure/paths/config.py` | Load paths configuration from `config/paths.yaml` with caching | `paths.yaml` | Module-level cache with mtime-based invalidation (`_config_cache: Dict[tuple, tuple]`) | Requires `config_dir` parameter (no inference) | Used by path resolution utilities |

#### Detailed Analysis

**1. `infrastructure.naming.mlflow.tags_registry.load_tags_registry()`**
- **Config File**: `config/tags.yaml`
- **Caching**: Path-based cache (`_registry_cache`, `_registry_cache_path`)
- **Inference Pattern**: 
  ```python
  if config_dir is None:
      from infrastructure.paths.utils import resolve_project_paths
      _, config_dir = resolve_project_paths(config_dir=None)
      if config_dir is None:
          from infrastructure.paths.utils import infer_config_dir
          config_dir = infer_config_dir()
  ```
- **Special Features**: Fallback to hardcoded defaults if file missing
- **Call Sites**: 
  - `training/hpo/execution/local/sweep.py` (2 call sites)
  - `training/hpo/execution/local/refit.py` (3 call sites)
  - `evaluation/selection/trial_finder.py` (2 call sites)
  - `infrastructure/tracking/mlflow/trackers/sweep_tracker.py` (1 call site)
  - `infrastructure/tracking/mlflow/hash_utils.py` (3 call sites)
  - And 5+ more

**2. `infrastructure.naming.mlflow.config.load_mlflow_config()`** (SSOT Candidate)
- **Config File**: `config/mlflow.yaml`
- **Caching**: Mtime-based cache (`_config_cache: Dict[tuple, tuple]`)
- **Inference Pattern**: 
  ```python
  if config_dir is None:
      from infrastructure.paths.utils import resolve_project_paths
      _, config_dir = resolve_project_paths(config_dir=None)
      if config_dir is None:
          from infrastructure.paths.utils import infer_config_dir
          config_dir = infer_config_dir()
  ```
- **Special Features**: Mtime-based cache invalidation, comprehensive
- **Call Sites**: 
  - Used internally by `get_naming_config()`, `get_index_config()`, `get_run_finder_config()`, `get_auto_increment_config()`, `get_tracking_config()`
  - 6+ direct call sites in naming and tracking modules

**3. `orchestration.jobs.tracking.config.loader.load_mlflow_config()`** (DUPLICATE - Remove)
- **Config File**: `config/mlflow.yaml` (same as #2)
- **Caching**: Simple cache without mtime check (`_config_cache`, `_config_cache_path`)
- **Inference Pattern**: 
  ```python
  if config_dir is None:
      from infrastructure.paths.utils import infer_config_dir
      config_dir = infer_config_dir()  # Direct, no resolve_project_paths()
  ```
- **Special Features**: Simpler implementation, less comprehensive
- **Call Sites**: 23+ call sites:
  - `training/hpo/tracking/setup.py` (1 call site)
  - `infrastructure/tracking/mlflow/finder.py` (1 call site)
  - `infrastructure/tracking/mlflow/trackers/benchmark_tracker.py` (2 call sites)
  - `infrastructure/tracking/mlflow/trackers/conversion_tracker.py` (2 call sites)
  - `infrastructure/tracking/mlflow/trackers/training_tracker.py` (1 call site)
  - `infrastructure/tracking/mlflow/artifacts/uploader.py` (1 call site)
  - `orchestration/jobs/tracking/config/__init__.py` (exports)
  - `orchestration/jobs/tracking/index/run_index.py` (1 call site)
  - `orchestration/jobs/tracking/naming/tags.py` (1 call site)
  - `orchestration/jobs/tracking/mlflow_config_loader.py` (1 call site)
  - `training/hpo/tracking/runs.py` (1 call site)
  - `tests/tracking/unit/test_mlflow_config_comprehensive.py` (test file)
  - `tests/config/unit/test_mlflow_yaml.py` (test file)
  - And more

**4. `infrastructure.paths.config.load_paths_config()`**
- **Config File**: `config/paths.yaml`
- **Caching**: Mtime-based cache (`_config_cache: Dict[tuple, tuple]`)
- **Inference Pattern**: Requires `config_dir` parameter (no inference)
- **Special Features**: Environment-specific overrides, validation
- **Call Sites**: Used by path resolution utilities

#### Overlap Summary

**Duplicate Config Loading**:
- `infrastructure.naming.mlflow.config.load_mlflow_config()` and `orchestration.jobs.tracking.config.loader.load_mlflow_config()` both load `mlflow.yaml`
- **Impact**: 23+ call sites need to be updated to use SSOT

**Inconsistent Inference Patterns**:
- `infrastructure.naming.mlflow.config.load_mlflow_config()` uses `resolve_project_paths()` pattern
- `orchestration.jobs.tracking.config.loader.load_mlflow_config()` uses direct `infer_config_dir()` pattern
- **Impact**: Inconsistent behavior, harder to maintain

**Re-inference Violations**:
- `training/hpo/tracking/setup.py::setup_hpo_mlflow_run()` re-infers `config_dir` in fallback path (lines 75-82, 195-197) even when parameter is provided
- **Impact**: Unnecessary computation, potential inconsistencies

### Step 2: Consolidate Config Loading with Caching Patterns

**Objective**: Remove duplicate `load_mlflow_config()` implementation and standardize caching pattern.

**Actions**:
1. Identify SSOT: `infrastructure.naming.mlflow.config.load_mlflow_config()` (most comprehensive)
2. Update `orchestration.jobs.tracking.config.loader`:
   - Remove `load_mlflow_config()` function
   - Import from `infrastructure.naming.mlflow.config` instead
   - Update `__init__.py` exports if needed
3. Find all call sites of `orchestration.jobs.tracking.config.loader.load_mlflow_config()`:
   ```bash
   grep -r "from.*orchestration.*jobs.*tracking.*config.*loader.*import.*load_mlflow_config\|orchestration\.jobs\.tracking\.config\.loader\.load_mlflow_config" --include="*.py" src/ tests/
   ```
4. Update imports to use SSOT:
   - `from orchestration.jobs.tracking.config.loader import load_mlflow_config` 
   - → `from infrastructure.naming.mlflow.config import load_mlflow_config`
5. Verify `tags_registry.py` pattern is appropriate (different file, keep separate but ensure consistent pattern)

**Success criteria**:
- `orchestration.jobs.tracking.config.loader.load_mlflow_config()` removed
- All call sites updated to use SSOT
- Tests pass: `uvx pytest tests/`
- Mypy passes: `uvx mypy src --show-error-codes`

**Verification**:
```bash
# Should return 0 results
grep -r "orchestration\.jobs\.tracking\.config\.loader\.load_mlflow_config\|from.*orchestration.*jobs.*tracking.*config.*loader.*import.*load_mlflow_config" --include="*.py" src/ tests/
```

### Step 3: Standardize Config Directory Inference to Use resolve_project_paths()

**Objective**: Ensure all config loading utilities use the standardized `resolve_project_paths()` pattern.

**Actions**:
1. Update `orchestration.jobs.tracking.config.loader.load_mlflow_config()` (if still exists after Step 2):
   - Replace direct `infer_config_dir()` call with `resolve_project_paths()` pattern
   - Use same pattern as `infrastructure.naming.mlflow.config.load_mlflow_config()`
2. Verify `infrastructure.naming.mlflow.config.load_mlflow_config()` uses correct pattern:
   - Should use `resolve_project_paths()` with fallback to `infer_config_dir()`
3. Verify `infrastructure.naming.mlflow.tags_registry.load_tags_registry()` uses correct pattern:
   - Should use `resolve_project_paths()` with fallback to `infer_config_dir()`
4. Check for other config loading utilities that don't use the pattern:
   ```bash
   grep -r "infer_config_dir()" --include="*.py" src/infrastructure src/orchestration | grep -v "resolve_project_paths"
   ```

**Success criteria**:
- All config loading utilities use `resolve_project_paths()` pattern
- Consistent fallback to `infer_config_dir()` when `resolve_project_paths()` returns None
- Tests pass: `uvx pytest tests/`
- Mypy passes: `uvx mypy src --show-error-codes`

**Verification**:
```bash
# Should show only resolve_project_paths() pattern or direct parameter usage
grep -r "if config_dir is None:" --include="*.py" src/infrastructure src/orchestration -A 3
```

### Step 4: Eliminate Re-inference of config_dir When Already Available

**Objective**: Trust provided `config_dir` parameter and only infer when explicitly None.

**Actions**:
1. Fix `setup_hpo_mlflow_run()` in `training/hpo/tracking/setup.py`:
   - Line 75-82: Remove re-inference in fallback path when `config_dir` parameter is provided
   - Trust provided `config_dir` parameter (line 30)
   - Only infer when `config_dir is None`
   - Update fallback path (line 195-197) to also trust provided parameter
2. Verify `load_tags_registry()` trusts provided parameter:
   - Line 194-200: Should only infer when `config_dir is None`
   - Current implementation is correct (only infers when None)
3. Verify `load_mlflow_config()` trusts provided parameter:
   - Line 55-61: Should only infer when `config_dir is None`
   - Current implementation is correct (only infers when None)
4. Check for other functions that re-infer config_dir unnecessarily:
   ```bash
   grep -r "config_dir.*=.*infer_config_dir\|config_dir.*=.*resolve_project_paths" --include="*.py" src/ -B 2 -A 2
   ```

**Success criteria**:
- `setup_hpo_mlflow_run()` trusts provided `config_dir` parameter
- No functions re-infer `config_dir` when parameter is provided
- All inference happens only when `config_dir is None`
- Tests pass: `uvx pytest tests/`
- Mypy passes: `uvx mypy src --show-error-codes`

**Verification**:
```bash
# Check that config_dir inference only happens when None
grep -r "if config_dir is None:" --include="*.py" src/ -A 5 | grep -v "resolve_project_paths\|infer_config_dir" || echo "All inference guarded by None check"
```

### Step 5: Verify No Breaking Changes and Update Tests

**Objective**: Ensure all changes are backward-compatible and tests are updated.

**Actions**:
1. Run full test suite:
   ```bash
   uvx pytest tests/ -v
   ```
2. Fix any test failures by updating imports and function calls
3. Run mypy check:
   ```bash
   uvx mypy src --show-error-codes
   ```
4. Fix any type errors introduced
5. Verify no deprecated warnings in test output
6. Check for any remaining references to removed functions:
   ```bash
   grep -r "orchestration\.jobs\.tracking\.config\.loader\.load_mlflow_config" --include="*.py" src/ tests/
   ```

**Success criteria**:
- All tests pass: `uvx pytest tests/`
- Mypy passes: `uvx mypy src --show-error-codes`
- No references to removed functions remain
- No breaking changes introduced (all imports updated correctly)

**Verification**:
```bash
# All should pass
uvx pytest tests/
uvx mypy src --show-error-codes
```

## Success Criteria (Overall)

- ✅ All duplicate `load_mlflow_config()` implementations removed
- ✅ All config loading utilities use standardized `resolve_project_paths()` pattern
- ✅ No re-inference of `config_dir` when parameter is already provided
- ✅ All tests pass: `pytest tests/`
- ✅ No breaking changes - all functionality preserved
- ✅ All imports updated correctly to use SSOT functions
- ✅ Codebase follows reuse-first principles

## Notes

- **Reuse-first**: This plan prioritizes reusing existing SSOT modules over creating new ones
- **Backward compatibility**: All changes maintain API compatibility by updating imports rather than changing function signatures
- **Incremental**: Steps can be executed independently, allowing for incremental progress
- **Testing**: Each step includes verification to ensure no regressions

## Related Plans

- `FINISHED-consolidate-utility-scripts-dry-violations.plan.md` - Previous utility consolidation (different scope)
- `FINISHED-consolidate-hpo-path-hash-inference-dry-violations.plan.md` - Related path inference consolidation

## Risk Assessment

**Low Risk**: 
- Changes are primarily import updates and function deletions
- SSOT functions already exist and are well-tested
- Backward compatibility maintained through import updates

**Mitigation**:
- Incremental execution allows for early detection of issues
- Comprehensive test suite provides safety net
- Mypy type checking catches import errors early


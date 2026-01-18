# Consolidate Path, Config, and Naming Utilities - Comprehensive Master Plan

## Goal

Eliminate all DRY violations across path resolution, configuration loading, and naming utilities by:
1. Consolidating duplicate config loaders and validation functions
2. Removing redundant `config_dir` inference when already available from callers
3. Standardizing path resolution patterns across all modules
4. Ensuring all functions trust provided `config_dir` parameter (DRY principle)
5. Breaking circular dependencies and removing unnecessary wrapper layers

## Status

**Last Updated**: 2026-01-18

### Completed Steps
- ✅ Step 1: Comprehensive audit and catalog of all utilities
- ✅ Step 2: Remove orchestration config loader duplication
- ✅ Step 3: Fix `setup_hpo_mlflow_run()` to trust provided `config_dir`
- ✅ Step 4: Fix duplicate inference in other functions
- ✅ Step 5: Standardize path resolution function usage
- ✅ Step 6: Consolidate naming policy loading (already complete - no orchestration files exist)
- ✅ Step 7: Consolidate run name building (already complete - no orchestration files exist)
- ✅ Step 8: Update all call sites to use SSOT functions
- ✅ Step 9: Remove deprecated/compatibility layers
- ✅ Step 10: Verify tests and type checking

### Pending Steps

NONE

## Preconditions

- All existing tests must pass before starting: `uvx pytest tests/`
- Mypy must pass: `uvx mypy src --show-error-codes`
- No active PRs that would conflict with these changes
- Repository uses `infrastructure.paths.utils.resolve_project_paths_with_fallback()` as SSOT for path resolution
- Repository uses `infrastructure.naming.mlflow.config.load_mlflow_config()` as SSOT for MLflow config loading

## Analysis Summary

### 1. Utility Scripts Catalog

#### Path Resolution Utilities

| File Path | Purpose | Key Functions | Status |
|-----------|---------|---------------|--------|
| `src/infrastructure/paths/utils.py` | **SSOT** for path resolution | `infer_config_dir()`, `resolve_project_paths()`, `resolve_project_paths_with_fallback()` | ✅ SSOT |
| `src/infrastructure/paths/repo.py` | Unified repository root detection | `detect_repo_root()`, `validate_repo_root()` | ✅ SSOT |
| `src/infrastructure/paths/resolve.py` | Output path resolution with patterns | `resolve_output_path()`, `build_output_path()` | ✅ SSOT |
| `src/infrastructure/paths/config.py` | Paths.yaml config loading | `load_paths_config()`, `load_repository_root_config()`, `apply_env_overrides()` | ✅ SSOT |
| `src/infrastructure/paths/parse.py` | Path parsing utilities | `parse_hpo_path_v2()`, `is_v2_path()`, `find_study_by_hash()` | ✅ SSOT |
| `src/infrastructure/paths/drive.py` | Google Drive path mapping | `get_drive_backup_base()`, `get_drive_backup_path()` | ✅ SSOT |
| `src/infrastructure/paths/validation.py` | Path validation utilities | `validate_path_before_mkdir()`, `validate_output_path()` | ✅ SSOT |
| `src/training/hpo/utils/paths.py` | HPO-specific path resolution | `resolve_hpo_output_dir()` | ✅ Domain-specific |
| `src/common/shared/notebook_setup.py` | **DEPRECATED** wrapper | `find_repository_root()` | ⚠️ Deprecated |

#### Config Loading Utilities

| File Path | Purpose | Key Functions | Status |
|-----------|---------|---------------|--------|
| `src/infrastructure/config/loader.py` | **SSOT** for experiment configs | `load_experiment_config()`, `load_all_configs()`, `compute_config_hash()` | ✅ SSOT |
| `src/infrastructure/naming/mlflow/config.py` | **SSOT** for MLflow config | `load_mlflow_config()`, `get_naming_config()`, `get_index_config()`, `get_auto_increment_config()`, `get_tracking_config()`, `get_run_finder_config()` | ✅ SSOT |
| `src/orchestration/jobs/tracking/config/loader.py` | MLflow config loader | `get_naming_config()`, `get_index_config()`, `get_auto_increment_config()`, `get_tracking_config()` | ❌ **DUPLICATE** |
| `src/orchestration/jobs/tracking/mlflow_config_loader.py` | Re-export wrapper | Re-exports from config/loader | ⚠️ Compatibility layer |
| `src/infrastructure/naming/display_policy.py` | Naming policy loading | `load_naming_policy()`, `format_run_name()`, `validate_naming_policy()` | ✅ SSOT |
| `src/training/config.py` | Training config loading | `load_config_file()`, `build_training_config()` | ✅ Domain-specific |

#### Naming Utilities

| File Path | Purpose | Key Functions | Status |
|-----------|---------|---------------|--------|
| `src/infrastructure/naming/mlflow/run_names.py` | **SSOT** for MLflow run names | `build_mlflow_run_name()` | ✅ SSOT |
| `src/orchestration/jobs/tracking/naming/run_names.py` | MLflow run name building | `build_mlflow_run_name()` | ❌ **DUPLICATE** (242 lines, identical) |
| `src/infrastructure/naming/mlflow/tags.py` | MLflow tag building | `build_mlflow_tags()`, `sanitize_tag_value()`, `get_tag_key()` | ✅ SSOT |
| `src/infrastructure/naming/mlflow/tags_registry.py` | Tag registry | `load_tags_registry()`, `TagsRegistry` | ✅ SSOT |
| `src/infrastructure/naming/mlflow/tag_keys.py` | Tag key getters | Multiple `get_*()` functions | ✅ SSOT (but re-infers config_dir) |
| `src/infrastructure/naming/mlflow/hpo_keys.py` | HPO key building | `build_hpo_study_key()`, `build_hpo_trial_key()` | ✅ SSOT |
| `src/infrastructure/naming/mlflow/run_keys.py` | Run key building | `build_mlflow_run_key()`, `build_counter_key()` | ✅ SSOT |
| `src/infrastructure/naming/display_policy.py` | Display policy | `load_naming_policy()`, `format_run_name()` | ✅ SSOT |
| `src/orchestration/jobs/tracking/naming/policy.py` | Naming policy | `load_naming_policy()`, `format_run_name()` | ❌ **DUPLICATE** (different caching) |
| `src/training/hpo/utils/helpers.py` | HPO helpers | `create_mlflow_run_name()` (legacy), `create_study_name()` | ⚠️ Legacy fallback |
| `src/training/hpo/tracking/setup.py` | HPO MLflow setup | `setup_hpo_mlflow_run()`, `commit_run_name_version()` | ⚠️ **Re-infers config_dir** |

### 2. Identified DRY Violations

#### Category 1: Config Loading Duplication (🔴 HIGH PRIORITY)

**Violation 1.1**: Duplicate `get_naming_config()` implementations
- **Location 1**: `src/infrastructure/naming/mlflow/config.py:154-175` (SSOT)
- **Location 2**: `src/orchestration/jobs/tracking/config/loader.py:89-110` (DUPLICATE)
- **Issue**: Orchestration version is a wrapper that calls infrastructure version, but both export the same function name. Creates confusion about which to use.
- **Impact**: Medium - Import confusion, maintenance burden

**Violation 1.2**: Duplicate validation functions
- **Location 1**: `src/infrastructure/naming/mlflow/config.py:86-152` - `_validate_naming_config()`, `_validate_index_config()`, `_validate_auto_increment_config()`, `_validate_run_finder_config()`
- **Location 2**: `src/orchestration/jobs/tracking/config/loader.py:20-368` - Identical validation functions
- **Issue**: Identical validation logic duplicated in both modules
- **Impact**: High - Maintenance burden, risk of divergence

**Violation 1.3**: Duplicate config accessor functions
- **Functions**: `get_index_config()`, `get_auto_increment_config()`, `get_tracking_config()`, `get_run_finder_config()`
- **Locations**: Both `infrastructure/naming/mlflow/config.py` and `orchestration/jobs/tracking/config/loader.py`
- **Issue**: Orchestration versions are thin wrappers that delegate to infrastructure versions, but both exist
- **Impact**: Medium - Unnecessary indirection, import confusion

**Call Sites**:
- `src/training/hpo/tracking/setup.py` - uses infrastructure version ✓
- `src/orchestration/jobs/tracking/index/version_counter.py` - uses orchestration version ✗
- `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py` - uses orchestration version ✗
- 15+ other files split between two versions

#### Category 2: Config Directory Re-inference (🔴 HIGH PRIORITY)

**Violation 2.1**: `setup_hpo_mlflow_run()` re-infers `config_dir`
- **Location**: `src/training/hpo/tracking/setup.py:104-111, 188-191, 220-223`
- **Issue**: Function receives `config_dir` parameter but re-infers it when `None`, even though caller (`sweep.py:812`) already has `project_config_dir` available
- **Evidence**: 
  - `sweep.py:636` stores `project_config_dir = config_dir`
  - `sweep.py:812` passes `config_dir=project_config_dir` to `setup_hpo_mlflow_run()`
  - `setup.py:104-111` re-infers `config_dir` when it's `None` (but it's not None when called from sweep)
- **Impact**: High - Violates DRY principle, unnecessary computation

**Violation 2.2**: `commit_run_name_version()` re-infers `config_dir`
- **Location**: `src/training/hpo/tracking/setup.py:302`
- **Issue**: Uses `resolve_project_paths_with_fallback()` to re-infer `config_dir` even when it could be passed
- **Impact**: Medium - Duplicate inference

**Violation 2.3**: `MLflowSweepTracker.start_sweep_run()` re-infers `config_dir`
- **Location**: `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py:126`
- **Issue**: Uses `infer_config_dir(path=output_dir)` even though `config_dir` could be passed from caller
- **Impact**: Medium - Duplicate inference

**Violation 2.4**: Multiple tag key getters re-infer `config_dir`
- **Location**: `src/infrastructure/naming/mlflow/tag_keys.py:141-264`
- **Issue**: Each `get_*()` function accepts `config_dir: Optional[Path] = None` and infers it if None
- **Pattern**: All functions call `infer_config_dir()` when `config_dir` is None
- **Impact**: Low - Consistent pattern but could be optimized if callers pass `config_dir`

**Violation 2.5**: Other functions re-infer `config_dir`
- **Locations**: 
  - `src/training/hpo/execution/local/cv.py:171-173` - infers config_dir even when available
  - `src/training/hpo/execution/local/refit.py:138-139` - infers config_dir even when available
  - `src/training/hpo/tracking/cleanup.py:160-162` - infers config_dir even when provided
  - `src/training/core/checkpoint_loader.py:118-123` - has fallback logic that re-infers
- **Impact**: Medium - Unnecessary re-computation across multiple files

#### Category 3: Naming Policy Duplication (🟠 MEDIUM PRIORITY)

**Violation 3.1**: Duplicate `load_naming_policy()` implementations
- **Location 1**: `src/infrastructure/naming/display_policy.py:51-100` (SSOT, mtime-based caching)
- **Location 2**: `src/orchestration/jobs/tracking/naming/policy.py` (DUPLICATE, module-level cache)
- **Issue**: Two modules provide naming policy loading with different caching strategies
- **Impact**: High - Different caching strategies can cause stale config issues, 25+ call sites split between two versions

**Violation 3.2**: Circular dependency
- **Issue**: `infrastructure.naming.display_policy` → `orchestration.jobs.tracking.naming.policy` (for `sanitize_semantic_suffix`)
- **Impact**: Medium - Circular dependency makes code harder to understand and maintain

**Call Sites**:
- `src/infrastructure/naming/mlflow/run_names.py` - uses infrastructure version ✓
- `src/orchestration/jobs/tracking/naming/run_names.py` - uses orchestration version ✗
- `src/training/hpo/tracking/setup.py` - uses infrastructure version ✓

#### Category 4: Run Name Building Duplication (🟠 MEDIUM PRIORITY)

**Violation 4.1**: Duplicate `build_mlflow_run_name()` implementations
- **Location 1**: `src/infrastructure/naming/mlflow/run_names.py` (SSOT, 242 lines)
- **Location 2**: `src/orchestration/jobs/tracking/naming/run_names.py` (DUPLICATE, 242 lines, **identical**)
- **Issue**: Two identical implementations maintained in parallel
- **Impact**: High - Identical code maintained in two places, risk of divergence, 36+ call sites total (31 infrastructure, 5 orchestration)

**Call Sites**:
- `src/training/hpo/execution/local/sweep.py` - uses infrastructure via `setup_hpo_mlflow_run()` ✓
- `src/orchestration/jobs/hpo/azureml/sweeps.py` - uses orchestration version ✗

#### Category 5: Path Resolution Inconsistencies (🟠 MEDIUM PRIORITY)

**Violation 5.1**: Inconsistent function usage
- **Functions**: 
  - `infer_config_dir()` - Direct inference
  - `resolve_project_paths()` - Resolves both root_dir and config_dir
  - `resolve_project_paths_with_fallback()` - Same as above but with fallback logic
- **Issue**: Three functions that do similar things. `resolve_project_paths_with_fallback()` calls `resolve_project_paths()`, which calls `infer_config_dir()`. This is good composition, but usage is inconsistent.
- **Impact**: Medium - Inconsistent patterns make code harder to understand

**Violation 5.2**: Manual path construction
- **Locations**: Some modules construct `root_dir / "config"` manually instead of using utilities
- **Issue**: Bypasses centralized path resolution
- **Impact**: Low - Potential inconsistencies

**Violation 5.3**: Hardcoded patterns
- **Locations**: 20+ files with `Path.cwd() / "config"` hardcoded
- **Issue**: Doesn't work in all contexts (Colab, AzureML, nested directories)
- **Impact**: Medium - Fails in edge cases

#### Category 6: Inconsistent Import Patterns (🟡 LOW PRIORITY)

**Violation 6.1**: Different modules import from different sources
- **Examples**:
  - Some import `get_naming_config` from `infrastructure.naming.mlflow.config`
  - Others import from `orchestration.jobs.tracking.config.loader`
  - Some use `resolve_project_paths()`, others use `resolve_project_paths_with_fallback()`
- **Impact**: Low - Codebase inconsistency, maintenance confusion

### 3. Grouped Overlaps

#### Group A: Config Loading (🔴 HIGH PRIORITY)
- **Duplicates**: `orchestration/jobs/tracking/config/loader.py` vs `infrastructure/naming/mlflow/config.py`
- **Redundant inference**: Multiple config loaders re-infer `config_dir`
- **Consolidation target**: Use `infrastructure/naming/mlflow/config.py` as SSOT, remove orchestration duplicates

#### Group B: Config Directory Inference (🔴 HIGH PRIORITY)
- **Files**: `paths/utils.py`, `paths/repo.py`, `training/hpo/tracking/setup.py`, `training/core/checkpoint_loader.py`, `training/orchestrator.py`
- **Pattern**: All infer `config_dir` from various sources (output_dir, start_path, cwd)
- **Violations**: Functions re-infer even when `config_dir` is provided
- **Consolidation target**: `infrastructure/paths/utils.py` already has `infer_config_dir()` and `resolve_project_paths_with_fallback()` as SSOT. All functions should trust provided `config_dir` parameter.

#### Group C: Naming Policy Loading (🟠 MEDIUM PRIORITY)
- **Duplicates**: `infrastructure/naming/display_policy.py` vs `orchestration/jobs/tracking/naming/policy.py`
- **Circular dependency**: `infrastructure` → `orchestration` → `infrastructure`
- **Consolidation target**: Use `infrastructure/naming/display_policy.py` as SSOT, move `sanitize_semantic_suffix` to infrastructure to break circular dependency

#### Group D: Run Name Building (🟠 MEDIUM PRIORITY)
- **Duplicates**: `infrastructure/naming/mlflow/run_names.py` vs `orchestration/jobs/tracking/naming/run_names.py`
- **Issue**: Identical 242-line implementations
- **Consolidation target**: Use `infrastructure/naming/mlflow/run_names.py` as SSOT, replace orchestration version with re-export

#### Group E: Path Resolution Patterns (🟠 MEDIUM PRIORITY)
- **Inconsistent patterns**: Multiple ways to resolve paths
- **Manual construction**: Some modules construct paths manually
- **Hardcoded patterns**: 20+ files with `Path.cwd() / "config"`
- **Consolidation target**: Standardize on `resolve_project_paths_with_fallback()` for most cases

## Consolidation Approach

### Principles

1. **Reuse-First**: Extend existing SSOT modules rather than creating new ones
2. **SRP Pragmatically**: Keep modules focused but avoid over-splitting
3. **Minimize Breaking Changes**: Use re-exports and compatibility layers during transition
4. **Trust Provided Parameters**: Functions should trust `config_dir` when provided, only infer when `None` (DRY principle)

### Strategy

**Phase 1: Eliminate Duplicates** (Low Risk)
- Remove duplicate implementations from orchestration modules
- Replace with re-exports pointing to infrastructure SSOT
- Update call sites incrementally

**Phase 2: Fix Redundant Inference** (Medium Risk)
- Update functions to fully trust provided `config_dir`
- Remove redundant inference calls
- Ensure `resolve_project_paths_with_fallback()` respects provided values

**Phase 3: Standardize Patterns** (Medium Risk)
- Replace all manual path resolution with SSOT functions
- Replace all hardcoded `Path.cwd() / "config"` with `infer_config_dir()`
- Update call sites to pass `config_dir` when available

**Phase 4: Remove Compatibility Layers** (Low Risk, after Phase 1-3 complete)
- Remove deprecated re-export modules
- Clean up circular dependencies

## Steps

### Step 1: Comprehensive Audit and Catalog of All Utilities

**Objective**: Create complete inventory of all path/config/naming utilities with their current usage patterns.

**Tasks**:
1. Document all files that import or use path/config/naming utilities
2. Create a mapping of which functions are used where
3. Identify all call sites that pass `config_dir` parameter
4. Identify all call sites that re-infer `config_dir` unnecessarily
5. Count imports from each module:
   ```bash
   grep -r "from infrastructure.naming.mlflow.config import" src/ | wc -l
   grep -r "from orchestration.jobs.tracking.config.loader import" src/ | wc -l
   grep -r "from orchestration.jobs.tracking.naming" src/ | wc -l
   grep -r "resolve_project_paths" src/ | wc -l
   grep -r "Path.cwd() / \"config\"" src/ | wc -l
   ```

**Success criteria**:
- Complete inventory document created in `docs/implementation_plans/audits/path-config-naming-inventory.md`
- All import statements cataloged
- All function call patterns documented
- Call site counts verified

**Verification**:
```bash
# Count imports
grep -r "from.*paths.*import\|from.*config.*import\|from.*naming.*import" src/ | wc -l

# List all files using path resolution
grep -r "resolve_project_paths\|infer_config_dir" src/ --include="*.py" | cut -d: -f1 | sort -u

# Find hardcoded patterns
grep -r "Path.cwd() / \"config\"" src/ --include="*.py" -n
```

---

### Step 2: Remove Orchestration Config Loader Duplication

**Objective**: Remove duplicate `get_naming_config()` and related functions from `orchestration/jobs/tracking/config/loader.py`, making it a simple re-export of infrastructure versions.

**Tasks**:
1. **Update `src/orchestration/jobs/tracking/config/loader.py`**:
   - Remove all duplicate `_validate_*_config()` functions (lines 20-368)
   - Replace all config accessor functions with re-exports:
     ```python
     from infrastructure.naming.mlflow.config import (
         get_naming_config,
         get_index_config,
         get_auto_increment_config,
         get_tracking_config,
         get_run_finder_config,
         load_mlflow_config,
     )
     
     __all__ = [
         "get_naming_config",
         "get_index_config",
         "get_auto_increment_config",
         "get_tracking_config",
         "get_run_finder_config",
         "load_mlflow_config",
     ]
     ```
   - Add deprecation warnings pointing to SSOT module
   - Keep module for backward compatibility (re-exports only)

2. **Find all imports from `orchestration.jobs.tracking.config.loader`**:
   ```bash
   grep -r "from orchestration.jobs.tracking.config.loader import" src/ --include="*.py"
   ```

3. **Update call sites** to use `infrastructure.naming.mlflow.config` directly:
   - `src/orchestration/jobs/tracking/index/version_counter.py`
   - `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py`
   - `src/training/hpo/tracking/setup.py` (if using orchestration version)
   - `src/training/hpo/tracking/cleanup.py` (if using orchestration version)
   - All other files found in Step 1

4. **Update `__init__.py` exports** if needed

**Success criteria**:
- `orchestration/jobs/tracking/config/loader.py` only contains re-exports (no duplicate implementations)
- All call sites updated to use infrastructure module directly (or re-export works)
- Deprecation warnings added
- Tests pass: `uvx pytest tests/ -k "naming|config"`

**Verification**:
```bash
# Check orchestration module is just re-exports
grep -v "^from\|^import\|^\"\"\"\|^#\|^$" src/orchestration/jobs/tracking/config/loader.py | head -20
# Should return minimal output (only function signatures if any)

# Verify no duplicate implementations
diff <(grep -A 50 "def get_naming_config" src/infrastructure/naming/mlflow/config.py) \
     <(grep -A 50 "def get_naming_config" src/orchestration/jobs/tracking/config/loader.py)
# Should show only import differences

# Verify all imports updated
grep -r "from orchestration.jobs.tracking.config.loader import" src/ --include="*.py" | grep -v "loader.py"
# Should return 0 results (or only in backward-compat wrapper)
```

---

### Step 3: Fix `setup_hpo_mlflow_run()` to Trust Provided `config_dir`

**Objective**: Make `setup_hpo_mlflow_run()` trust the provided `config_dir` parameter instead of re-inferring it.

**Tasks**:
1. **Update `setup_hpo_mlflow_run()` in `src/training/hpo/tracking/setup.py`**:
   - **Line 104-111**: Remove redundant inference for hash computation. Trust provided `config_dir`:
     ```python
     # Before:
     resolved_config_dir = config_dir
     if resolved_config_dir is None:
         _, resolved_config_dir = resolve_project_paths_with_fallback(...)
     
     # After:
     resolved_config_dir = config_dir
     if resolved_config_dir is None:
         # Only infer when truly None and cannot be derived
         _, resolved_config_dir = resolve_project_paths_with_fallback(
             output_dir=output_dir,
             config_dir=None,
         )
     ```
   - **Line 188-191**: Trust provided `config_dir` parameter:
     ```python
     # Before:
     root_dir, config_dir = resolve_project_paths_with_fallback(
         output_dir=output_dir,
         config_dir=config_dir,  # May re-infer even if provided
     )
     
     # After:
     # Trust provided config_dir if not None
     if config_dir is not None:
         # Derive root_dir from config_dir
         from infrastructure.paths.repo import detect_repo_root
         root_dir = detect_repo_root(config_dir=config_dir)
     else:
         # Only infer when explicitly None
         root_dir, config_dir = resolve_project_paths_with_fallback(
             output_dir=output_dir,
             config_dir=None,
         )
     ```
   - **Line 220-223**: Apply same pattern in fallback path
   - Update function docstring to clarify behavior: "Trusts provided `config_dir` parameter. Only infers when explicitly None."

2. **Update `commit_run_name_version()` similarly** (line 302):
   - Trust provided `config_dir` parameter
   - Only infer when explicitly None

3. **Verify that `sweep.py` correctly passes `project_config_dir`**:
   - Line 636: `project_config_dir = config_dir` ✓ (already correct)
   - Line 812: `config_dir=project_config_dir` ✓ (already correct)

**Success criteria**:
- `setup_hpo_mlflow_run()` trusts provided `config_dir` parameter (no redundant inference when provided)
- Only infers when truly `None` and cannot be derived
- `commit_run_name_version()` follows same pattern
- Function docstring updated to document behavior
- Tests pass: `uvx pytest tests/hpo/integration/test_hpo_sweep_setup.py::test_setup_hpo_mlflow_run_trusts_provided_config_dir`
- Mypy passes: `uvx mypy src/training/hpo/tracking/setup.py`

**Verification**:
```bash
# Check function trusts config_dir
grep -A 20 "def setup_hpo_mlflow_run" src/training/hpo/tracking/setup.py | grep -E "config_dir|infer"

# Run specific test
uvx pytest tests/hpo/integration/test_hpo_sweep_setup.py::test_setup_hpo_mlflow_run_trusts_provided_config_dir -v

# Check sweep.py passes config_dir
grep -B 2 -A 5 "setup_hpo_mlflow_run" src/training/hpo/execution/local/sweep.py | grep config_dir
```

---

### Step 4: Fix Duplicate Inference in Other Functions

**Objective**: Apply same "trust provided config_dir" pattern to other functions that re-infer unnecessarily.

**Functions to fix**:
1. `src/training/hpo/execution/local/cv.py:171-173` - `run_cv_trials()`
2. `src/training/hpo/execution/local/refit.py:138-139` - `run_refit()`
3. `src/training/hpo/tracking/cleanup.py:160-162` - `cleanup_old_runs()`
4. `src/training/hpo/tracking/runs.py:27` - `create_trial_run()`
5. `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py:126` - `start_sweep_run()`
6. `src/training/core/checkpoint_loader.py:118-123` - `resolve_from_config()`
7. Any other functions identified in Step 1

**Tasks**:
1. For each function, update to trust provided `config_dir`:
   - Check `if config_dir is not None: use it directly`
   - Only call inference functions when `config_dir is None`
2. Update function signatures to accept `config_dir: Optional[Path] = None` if not already
3. Update docstrings to document behavior: "Trusts provided `config_dir` parameter. Only infers when explicitly None."
4. Update callers to pass `config_dir` when available
5. Update tests

**Success criteria**:
- All identified functions trust provided `config_dir`
- Only infer when `config_dir is None`
- Callers updated to pass `config_dir` when available
- Tests pass: `uvx pytest tests/`
- Mypy passes: `uvx mypy src/`

**Verification**:
```bash
# Find functions that receive config_dir
grep -r "def.*config_dir" src/ --include="*.py" | grep -v "test"

# Check they trust the parameter
for file in $(grep -rl "def.*config_dir" src/ --include="*.py" | grep -v test); do
  echo "=== $file ==="
  grep -A 10 "def.*config_dir" "$file" | head -15
done

# Run tests for modified modules
uvx pytest tests/ -k "cv_trials or refit or cleanup or trial_run or sweep_tracker"
```

---

### Step 5: Standardize Path Resolution Function Usage

**Objective**: Standardize all call sites to use `resolve_project_paths_with_fallback()` as the primary path resolution function.

**Tasks**:
1. **Find all usages of `resolve_project_paths()` (without `_with_fallback`)**:
   ```bash
   grep -r "resolve_project_paths(" src/ --include="*.py" | grep -v "_with_fallback"
   ```
   - Replace with `resolve_project_paths_with_fallback()` where appropriate
   - Keep `resolve_project_paths()` only when fallback is explicitly not desired

2. **Find all manual path construction patterns**:
   ```bash
   grep -rn "config_dir.*=.*root_dir.*config\|config_dir.*=.*/.*config" src/ --include="*.py"
   ```
   - Replace with `resolve_project_paths_with_fallback()`

3. **Find all hardcoded `Path.cwd() / "config"` patterns**:
   ```bash
   grep -rn "Path.cwd() / \"config\"" src/ --include="*.py"
   ```
   - Replace with `infer_config_dir()` from `infrastructure.paths.utils`

4. **Update function documentation** in `paths/utils.py`:
   - Clarify when to use each function:
     - `resolve_project_paths_with_fallback()` - Primary function (most call sites)
     - `resolve_project_paths()` - When fallback not needed
     - `infer_config_dir()` - Only for direct inference without root_dir

**Files to modify** (examples, full list from grep):
- `src/training/core/trainer.py:525-526` - uses `resolve_project_paths()` (should use `_with_fallback`)
- `src/training/hpo/execution/local/cv.py:171-173` - manual pattern
- `src/infrastructure/naming/mlflow/run_names.py` - manual pattern
- All files with `Path.cwd() / "config"` (20+ files)

**Success criteria**:
- All call sites use `resolve_project_paths_with_fallback()` unless there's a specific reason not to
- No hardcoded `Path.cwd() / "config"` patterns remain
- No manual `config_dir = root_dir / "config"` patterns remain
- Function documentation clearly explains when to use which function
- Tests pass: `uvx pytest tests/config/unit/test_paths.py`

**Verification**:
```bash
# Find all usages
grep -r "resolve_project_paths(" src/ --include="*.py" | grep -v "_with_fallback"
# Should return minimal results (only where fallback explicitly not desired)

# Check function is used consistently
grep -r "resolve_project_paths_with_fallback" src/ --include="*.py" | wc -l
# Count should be high (most call sites)

# Verify no hardcoded patterns
grep -r "Path.cwd() / \"config\"" src/ --include="*.py"
# Should return 0 results

# Verify no manual construction
grep -rn "config_dir.*=.*root_dir.*config" src/ --include="*.py"
# Should return minimal results (only in infrastructure.paths.utils itself)
```

---

### Step 6: Consolidate Naming Policy Loading

**Objective**: Consolidate naming policy loading to infrastructure SSOT, break circular dependency.

**Tasks**:
1. **Move `sanitize_semantic_suffix()` to infrastructure**:
   - Extract from `orchestration.jobs.tracking.naming.policy`
   - Add to `infrastructure.naming.display_policy` or new `infrastructure.naming.utils`
   - Update `infrastructure.naming.display_policy` to use local version (break circular dependency)

2. **Update `src/orchestration/jobs/tracking/naming/policy.py`**:
   - Replace `load_naming_policy()`, `format_run_name()`, etc. with re-exports:
     ```python
     from infrastructure.naming.display_policy import (
         load_naming_policy,
         format_run_name,
         validate_naming_policy,
         validate_run_name,
         parse_parent_training_id,
     )
     from infrastructure.naming.utils import sanitize_semantic_suffix  # or wherever moved
     
     __all__ = [
         "load_naming_policy",
         "format_run_name",
         "validate_naming_policy",
         "validate_run_name",
         "parse_parent_training_id",
         "sanitize_semantic_suffix",
     ]
     ```
   - Add deprecation warnings

3. **Update all call sites**:
   - Find all imports: `from orchestration.jobs.tracking.naming.policy import`
   - Replace with: `from infrastructure.naming.display_policy import`
   - Update call sites (estimated 10+ files)

**Success criteria**:
- Circular dependency broken (no `infrastructure` → `orchestration` → `infrastructure`)
- `orchestration.jobs.tracking.naming.policy` only contains re-exports
- All call sites updated to use infrastructure version
- Tests pass: `uvx pytest tests/infrastructure/naming/ tests/orchestration/jobs/tracking/naming/`
- Mypy passes: `uvx mypy src/infrastructure/naming/ src/orchestration/jobs/tracking/naming/`

**Verification**:
```bash
# Verify no circular imports
python -c "from infrastructure.naming.display_policy import load_naming_policy; print('OK')"
# Should not import orchestration module

# Check orchestration module is just re-exports
wc -l src/orchestration/jobs/tracking/naming/policy.py
# Should be < 20 lines (just imports and __all__)
```

---

### Step 7: Consolidate Run Name Building

**Objective**: Remove duplicate `build_mlflow_run_name()` implementation.

**Tasks**:
1. **Update `src/orchestration/jobs/tracking/naming/run_names.py`**:
   - Remove entire implementation (242 lines)
   - Replace with re-export:
     ```python
     from infrastructure.naming.mlflow.run_names import build_mlflow_run_name
     
     __all__ = ["build_mlflow_run_name"]
     ```
   - Add deprecation warning

2. **Update all call sites**:
   - Find all imports: `from orchestration.jobs.tracking.naming.run_names import build_mlflow_run_name`
   - Replace with: `from infrastructure.naming.mlflow.run_names import build_mlflow_run_name`
   - Update call sites (estimated 5+ files)

3. **Verify compatibility**:
   - Ensure orchestration version's dependencies (if any) are satisfied by infrastructure version
   - Check that function signatures match exactly

**Success criteria**:
- `orchestration.jobs.tracking.naming.run_names` only contains re-export
- All call sites updated to use infrastructure version (or re-export works)
- Tests pass: `uvx pytest tests/orchestration/jobs/tracking/naming/ tests/infrastructure/naming/`
- Mypy passes: `uvx mypy src/orchestration/jobs/tracking/naming/run_names.py`

**Verification**:
```bash
# Verify orchestration version is just re-export
wc -l src/orchestration/jobs/tracking/naming/run_names.py
# Should be < 10 lines (just imports and __all__)

# Check no duplicate implementations
grep -r "def build_mlflow_run_name" src/ --include="*.py" | grep -v test
# Should find only infrastructure version and orchestration re-export
```

---

### Step 8: Update All Call Sites to Use SSOT Functions

**Objective**: Update all import statements and function calls to use the consolidated utilities.

**Tasks**:
1. **Update imports for config functions**:
   - Find all remaining imports from `orchestration.jobs.tracking.config.loader`
   - Change to `infrastructure.naming.mlflow.config`
   - Update files found in Step 1

2. **Update imports for naming policy**:
   - Find all imports from `orchestration.jobs.tracking.naming.policy`
   - Change to `infrastructure.naming.display_policy`
   - Update files found in Step 1

3. **Update imports for run names**:
   - Find all imports from `orchestration.jobs.tracking.naming.run_names`
   - Change to `infrastructure.naming.mlflow.run_names`
   - Update files found in Step 1

4. **Ensure all path resolution uses `resolve_project_paths_with_fallback()`**:
   - Update any remaining `resolve_project_paths()` calls
   - Update any manual path construction
   - Update any hardcoded patterns

5. **Ensure all functions trust provided `config_dir` parameter**:
   - Update callers to pass `config_dir` when available
   - Remove redundant inference calls

6. **Run full test suite**:
   ```bash
   uvx pytest tests/ -x
   ```

**Success criteria**:
- All imports updated to use SSOT modules
- All function calls use consolidated utilities
- All path resolution uses `resolve_project_paths_with_fallback()` consistently
- All callers pass `config_dir` when available
- Full test suite passes: `uvx pytest tests/`
- Mypy passes: `uvx mypy src --show-error-codes`

**Verification**:
```bash
# Check no imports from orchestration config loader (except re-exports)
grep -r "from orchestration.jobs.tracking.config.loader import" src/ --include="*.py" | grep -v "loader.py"

# Check no imports from orchestration naming modules (except re-exports)
grep -r "from orchestration.jobs.tracking.naming" src/ --include="*.py" | grep -v "policy.py\|run_names.py"

# Run full test suite
uvx pytest tests/ -x

# Run mypy
uvx mypy src --show-error-codes
```

---

### Step 9: Remove Deprecated/Compatibility Layers

**Objective**: Clean up deprecated code after migration is complete.

**Tasks**:
1. **Evaluate `orchestration.jobs.tracking.config.loader.py`**:
   - If all call sites migrated (Step 8), mark entire module as deprecated
   - Add deprecation warnings to all exported functions
   - Update module docstring with migration instructions
   - Keep module for backward compatibility (don't delete yet)

2. **Evaluate `orchestration.jobs.tracking/mlflow_config_loader.py`**:
   - If only used for backward compatibility, keep as thin wrapper
   - Update docstring to clarify it's a compatibility layer

3. **Evaluate `orchestration.jobs.tracking.naming/policy.py` and `run_names.py`**:
   - If all call sites migrated, mark as deprecated
   - Keep re-exports for backward compatibility

4. **Remove deprecated `find_repository_root()`**:
   - Find all usages of `find_repository_root()` from `common/shared/notebook_setup.py`
   - Replace with `detect_repo_root()` from `infrastructure.paths.repo`
   - Remove deprecated function

5. **Document deprecation timeline**:
   - Create deprecation notice in module docstrings
   - Plan removal in future major version (if applicable)

**Success criteria**:
- Deprecated modules clearly marked
- Migration path documented
- No breaking changes (backward compatibility maintained)
- Tests pass: `uvx pytest tests/`

**Verification**:
```bash
# Check deprecation warnings added
grep -r "@deprecated\|DeprecationWarning" src/orchestration/jobs/tracking/config/loader.py
grep -r "@deprecated\|DeprecationWarning" src/orchestration/jobs/tracking/naming/

# Check no direct imports from deprecated modules (except re-exports)
grep -r "from infrastructure.naming.mlflow.policy import" src/ --include="*.py"
# Should return 0 results (or only deprecation warnings)

# Verify deprecated function removed or marked
grep -r "find_repository_root" src/ --include="*.py" | grep -v "detect_repo_root"
# Should return 0 results
```

---

### Step 10: Verify Tests and Type Checking

**Objective**: Ensure all tests pass and verify consolidation is complete.

**Tasks**:
1. **Run full test suite**:
   ```bash
   uvx pytest tests/ -v
   ```

2. **Fix any test failures**:
   - Update test imports if needed
   - Update test mocks if function signatures changed
   - Update assertions if behavior changed (should be minimal)

3. **Run mypy**:
   ```bash
   uvx mypy src --show-error-codes
   ```

4. **Fix type errors**:
   - Update type hints if needed
   - Fix any import-related type errors

5. **Verify no regressions**:
   - Run a sample HPO sweep to ensure paths/config work correctly
   - Check that duplicate inference is eliminated (add assertions in tests)

6. **Update test documentation**:
   - Document new import patterns in test files if needed
   - Update test fixtures if config loading changed

**Success criteria**:
- All tests pass: `uvx pytest tests/` (exit code 0)
- Mypy passes: `uvx mypy src --show-error-codes` (exit code 0)
- No test regressions
- Test coverage maintained or improved
- No linter errors

**Verification**:
```bash
# Run tests
uvx pytest tests/ -v --tb=short

# Run mypy
uvx mypy src --show-error-codes

# Check for remaining duplicate inference patterns
grep -rn "resolve_project_paths_with_fallback.*config_dir=config_dir" src/ --include="*.py"
# Should find minimal results (only when config_dir is actually None)

# Check for duplicate function definitions
for func in get_naming_config get_index_config get_auto_increment_config build_mlflow_run_name load_naming_policy; do
  echo "=== $func ==="
  grep -r "def $func" src/ --include="*.py" | grep -v test
done
# Should find only SSOT implementations and re-exports
```

## Success Criteria (Overall)

- ✅ No duplicate implementations of config loaders, naming policy, or run name building
- ✅ All functions trust provided `config_dir` parameter (no redundant inference)
- ✅ All path resolution uses SSOT functions (`resolve_project_paths_with_fallback()`, `infer_config_dir()`)
- ✅ No hardcoded `Path.cwd() / "config"` patterns
- ✅ No manual root finding patterns
- ✅ Circular dependencies broken
- ✅ All call sites updated to use SSOT functions
- ✅ All tests pass: `uvx pytest tests/`
- ✅ Mypy passes: `uvx mypy src --show-error-codes`
- ✅ No breaking changes (re-exports maintain compatibility)
- ✅ Documentation updated (docstrings, migration guides)

## Notes

- **Re-exports**: Use re-exports during transition to maintain backward compatibility
- **Incremental**: Update call sites incrementally, one module at a time
- **Testing**: Run full test suite after each step to catch regressions early
- **Documentation**: Update docstrings to reference SSOT modules
- **Breaking Changes**: Minimal - function signatures remain compatible, only behavior changes (trusting provided config_dir)
- **Migration Path**: Can be done incrementally, function by function
- **Rollback Plan**: Each step is independent, can revert individual changes if issues arise

## Related Plans

- `FINISHED-20260118-1200-consolidate-mlflow-scripts-dry-violations-unified.plan.md` - Related MLflow consolidation
- `FINISHED-20260118-1500-consolidate-all-scripts-dry-violations-unified-master.plan.md` - Master consolidation plan
- `FINISHED-20260117-2350-consolidate-utility-scripts-dry-violations-unified.plan.md` - General utility consolidation


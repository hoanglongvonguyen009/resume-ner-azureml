# Consolidate Path and Naming Utilities

## Goal

Eliminate DRY violations in path and naming utilities by consolidating duplicate implementations, removing redundant inference logic, and establishing single sources of truth for common operations.

## Status

**Last Updated**: 2026-01-15

### Completed Steps
- ✅ Step 1: Audit and document all path/naming utilities (see `consolidate-path-naming-utilities-audit.md`)
- ✅ Step 2: Consolidate duplicate `build_mlflow_run_name` implementations
- ✅ Step 3: Consolidate duplicate `format_run_name` implementations
- ✅ Step 4: Consolidate duplicate `load_naming_policy` implementations (completed as part of Step 3)
- ✅ Step 5: Eliminate redundant `config_dir` inference
- ✅ Step 6: Consolidate project root finding logic
- ✅ Step 7: Update all call sites to use consolidated utilities
- ✅ Step 8: Remove deprecated/duplicate modules (deprecation warnings added)

### Pending Steps
- ⏳ None (all steps completed - plan ready for FINISHED prefix)

## Preconditions

- All existing tests must pass before starting
- No active PRs that would conflict with these changes
- Backup of current working state

## Analysis Summary

### 1. Utility Scripts Found

#### Path Domain (`domain: paths`)
1. **`src/infrastructure/paths/drive.py`** - Drive backup path mapping and Colab-specific path resolution
2. **`src/infrastructure/paths/utils.py`** - Path utility functions, find project root directory
3. **`src/infrastructure/paths/config.py`** - Load and manage paths.yaml configuration with caching
4. **`src/infrastructure/paths/resolve.py`** - Resolve all output paths (single authority for filesystem layout)
5. **`src/infrastructure/paths/parse.py`** - Parse HPO and other output paths to extract components

#### Naming Domain (`domain: naming`)
1. **`src/infrastructure/naming/mlflow/run_names.py`** - Generate human-readable MLflow run names from NamingContext
2. **`src/infrastructure/naming/display_policy.py`** - Load naming policy from YAML, format and validate display/run names
3. **`src/infrastructure/naming/mlflow/policy.py`** - Backward-compatible re-exports for naming policy helpers (legacy bridge)
4. **`src/infrastructure/naming/mlflow/tags.py`** - Build MLflow tag dictionaries from naming contexts
5. **`src/infrastructure/naming/mlflow/run_keys.py`** - Build stable run_key identifiers and hashes
6. **`src/infrastructure/naming/context.py`** - Define NamingContext dataclass and factory function
7. **`src/infrastructure/naming/context_tokens.py`** - Expand NamingContext into token dictionary
8. **`src/infrastructure/naming/mlflow/config.py`** - Load MLflow configuration from YAML with caching
9. **`src/infrastructure/naming/mlflow/tag_keys.py`** - Provide centralized tag key definitions
10. **`src/infrastructure/naming/mlflow/tags_registry.py`** - Manage centralized MLflow tag key registry
11. **`src/infrastructure/naming/mlflow/hpo_keys.py`** - Build HPO-specific keys (study, trial, family)
12. **`src/infrastructure/naming/experiments.py`** - Build experiment and stage names
13. **`src/infrastructure/naming/mlflow/refit_keys.py`** - Compute refit protocol fingerprints

#### Orchestration Naming (Duplicate/Compatibility Layer)
1. **`src/orchestration/jobs/tracking/naming/run_names.py`** - Duplicate of `infrastructure.naming.mlflow.run_names`
2. **`src/orchestration/jobs/tracking/naming/policy.py`** - Duplicate of `infrastructure.naming.display_policy`

### 2. DRY Violations Identified

#### Category A: Duplicate Function Implementations

**A1. Duplicate `build_mlflow_run_name`**
- **Location 1**: `src/infrastructure/naming/mlflow/run_names.py:80`
- **Location 2**: `src/orchestration/jobs/tracking/naming/run_names.py:57`
- **Issue**: Nearly identical implementations (242 lines vs 242 lines), both handle same logic
- **Impact**: Changes must be made in two places, risk of divergence

**A2. Duplicate `format_run_name`**
- **Location 1**: `src/infrastructure/naming/display_policy.py:346`
- **Location 2**: `src/orchestration/jobs/tracking/naming/policy.py:353`
- **Issue**: Same function signature and logic, different implementations
- **Impact**: Policy formatting logic duplicated

**A3. Duplicate `load_naming_policy`**
- **Location 1**: `src/infrastructure/naming/display_policy.py:51` (with mtime-based caching)
- **Location 2**: `src/orchestration/jobs/tracking/naming/policy.py:26` (with module-level cache)
- **Issue**: Different caching strategies, same purpose
- **Impact**: Inconsistent caching behavior, potential cache misses

#### Category B: Redundant Inference Logic

**B1. Multiple `config_dir` Inference Patterns**
- **Pattern 1**: `infer_config_dir_from_path(path)` in `src/infrastructure/tracking/mlflow/utils.py:113`
- **Pattern 2**: `Path.cwd() / "config"` hardcoded in 20+ locations
- **Pattern 3**: `config_dir.parent` inference in multiple places
- **Pattern 4**: Manual walking up directory tree to find config (in `sweep.py`, `cv.py`, etc.)
- **Issue**: Same logic implemented differently across codebase
- **Impact**: Inconsistent behavior, especially when running from notebooks

**B2. Redundant `config_dir` Inference When Already Available**
- **Example 1**: `setup_hpo_mlflow_run()` re-infers `config_dir` even though caller has `project_config_dir` (fixed in recent commit)
- **Example 2**: `build_mlflow_run_name()` infers `root_dir` from `output_dir` when `config_dir` is available
- **Example 3**: Multiple functions accept `config_dir` but then re-infer it if `None`
- **Issue**: Callers often have `config_dir` but functions don't accept it or ignore it
- **Impact**: Unnecessary computation, potential inconsistencies

**B3. Duplicate Project Root Finding**
- **Location 1**: `src/infrastructure/paths/utils.py:35` - `find_project_root(config_dir)` (looks for `src/training/`)
- **Location 2**: `src/infrastructure/tracking/mlflow/utils.py:113` - `infer_config_dir_from_path()` (looks for `config/` and `src/`)
- **Location 3**: Manual implementations in `sweep.py:689`, `cv.py:185`, `trial_finder.py:436`
- **Issue**: Different heuristics for finding project root
- **Impact**: Inconsistent results, especially in edge cases

#### Category C: Duplicate Root Directory Inference

**C1. Root Directory from Output Directory**
- **Pattern**: Walk up from `output_dir` until finding "outputs" directory, then use parent
- **Locations**: `build_mlflow_run_name()` (both implementations), `setup_hpo_mlflow_run()`, `cv.py`, etc.
- **Issue**: Same logic duplicated 10+ times
- **Impact**: Changes must be made in multiple places

**C2. Root Directory from Config Directory**
- **Pattern**: `config_dir.parent` or `find_project_root(config_dir)`
- **Locations**: Multiple files use `config_dir.parent`, others use `find_project_root()`
- **Issue**: Inconsistent approach
- **Impact**: Potential bugs when `config_dir` is not at project root

### 3. Overlap Categories

#### Category 1: Path Handling
- **Files**: `paths/utils.py`, `paths/resolve.py`, `paths/parse.py`, `paths/config.py`
- **Overlaps**: 
  - Project root finding (utils.py vs manual implementations)
  - Path pattern resolution (resolve.py vs manual string building)
- **Consolidation Target**: Keep `paths/` module structure, but ensure single implementations

#### Category 2: Config Directory Inference
- **Files**: `tracking/mlflow/utils.py`, `paths/utils.py`, and 20+ call sites
- **Overlaps**: 
  - `infer_config_dir_from_path()` vs `Path.cwd() / "config"` vs manual walking
  - Different fallback strategies
- **Consolidation Target**: Single `infer_config_dir()` function in `paths/utils.py`

#### Category 3: Naming Policy Loading
- **Files**: `naming/display_policy.py`, `orchestration/jobs/tracking/naming/policy.py`
- **Overlaps**: 
  - `load_naming_policy()` with different caching strategies
  - `format_run_name()` with same logic
- **Consolidation Target**: Use `infrastructure.naming.display_policy` as SSOT, remove orchestration duplicate

#### Category 4: Run Name Building
- **Files**: `naming/mlflow/run_names.py`, `orchestration/jobs/tracking/naming/run_names.py`
- **Overlaps**: 
  - Identical `build_mlflow_run_name()` implementations
  - Same root_dir inference logic
- **Consolidation Target**: Use `infrastructure.naming.mlflow.run_names` as SSOT, make orchestration version a thin re-export

#### Category 5: Root Directory Inference
- **Files**: Multiple files with manual root_dir inference
- **Overlaps**: 
  - Walking up from output_dir
  - Deriving from config_dir
  - Hardcoded `Path.cwd()`
- **Consolidation Target**: Centralize in `paths/utils.py` with `find_project_root()` and `infer_root_dir()`

## Steps

### Step 1: Audit and Document All Path/Naming Utilities

**Objective**: Create comprehensive inventory of all utilities, their call sites, and dependencies.

**Tasks**:
1. Document all functions in path/naming modules with their signatures
2. List all call sites for each function using grep/codebase search
3. Identify import chains and dependencies
4. Create dependency graph showing relationships

**Success criteria**:
- Complete list of all path/naming utilities with call counts
- Dependency graph document created
- All import statements mapped

**Verification**:
```bash
# Count call sites for key functions
grep -r "build_mlflow_run_name" src --include="*.py" | wc -l
grep -r "format_run_name" src --include="*.py" | wc -l
grep -r "load_naming_policy" src --include="*.py" | wc -l
grep -r "infer_config_dir" src --include="*.py" | wc -l
```

### Step 2: Consolidate Duplicate `build_mlflow_run_name` Implementations

**Objective**: Remove duplicate implementation in `orchestration/jobs/tracking/naming/run_names.py`, make it a re-export.

**Tasks**:
1. Compare both implementations line-by-line to identify any differences
2. If identical, replace orchestration version with re-export:
   ```python
   from infrastructure.naming.mlflow.run_names import build_mlflow_run_name
   __all__ = ["build_mlflow_run_name"]
   ```
3. If differences exist, merge them into infrastructure version, then re-export
4. Update all imports from orchestration module to infrastructure module
5. Update `orchestration/jobs/tracking/naming/__init__.py` to re-export

**Success criteria**:
- Only one implementation of `build_mlflow_run_name` exists
- All tests pass
- No import errors
- Mypy passes: `uvx mypy src --show-error-codes`

**Files to modify**:
- `src/orchestration/jobs/tracking/naming/run_names.py` (replace with re-export)
- `src/orchestration/jobs/tracking/naming/__init__.py` (update exports)
- All files importing from orchestration module (update imports)

**Verification**:
```bash
# Verify only one implementation
grep -r "def build_mlflow_run_name" src --include="*.py"
# Should show only infrastructure.naming.mlflow.run_names

# Run tests
uvx pytest tests/ -k "naming" -v
```

### Step 3: Consolidate Duplicate `format_run_name` Implementations

**Objective**: Remove duplicate in `orchestration/jobs/tracking/naming/policy.py`, use infrastructure version.

**Tasks**:
1. Compare both `format_run_name` implementations
2. Compare both `load_naming_policy` implementations (different caching strategies)
3. Merge best caching strategy (mtime-based from display_policy.py) into infrastructure version
4. Replace orchestration version with re-export
5. Update `sanitize_semantic_suffix` to be in infrastructure if it's only used there
6. Update all imports

**Success criteria**:
- Only one implementation of `format_run_name` and `load_naming_policy`
- Mtime-based caching used consistently
- All tests pass
- Mypy passes

**Files to modify**:
- `src/orchestration/jobs/tracking/naming/policy.py` (replace with re-exports)
- `src/infrastructure/naming/display_policy.py` (ensure it has best implementation)
- All files importing from orchestration module

**Verification**:
```bash
# Verify single implementation
grep -r "def format_run_name" src --include="*.py"
grep -r "def load_naming_policy" src --include="*.py"

# Run tests
uvx pytest tests/ -k "policy" -v
```

### Step 4: Consolidate Duplicate `load_naming_policy` Implementations

**Objective**: Ensure single implementation with consistent caching (already addressed in Step 3, but verify).

**Tasks**:
1. Verify infrastructure version uses mtime-based caching (better than module-level cache)
2. Ensure all call sites use infrastructure version
3. Remove any remaining orchestration imports

**Success criteria**:
- Single `load_naming_policy` implementation
- Consistent caching behavior
- All tests pass

### Step 5: Eliminate Redundant `config_dir` Inference ✅

**Objective**: Centralize `config_dir` inference logic and eliminate redundant inference when `config_dir` is already available.

**Status**: ✅ Completed

**Tasks**:
1. Move `infer_config_dir_from_path()` from `tracking/mlflow/utils.py` to `paths/utils.py` (better location)
2. Rename to `infer_config_dir()` for clarity
3. Update function to accept optional `config_dir` parameter - if provided, return it; otherwise infer
4. Find all places that re-infer `config_dir` when it's available from caller
5. Update function signatures to accept `config_dir: Optional[Path] = None`
6. Update call sites to pass `config_dir` when available
7. Replace all `Path.cwd() / "config"` hardcoded patterns with `infer_config_dir()`

**Success criteria**:
- Single `infer_config_dir()` function in `paths/utils.py`
- All hardcoded `Path.cwd() / "config"` replaced
- Functions accept `config_dir` parameter when available
- No redundant inference when `config_dir` is already known
- All tests pass

**Files to modify**:
- `src/infrastructure/paths/utils.py` (add `infer_config_dir()`)
- `src/infrastructure/tracking/mlflow/utils.py` (remove function, import from paths)
- All files with hardcoded `Path.cwd() / "config"` (20+ files)
- Functions that re-infer `config_dir` unnecessarily

**Verification**:
```bash
# Verify no hardcoded patterns (only in docstrings)
grep -r 'Path\.cwd\(\) / "config"' src --include="*.py"
# Should return 0-3 results (only in docstrings/comments)

# Verify single inference function
grep -r "def infer_config" src --include="*.py"
# Should show only paths/utils.py

# Run tests
uvx pytest tests/ -v
```

**Completed**:
- ✅ Moved `infer_config_dir_from_path()` to `paths/utils.py` as `infer_config_dir()`
- ✅ Updated function to accept optional `config_dir` parameter (returns directly if provided)
- ✅ Replaced 8 hardcoded `Path.cwd() / "config"` patterns with `infer_config_dir()`
- ✅ Maintained backward compatibility via re-export in `tracking/mlflow/utils.py`
- ✅ All remaining `Path.cwd() / "config"` occurrences are in docstrings only

### Step 6: Consolidate Project Root Finding Logic ✅

**Objective**: Single source of truth for finding project root directory.

**Status**: ✅ Completed

**Tasks**:
1. Enhance `find_project_root()` in `paths/utils.py` to handle multiple scenarios:
   - From `config_dir`: current implementation (looks for `src/training/`)
   - From any path: walk up looking for both `config/` and `src/` directories
   - From `output_dir`: walk up to find "outputs", then parent
2. Add `infer_root_dir()` helper that tries multiple strategies
3. Replace all manual project root finding with `find_project_root()` or `infer_root_dir()`
4. Update `infer_config_dir()` to use `find_project_root()` internally

**Success criteria**:
- Single `find_project_root()` function handles all cases
- All manual root finding logic removed
- Consistent behavior across codebase
- All tests pass

**Files to modify**:
- `src/infrastructure/paths/utils.py` (enhance `find_project_root()`)
- All files with manual root finding (sweep.py, cv.py, trial_finder.py, etc.)

**Verification**:
```bash
# Verify no manual root finding
grep -r 'current\.name == "outputs"' src --include="*.py" | grep -v "paths/utils.py"
# Should return 0 results

# Verify minimal .parent chains (only in test files or comments)
grep -r '\.parent\.parent\.parent' src --include="*.py" | grep -v "test_" | grep -v "# Go up to"
# Should show minimal results (only in paths/utils.py or comments)

# Run tests
uvx pytest tests/ -v
```

**Completed**:
- ✅ Enhanced `find_project_root()` to handle multiple strategies (output_dir, config_dir, start_path, cwd)
- ✅ Added `infer_root_dir()` convenience function
- ✅ Replaced all manual root finding logic (10+ locations) with `find_project_root()`
- ✅ Updated `infer_config_dir()` to use `find_project_root()` internally
- ✅ All manual `.parent.parent.parent` chains and `current.name == "outputs"` checks removed

### Step 7: Update All Call Sites to Use Consolidated Utilities ✅

**Objective**: Ensure all code uses consolidated utilities, not duplicates.

**Status**: ✅ Completed

**Tasks**:
1. Update all imports to use infrastructure modules:
   - `from infrastructure.naming.mlflow.run_names import build_mlflow_run_name`
   - `from infrastructure.naming.display_policy import load_naming_policy, format_run_name`
   - `from infrastructure.paths.utils import find_project_root, infer_config_dir`
2. Remove orchestration naming imports where possible
3. Update function calls to pass `config_dir` when available
4. Replace manual inference with utility functions

**Success criteria**:
- All imports use infrastructure modules
- No orchestration naming imports (except for compatibility re-exports)
- All functions receive `config_dir` when available
- All tests pass
- Mypy passes: `uvx mypy src --show-error-codes`

**Verification**:
```bash
# Check for remaining orchestration naming imports
grep -r "from orchestration.*naming" src --include="*.py" | grep -v "__init__"
# Should only show re-export files

# Run full test suite
uvx pytest tests/ -v
```

**Completed**:
- ✅ Updated all `infer_config_dir_from_path` imports to use `infer_config_dir` from `infrastructure.paths.utils`
- ✅ Replaced 30+ call sites across all tracker modules and training modules
- ✅ Updated `get_naming_config` imports to use infrastructure version (2 locations)
- ✅ All imports now use consolidated infrastructure modules
- ✅ Backward compatibility maintained via re-exports in `tracking/mlflow/utils.py`
- ✅ All consolidated utilities verified to import successfully

**Verification**:
```bash
# Run mypy to verify type safety
uvx mypy src --show-error-codes

# Run full test suite
uvx pytest tests/ -v
```

### Step 8: Remove Deprecated/Duplicate Modules ✅

**Objective**: Clean up deprecated compatibility layers after migration period.

**Status**: ✅ Completed

**Tasks**:
1. ✅ Mark orchestration naming modules as deprecated with warnings
2. ✅ Add deprecation notices with migration instructions
3. ⏳ After verification period (1-2 releases), remove duplicate modules:
   - `src/orchestration/jobs/tracking/naming/run_names.py` (keep only re-export)
   - `src/orchestration/jobs/tracking/naming/policy.py` (keep only re-export)
4. ✅ Update `__init__.py` files to maintain backward compatibility

**Note**: Task 3 (actual module removal) is deferred until after deprecation period. Deprecation warnings are in place to guide migration.

**Success criteria**:
- Deprecation warnings added
- All imports still work (via re-exports)
- Documentation updated
- No breaking changes for external code

**Verification**:
```bash
# Verify re-exports work
python -c "from orchestration.jobs.tracking.naming import build_mlflow_run_name; print('OK')"

# Run tests
uvx pytest tests/ -v
```

## Success Criteria (Overall)

- ✅ Single implementation of `build_mlflow_run_name` (infrastructure version)
- ✅ Single implementation of `format_run_name` (infrastructure version)
- ✅ Single implementation of `load_naming_policy` (infrastructure version)
- ✅ Single `infer_config_dir()` function in `paths/utils.py`
- ✅ Single `find_project_root()` function handling all cases
- ✅ No hardcoded `Path.cwd() / "config"` patterns
- ✅ No redundant `config_dir` inference when already available
- ✅ All tests pass: `uvx pytest tests/`
- ✅ Mypy passes: `uvx mypy src --show-error-codes`
- ✅ No breaking changes (backward compatibility maintained via re-exports)
- ✅ Reduced code duplication (target: <5% overlap in path/naming utilities)

## Notes

- **Reuse-first principle**: Extend existing infrastructure modules rather than creating new ones
- **SRP pragmatically**: Keep related utilities together (paths together, naming together)
- **Backward compatibility**: Use re-exports in orchestration modules to avoid breaking changes
- **Incremental approach**: Each step can be done independently and tested
- **Testing**: Run full test suite after each step to catch regressions early

## Risks and Mitigations

- **Risk**: Breaking changes if imports are updated incorrectly
  - **Mitigation**: Use re-exports to maintain backward compatibility, update imports incrementally
- **Risk**: Performance regression from additional function calls
  - **Mitigation**: Minimal overhead, caching already in place for policy loading
- **Risk**: Edge cases in root finding logic
  - **Mitigation**: Comprehensive testing, fallback strategies in place


# Consolidate MLflow Run Creation and Tag Helper DRY Violations

## Goal

Eliminate code duplication in MLflow run creation and tag building logic by consolidating overlapping functions into clear single sources of truth, while maintaining backward compatibility and minimizing breaking changes.

## Status

**Last Updated**: 2026-01-15

**Status**: ⏳ **PENDING** - Plan created, awaiting implementation

### Completed Steps
- ✅ Step 1: Catalog all MLflow-tagged utility scripts and identify overlaps
- ⏳ Step 2: Consolidate run creation logic
- ⏳ Step 3: Consolidate tag building helpers
- ⏳ Step 4: Update all call sites to use consolidated functions
- ⏳ Step 5: Verify behavior and run tests

### Pending Steps
- ⏳ Step 2: Consolidate run creation logic
- ⏳ Step 3: Consolidate tag building helpers
- ⏳ Step 4: Update all call sites to use consolidated functions
- ⏳ Step 5: Verify behavior and run tests

## Preconditions

- The following implementation plans are already **FINISHED** and must not be duplicated:
  - `FINISHED-consolidate-mlflow-utilities-duplication.plan.md` (MLflow utility re-export layers)
  - `FINISHED-consolidate-mlflow-tagged-workflows-and-utilities-8f3a9c1b.plan.md` (setup/context, selection/workflows, artifact acquisition)
  - `FINISHED-consolidate-naming-utilities-dry-violations-83f1a2c7.plan.md` (naming/tag utilities)
- Changes in this plan must:
  - Reuse existing infrastructure modules under `infrastructure.tracking.mlflow.*`
  - Avoid reintroducing re-export layers already removed by previous plans
  - Preserve public workflow contracts (function names, argument shapes) where feasible
  - Maintain backward compatibility for existing call sites

## MLflow-Tagged Utility Scripts Inventory

All scripts tagged with `mlflow` in metadata, organized by responsibility:

### 1. MLflow Setup/Configuration (Domain: tracking)
- **`src/infrastructure/tracking/mlflow/setup.py`**
  - **Purpose**: MLflow experiment setup utilities (SSOT for MLflow configuration)
  - **Functions**: `setup_mlflow()`, `setup_mlflow_for_stage()`
  - **Status**: ✅ Already consolidated (SSOT established in prior plan)

### 2. MLflow Run Creation (Domain: tracking, training)
- **`src/infrastructure/tracking/mlflow/runs.py`**
  - **Purpose**: Create MLflow runs including child runs; resolve experiments and manage run lifecycle
  - **Functions**: `create_child_run()` (context manager), `create_run_safe()`, `get_or_create_experiment()`, `resolve_experiment_id()`
  - **Status**: ⚠️ **OVERLAP IDENTIFIED** - See DRY violations below

- **`src/training/execution/mlflow_setup.py`**
  - **Purpose**: Create MLflow runs for training execution; set up MLflow tracking for training subprocesses
  - **Functions**: `create_training_mlflow_run()`, `create_training_child_run()`, `setup_mlflow_tracking_env()`
  - **Status**: ⚠️ **OVERLAP IDENTIFIED** - See DRY violations below

### 3. MLflow Tag Building (Domain: training)
- **`src/training/execution/tag_helpers.py`**
  - **Purpose**: Add training-specific tags to MLflow runs; handle lineage tags for final training from HPO
  - **Functions**: `add_training_tags()`, `add_training_tags_with_lineage()`, `_build_lineage_tags_dict()`, `_get_training_tag_keys()`
  - **Status**: ⚠️ **OVERLAP IDENTIFIED** - See DRY violations below

- **`src/training/execution/tags.py`**
  - **Purpose**: Apply lineage tags to final training MLflow runs; link final training runs back to HPO origins
  - **Functions**: `apply_lineage_tags()`
  - **Status**: ⚠️ **OVERLAP IDENTIFIED** - Uses `_build_lineage_tags_dict()` from `tag_helpers.py` (good), but has duplicate run finding logic

### 4. MLflow Run Finding (Domain: tracking)
- **`src/infrastructure/tracking/mlflow/finder.py`**
  - **Purpose**: Find MLflow runs using priority-based retrieval strategies
  - **Functions**: `find_mlflow_run()`, `find_run_by_trial_id()`
  - **Status**: ✅ Already consolidated (SSOT for run finding)

### 5. MLflow Queries (Domain: tracking)
- **`src/infrastructure/tracking/mlflow/queries.py`**
  - **Purpose**: MLflow query patterns for reusable querying logic
  - **Functions**: `query_runs_by_tags()`, `find_best_run_by_metric()`, `group_runs_by_variant()`
  - **Status**: ✅ Already consolidated (SSOT for query patterns)

### 6. MLflow Trackers (Domain: tracking)
- **`src/infrastructure/tracking/mlflow/trackers/training_tracker.py`**
- **`src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py`**
- **`src/infrastructure/tracking/mlflow/trackers/benchmark_tracker.py`**
- **`src/infrastructure/tracking/mlflow/trackers/conversion_tracker.py`**
  - **Purpose**: Stage-specific MLflow run tracking
  - **Status**: ✅ Domain-specific trackers (no consolidation needed)

### 7. MLflow Utilities (Domain: tracking)
- **`src/infrastructure/tracking/mlflow/utils.py`** - Retry logic, run ID detection
- **`src/infrastructure/tracking/mlflow/urls.py`** - URL generation
- **`src/infrastructure/tracking/mlflow/hash_utils.py`** - Hash retrieval/computation
- **Status**: ✅ Already consolidated (SSOT established)

### 8. MLflow Run Names (Domain: training)
- **`src/training/execution/run_names.py`**
  - **Purpose**: Build MLflow run names with fallback logic
  - **Functions**: `build_training_run_name_with_fallback()`
  - **Status**: ✅ Domain-specific to training (no consolidation needed)

## Identified DRY Violations

### Category 1: Run Creation Overlaps

**Issue**: Multiple modules contain overlapping logic for creating MLflow runs, especially child runs.

#### Overlap 1: Child Run Creation

**Files Involved**:
1. **`infrastructure.tracking.mlflow.runs.create_child_run()`** (lines 42-235)
   - Context manager that creates and starts a child run
   - Handles experiment ID resolution from parent run
   - Sets Azure ML-specific tags
   - Automatically ends run on context exit

2. **`training.execution.mlflow_setup.create_training_child_run()`** (lines 272-384)
   - Creates child run via client API (returns run_id, run_object tuple)
   - Similar experiment ID resolution logic
   - Similar Azure ML tag handling
   - Similar parent run ID handling
   - **Difference**: Returns tuple instead of context manager

3. **`training.execution.mlflow_setup.create_training_mlflow_run()`** (lines 48-208)
   - Can create child runs when `create_as_child=True` and `parent_run_id` provided
   - Delegates to `create_training_child_run()` in that case
   - Also handles standalone run creation

**Duplicated Logic**:
- Experiment ID resolution from parent run (lines 76-102 in `runs.py` vs lines 315-335 in `mlflow_setup.py`)
- Azure ML tag building (lines 130-134 in `runs.py` vs lines 338-354 in `mlflow_setup.py`)
- Parent run ID tag setting (lines 124-127 in `runs.py` vs lines 339-342 in `mlflow_setup.py`)
- Child run creation via client API (lines 158-202 in `runs.py` vs lines 361-376 in `mlflow_setup.py`)

**Impact**: ~150 lines of duplicated logic across 2 modules

#### Overlap 2: Standalone Run Creation

**Files Involved**:
1. **`infrastructure.tracking.mlflow.runs.create_run_safe()`** (lines 237-278)
   - Simple safe run creation with error handling
   - Handles parent run ID tags

2. **`training.execution.mlflow_setup.create_training_mlflow_run()`** (lines 48-208)
   - More complex run creation with index updating
   - Handles parent run ID tags
   - Handles experiment resolution
   - Updates local MLflow index

**Duplicated Logic**:
- Run creation via client API (lines 264-268 in `runs.py` vs lines 166-170 in `mlflow_setup.py`)
- Parent run ID tag handling (lines 260-261 in `runs.py` vs lines 154-163 in `mlflow_setup.py`)

**Impact**: ~30 lines of duplicated logic

### Category 2: Tag Building Overlaps

**Issue**: Tag building logic is split across multiple modules with some duplication.

#### Overlap 1: Lineage Tag Building

**Files Involved**:
1. **`training.execution.tag_helpers._build_lineage_tags_dict()`** (lines 142-230)
   - Builds lineage tags dictionary from lineage dict
   - Handles all `code.lineage.*` tags
   - Used by both `add_training_tags_with_lineage()` and `apply_lineage_tags()`

2. **`training.execution.tags.apply_lineage_tags()`** (lines 42-144)
   - Applies lineage tags to existing MLflow run
   - Uses `_build_lineage_tags_dict()` from `tag_helpers` (good reuse)
   - **BUT**: Has duplicate run finding logic (lines 82-115) that overlaps with `infrastructure.tracking.mlflow.finder.find_mlflow_run()`

**Duplicated Logic**:
- Run finding with fallback to direct MLflow query (lines 82-115 in `tags.py` vs `finder.find_mlflow_run()`)
- Tag key retrieval (lines 118-121 in `tags.py` vs `_get_training_tag_keys()` in `tag_helpers.py`)

**Impact**: ~40 lines of duplicated logic

#### Overlap 2: Tag Key Retrieval

**Files Involved**:
1. **`training.execution.tag_helpers._get_training_tag_keys()`** (lines 233-273)
   - Consolidates tag key retrieval pattern
   - Returns dictionary mapping tag key names to actual tag key strings

2. **`training.execution.tags.apply_lineage_tags()`** (lines 118-121)
   - Directly imports and calls tag key functions instead of using `_get_training_tag_keys()`

**Status**: ✅ **Already consolidated** - `tags.py` uses `_build_lineage_tags_dict()` which is good, but could use `_get_training_tag_keys()` helper more consistently

**Impact**: Minor - already mostly consolidated

## Consolidation Approach

### Strategy: Reuse-First with Pragmatic SRP

1. **Run Creation Consolidation**:
   - **SSOT**: `infrastructure.tracking.mlflow.runs` should be the single source of truth for run creation
   - **Action**: Extend `runs.create_child_run()` to support both context manager and tuple return patterns
   - **Action**: Refactor `training.execution.mlflow_setup.create_training_child_run()` to delegate to `runs.create_child_run()`
   - **Action**: Refactor `training.execution.mlflow_setup.create_training_mlflow_run()` to use `runs` module functions where possible
   - **Preserve**: Keep `create_training_mlflow_run()` for training-specific logic (index updating, training-specific tags)

2. **Tag Building Consolidation**:
   - **SSOT**: `training.execution.tag_helpers` should remain the SSOT for tag building helpers
   - **Action**: Refactor `training.execution.tags.apply_lineage_tags()` to use `finder.find_mlflow_run()` instead of duplicate run finding logic
   - **Action**: Ensure `apply_lineage_tags()` uses `_get_training_tag_keys()` helper consistently
   - **Preserve**: Keep `apply_lineage_tags()` for its specific use case (applying tags to existing runs)

3. **Minimize Breaking Changes**:
   - Keep function signatures stable where possible
   - Add deprecation warnings for functions that will be removed
   - Provide backward compatibility wrappers if needed

## Steps

### Step 1: Catalog all MLflow-tagged utility scripts and identify overlaps

**Objective**: Create comprehensive inventory of all MLflow-tagged scripts and document overlaps.

**Actions**:
1. Search for all files with `tags:.*mlflow` in metadata
2. Read each file's metadata block and document:
   - File path
   - Type (utility, script, workflow)
   - Domain
   - Responsibility summary
   - Key functions
3. Identify overlapping responsibilities:
   - Run creation logic
   - Tag building logic
   - Run finding logic (already consolidated)
   - Query patterns (already consolidated)
4. Document overlaps in this plan

**Success criteria**:
- ✅ Complete inventory table created (see above)
- ✅ All overlaps identified and documented
- ✅ Overlaps grouped into clear categories

**Status**: ✅ **COMPLETE** - Inventory and overlaps documented above

---

### Step 2: Consolidate run creation logic

**Objective**: Eliminate duplication in child run creation by making `infrastructure.tracking.mlflow.runs` the SSOT.

**Actions**:
1. **Extend `runs.create_child_run()` to support tuple return pattern**:
   - Add optional parameter `return_tuple: bool = False`
   - When `return_tuple=True`, return `(run_id, run_object)` tuple instead of context manager
   - This allows `create_training_child_run()` to delegate to it

2. **Refactor `training.execution.mlflow_setup.create_training_child_run()`**:
   - Change implementation to call `runs.create_child_run()` with `return_tuple=True`
   - Remove duplicated experiment ID resolution logic
   - Remove duplicated Azure ML tag building logic
   - Keep function signature stable for backward compatibility

3. **Refactor `training.execution.mlflow_setup.create_training_mlflow_run()`**:
   - When `create_as_child=True`, delegate to `create_training_child_run()` (which now uses `runs.create_child_run()`)
   - For standalone runs, consider using `runs.create_run_safe()` for basic run creation, then add training-specific logic (index updating, etc.)
   - Document that this function adds training-specific logic on top of base run creation

4. **Update docstrings**:
   - Document that `runs.create_child_run()` is the SSOT for child run creation
   - Document that `mlflow_setup` functions add training-specific logic

**Success criteria**:
- ✅ `runs.create_child_run()` supports both context manager and tuple return patterns
- ✅ `create_training_child_run()` delegates to `runs.create_child_run()` with no duplicated logic
- ✅ `create_training_mlflow_run()` uses `runs` module functions where possible
- ✅ All function signatures remain stable (backward compatible)
- ✅ `uvx mypy src/infrastructure/tracking/mlflow/runs.py src/training/execution/mlflow_setup.py` passes with 0 errors

---

### Step 3: Consolidate tag building helpers

**Objective**: Eliminate duplicate run finding logic in `tags.apply_lineage_tags()` by using the SSOT finder.

**Actions**:
1. **Refactor `training.execution.tags.apply_lineage_tags()`**:
   - Replace duplicate run finding logic (lines 82-115) with call to `infrastructure.tracking.mlflow.finder.find_mlflow_run()`
   - Use `finder.find_mlflow_run()` with appropriate parameters (experiment_name, context, output_dir, strict=False)
   - Remove fallback direct MLflow query (lines 101-115) - let `finder.find_mlflow_run()` handle fallbacks
   - Keep the function's specific responsibility: applying tags to existing runs

2. **Ensure consistent tag key usage**:
   - Verify `apply_lineage_tags()` uses `_get_training_tag_keys()` helper where appropriate
   - Currently it directly imports tag key functions - consider using helper for consistency

3. **Update docstrings**:
   - Document that `tag_helpers` is the SSOT for tag building helpers
   - Document that `tags.apply_lineage_tags()` uses `finder.find_mlflow_run()` for run finding

**Success criteria**:
- ✅ `apply_lineage_tags()` uses `finder.find_mlflow_run()` instead of duplicate logic
- ✅ No duplicate run finding code remains in `tags.py`
- ✅ Tag key retrieval uses helper functions consistently
- ✅ `uvx mypy src/training/execution/tags.py` passes with 0 errors

---

### Step 4: Update all call sites to use consolidated functions

**Objective**: Ensure all call sites use the consolidated functions correctly.

**Actions**:
1. **Search for call sites**:
   ```bash
   grep -r "create_training_child_run\|create_training_mlflow_run" src/
   grep -r "apply_lineage_tags" src/
   ```

2. **Verify call sites**:
   - Check that call sites use correct function signatures
   - Verify no call sites rely on internal implementation details that were removed
   - Update any call sites that need changes due to consolidation

3. **Update imports if needed**:
   - Ensure imports are correct after consolidation
   - Check for any circular import issues

**Success criteria**:
- ✅ All call sites verified to work with consolidated functions
- ✅ No broken imports
- ✅ No call sites rely on removed internal implementation details
- ✅ `grep -r "from.*mlflow_setup\|from.*tags" src/` shows correct import patterns

---

### Step 5: Verify behavior and run tests

**Objective**: Ensure all functionality works correctly after consolidation.

**Actions**:
1. **Run type checking**:
   ```bash
   uvx mypy src/infrastructure/tracking/mlflow/runs.py
   uvx mypy src/training/execution/mlflow_setup.py
   uvx mypy src/training/execution/tags.py
   uvx mypy src/training/execution/tag_helpers.py
   ```

2. **Run linter**:
   ```bash
   # Check for any linter errors in modified files
   ```

3. **Run relevant tests**:
   ```bash
   pytest tests/infrastructure/tracking/mlflow/ -v
   pytest tests/training/execution/ -v -k mlflow
   ```

4. **Verify backward compatibility**:
   - Check that function signatures haven't changed
   - Verify that existing workflows still work

**Success criteria**:
- ✅ All type checks pass (`uvx mypy` shows 0 errors)
- ✅ No linter errors introduced
- ✅ All relevant tests pass
- ✅ Backward compatibility maintained (function signatures stable)
- ✅ No regressions in MLflow run creation or tag application

---

## Success Criteria (Overall)

- ✅ **Code reduction**: ~200+ lines of duplicated logic removed
- ✅ **Single source of truth**: 
  - `infrastructure.tracking.mlflow.runs` is SSOT for run creation
  - `training.execution.tag_helpers` is SSOT for tag building helpers
  - `infrastructure.tracking.mlflow.finder` is SSOT for run finding (already established)
- ✅ **Reduced confusion**: Fewer modules with overlapping responsibilities
- ✅ **Backward compatibility**: All function signatures remain stable
- ✅ **Type safety**: All code passes Mypy type checking
- ✅ **Functionality**: All existing functionality preserved
- ✅ **Maintainability**: Future changes only need to be made in one place

## Notes

### Import Path Strategy

- **Source of Truth for Run Creation**: `infrastructure.tracking.mlflow.runs`
  - `create_child_run()` - Context manager for child runs (supports tuple return)
  - `create_run_safe()` - Safe run creation with error handling
  - `get_or_create_experiment()` - Experiment resolution
  - `resolve_experiment_id()` - Experiment ID resolution strategies

- **Training-Specific Extensions**: `training.execution.mlflow_setup`
  - `create_training_mlflow_run()` - Adds training-specific logic (index updating, training tags)
  - `create_training_child_run()` - Delegates to `runs.create_child_run()` (backward compat wrapper)
  - `setup_mlflow_tracking_env()` - Environment variable setup for subprocesses

- **Source of Truth for Tag Building**: `training.execution.tag_helpers`
  - `add_training_tags()` - Simple training tags
  - `add_training_tags_with_lineage()` - Training tags with lineage
  - `_build_lineage_tags_dict()` - Lineage tag dictionary builder (internal helper)

- **Tag Application**: `training.execution.tags`
  - `apply_lineage_tags()` - Applies lineage tags to existing runs (uses `finder.find_mlflow_run()`)

### Risk Assessment

- **Low Risk**: Run creation consolidation - functions are simple wrappers, no complex logic
- **Low Risk**: Tag building consolidation - already mostly consolidated, just removing duplicate run finding
- **Medium Risk**: Need to verify all call sites work correctly after consolidation
- **Low Risk**: Backward compatibility maintained - function signatures remain stable

### Rollback Plan

If issues arise:
1. Revert commits in reverse order
2. Restore original function implementations from git history
3. Revert any call site changes

## Related Plans

- `FINISHED-consolidate-mlflow-utilities-duplication.plan.md` - MLflow utility re-export layers
- `FINISHED-consolidate-mlflow-tagged-workflows-and-utilities-8f3a9c1b.plan.md` - Setup/context, selection/workflows, artifact acquisition
- `FINISHED-consolidate-naming-utilities-dry-violations-83f1a2c7.plan.md` - Naming/tag utilities


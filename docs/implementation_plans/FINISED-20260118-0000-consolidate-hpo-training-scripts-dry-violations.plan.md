# Consolidate HPO and Training Scripts - DRY Violations Removal Plan

> **Note**: This plan builds on **completed consolidation work** and applies established SSOT patterns specifically to **HPO and training execution scripts** (`type: script` entry points).

## Goal

Eliminate DRY violations across HPO and training **execution scripts** by applying established SSOT patterns from completed consolidation plans, removing duplicate inference patterns (especially `config_dir` re-inference), and ensuring consistent use of centralized utilities.

This plan focuses specifically on **HPO and training execution scripts** (entry points with `type: script`), identifying:
- Duplicate `config_dir` inference patterns (even when `config_dir` is already available)
- Overlapping path resolution logic in execution scripts
- Duplicate MLflow setup and naming patterns in execution scripts
- Near-duplicate config loading patterns in execution scripts
- Redundant hash computation patterns in execution scripts

**Scope**: This plan complements the broader utility consolidation by focusing on **execution scripts** rather than utility functions. The completed utility plan (`20260117-2350-consolidate-utility-scripts-dry-violations-unified.plan.md`) already addressed utility-level consolidation.

## Status

**Last Updated**: 2026-01-18

**Note**: A summary document exists (`complete/consolidate-hpo-training-scripts-dry-violations-SUMMARY.md`) indicating similar work may have been completed previously. This plan consolidates findings from all related plans and provides a comprehensive implementation guide.

### Relationship to Completed Plans

#### ✅ Completed: Utility Script Consolidation
**Plan**: `20260117-2350-consolidate-utility-scripts-dry-violations-unified.plan.md` (✅ Completed)

**Established SSOT patterns for:**
- ✅ `config_dir` inference (trust provided parameter pattern)
- ✅ Path resolution utilities (`resolve_project_paths()`, `build_output_path()`)
- ✅ MLflow setup and naming (infrastructure modules as SSOT)
- ✅ Tags registry loading (trust provided `config_dir`)
- ✅ Config loading (use `load_yaml()` SSOT)

**This plan applies those SSOT patterns specifically to execution scripts** that may not yet be using them consistently.

#### ✅ Completed: Workflow Patterns Standardization
**Plan**: `FINISHED-20260117-2300-workflow-patterns-unified-comprehensive.plan.md` (✅ Completed)

**Established standard patterns for:**
- ✅ Function signature standardization (parameters, naming, metadata)
- ✅ Logging pattern consistency (`logger` from `get_logger(__name__)`)
- ✅ MLflow setup pattern consistency (`setup_mlflow()` SSOT)
- ✅ Platform/environment parameter handling
- ✅ Backup parameter naming (`backup_to_drive`, `restore_from_drive`)

**This plan ensures execution scripts follow these workflow patterns** when they're called from workflows.

### Completed Steps
- ✅ Step 0: Comprehensive analysis and cataloging (completed)
- ✅ Coordination with utility plan: Identified which SSOT patterns to apply
- ✅ Coordination with workflow plan: Identified which workflow patterns to follow

### Completed Steps
- ✅ Step 1: Audit all HPO and training scripts
- ✅ Step 2: Identify and categorize DRY violations
- ✅ Step 3: Consolidate config_dir inference patterns (apply trust principle to execution scripts)
- ✅ Step 4: Consolidate path resolution utilities (use SSOT in execution scripts)
- ✅ Step 5: Consolidate MLflow setup patterns (use SSOT in execution scripts)
- ✅ Step 6: Consolidate hash computation patterns (extract common patterns)

### Completed Steps
- ✅ Step 7: Update all call sites (ensure execution scripts use SSOT utilities)
- ✅ Step 8: Verify tests pass and mypy is clean

### Pending Steps
- ⏳ Step 9: Document consolidation patterns

## Preconditions

- ✅ **Completed**: `20260117-2350-consolidate-utility-scripts-dry-violations-unified.plan.md` - Utility-level consolidation already completed
- ✅ **Completed**: `FINISHED-20260117-2300-workflow-patterns-unified-comprehensive.plan.md` - Workflow patterns standardized
- Existing `infrastructure.paths.utils.resolve_project_paths()` function (SSOT for path resolution)
- Existing `infrastructure.paths.utils.infer_config_dir()` function (SSOT for config_dir inference)
- Existing `infrastructure.tracking.mlflow.hash_utils` functions (SSOT for hash computation)
- All scripts have proper metadata blocks (`@meta`)
- Tests exist for utility functions

**Note**: The utility consolidation plan already established SSOT patterns. This plan applies those patterns specifically to execution scripts.

## HPO and Training Scripts Inventory

### 1. HPO Execution Scripts

| File | Purpose | Key Functions | Entry Point |
|------|---------|---------------|-------------|
| `src/training/hpo/execution/local/sweep.py` | Run local HPO sweeps using Optuna | `run_local_hpo_sweep()`, `create_local_hpo_objective()` | ✅ `type: script` |
| `src/training/hpo/execution/local/trial.py` | Execute single HPO training trial | `run_training_trial()`, `TrialExecutor` | ✅ `type: script` |
| `src/training/hpo/execution/local/refit.py` | Execute refit training on full dataset | `run_refit_training()` | ✅ `type: script` |
| `src/training/hpo/execution/local/cv.py` | Orchestrate k-fold cross-validation for HPO trials | `run_training_trial_with_cv()` | ✅ `type: script` |

**Key Responsibilities:**
- Coordinate trial execution
- Manage MLflow tracking
- Handle checkpoint cleanup
- Create nested MLflow run structure (trial → folds)
- Aggregate fold metrics

### 2. Training Execution Scripts

| File | Purpose | Key Functions | Entry Point |
|------|---------|---------------|-------------|
| `src/training/cli/train.py` | Main training entry point | `main()`, `parse_training_arguments()` | ✅ `type: script` |
| `src/training/orchestrator.py` | Orchestrate training execution | `run_training()` | ✅ `type: script` |
| `src/training/execution/executor.py` | Execute final training with best HPO configuration | `run_final_training_workflow()` | ✅ `type: script` |
| `src/orchestration/jobs/training.py` | Create Azure ML final training jobs | `create_final_training_job()`, `build_final_training_config()` | ✅ `type: script` |

**Key Responsibilities:**
- Launch single- or multi-GPU training
- Set up MLflow tracking
- Handle distributed training context
- Manage training run lifecycle
- Build final training configuration

### 3. HPO Tracking and Setup Utilities

| File | Purpose | Key Functions |
|------|---------|---------------|
| `src/training/hpo/tracking/setup.py` | MLflow run setup for HPO | `setup_hpo_mlflow_run()`, `commit_run_name_version()` |
| `src/training/hpo/tracking/runs.py` | Trial run creation for HPO | `create_trial_run_no_cv()`, `finalize_trial_run_no_cv()` |
| `src/training/hpo/tracking/cleanup.py` | Cleanup interrupted runs | `cleanup_interrupted_runs()` |

**Key Responsibilities:**
- Create HPO parent runs
- Create trial-level runs
- Set up naming context
- Commit run name versions

## DRY Violations Identified

### Category 1: Config Directory Inference Duplication

**Problem**: Multiple scripts re-infer `config_dir` even when it's already available from callers.

**Examples:**

1. **`sweep.py` (line 608)**: Has `project_config_dir = config_dir` but `setup_hpo_mlflow_run()` re-infers `config_dir` instead of using it.

```python
# sweep.py line 633
project_config_dir = config_dir

# sweep.py line 807-818
hpo_parent_context, mlflow_run_name = setup_hpo_mlflow_run(
    # ...
    config_dir=project_config_dir,  # Pass project config_dir to avoid re-inference (DRY)
)
```

**However**, `setup_hpo_mlflow_run()` still has inference logic that runs when `config_dir=None`:

```python
# setup.py lines 168-176
if config_dir is None:
    root_dir, config_dir = resolve_project_paths(
        output_dir=output_dir,
        config_dir=None,
    )
    # Fallback if resolve_project_paths() didn't find config_dir
    if config_dir is None:
        from infrastructure.paths.utils import infer_config_dir
        config_dir = infer_config_dir(path=root_dir) if root_dir else infer_config_dir()
```

**Issue**: Even though `sweep.py` passes `config_dir`, the function signature allows `None`, and other callers might pass `None`, causing re-inference.

2. **`refit.py` (lines 137-150)**: Re-infers `config_dir` even when it's provided:

```python
# refit.py line 67
config_dir: Path,

# refit.py lines 137-150
root_dir, resolved_config_dir = resolve_project_paths(
    config_dir=config_dir,  # Use provided config_dir
)
# Use resolved config_dir, or provided config_dir, or infer as last resort
config_dir = resolved_config_dir or config_dir
if config_dir is None:
    from infrastructure.paths.utils import infer_config_dir
    config_dir = infer_config_dir(path=root_dir) if root_dir else infer_config_dir()
```

**Issue**: `resolve_project_paths()` should trust provided `config_dir` and return it directly, but the code still has fallback inference logic.

3. **`cv.py` (lines 177-189)**: Similar pattern - re-infers `config_dir` even when provided:

```python
# cv.py line 47
config_dir: Path,

# cv.py lines 177-189
root_dir, resolved_config_dir = resolve_project_paths(
    output_dir=output_dir,
    config_dir=config_dir,  # Use provided config_dir if available
)
# Use resolved config_dir, or provided config_dir, or infer as last resort
config_dir = resolved_config_dir or config_dir
if config_dir is None:
    from infrastructure.paths.utils import infer_config_dir
    config_dir = infer_config_dir(path=root_dir) if root_dir else infer_config_dir()
```

**Pattern**: All these scripts follow the same pattern:
1. Accept `config_dir` as parameter
2. Call `resolve_project_paths()` with `config_dir`
3. Still have fallback inference logic "just in case"

**Root Cause**: `resolve_project_paths()` should be the SSOT, but callers don't trust it and add redundant fallback logic.

### Category 2: Path Resolution Duplication

**Problem**: Multiple scripts duplicate path resolution logic instead of using centralized utilities.

**Examples:**

1. **`sweep.py` (lines 717-733)**: Duplicates v2 folder creation logic:

```python
# sweep.py lines 717-733
from infrastructure.paths.utils import resolve_project_paths

root_dir, resolved_config_dir = resolve_project_paths(
    output_dir=output_dir,
    config_dir=project_config_dir,  # Use provided project_config_dir
)
# Standardized fallback: use resolved value, or provided parameter, or infer
if root_dir is None:
    root_dir = Path.cwd()
# Use resolved config_dir, or provided project_config_dir, or infer as last resort
config_dir = resolved_config_dir or project_config_dir
if config_dir is None:
    from infrastructure.paths.utils import infer_config_dir
    config_dir = infer_config_dir(path=root_dir) if root_dir else infer_config_dir()
```

**Issue**: This pattern is repeated in `refit.py`, `cv.py`, and other scripts. Should be extracted to a shared utility.

2. **`refit.py` (lines 234-243)**: Similar duplication:

```python
# refit.py lines 234-243
from infrastructure.paths.utils import resolve_project_paths

root_dir, resolved_config_dir = resolve_project_paths(
    output_dir=output_dir,
    config_dir=config_dir,
)
if root_dir is None:
    root_dir = Path.cwd()
config_dir_for_path = resolved_config_dir or config_dir
```

**Pattern**: All scripts have the same "standardized fallback" logic that should be centralized.

### Category 3: Hash Computation Duplication

**Problem**: Multiple scripts compute `study_key_hash` and `trial_key_hash` using similar patterns.

**Examples:**

1. **`sweep.py` (lines 654-659)**: Computes `study_key_hash` early:

```python
# sweep.py lines 654-659
from infrastructure.tracking.mlflow.hash_utils import compute_study_key_hash_v2
study_key_hash = compute_study_key_hash_v2(
    data_config, hpo_config, train_config, backbone, project_config_dir
)
```

2. **`cv.py` (lines 118-136)**: Similar computation with fallback hierarchy:

```python
# cv.py lines 118-136
from infrastructure.tracking.mlflow.hash_utils import (
    get_study_key_hash_from_run,
    compute_study_key_hash_v2,
    compute_trial_key_hash_from_configs,
)

if not computed_study_key_hash and hpo_parent_run_id:
    computed_study_key_hash = get_study_key_hash_from_run(
        hpo_parent_run_id, client, config_dir
    )

if not computed_study_key_hash and data_config and hpo_config and train_config:
    computed_study_key_hash = compute_study_key_hash_v2(
        data_config, hpo_config, train_config, backbone, config_dir
    )
```

3. **`refit.py` (lines 156-170)**: Similar pattern:

```python
# refit.py lines 156-170
from infrastructure.tracking.mlflow.hash_utils import get_study_key_hash_from_run

if not computed_study_key_hash and hpo_parent_run_id:
    computed_study_key_hash = get_study_key_hash_from_run(
        hpo_parent_run_id, client, config_dir
    )
```

**Pattern**: All scripts follow the same fallback hierarchy:
1. Use provided hash (if available)
2. Retrieve from MLflow run tags (SSOT)
3. Compute from configs (fallback)

**Issue**: This pattern is duplicated across multiple files. Should be extracted to a shared utility.

### Category 4: MLflow Run Creation Duplication

**Problem**: Multiple scripts create MLflow runs with similar patterns.

**Examples:**

1. **`cv.py` (lines 390-597)**: Creates trial run with extensive setup:
   - Build systematic run name
   - Compute hashes
   - Build tags
   - Create run

2. **`refit.py` (lines 375-403)**: Similar pattern for refit runs:
   - Uses `create_training_mlflow_run()` (good - SSOT)
   - But has duplicate setup logic before calling it

**Pattern**: Both create runs with:
- Naming context creation
- Hash computation
- Tag building
- Run creation

**Issue**: Some of this logic could be shared, but the patterns are already using shared utilities (`create_training_mlflow_run()`). The duplication is in the **setup logic** before calling the shared utility.

## Consolidation Approach

### Principle 1: Trust Provided Parameters (DRY)

**Rule**: If a function receives `config_dir` as a parameter, it should **trust** it and not re-infer it unless it's explicitly `None`.

**Current Problem**: Functions accept `config_dir: Optional[Path] = None` but then re-infer it even when provided.

**Solution**: 
1. Make `config_dir` required (not Optional) when it's always available from callers
2. Or, if Optional, only infer when `None` and document the trust principle

### Principle 2: Single Source of Truth (SSOT)

**Rule**: Use centralized utilities for common operations:
- `resolve_project_paths()` for path resolution (from utility plan ✅)
- `infer_config_dir()` for config_dir inference (only when needed, from utility plan ✅)
- `infrastructure.tracking.mlflow.hash_utils` for hash computation
- `create_training_mlflow_run()` for MLflow run creation (from workflow plan ✅)
- `setup_mlflow()` for MLflow setup (from workflow plan ✅)

**Current Problem**: Scripts duplicate logic even when SSOT utilities exist.

**Solution**: Remove duplicate logic and use SSOT utilities directly.

### Principle 3: Extract Common Patterns

**Rule**: When the same pattern appears in 3+ files, extract it to a shared utility.

**Current Problem**: The "standardized fallback" pattern for path resolution appears in multiple files.

**Solution**: Extract to `infrastructure.paths.utils.resolve_project_paths_with_fallback()` or similar.

### Principle 4: Minimize Breaking Changes

**Rule**: Keep function signatures compatible, only change internal implementation.

**Current Problem**: Some functions might break if we remove fallback logic.

**Solution**: 
1. Keep Optional parameters but document trust principle
2. Add deprecation warnings for redundant inference
3. Gradually migrate callers to pass `config_dir` explicitly

## Implementation Steps

### Step 1: Audit All HPO and Training Scripts

**Goal**: Complete inventory of all scripts, their responsibilities, and current DRY violations.

**Tasks**:
1. List all files in `src/training/hpo/execution/` and `src/training/execution/`
2. Document each script's purpose, key functions, and entry points
3. Identify all `config_dir` inference patterns
4. Identify all path resolution patterns
5. Identify all hash computation patterns
6. Identify all MLflow run creation patterns

**Success Criteria**:
- Complete inventory document created
- All DRY violations cataloged with file paths and line numbers
- Patterns grouped into categories

**Files to Audit**:
- `src/training/hpo/execution/local/sweep.py`
- `src/training/hpo/execution/local/trial.py`
- `src/training/hpo/execution/local/refit.py`
- `src/training/hpo/execution/local/cv.py`
- `src/training/cli/train.py`
- `src/training/orchestrator.py`
- `src/training/execution/executor.py`
- `src/orchestration/jobs/training.py`
- `src/training/hpo/tracking/setup.py`
- `src/training/hpo/tracking/runs.py`
- `src/training/hpo/tracking/cleanup.py`

### Step 2: Identify and Categorize DRY Violations

**Goal**: Group all violations into clear categories with examples.

**Tasks**:
1. Create violation categories:
   - Config directory inference duplication
   - Path resolution duplication
   - Hash computation duplication
   - MLflow run creation duplication
   - Config loading duplication
2. For each category, list:
   - Files affected
   - Line numbers
   - Pattern description
   - Proposed consolidation approach

**Success Criteria**:
- All violations categorized
- Examples provided for each category
- Consolidation approach documented

### Step 3: Consolidate config_dir Inference Patterns

**Goal**: Apply trust principle to execution scripts - remove redundant `config_dir` inference when parameter is already provided.

**Note**: The utility consolidation plan already established the trust principle. This step applies it to execution scripts.

**Tasks**:
1. Verify `resolve_project_paths()` already trusts provided `config_dir` (from utility plan ✅):
   - If `config_dir` is provided and not None, it returns it directly
   - Only infers when `config_dir` is explicitly `None`
   - Trust principle already documented in docstring
2. Update all execution script call sites to pass `config_dir` explicitly:
   - `sweep.py`: Pass `project_config_dir` to all functions
   - `refit.py`: Pass `config_dir` to all functions
   - `cv.py`: Pass `config_dir` to all functions
   - `setup.py`: Trust provided `config_dir` parameter
3. Remove redundant fallback inference logic:
   - Remove `if config_dir is None: infer_config_dir()` patterns when `config_dir` is already provided
   - Keep inference only when `config_dir` is truly Optional and might be None

**Success Criteria**:
- `resolve_project_paths()` trusts provided `config_dir` (already done ✅)
- All call sites pass `config_dir` explicitly
- Redundant inference logic removed
- Tests pass: `uvx pytest tests/ -k "config_dir"`
- Mypy passes: `uvx mypy src/training/hpo/execution/ src/training/execution/`

**Files to Modify**:
- `src/training/hpo/execution/local/sweep.py`
- `src/training/hpo/execution/local/refit.py`
- `src/training/hpo/execution/local/cv.py`
- `src/training/hpo/tracking/setup.py`

### Step 4: Consolidate Path Resolution Utilities

**Goal**: Extract common "standardized fallback" pattern to shared utility.

**Tasks**:
1. Create `resolve_project_paths_with_fallback()` utility:
   ```python
   def resolve_project_paths_with_fallback(
       output_dir: Optional[Path] = None,
       config_dir: Optional[Path] = None,
   ) -> tuple[Path, Path]:
       """
       Resolve project paths with standardized fallback logic.
       
       Trusts provided config_dir if not None.
       """
       root_dir, resolved_config_dir = resolve_project_paths(
           output_dir=output_dir,
           config_dir=config_dir,
       )
       # Standardized fallback
       if root_dir is None:
           root_dir = Path.cwd()
       config_dir = resolved_config_dir or config_dir
       if config_dir is None:
           config_dir = infer_config_dir(path=root_dir) if root_dir else infer_config_dir()
       return root_dir, config_dir
   ```
2. Replace duplicate patterns in:
   - `sweep.py` (lines 717-733)
   - `refit.py` (lines 137-150, 234-243)
   - `cv.py` (lines 177-189, 255-261)
   - Other files with similar patterns

**Success Criteria**:
- `resolve_project_paths_with_fallback()` created
- All duplicate patterns replaced
- Tests pass: `uvx pytest tests/infrastructure/paths/`
- Mypy passes: `uvx mypy src/infrastructure/paths/`

**Files to Modify**:
- `src/infrastructure/paths/utils.py` (add new function)
- `src/training/hpo/execution/local/sweep.py`
- `src/training/hpo/execution/local/refit.py`
- `src/training/hpo/execution/local/cv.py`

### Step 5: Consolidate MLflow Setup Patterns

**Goal**: Ensure all scripts use SSOT utilities for MLflow setup (from workflow plan ✅).

**Tasks**:
1. Verify all scripts use:
   - `infrastructure.tracking.mlflow.setup.setup_mlflow()` for MLflow setup (from workflow plan ✅)
   - `create_training_mlflow_run()` for run creation (from workflow plan ✅)
   - `setup_hpo_mlflow_run()` for HPO-specific setup
2. Remove duplicate MLflow setup logic
3. Ensure consistent usage patterns across all scripts

**Success Criteria**:
- All scripts use SSOT utilities
- No duplicate MLflow setup logic
- Tests pass: `uvx pytest tests/tracking/ tests/training/hpo/tracking/`
- Mypy passes: `uvx mypy src/training/hpo/tracking/ src/training/execution/`

**Files to Review**:
- `src/training/hpo/execution/local/sweep.py`
- `src/training/hpo/execution/local/refit.py`
- `src/training/hpo/execution/local/cv.py`
- `src/training/orchestrator.py`
- `src/training/execution/executor.py`

### Step 6: Consolidate Hash Computation Patterns

**Goal**: Extract common hash computation fallback hierarchy to shared utility.

**Tasks**:
1. Create `get_or_compute_study_key_hash()` utility:
   ```python
   def get_or_compute_study_key_hash(
       study_key_hash: Optional[str] = None,
       hpo_parent_run_id: Optional[str] = None,
       data_config: Optional[Dict[str, Any]] = None,
       hpo_config: Optional[Dict[str, Any]] = None,
       train_config: Optional[Dict[str, Any]] = None,
       backbone: Optional[str] = None,
       config_dir: Optional[Path] = None,
   ) -> Optional[str]:
       """
       Get or compute study_key_hash using fallback hierarchy:
       1. Use provided study_key_hash
       2. Retrieve from MLflow run tags (SSOT)
       3. Compute from configs (fallback)
       """
   ```
2. Create `get_or_compute_trial_key_hash()` utility (similar pattern)
3. Replace duplicate patterns in:
   - `sweep.py` (lines 654-659, 1154-1165)
   - `refit.py` (lines 156-170, 175-188)
   - `cv.py` (lines 118-136, 448-492)

**Success Criteria**:
- Hash computation utilities created
- All duplicate patterns replaced
- Tests pass: `uvx pytest tests/infrastructure/tracking/mlflow/hash_utils/`
- Mypy passes: `uvx mypy src/infrastructure/tracking/mlflow/hash_utils/`

**Files to Modify**:
- `src/infrastructure/tracking/mlflow/hash_utils.py` (add new functions)
- `src/training/hpo/execution/local/sweep.py`
- `src/training/hpo/execution/local/refit.py`
- `src/training/hpo/execution/local/cv.py`

### Step 7: Update All Call Sites

**Goal**: Ensure all call sites use consolidated utilities and pass parameters explicitly.

**Tasks**:
1. Update all function calls to pass `config_dir` explicitly:
   - `sweep.py`: Update calls to `setup_hpo_mlflow_run()`, `commit_run_name_version()`, etc.
   - `refit.py`: Update calls to `build_output_path()`, `build_mlflow_run_name()`, etc.
   - `cv.py`: Update calls to `build_output_path()`, `_create_trial_run()`, etc.
2. Replace duplicate patterns with consolidated utilities:
   - Use `resolve_project_paths_with_fallback()` instead of inline patterns
   - Use `get_or_compute_study_key_hash()` instead of inline fallback logic
   - Use `get_or_compute_trial_key_hash()` instead of inline fallback logic
3. Verify no regressions:
   - Run tests: `uvx pytest tests/training/hpo/ tests/training/execution/`
   - Check mypy: `uvx mypy src/training/hpo/execution/ src/training/execution/`

**Success Criteria**:
- All call sites updated
- No duplicate patterns remain
- All tests pass
- Mypy is clean

**Files to Modify**:
- `src/training/hpo/execution/local/sweep.py`
- `src/training/hpo/execution/local/refit.py`
- `src/training/hpo/execution/local/cv.py`
- `src/training/hpo/tracking/setup.py`
- Any other files with duplicate patterns

### Step 8: Verify Tests Pass and Mypy is Clean

**Goal**: Ensure no regressions introduced by consolidation.

**Tasks**:
1. Run all relevant tests:
   ```bash
   uvx pytest tests/training/hpo/ tests/training/execution/ tests/infrastructure/paths/ tests/infrastructure/tracking/mlflow/
   ```
2. Run mypy on modified files:
   ```bash
   uvx mypy src/training/hpo/execution/ src/training/execution/ src/infrastructure/paths/ src/infrastructure/tracking/mlflow/hash_utils.py
   ```
3. Fix any test failures or mypy errors
4. Document any pre-existing failures (if any)

**Success Criteria**:
- All tests pass (or pre-existing failures documented)
- Mypy is clean (no new errors)
- No regressions introduced

### Step 9: Document Consolidation Patterns

**Goal**: Document the consolidation patterns for future reference.

**Tasks**:
1. Update `docs/implementation_plans/complete/` with summary document
2. Document:
   - Trust principle for `config_dir` parameter
   - SSOT utilities and when to use them
   - Common patterns and their consolidated versions
   - Migration guide for future scripts
3. Add examples to docstrings of consolidated utilities

**Success Criteria**:
- Summary document created
- Patterns documented with examples
- Migration guide available

## Success Criteria (Overall)

- ✅ All HPO and training scripts use SSOT utilities
- ✅ No duplicate `config_dir` inference when parameter is provided
- ✅ No duplicate path resolution patterns
- ✅ No duplicate hash computation patterns
- ✅ All tests pass
- ✅ Mypy is clean
- ✅ Consolidation patterns documented

## Notes

### Relationship to Other Plans

- **`20260117-2350-consolidate-utility-scripts-dry-violations-unified.plan.md`** (✅ Completed): 
  - This plan addressed utility-level consolidation (functions with `type: utility` or `type: config`)
  - Established SSOT patterns for `config_dir` inference, path resolution, MLflow setup, etc.
  - **This current plan applies those SSOT patterns specifically to execution scripts** (`type: script` entry points)
  
- **`FINISHED-20260117-2300-workflow-patterns-unified-comprehensive.plan.md`** (✅ Completed):
  - This plan standardized workflow function signatures and patterns
  - Established standard parameter patterns (`backup_enabled`, `backup_to_drive`, `platform`, etc.)
  - Established logging patterns (`logger` from `get_logger(__name__)`)
  - Established MLflow setup patterns (`setup_mlflow()` SSOT)
  - **This current plan ensures execution scripts follow these workflow patterns**

- **Other Related Plans**:
  - `FINISHED-20260117-2000-consolidate-drive-backup-scripts-dry-violations.plan.md` (✅ Completed) - Backup consolidation
  - `FINISHED-20260117-1910-centralize-incremental-study-db-backup-569526b.plan.md` (✅ Completed) - Study DB backup
  - `FINISHED-20260117-1630-fix-study-db-drive-backup-issue.plan.md` (✅ Completed) - Study DB backup fix
  - `FINISHED-20250120-0000-consolidate-dry-violations-from-readme-analysis.plan.md` (✅ Completed) - Early DRY consolidation from README analysis
  - `FINISHED-20260117-2100-remove-notebook-fallbacks-redundancy.plan.md` (✅ Completed) - Notebook fallback removal
  - `FINISHED-20260117-1544-migrate-resolve-storage-path-to-v2-hash-based.plan.md` (✅ Completed) - Storage path migration

**Note on Master Plan**: The utility consolidation plan references `MASTER-20260117-2349-combined-workflow-utility-consolidation.plan.md`, but this master plan does not exist in the current worktree. This may be in another worktree or may not have been created yet. The current plan coordinates with all available related plans in this worktree.

### Key Differences from Utility Plan

- **Scope**: This plan focuses on **execution scripts** (entry points), not utility functions
- **Focus**: HPO and training execution scripts specifically (`sweep.py`, `trial.py`, `refit.py`, `cv.py`, `train.py`, `orchestrator.py`, `executor.py`)
- **Pattern**: Applies SSOT patterns established in utility plan to execution scripts
- **Status**: This plan is **pending** (utility plan is completed)

### Consolidation Principles

- The consolidation approach prioritizes **minimizing breaking changes** by keeping function signatures compatible.
- The **trust principle** for `config_dir` is critical: if a function receives `config_dir`, it should trust it and not re-infer it.
- Some duplication may be acceptable if it improves readability or is domain-specific (e.g., HPO-specific vs training-specific logic).
- **Reuse-first**: Use SSOT utilities established in the utility consolidation plan rather than creating new ones.


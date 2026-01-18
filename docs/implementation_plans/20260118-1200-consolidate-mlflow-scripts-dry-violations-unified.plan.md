# Consolidate MLflow Scripts - DRY Violations (Unified Plan)

> **Note**: This is a **comprehensive unified plan** combining insights from multiple worktrees. This plan focuses on **MLflow infrastructure modules** (`infrastructure.tracking.mlflow.*`, `training.hpo.tracking.*`), while the HPO plan (`20260118-0000-consolidate-hpo-training-scripts-dry-violations.plan.md`) focuses on **execution scripts** (`training.hpo.execution.local.*`). Both plans must be executed together as they address different layers of the same issues.

## Goal

Eliminate DRY violations across all MLflow-related utility scripts by consolidating overlapping responsibilities, duplicated logic, and near-duplicate patterns into a unified, reusable architecture that follows reuse-first principles and minimizes breaking changes.

This plan specifically addresses:
- Duplicate `config_dir` inference (especially in `setup_hpo_mlflow_run()`)
- Inconsistent path resolution patterns across workflows
- Near-duplicate hash computation and retrieval patterns
- Inconsistent usage of centralized utilities
- MLflow setup pattern inconsistencies
- Deprecated wrapper modules

## Status

**Last Updated**: 2026-01-18  
**Combined from**: Multiple worktree plans (JFgGj, f5gCR, kO9Gn, X58hU, 5Nlzm)

### Completed Steps
- ✅ Step 0: Comprehensive inventory and analysis of MLflow-related scripts
- ✅ Step 1: Remove redundant path inference from `setup_hpo_mlflow_run()` (coordinate with HPO Plan Step 3)
- ✅ Step 2: Consolidate hash computation fallback in `setup_hpo_mlflow_run()`
- ✅ Step 3: Audit and standardize path resolution in execution scripts
- ✅ Step 4: Audit and standardize hash retrieval in execution scripts
- ✅ Step 5: Document MLflow setup layering
- ✅ Step 6: Remove deprecated wrapper (`orchestration/jobs/hpo/local/mlflow/run_setup.py`)

### Pending Steps
- ✅ Step 7: Verify tests and type checking
- ✅ Step 8: Document consolidation patterns

## Relationship to Other Plans

### ⚠️ CRITICAL: Coordinate with HPO/Training Scripts Consolidation
**Plan**: `20260118-0000-consolidate-hpo-training-scripts-dry-violations.plan.md`

**Overlap**: Both plans address `setup_hpo_mlflow_run()` `config_dir` re-inference:
- **HPO Plan Category 1** (line 132-167): Identifies issue from execution script perspective (`sweep.py` passes `project_config_dir` but `setup_hpo_mlflow_run()` still re-infers)
- **This Plan Step 1**: Fixes `setup_hpo_mlflow_run()` itself to trust provided `config_dir`

**Coordination Strategy**:
- **HPO Plan Step 3**: Updates execution scripts (`sweep.py`, `cv.py`, `refit.py`) to pass `config_dir` explicitly
- **This Plan Step 1**: Fixes `setup_hpo_mlflow_run()` in `training.hpo.tracking.setup` to trust provided `config_dir`

**Action**: Execute **Step 1 of this plan** together with **Step 3 of HPO plan** - both are required for the fix to work correctly.

### ✅ Completed: Utility Script Consolidation
**Plan**: `FINISHED-20260117-2350-consolidate-utility-scripts-dry-violations-unified.plan.md` (✅ Completed)

- **Established SSOT patterns**: Path resolution (`resolve_project_paths_with_fallback()`), `config_dir` trust principle
- **This plan**: Ensures MLflow modules use these SSOT patterns correctly

### ✅ Completed: Workflow Patterns Standardization
**Plan**: `FINISHED-20260117-2300-workflow-patterns-unified-comprehensive.plan.md` (✅ Completed)

- **Established patterns**: MLflow setup consistency (`infrastructure.tracking.mlflow.setup.setup_mlflow()` SSOT)
- **This plan**: Verifies MLflow modules follow these workflow patterns

## Preconditions

- ✅ Existing `infrastructure.paths.utils.resolve_project_paths_with_fallback()` function (SSOT for path resolution)
- ✅ Existing `infrastructure.tracking.mlflow.setup.setup_mlflow()` function (SSOT for MLflow setup)
- ✅ Existing `infrastructure.tracking.mlflow.hash_utils` functions (SSOT for hash computation)
- All scripts have proper metadata blocks (`@meta`)
- Tests exist for utility functions
- Mypy is configured and passing

## MLflow Scripts Inventory

### 1. MLflow Setup & Configuration Scripts (SSOT Layer)

| File | Purpose | Key Functions | Notes |
|------|---------|---------------|-------|
| `src/infrastructure/tracking/mlflow/setup.py` | **SSOT for MLflow experiment setup** | `setup_mlflow()`, `_ensure_azureml_compatibility()`, `_set_azureml_artifact_timeout()` | Primary setup function, wraps cross-platform setup |
| `src/common/shared/mlflow_setup.py` | Cross-platform MLflow setup utilities | `setup_mlflow_cross_platform()`, `create_ml_client_from_config()`, `setup_mlflow_from_config()` | Low-level Azure ML and local tracking setup |

**Key Responsibilities:**
- MLflow experiment configuration (`setup_mlflow()` - SSOT)
- Cross-platform tracking URI setup (Azure ML vs local)
- Azure ML compatibility and fallbacks

### 2. MLflow Hash Utilities (SSOT Layer)

| File | Purpose | Key Functions | Notes |
|------|---------|---------------|-------|
| `src/infrastructure/tracking/mlflow/hash_utils.py` | **SSOT for hash retrieval and computation** | `get_or_compute_study_key_hash()`, `get_or_compute_trial_key_hash()`, `compute_study_key_hash_v2()`, `get_study_key_hash_from_run()` | Centralized hash utilities with fallback hierarchy |

**Key Responsibilities:**
- Hash retrieval from MLflow run tags (SSOT)
- Hash computation from configs (fallback)
- Fallback hierarchy: provided → tags → compute

### 3. MLflow Run Creation & Lifecycle (SSOT Layer)

| File | Purpose | Key Functions | Notes |
|------|---------|---------------|-------|
| `src/infrastructure/tracking/mlflow/runs.py` | **SSOT for MLflow run creation** | `create_child_run_core()`, `get_or_create_experiment()`, `resolve_experiment_id()` | Core run creation logic |
| `src/infrastructure/tracking/mlflow/utils.py` | Retry logic and run ID utilities | `retry_with_backoff()`, `get_mlflow_run_id()` | Utility functions |
| `src/infrastructure/tracking/mlflow/queries.py` | MLflow query patterns | `query_runs_by_tags()`, `find_best_run_by_metric()` | Query utilities |

### 4. Training/HPO-Specific MLflow Modules (Domain Layer)

| File | Purpose | Key Functions | Notes |
|------|---------|---------------|-------|
| `src/training/hpo/tracking/setup.py` | HPO-specific MLflow run setup | `setup_hpo_mlflow_run()`, `commit_run_name_version()` | HPO-specific run name/context creation (no setup) |
| `src/training/execution/mlflow_setup.py` | Training execution MLflow run creation | `create_training_mlflow_run()`, `setup_mlflow_tracking_env()`, `create_training_child_run()` | Training run lifecycle management |
| `src/training/hpo/tracking/cleanup.py` | Interrupted run cleanup | `cleanup_interrupted_runs()`, `should_skip_cleanup()` | Cleanup utilities |

### 5. Path Resolution Utilities (SSOT Layer)

| File | Purpose | Key Functions | Notes |
|------|---------|---------------|-------|
| `src/infrastructure/paths/utils.py` | **SSOT for path resolution** | `resolve_project_paths_with_fallback()`, `resolve_project_paths()`, `infer_config_dir()` | Trust provided `config_dir` parameter (DRY principle) |

### 6. HPO Execution Scripts Using MLflow (Execution Layer)

| File | Purpose | Key MLflow Usage | Notes |
|------|---------|------------------|-------|
| `src/training/hpo/execution/local/sweep.py` | Run local HPO sweeps | Uses `setup_hpo_mlflow_run()`, computes `study_key_hash` early, has `project_config_dir` | Passes `project_config_dir` to avoid re-inference |
| `src/training/hpo/execution/local/cv.py` | Orchestrate k-fold CV for HPO trials | Uses MLflow for trial and fold runs | Creates nested run structure |
| `src/training/hpo/execution/local/refit.py` | Execute refit training | Uses MLflow for refit runs | Creates child runs |
| `src/orchestration/jobs/hpo/local/mlflow/run_setup.py` | Backward compatibility wrapper | Re-exports from `training.hpo.tracking.setup` | **Deprecated**, should use direct import |

## DRY Violations Identified

### Category 1: Path Inference Duplication

**Problem**: Multiple functions re-infer `config_dir` even when it's already available from callers, violating the DRY principle and the "trust provided parameter" pattern.

#### Violation 1.1: `setup_hpo_mlflow_run()` Re-infers `config_dir`

**Location**: `src/training/hpo/tracking/setup.py:86-88, 162-165, 192-194`

**Issue**: The function has logic to infer `config_dir` in multiple places even though callers (e.g., `sweep.py` line 806) already provide `project_config_dir`.

**Current Pattern**:
```python
# setup_hpo_mlflow_run() line 86-88
if config_dir is None:
    from infrastructure.paths.utils import resolve_project_paths_with_fallback
    _, config_dir = resolve_project_paths_with_fallback(output_dir=output_dir, config_dir=None)

# setup_hpo_mlflow_run() line 162-165
from infrastructure.paths.utils import resolve_project_paths_with_fallback
root_dir, config_dir = resolve_project_paths_with_fallback(
    output_dir=output_dir,
    config_dir=config_dir,  # Trust provided config_dir if not None
)

# setup_hpo_mlflow_run() line 192-194 (fallback path)
if config_dir is None:
    from infrastructure.paths.utils import infer_config_dir
    config_dir = infer_config_dir()
```

**Caller Pattern** (from `sweep.py`):
```python
# sweep.py line 630
project_config_dir = config_dir

# sweep.py line 806
hpo_parent_context, mlflow_run_name = setup_hpo_mlflow_run(
    # ...
    config_dir=project_config_dir,  # Pass project config_dir to avoid re-inference (DRY)
)
```

**Root Cause**: The function already uses `resolve_project_paths_with_fallback()` which trusts provided `config_dir`, but there's redundant inference logic at line 86-88 before that check.

**Impact**: 
- Redundant path resolution (performs same inference twice)
- Potential inconsistency if inference paths differ
- Performance overhead (unnecessary file system operations)

#### Violation 1.2: Inconsistent Path Resolution Across Workflows

**Location**: Multiple execution scripts (`sweep.py`, `cv.py`, `refit.py`)

**Issue**: Different scripts use different patterns for resolving paths:
- Some use `resolve_project_paths_with_fallback()` directly
- Some manually infer using `infer_config_dir()`
- Some pass `config_dir` explicitly, others don't

**Examples**:
- `sweep.py` line 714-719: Uses `resolve_project_paths_with_fallback()` with `project_config_dir`
- `sweep.py` line 690-695: Uses `resolve_project_paths()` with `project_config_dir`
- `cv.py` lines 171-173, 244-246: Multiple resolutions within same function

**Root Cause**: Lack of consistent pattern enforcement across execution scripts.

### Category 2: Hash Computation Duplication

**Problem**: Hash computation logic appears in multiple places, with some scripts computing hashes manually instead of using centralized utilities.

#### Violation 2.1: `setup_hpo_mlflow_run()` Has Legacy Hash Computation

**Location**: `src/training/hpo/tracking/setup.py:78-108`

**Issue**: `setup_hpo_mlflow_run()` has its own hash computation logic (using legacy `build_hpo_study_key()` v1) as a fallback, which duplicates patterns from centralized utilities.

**Current Pattern**:
```python
# setup_hpo_mlflow_run() line 78-98
if study_key_hash is None and data_config and hpo_config:
    try:
        from infrastructure.naming.mlflow.hpo_keys import (
            build_hpo_study_key,
            build_hpo_study_key_hash,
        )
        # ... infers config_dir again ...
        if config_dir is None:
            from infrastructure.paths.utils import resolve_project_paths_with_fallback
            _, config_dir = resolve_project_paths_with_fallback(output_dir=output_dir, config_dir=None)
        
        study_key = build_hpo_study_key(
            data_config=data_config,
            hpo_config=hpo_config,
            model=backbone,
            benchmark_config=benchmark_config,
        )
        study_key_hash = build_hpo_study_key_hash(study_key)
```

**Issue**: This uses v1 hash computation (legacy `build_hpo_study_key()`) instead of v2 (`compute_study_key_hash_v2()`), and re-infers `config_dir` instead of trusting the parameter.

**Root Cause**: Fallback logic predates centralized hash utilities.

#### Violation 2.2: Inconsistent Hash Retrieval Patterns

**Location**: Multiple execution scripts (`cv.py`, `refit.py`, selection workflows)

**Issue**: Some scripts manually retrieve hashes from MLflow runs instead of using centralized `get_or_compute_study_key_hash()` utility.

**Current Pattern** (inconsistent):
- Some scripts use `infrastructure.tracking.mlflow.hash_utils.get_or_compute_study_key_hash()`
- Others manually call `MlflowClient().get_run()` and extract tags
- Others compute hashes manually

**Root Cause**: Centralized utilities exist but aren't consistently used.

### Category 3: MLflow Setup Pattern Inconsistency

**Problem**: Different modules handle MLflow setup differently, with some scripts calling setup directly and others assuming it's already configured.

#### Violation 3.1: `setup_hpo_mlflow_run()` Assumes MLflow Already Configured

**Location**: `src/training/hpo/tracking/setup.py:30-232`

**Issue**: `setup_hpo_mlflow_run()` creates naming context and run names but doesn't set up MLflow tracking URI/experiment. It assumes `infrastructure.tracking.mlflow.setup.setup_mlflow()` was called first.

**Current Pattern**: Documented in docstring but not enforced:
```python
"""
**Layering**:
- MLflow setup/configuration is handled by `infrastructure.tracking.mlflow.setup.setup_mlflow()`
  (SSOT). HPO orchestrators should call this before using functions in this module.
"""
```

**Issue**: Some callers may forget to call `setup_mlflow()` first, leading to errors.

**Root Cause**: Separation of concerns (setup vs. run creation) but unclear in practice.

### Category 4: Deprecated Wrapper Module

**Problem**: Backward compatibility wrapper that should be removed.

#### Violation 4.1: `orchestration/jobs/hpo/local/mlflow/run_setup.py` is Deprecated

**Location**: `src/orchestration/jobs/hpo/local/mlflow/run_setup.py`

**Issue**: This module is a backward compatibility wrapper that re-exports from `training.hpo.tracking.setup`. Should be removed in favor of direct imports.

**Root Cause**: Module migration left behind wrapper for compatibility.

## Consolidation Approach

### Principle 1: Reuse-First

- **Extend existing modules** rather than creating new ones
- **Use SSOT functions** (`infrastructure.tracking.mlflow.setup.setup_mlflow()`, `infrastructure.paths.utils.resolve_project_paths_with_fallback()`, `infrastructure.tracking.mlflow.hash_utils`)
- **Trust provided parameters** (e.g., `config_dir`) to avoid re-inference

### Principle 2: SRP Pragmatically

- Keep separation of concerns but reduce duplication:
  - `infrastructure.tracking.mlflow.setup.setup_mlflow()` - MLflow experiment setup (SSOT)
  - `training.hpo.tracking.setup.setup_hpo_mlflow_run()` - HPO-specific run name/context creation (no setup)
  - `training.execution.mlflow_setup.create_training_mlflow_run()` - Training run creation (no setup)
- **Remove redundant inference logic** from `setup_hpo_mlflow_run()`
- **Consolidate hash computation fallback** to use centralized utilities

### Principle 3: Minimize Breaking Changes

- **Keep function signatures** (add optional parameters if needed)
- **Maintain backward compatibility** (existing calls continue to work)
- **Update callers incrementally** (prioritize high-impact violations)

## Implementation Steps

### Step 1: Remove Redundant Path Inference from `setup_hpo_mlflow_run()`

**⚠️ COORDINATE WITH HPO PLAN STEP 3**

**Goal**: Eliminate duplicate `config_dir` inference in `setup_hpo_mlflow_run()` by trusting the provided parameter.

**Note**: This complements HPO Plan Step 3 which ensures call sites pass `config_dir` correctly.

**Current Issues**:
- Line 86-88: Redundant inference before `resolve_project_paths_with_fallback()` is called
- Line 192-194: Redundant inference in fallback path

**Changes**:
1. Remove line 86-88 inference logic (trust `resolve_project_paths_with_fallback()` at line 162-165)
2. Update fallback path (line 192-194) to use `resolve_project_paths_with_fallback()` instead of `infer_config_dir()`

**Files to Modify**:
- `src/training/hpo/tracking/setup.py`

**Success Criteria**:
- `setup_hpo_mlflow_run()` only infers `config_dir` via `resolve_project_paths_with_fallback()` (trusts provided parameter)
- No redundant path resolution
- All tests pass: `uvx pytest tests/ -k "setup_hpo_mlflow_run"`

**Coordination**:
- Execute together with **HPO Plan Step 3** (ensures call sites pass `config_dir`)
- Test together to ensure end-to-end fix works

**Verification**:
```bash
# Check that config_dir is not re-inferred when provided
grep -n "if config_dir is None" src/training/hpo/tracking/setup.py
# Should only show inference when config_dir is truly None, not when provided
```

---

### Step 2: Consolidate Hash Computation Fallback in `setup_hpo_mlflow_run()`

**Goal**: Use centralized hash utilities (`compute_study_key_hash_v2()`) instead of legacy v1 computation.

**Current Issues**:
- Line 78-98: Uses legacy `build_hpo_study_key()` v1 instead of v2
- Re-infers `config_dir` instead of trusting parameter

**Changes**:
1. Replace legacy v1 computation with `infrastructure.tracking.mlflow.hash_utils.compute_study_key_hash_v2()`
2. Remove redundant `config_dir` inference (trust provided parameter)
3. Require `train_config` for v2 computation (update function signature if needed)

**Files to Modify**:
- `src/training/hpo/tracking/setup.py`

**Success Criteria**:
- `setup_hpo_mlflow_run()` uses `compute_study_key_hash_v2()` for fallback
- No redundant `config_dir` inference
- All tests pass: `uvx pytest tests/ -k "setup_hpo_mlflow_run"`

**Verification**:
```bash
# Check for legacy hash computation
grep -n "build_hpo_study_key\|build_hpo_study_key_hash" src/training/hpo/tracking/setup.py
# Should not appear (replaced with compute_study_key_hash_v2)
```

---

### Step 3: Audit and Standardize Path Resolution in Execution Scripts

**Goal**: Ensure all execution scripts use consistent path resolution pattern.

**Note**: This step builds on patterns established in `FINISHED-20260117-2350-consolidate-utility-scripts-dry-violations-unified.plan.md`. This step ensures execution scripts use those utilities consistently.

**Tasks**:
1. Audit all execution scripts (`sweep.py`, `cv.py`, `refit.py`, `trial.py`)
2. Identify scripts that manually infer `config_dir` instead of using `resolve_project_paths_with_fallback()`
3. Update scripts to:
   - Use `resolve_project_paths_with_fallback()` consistently
   - Pass `config_dir` explicitly when available (trust provided parameter)
   - Avoid redundant inference

**Files to Audit**:
- `src/training/hpo/execution/local/sweep.py`
- `src/training/hpo/execution/local/cv.py`
- `src/training/hpo/execution/local/refit.py`
- `src/training/hpo/execution/local/trial.py`

**Success Criteria**:
- All execution scripts use `resolve_project_paths_with_fallback()` consistently
- No manual `infer_config_dir()` calls (unless necessary for backward compatibility)
- All tests pass: `uvx pytest tests/`

**Verification**:
```bash
# Check for inconsistent patterns
grep -n "resolve_project_paths\|infer_config_dir" src/training/hpo/execution/local/*.py
# Should show consistent use of resolve_project_paths_with_fallback()
```

---

### Step 4: Audit and Standardize Hash Retrieval in Execution Scripts

**Goal**: Ensure all execution scripts use centralized hash utilities.

**Tasks**:
1. Search for manual MLflow hash retrieval patterns (direct `MlflowClient().get_run()` calls)
2. Replace with `infrastructure.tracking.mlflow.hash_utils.get_or_compute_study_key_hash()` or `get_or_compute_trial_key_hash()`
3. Ensure consistent fallback hierarchy: provided → tags → compute

**Files to Audit**:
- `src/training/hpo/execution/local/cv.py`
- `src/training/hpo/execution/local/refit.py`
- `src/evaluation/selection/artifact_unified/discovery.py`

**Success Criteria**:
- All hash retrieval uses centralized utilities
- No manual `MlflowClient().get_run()` calls for hash extraction
- All tests pass: `uvx pytest tests/`

**Verification**:
```bash
# Check for manual hash retrieval
grep -rn "client\.get_run\|get_run.*tags.*study_key_hash\|get_run.*tags.*trial_key_hash" src/training/hpo/execution/ src/evaluation/selection/
# Should not appear (use centralized utilities instead)
```

---

### Step 5: Document MLflow Setup Layering

**Goal**: Clarify MLflow setup responsibilities and ensure consistent usage.

**Tasks**:
1. Update docstrings in `training.hpo.tracking.setup` and `training.execution.mlflow_setup` to clearly state:
   - MLflow setup (`setup_mlflow()`) must be called first
   - These modules handle run creation/naming, not setup
2. Add runtime checks (optional) to warn if MLflow not configured
3. Update README or architecture docs to document the layering

**Files to Modify**:
- `src/training/hpo/tracking/setup.py`
- `src/training/execution/mlflow_setup.py`
- `docs/architecture/mlflow-layering.md` (create if needed)

**Success Criteria**:
- Clear documentation of MLflow setup layering
- Docstrings updated to state requirements
- Optional runtime warnings if setup not done

---

### Step 6: Remove Deprecated Wrapper (`orchestration/jobs/hpo/local/mlflow/run_setup.py`)

**Goal**: Remove backward compatibility wrapper that re-exports from new location.

**Current Status**: `src/orchestration/jobs/hpo/local/mlflow/run_setup.py` is a backward compatibility wrapper.

**Tasks**:
1. Search for imports from `orchestration.jobs.hpo.local.mlflow.run_setup`
2. Update to import directly from `training.hpo.tracking.setup`
3. Remove wrapper file

**Files to Modify**:
- `src/orchestration/jobs/hpo/local/mlflow/run_setup.py` (delete)
- Any files importing from it

**Success Criteria**:
- No imports from deprecated wrapper
- Wrapper file removed
- All tests pass: `uvx pytest tests/`

**Verification**:
```bash
# Check for imports from deprecated wrapper
grep -rn "from orchestration.jobs.hpo.local.mlflow.run_setup\|from orchestration.jobs.hpo.local.mlflow import run_setup" src/ tests/
# Should not appear
```

---

### Step 7: Verify Tests and Type Checking

**Goal**: Ensure all changes maintain test coverage and type safety.

**Tasks**:
1. Run all MLflow-related tests: `uvx pytest tests/ -k "mlflow"`
2. Run mypy on modified files: `uvx mypy src/training/hpo/tracking/setup.py src/infrastructure/tracking/mlflow/`
3. Fix any type errors or test failures
4. Ensure no regressions in existing functionality

**Success Criteria**:
- All tests pass: `uvx pytest tests/`
- Mypy passes: `uvx mypy src --show-error-codes`
- No type errors in modified files

**Verification**:
```bash
# Run tests
uvx pytest tests/training/hpo/tracking/ -v
uvx pytest tests/tracking/ -v

# Run mypy
uvx mypy src/training/hpo/tracking/ src/infrastructure/tracking/mlflow/ --show-error-codes
```

---

### Step 8: Document Consolidation Patterns

**Goal**: Document the consolidated patterns for future reference.

**Tasks**:
1. Create or update `docs/architecture/mlflow-utilities.md` with:
   - SSOT functions and their responsibilities
   - Path resolution pattern (trust provided `config_dir`)
   - Hash computation pattern (use centralized utilities)
   - MLflow setup layering
2. Update README files if needed

**Files to Create/Modify**:
- `docs/architecture/mlflow-utilities.md` (create)

**Success Criteria**:
- Documentation created explaining consolidated patterns
- Examples provided for common use cases

---

## Success Criteria (Overall)

- ✅ No redundant `config_dir` inference (trust provided parameter pattern enforced)
- ✅ All hash computation uses centralized utilities (`hash_utils.py`)
- ✅ All path resolution uses `resolve_project_paths_with_fallback()`
- ✅ MLflow setup layering clearly documented and enforced
- ✅ All execution scripts use consistent patterns
- ✅ All tests pass: `uvx pytest tests/`
- ✅ Mypy passes: `uvx mypy src --show-error-codes`
- ✅ Deprecated wrapper removed
- ✅ Documentation updated with consolidation patterns
- ✅ Coordination with HPO plan verified

## Notes

- **Prioritization**: Start with Step 1 (highest impact, removes most duplication)
- **Coordination**: Step 1 must be executed together with HPO Plan Step 3
- **Testing**: After each step, run tests to ensure no regressions
- **Breaking Changes**: Minimize by keeping function signatures compatible
- **Incremental**: Update callers incrementally rather than all at once

## References

### Related Plans
- **HPO/Training Scripts Consolidation**: `20260118-0000-consolidate-hpo-training-scripts-dry-violations.plan.md` (execution scripts focus)
- **Utility Scripts Consolidation**: `FINISHED-20260117-2350-consolidate-utility-scripts-dry-violations-unified.plan.md` (✅ Completed)
- **Workflow Patterns**: `FINISHED-20260117-2300-workflow-patterns-unified-comprehensive.plan.md` (✅ Completed)

### Related Analysis Documents
- **MLflow Scripts Analysis**: `20260118-1200-mlflow-scripts-analysis.md` (complete catalog of MLflow scripts)
- **Plan Comparison**: `20260118-1200-mlflow-consolidation-plan-comparison.md` (comparison of plans from different worktrees)

### SSOT Modules
- `src/infrastructure/tracking/mlflow/setup.py` - MLflow setup SSOT
- `src/infrastructure/tracking/mlflow/runs.py` - MLflow run creation SSOT
- `src/infrastructure/tracking/mlflow/hash_utils.py` - Hash computation SSOT
- `src/infrastructure/paths/utils.py` - Path resolution SSOT


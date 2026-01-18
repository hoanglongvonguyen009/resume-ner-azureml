# Consolidate All Scripts - DRY Violations (Unified Master Plan)

> **Note**: This is a **comprehensive unified master plan** combining insights from **all 6 worktrees** (0wSIE, DKnQn, KqT6o, SU3Tr, XCxan, ivCvB) and three related consolidation plans:
> - **MLflow Scripts Consolidation** (`20260118-1200-consolidate-mlflow-scripts-dry-violations-unified.plan.md`) - found in all 6 worktrees
> - **Path/Naming Scripts Consolidation** - found in multiple worktrees with variations:
>   - `20260118-0055-consolidate-path-naming-scripts-dry-violations.plan.md` (SU3Tr - 589 lines, most comprehensive)
>   - `20260118-0055-consolidate-path-naming-utilities-dry-violations.plan.md` (0wSIE - 489 lines)
>   - `20260118-1400-consolidate-path-naming-scripts-dry-violations.plan.md` (DKnQn, KqT6o, XCxan - 349-504 lines)
>   - `20260118-1400-consolidate-path-naming-utilities-dry-violations.plan.md` (ivCvB - 485 lines)
> - **HPO/Training Scripts Consolidation** (`FINISED-20260118-0000-consolidate-hpo-training-scripts-dry-violations.plan.md`) - found in all 6 worktrees
>
> **Unique contributions from worktrees**:
> - **SU3Tr**: Additional steps for `cleanup_interrupted_runs()` and standardizing on `resolve_project_paths_with_fallback()`
> - **All worktrees**: Variations and refinements of the same core consolidation themes
>
> This master plan addresses DRY violations across **all layers**: infrastructure utilities, MLflow modules, path/naming utilities, and execution scripts.

## Goal

Eliminate DRY violations across **all utility and execution scripts** by consolidating overlapping responsibilities, duplicated logic, and near-duplicate patterns into a unified, reusable architecture that follows reuse-first principles and minimizes breaking changes.

This plan specifically addresses:
- Duplicate `config_dir` inference (especially in `setup_hpo_mlflow_run()` and other modules)
- Inconsistent path resolution patterns across all workflows
- Near-duplicate hash computation and retrieval patterns
- Inconsistent usage of centralized utilities
- MLflow setup pattern inconsistencies
- Naming fallback logic duplication
- Deprecated wrapper modules

## Status

**Last Updated**: 2026-01-18  
**Combined from**: Multiple worktree plans (0wSIE, DKnQn, KqT6o, SU3Tr, XCxan, ivCvB) and three related consolidation plans

### Completed Steps
- ✅ Step 0: Comprehensive inventory and analysis of all scripts across all layers
- ✅ Step 1: Fix `setup_hpo_mlflow_run()` to trust provided `config_dir` parameter (MLflow + Path/Naming)
- ✅ Step 2: Consolidate hash computation fallback in `setup_hpo_mlflow_run()` (MLflow)
- ✅ Step 3: Audit and standardize path resolution in all execution scripts (HPO/Training + Path/Naming)
- ✅ Step 4: Audit and standardize hash retrieval in all execution scripts (HPO/Training + MLflow)
- ✅ Step 5: Consolidate `config_dir` inference patterns in naming modules (Path/Naming)
- ✅ Step 6: Consolidate hash extraction patterns in evaluation modules (Path/Naming)
- ✅ Step 7: Consolidate naming fallback logic (Path/Naming)
- ✅ Step 8: Update `cleanup_interrupted_runs()` to trust provided `config_dir` (Path/Naming - from SU3Tr)
- ✅ Step 9: Standardize on `resolve_project_paths_with_fallback()` (Replace `resolve_project_paths()`) (Path/Naming - from SU3Tr)

### Completed Steps (Continued)
- ✅ Step 10: Document MLflow setup layering (MLflow)
- ✅ Step 11: Remove deprecated wrapper modules (MLflow)
- ✅ Step 12: Verify tests and type checking (All)

### Pending Steps
- ⏳ Step 13: Document consolidation patterns (All)

## Relationship to Other Plans

### ✅ Completed: Utility Script Consolidation
**Plan**: `FINISHED-20260117-2350-consolidate-utility-scripts-dry-violations-unified.plan.md` (✅ Completed)

- **Established SSOT patterns**: Path resolution (`resolve_project_paths_with_fallback()`), `config_dir` trust principle
- **This plan**: Ensures all modules (MLflow, path/naming, execution) use these SSOT patterns correctly

### ✅ Completed: Workflow Patterns Standardization
**Plan**: `FINISHED-20260117-2300-workflow-patterns-unified-comprehensive.plan.md` (✅ Completed)

- **Established patterns**: MLflow setup consistency (`infrastructure.tracking.mlflow.setup.setup_mlflow()` SSOT)
- **This plan**: Verifies all modules follow these workflow patterns

### ⚠️ CRITICAL: Coordinate with Related Plans
**Plans**: 
- `20260118-1200-consolidate-mlflow-scripts-dry-violations-unified.plan.md` (MLflow focus)
- `20260118-1400-consolidate-path-naming-scripts-dry-violations.plan.md` (Path/Naming focus)
- `FINISED-20260118-0000-consolidate-hpo-training-scripts-dry-violations.plan.md` (Execution scripts focus)

**Overlap**: All three plans address `setup_hpo_mlflow_run()` `config_dir` re-inference from different perspectives:
- **MLflow Plan Step 1**: Fixes `setup_hpo_mlflow_run()` itself to trust provided `config_dir`
- **Path/Naming Plan Step 1**: Also fixes `setup_hpo_mlflow_run()` to trust provided `config_dir`
- **HPO Plan Step 3**: Updates execution scripts to pass `config_dir` explicitly

**Action**: Execute **Step 1 of this master plan** which combines all three approaches - fixes `setup_hpo_mlflow_run()` AND ensures execution scripts pass `config_dir` correctly.

## Preconditions

- ✅ Existing `infrastructure.paths.utils.resolve_project_paths_with_fallback()` function (SSOT for path resolution)
- ✅ Existing `infrastructure.paths.repo.detect_repo_root()` function (SSOT for repository root detection)
- ✅ Existing `infrastructure.tracking.mlflow.setup.setup_mlflow()` function (SSOT for MLflow setup)
- ✅ Existing `infrastructure.tracking.mlflow.hash_utils` functions (SSOT for hash computation)
- ✅ Existing `infrastructure.naming.mlflow.run_names.build_mlflow_run_name()` function (SSOT for systematic naming)
- All scripts have proper metadata blocks (`@meta`)
- Tests exist for utility functions
- Mypy is configured and passing

## Comprehensive Scripts Inventory

### 1. Path Resolution Utilities (SSOT Layer)

| File | Purpose | Key Functions | Notes |
|------|---------|---------------|-------|
| `src/infrastructure/paths/utils.py` | **SSOT for path resolution** | `infer_config_dir()`, `resolve_project_paths()`, `resolve_project_paths_with_fallback()` | Primary path resolution utilities, trusts provided `config_dir` |
| `src/infrastructure/paths/repo.py` | **SSOT for repository root detection** | `detect_repo_root()`, `validate_repo_root()` | Unified repository root detection with configurable search strategies |
| `src/infrastructure/paths/resolve.py` | **SSOT for output path building** | `build_output_path()`, `resolve_output_path()` | Builds output paths from naming contexts using patterns from `config/paths.yaml` |
| `src/training/hpo/utils/paths.py` | HPO-specific path resolution | `resolve_hpo_output_dir()` | Google Drive path mapping in Colab (domain-specific, not duplicate) |

### 2. Naming Utilities (SSOT Layer)

| File | Purpose | Key Functions | Notes |
|------|---------|---------------|-------|
| `src/infrastructure/naming/mlflow/run_names.py` | **SSOT for systematic MLflow run naming** | `build_mlflow_run_name()`, `_build_legacy_run_name()` | Primary MLflow run name generation |
| `src/infrastructure/naming/mlflow/config.py` | **SSOT for MLflow config loading** | `load_mlflow_config()`, `get_naming_config()` | Loads MLflow configuration from YAML with caching |
| `src/infrastructure/naming/display_policy.py` | **SSOT for display name formatting** | `format_run_name()`, `load_naming_policy()` | Formats display names using policy patterns |
| `src/infrastructure/naming/experiments.py` | **SSOT for experiment name building** | `build_mlflow_experiment_name()`, `build_aml_experiment_name()` | Builds experiment names for MLflow and AzureML |
| `src/training/execution/run_names.py` | Training run name building with fallback | `build_training_run_name_with_fallback()`, `_try_systematic_naming()` | Uses infrastructure naming as primary, fallback for training-specific cases |
| `src/training/hpo/utils/helpers.py` | HPO helper functions | `create_study_name()`, `create_mlflow_run_name()` | Legacy fallback naming (deprecated, kept for backward compatibility) |

### 3. MLflow Setup & Configuration Scripts (SSOT Layer)

| File | Purpose | Key Functions | Notes |
|------|---------|---------------|-------|
| `src/infrastructure/tracking/mlflow/setup.py` | **SSOT for MLflow experiment setup** | `setup_mlflow()`, `_ensure_azureml_compatibility()`, `_set_azureml_artifact_timeout()` | Primary setup function, wraps cross-platform setup |
| `src/common/shared/mlflow_setup.py` | Cross-platform MLflow setup utilities | `setup_mlflow_cross_platform()`, `create_ml_client_from_config()`, `setup_mlflow_from_config()` | Low-level Azure ML and local tracking setup |
| `src/infrastructure/tracking/mlflow/hash_utils.py` | **SSOT for hash retrieval and computation** | `get_or_compute_study_key_hash()`, `get_or_compute_trial_key_hash()`, `compute_study_key_hash_v2()`, `get_study_key_hash_from_run()` | Centralized hash utilities with fallback hierarchy |
| `src/infrastructure/tracking/mlflow/runs.py` | **SSOT for MLflow run creation** | `create_child_run_core()`, `get_or_create_experiment()`, `resolve_experiment_id()` | Core run creation logic |
| `src/training/hpo/tracking/setup.py` | HPO-specific MLflow run setup | `setup_hpo_mlflow_run()`, `commit_run_name_version()` | **ISSUE**: Re-infers `config_dir` even when provided (DRY violation) |

### 4. Execution Scripts (Orchestration Layer)

| File | Purpose | Key Functions | Notes |
|------|---------|---------------|-------|
| `src/training/hpo/execution/local/sweep.py` | Run local HPO sweeps | `run_local_sweep()` | **ISSUE**: Has `project_config_dir` (line 608) but `setup_hpo_mlflow_run()` re-infers instead of using it |
| `src/training/hpo/execution/local/cv.py` | Orchestrate k-fold CV for HPO trials | `run_training_trial_with_cv()` | Uses `resolve_project_paths_with_fallback()` correctly |
| `src/training/hpo/execution/local/refit.py` | Execute refit training | `run_refit_training()` | Uses `resolve_project_paths_with_fallback()` correctly |
| `src/training/hpo/execution/local/trial.py` | Execute single HPO trial | `run_training_trial()`, `TrialExecutor` | Uses `detect_repo_root()` correctly |

### 5. Evaluation/Selection Modules

| File | Purpose | Key Functions | Notes |
|------|---------|---------------|-------|
| `src/evaluation/selection/trial_finder.py` | Trial finding and hash extraction | `_extract_hashes_from_trial_dir()`, `format_trial_identifier()` | **ISSUE**: Duplicates hash extraction patterns from SSOT |
| `src/evaluation/selection/study_summary.py` | Study summary and hash info | `get_trial_hash_info()`, `find_trial_hash_info_for_study()` | **ISSUE**: Duplicates hash extraction patterns from SSOT |

### 6. Backward Compatibility Wrappers

| File | Purpose | Key Functions | Notes |
|------|---------|---------------|-------|
| `src/orchestration/jobs/hpo/local/mlflow/run_setup.py` | Backward compatibility wrapper | Re-exports from `training.hpo.tracking.setup` | **DEPRECATED**, should use direct import |
| `src/common/shared/notebook_setup.py` | Notebook setup utilities | `find_repository_root()` | **DEPRECATED**: Wrapper for `detect_repo_root()`, kept for backward compatibility |

## DRY Violations Identified (Unified)

### Category 1: Path Resolution Duplication

#### Violation 1.1: `setup_hpo_mlflow_run()` Re-infers `config_dir`
**Location**: `src/training/hpo/tracking/setup.py:188-195, 221-225, 300-307`

**Issue**: Function accepts `config_dir` parameter but re-infers it using `resolve_project_paths_with_fallback()` even when provided.

**Root Cause**: The function doesn't trust the provided `config_dir` parameter completely.

**Impact**: Unnecessary path inference, potential inconsistencies, performance overhead.

**Solution**: Trust provided `config_dir` completely. Only infer when `config_dir` is `None`.

#### Violation 1.2: `sweep.py` Has `project_config_dir` But It's Re-inferred
**Location**: `src/training/hpo/execution/local/sweep.py:636, 812`

**Issue**: `run_local_sweep()` stores `project_config_dir = config_dir` at line 636, but when calling `setup_hpo_mlflow_run()` at line 812, the function re-infers `config_dir` instead of using the provided value.

**Root Cause**: `setup_hpo_mlflow_run()` doesn't fully trust the provided `config_dir` parameter.

**Solution**: Fix `setup_hpo_mlflow_run()` to trust provided `config_dir` (see Violation 1.1 solution).

#### Violation 1.3: `load_mlflow_config()` Re-infers `config_dir`
**Location**: `src/infrastructure/naming/mlflow/config.py:55-61`

**Issue**: Function has fallback logic to infer `config_dir` even when callers may already have it available.

**Solution**: Trust provided `config_dir` parameter. Only infer when truly None.

### Category 2: Hash Computation/Extraction Duplication

#### Violation 2.1: `setup_hpo_mlflow_run()` Has Legacy Hash Computation
**Location**: `src/training/hpo/tracking/setup.py:78-108`

**Issue**: Uses legacy `build_hpo_study_key()` v1 instead of v2, and re-infers `config_dir` instead of trusting the parameter.

**Solution**: Use `compute_study_key_hash_v2()` from centralized utilities, trust provided `config_dir`.

#### Violation 2.2: `_extract_hashes_from_trial_dir()` Duplicates Hash Extraction
**Location**: `src/evaluation/selection/trial_finder.py:117-138`

**Issue**: Manually extracts hashes from trial metadata files, duplicating patterns from centralized hash utilities.

**Solution**: Use `get_or_compute_study_key_hash()` and `get_or_compute_trial_key_hash()` from centralized utilities.

#### Violation 2.3: `get_trial_hash_info()` Duplicates Hash Extraction
**Location**: `src/evaluation/selection/study_summary.py:65-80`

**Issue**: Manually extracts hash information from trial directories, duplicating patterns from centralized utilities.

**Solution**: Use centralized hash utilities instead of manual extraction.

### Category 3: Naming Fallback Logic Duplication

#### Violation 3.1: `build_training_run_name_with_fallback()` Has Duplicate Fallback Logic
**Location**: `src/training/execution/run_names.py:55-146`

**Issue**: Implements fallback logic that duplicates patterns from centralized naming utilities.

**Solution**: Use `build_mlflow_run_name()` from SSOT as primary, keep fallback only for training-specific cases.

#### Violation 3.2: `create_mlflow_run_name()` Has Legacy Fallback Logic
**Location**: `src/training/hpo/utils/helpers.py:232-274`

**Issue**: Implements legacy fallback logic that duplicates patterns from centralized naming utilities.

**Solution**: Document as deprecated, use `build_mlflow_run_name()` from SSOT.

### Category 4: Deprecated Wrapper Modules

#### Violation 4.1: `orchestration/jobs/hpo/local/mlflow/run_setup.py` is Deprecated
**Location**: `src/orchestration/jobs/hpo/local/mlflow/run_setup.py`

**Issue**: Backward compatibility wrapper that re-exports from `training.hpo.tracking.setup`. Should be removed.

**Solution**: Update all imports to use direct import, remove wrapper file.

## Consolidation Approach

### Principle 1: Reuse-First
- **Extend existing modules** rather than creating new ones
- **Use SSOT functions** (`infrastructure.paths.utils.resolve_project_paths_with_fallback()`, `infrastructure.tracking.mlflow.setup.setup_mlflow()`, `infrastructure.tracking.mlflow.hash_utils`, `infrastructure.naming.mlflow.run_names.build_mlflow_run_name()`)
- **Trust provided parameters** (e.g., `config_dir`) to avoid re-inference

### Principle 2: SRP Pragmatically
- Keep separation of concerns but reduce duplication:
  - Infrastructure layer: SSOT functions
  - Domain layer: Domain-specific helpers (use SSOT when possible)
  - Execution layer: Orchestration scripts (use SSOT utilities)
- **Remove redundant inference logic** from all layers
- **Consolidate hash computation/extraction** to use centralized utilities
- **Consolidate naming fallback** to use centralized utilities

### Principle 3: Minimize Breaking Changes
- **Keep function signatures** (add optional parameters if needed)
- **Maintain backward compatibility** (existing calls continue to work)
- **Update callers incrementally** (prioritize high-impact violations)

## Implementation Steps

### Step 1: Fix `setup_hpo_mlflow_run()` to Trust Provided `config_dir` Parameter

**⚠️ COORDINATES WITH ALL THREE RELATED PLANS**

**Goal**: Eliminate redundant `config_dir` inference in `setup_hpo_mlflow_run()` when `config_dir` is already provided.

**Changes**:
1. Modify `setup_hpo_mlflow_run()` in `src/training/hpo/tracking/setup.py` to trust provided `config_dir` completely
2. Only call `resolve_project_paths_with_fallback()` when `config_dir` is `None`
3. When `config_dir` is provided, derive `root_dir` from it directly using `detect_repo_root(config_dir=config_dir)`
4. Remove redundant inference logic at lines 86-88 and 192-194

**Files to Modify**:
- `src/training/hpo/tracking/setup.py` (lines 86-88, 188-195, 221-225, 300-307)

**Success Criteria**:
- `setup_hpo_mlflow_run()` only infers `config_dir` when it's `None`
- When `config_dir` is provided, it's used directly without re-inference
- `root_dir` is derived from provided `config_dir` using `detect_repo_root(config_dir=config_dir)`
- All existing tests pass
- Mypy passes: `uvx mypy src/training/hpo/tracking/setup.py --show-error-codes`

**Verification**:
```bash
# Check that config_dir is trusted when provided
grep -A 10 "def setup_hpo_mlflow_run" src/training/hpo/tracking/setup.py | grep -E "config_dir|resolve_project_paths"

# Verify tests pass
uvx pytest tests/ -k "setup_hpo_mlflow_run" -v

# Verify type checking
uvx mypy src/training/hpo/tracking/setup.py --show-error-codes
```

---

### Step 2: Consolidate Hash Computation Fallback in `setup_hpo_mlflow_run()`

**Goal**: Use centralized hash utilities (`compute_study_key_hash_v2()`) instead of legacy v1 computation.

**Changes**:
1. Replace legacy v1 computation with `infrastructure.tracking.mlflow.hash_utils.compute_study_key_hash_v2()`
2. Remove redundant `config_dir` inference (trust provided parameter)
3. Require `train_config` for v2 computation (update function signature if needed)

**Files to Modify**:
- `src/training/hpo/tracking/setup.py` (lines 78-108)

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

### Step 3: Audit and Standardize Path Resolution in All Execution Scripts

**Goal**: Ensure all execution scripts use consistent path resolution pattern.

**Tasks**:
1. Audit all execution scripts (`sweep.py`, `cv.py`, `refit.py`, `trial.py`)
2. Verify scripts use `resolve_project_paths_with_fallback()` consistently
3. Verify scripts pass `config_dir` explicitly when available
4. Remove any manual `infer_config_dir()` calls (unless necessary for backward compatibility)

**Files to Audit**:
- `src/training/hpo/execution/local/sweep.py`
- `src/training/hpo/execution/local/cv.py`
- `src/training/hpo/execution/local/refit.py`
- `src/training/hpo/execution/local/trial.py`

**Success Criteria**:
- All execution scripts use `resolve_project_paths_with_fallback()` consistently
- All calls to `setup_hpo_mlflow_run()` pass `config_dir` explicitly when available
- No redundant path inference when `config_dir` is already known
- All tests pass: `uvx pytest tests/`

**Verification**:
```bash
# Check for path resolution patterns
grep -r "resolve_project_paths\|infer_config_dir\|detect_repo_root" src/training/hpo/execution/local/

# Check for setup_hpo_mlflow_run calls
grep -r "setup_hpo_mlflow_run" src/training/hpo/execution/local/ -A 5

# Verify tests pass
uvx pytest tests/ -k "hpo.*execution" -v
```

---

### Step 4: Audit and Standardize Hash Retrieval in All Execution Scripts

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

### Step 5: Consolidate `config_dir` Inference Patterns in Naming Modules

**Goal**: Ensure all naming modules trust provided `config_dir` parameter and use SSOT functions consistently.

**Tasks**:
1. Update `load_mlflow_config()` to trust provided `config_dir` parameter
   - Only infer when `config_dir` is None and no other information available
   - Use `resolve_project_paths_with_fallback()` for inference (SSOT)
2. Audit all naming modules for `config_dir` parameter handling
   - Ensure functions accept `config_dir` parameter when path resolution is needed
   - Ensure functions trust provided `config_dir` parameter
3. Update evaluation modules to accept `config_dir` parameter
   - `trial_finder.py`: Add `config_dir` parameter to functions that need path resolution
   - `study_summary.py`: Add `config_dir` parameter to functions that need path resolution

**Files to Modify**:
- `src/infrastructure/naming/mlflow/config.py`
- `src/evaluation/selection/trial_finder.py`
- `src/evaluation/selection/study_summary.py`

**Success Criteria**:
- All naming modules trust provided `config_dir` parameter
- All naming modules use SSOT functions for inference
- No redundant `config_dir` inference
- All tests pass: `uvx pytest tests/`

**Verification**:
```bash
# Check for redundant config_dir inference
grep -rn "if config_dir is None" src/infrastructure/naming/ src/evaluation/selection/
# Should only show inference when config_dir is truly None, not when provided
```

---

### Step 6: Consolidate Hash Extraction Patterns in Evaluation Modules

**Goal**: Ensure all hash extraction uses centralized utilities from `infrastructure.tracking.mlflow.hash_utils`.

**Tasks**:
1. Update `_extract_hashes_from_trial_dir()` in `trial_finder.py` to use centralized utilities
   - Replace manual hash extraction with `get_or_compute_study_key_hash()` and `get_or_compute_trial_key_hash()`
   - Keep function signature for backward compatibility
2. Update `get_trial_hash_info()` in `study_summary.py` to use centralized utilities
   - Replace manual hash extraction with centralized utilities
   - Keep function signature for backward compatibility
3. Search for other manual hash extraction patterns
   - Replace with centralized utilities where possible

**Files to Modify**:
- `src/evaluation/selection/trial_finder.py`
- `src/evaluation/selection/study_summary.py`

**Success Criteria**:
- All hash extraction uses centralized utilities
- No manual hash extraction from trial metadata
- All tests pass: `uvx pytest tests/`

**Verification**:
```bash
# Check for manual hash extraction
grep -rn "meta\.get.*study_key_hash\|meta\.get.*trial_key_hash" src/evaluation/selection/
# Should not appear (use centralized utilities instead)
```

---

### Step 7: Consolidate Naming Fallback Logic

**Goal**: Ensure all naming fallback logic uses centralized utilities from `infrastructure.naming.mlflow.run_names`.

**Tasks**:
1. Update `build_training_run_name_with_fallback()` in `run_names.py` to use centralized utilities
   - Replace fallback logic with calls to `build_mlflow_run_name()` (SSOT)
   - Keep function signature for backward compatibility
2. Update `create_mlflow_run_name()` in `helpers.py` to use centralized utilities
   - Replace legacy fallback logic with calls to `build_mlflow_run_name()` (SSOT)
   - Keep function signature for backward compatibility (document as deprecated)
3. Search for other naming fallback patterns
   - Replace with centralized utilities where possible

**Files to Modify**:
- `src/training/execution/run_names.py`
- `src/training/hpo/utils/helpers.py`

**Success Criteria**:
- All naming fallback logic uses centralized utilities
- No duplicate naming fallback patterns
- All tests pass: `uvx pytest tests/`

**Verification**:
```bash
# Check for duplicate naming fallback patterns
grep -rn "_build.*fallback.*name\|_build.*legacy.*name" src/training/
# Should not appear (use centralized utilities instead)
```

---

### Step 8: Update `cleanup_interrupted_runs()` to Trust Provided `config_dir`

**Goal**: Ensure `cleanup_interrupted_runs()` trusts provided `config_dir` parameter (from SU3Tr worktree).

**Tasks**:
1. Update `cleanup_interrupted_runs()` in `src/training/hpo/tracking/cleanup.py` to trust provided `config_dir` parameter
   - Only infer when `config_dir` is None
   - Use `resolve_project_paths_with_fallback()` for inference (SSOT)
2. Update call sites to pass `config_dir` explicitly when available

**Files to Modify**:
- `src/training/hpo/tracking/cleanup.py`

**Success Criteria**:
- `cleanup_interrupted_runs()` trusts provided `config_dir` parameter
- Only infers when truly necessary
- All tests pass: `uvx pytest tests/`

**Verification**:
```bash
# Check cleanup function
grep -A 10 "def cleanup_interrupted_runs" src/training/hpo/tracking/cleanup.py
grep -A 3 "resolve_project_paths_with_fallback" src/training/hpo/tracking/cleanup.py
```

---

### Step 9: Standardize on `resolve_project_paths_with_fallback()` (Replace `resolve_project_paths()`)

**Goal**: Replace all `resolve_project_paths()` calls with `resolve_project_paths_with_fallback()` for consistency (from SU3Tr worktree).

**Tasks**:
1. Find all calls to `resolve_project_paths()`:
   - `sweep.py` line 696-701
   - Search for other occurrences across codebase
2. Replace with `resolve_project_paths_with_fallback()`
3. Verify behavior is equivalent (both trust provided `config_dir`)
4. Update any comments/documentation

**Success Criteria**:
- All `resolve_project_paths()` calls replaced with `resolve_project_paths_with_fallback()`
- Behavior is unchanged (both utilities trust provided `config_dir`)
- Tests pass

**Verification**:
```bash
# Find all resolve_project_paths calls (should be 0 after fix)
grep -rn "resolve_project_paths(" src/ --include="*.py" | grep -v "resolve_project_paths_with_fallback"
```

---

### Step 10: Document MLflow Setup Layering

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

### Step 11: Remove Deprecated Wrapper Modules

**Goal**: Remove backward compatibility wrapper that re-exports from new location.

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

### Step 12: Verify Tests and Type Checking

**Goal**: Ensure all changes maintain test coverage and type safety.

**Tasks**:
1. Run all related tests: `uvx pytest tests/ -k "mlflow\|path\|naming\|config_dir"`
2. Run mypy on modified files: `uvx mypy src/training/hpo/tracking/ src/infrastructure/tracking/mlflow/ src/infrastructure/paths/ src/infrastructure/naming/ src/evaluation/selection/`
3. Fix any type errors or test failures
4. Ensure no regressions in existing functionality

**Success Criteria**:
- All tests pass: `uvx pytest tests/`
- Mypy passes: `uvx mypy src --show-error-codes`
- No type errors in modified files

**Verification**:
```bash
# Run tests
uvx pytest tests/training/hpo/tracking/ tests/tracking/ tests/infrastructure/paths/ tests/infrastructure/naming/ tests/evaluation/selection/ -v

# Run mypy
uvx mypy src/training/hpo/tracking/ src/infrastructure/tracking/mlflow/ src/infrastructure/paths/ src/infrastructure/naming/ src/evaluation/selection/ --show-error-codes
```

---

### Step 13: Document Consolidation Patterns

**Goal**: Document the consolidated patterns for future reference.

**Tasks**:
1. Create or update `docs/architecture/consolidated-patterns.md` with:
   - SSOT functions and their responsibilities
   - Path resolution pattern (trust provided `config_dir`)
   - Hash computation pattern (use centralized utilities)
   - MLflow setup layering
   - Naming fallback pattern (use centralized utilities)
2. Update README files if needed

**Files to Create/Modify**:
- `docs/architecture/consolidated-patterns.md` (create)

**Success Criteria**:
- Documentation created explaining consolidated patterns
- Examples provided for common use cases

---

## Success Criteria (Overall)

- ✅ No redundant `config_dir` inference (trust provided parameter pattern enforced)
- ✅ All hash computation/extraction uses centralized utilities (`hash_utils.py`)
- ✅ All path resolution uses `resolve_project_paths_with_fallback()` (SSOT)
- ✅ All naming fallback uses centralized utilities (`run_names.py`)
- ✅ MLflow setup layering clearly documented and enforced
- ✅ All execution scripts use consistent patterns
- ✅ All tests pass: `uvx pytest tests/`
- ✅ Mypy passes: `uvx mypy src --show-error-codes`
- ✅ Deprecated wrapper removed
- ✅ Documentation updated with consolidation patterns

## Notes

- **Prioritization**: Start with Step 1 (highest impact, removes most duplication)
- **Coordination**: Step 1 must be executed together with related plans' Step 1
- **Testing**: After each step, run tests to ensure no regressions
- **Breaking Changes**: Minimize by keeping function signatures compatible
- **Incremental**: Update callers incrementally rather than all at once

## References

### Related Plans
- **MLflow Scripts Consolidation**: `20260118-1200-consolidate-mlflow-scripts-dry-violations-unified.plan.md`
- **Path/Naming Scripts Consolidation**: `20260118-1400-consolidate-path-naming-scripts-dry-violations.plan.md`
- **HPO/Training Scripts Consolidation**: `FINISED-20260118-0000-consolidate-hpo-training-scripts-dry-violations.plan.md`
- **Utility Scripts Consolidation**: `FINISHED-20260117-2350-consolidate-utility-scripts-dry-violations-unified.plan.md` (✅ Completed)
- **Workflow Patterns**: `FINISHED-20260117-2300-workflow-patterns-unified-comprehensive.plan.md` (✅ Completed)

### SSOT Modules
- `src/infrastructure/paths/utils.py` - Path resolution SSOT
- `src/infrastructure/paths/repo.py` - Repository root detection SSOT
- `src/infrastructure/tracking/mlflow/setup.py` - MLflow setup SSOT
- `src/infrastructure/tracking/mlflow/runs.py` - MLflow run creation SSOT
- `src/infrastructure/tracking/mlflow/hash_utils.py` - Hash computation SSOT
- `src/infrastructure/naming/mlflow/run_names.py` - MLflow run naming SSOT
- `src/infrastructure/naming/mlflow/config.py` - MLflow config loading SSOT


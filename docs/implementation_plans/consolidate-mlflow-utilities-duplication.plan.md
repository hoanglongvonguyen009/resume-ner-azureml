# Consolidate MLflow Utilities Duplication

## Goal

Eliminate code duplication in MLflow utility modules by consolidating re-export layers and removing deprecated backward-compatibility shims. This will reduce import path confusion, improve maintainability, and establish a clear single source of truth for MLflow utilities.

## Status

**Last Updated**: 2026-01-14

### Completed Steps
- None yet

### Pending Steps
- ⏳ Step 1: Analyze and document all MLflow utility re-export layers
- ⏳ Step 2: Consolidate MLflow utility re-exports
- ⏳ Step 3: Remove deprecated orchestration.mlflow_utils module
- ⏳ Step 4: Update all imports to use infrastructure.tracking.mlflow directly
- ⏳ Step 5: Verify no broken imports and run tests

## Preconditions

- All existing tests pass
- No active PRs modifying MLflow utility modules
- Understanding of current import patterns across codebase

## Utility Scripts Inventory

This section documents all utility scripts found in the codebase (tagged with `type: utility` in metadata).

### MLflow Utilities (Domain: tracking)
- `src/infrastructure/tracking/mlflow/utils.py` - Retry logic, run ID detection, config inference
- `src/infrastructure/tracking/mlflow/urls.py` - MLflow URL generation
- `src/infrastructure/tracking/mlflow/runs.py` - Run creation (child runs, etc.)
- `src/infrastructure/tracking/mlflow/setup.py` - MLflow setup for stages
- `src/infrastructure/tracking/mlflow/hash_utils.py` - MLflow-specific hash retrieval/computation
- `src/infrastructure/tracking/mlflow/queries.py` - MLflow query patterns

### Naming Utilities (Domain: naming)
- `src/infrastructure/naming/mlflow/run_keys.py` - Run key building and hashing
- `src/infrastructure/naming/mlflow/hpo_keys.py` - HPO key building and hashing
- `src/infrastructure/naming/mlflow/refit_keys.py` - Refit protocol fingerprint computation
- `src/infrastructure/naming/mlflow/tags_registry.py` - Tag registry loading
- `src/infrastructure/naming/mlflow/config.py` - Naming configuration utilities
- `src/infrastructure/naming/display_policy.py` - Display policy utilities

### Config Utilities (Domain: config)
- `src/infrastructure/config/run_mode.py` - Run mode extraction
- `src/infrastructure/config/selection.py` - Selection config utilities
- `src/infrastructure/config/run_decision.py` - Run decision logic
- `src/infrastructure/config/variants.py` - Variant computation

### Path Utilities (Domain: paths)
- `src/infrastructure/paths/utils.py` - Path utility functions (find project root)
- `src/infrastructure/paths/config.py` - Config path utilities

### Shared Utilities (Domain: shared)
- `src/common/shared/hash_utils.py` - Basic hash computation (compute_hash_64, compute_hash_16, compute_json_hash, compute_selection_cache_key)
- `src/common/shared/file_utils.py` - File validation utilities
- `src/common/shared/dict_utils.py` - Dictionary utilities (deep_merge)
- `src/common/shared/yaml_utils.py` - YAML loading utilities
- `src/common/shared/logging_utils.py` - Logging configuration utilities
- `src/common/shared/cli_utils.py` - CLI argument parsing utilities
- `src/common/shared/notebook_setup.py` - Notebook environment detection and setup

### Selection Utilities (Domain: selection)
- `src/evaluation/selection/cache.py` - Cache management for best model selection
- `src/evaluation/selection/trial_finder.py` - Trial finding utilities
- `src/evaluation/selection/study_summary.py` - Study summary utilities
- `src/evaluation/selection/disk_loader.py` - Disk-based artifact loading
- `src/evaluation/selection/mlflow_selection.py` - MLflow-based selection
- `src/evaluation/selection/local_selection_v2.py` - Local selection utilities
- `src/evaluation/selection/artifact_acquisition.py` - Artifact acquisition utilities
- `src/evaluation/selection/artifact_unified/validation.py` - Artifact validation
- `src/evaluation/selection/artifact_unified/compat.py` - Artifact compatibility
- `src/evaluation/selection/artifact_unified/discovery.py` - Artifact discovery
- `src/evaluation/selection/artifact_unified/acquisition.py` - Unified artifact acquisition
- `src/evaluation/selection/artifact_unified/selectors.py` - Artifact selectors

### Benchmarking Utilities (Domain: benchmarking)
- `src/evaluation/benchmarking/utils.py` - Benchmark execution utilities
- `src/evaluation/benchmarking/execution.py` - Benchmark execution
- `src/evaluation/benchmarking/formatting.py` - Benchmark formatting

### Training Utilities (Domain: training)
- `src/training/core/cv_utils.py` - Cross-validation utilities
- `src/training/core/evaluator.py` - Model evaluation utilities
- `src/training/core/model.py` - Model utilities
- `src/training/core/trainer.py` - Training utilities
- `src/training/core/metrics.py` - Metrics utilities
- `src/training/core/checkpoint_loader.py` - Checkpoint loading utilities
- `src/training/execution/distributed.py` - Distributed training utilities
- `src/training/execution/subprocess_runner.py` - Subprocess execution utilities
- `src/training/execution/tags.py` - Training tag utilities
- `src/training/execution/lineage.py` - Training lineage utilities
- `src/training/execution/mlflow_setup.py` - MLflow setup for training
- `src/training/hpo/utils/helpers.py` - HPO-specific helpers (generate_run_id, setup_checkpoint_storage, etc.)
- `src/training/hpo/core/study.py` - HPO study utilities
- `src/training/hpo/core/optuna_integration.py` - Optuna integration utilities
- `src/training/hpo/core/search_space.py` - Search space utilities
- `src/training/hpo/checkpoint/cleanup.py` - Checkpoint cleanup utilities
- `src/training/hpo/checkpoint/storage.py` - Checkpoint storage utilities

### Deployment Utilities (Domain: deployment)
- `src/deployment/api/inference.py` - Inference utilities
- `src/deployment/api/model_loader.py` - Model loading utilities
- `src/deployment/api/entities.py` - API entity utilities
- `src/deployment/api/response_converters.py` - Response conversion utilities
- `src/deployment/api/extractors.py` - Data extraction utilities
- `src/deployment/api/middleware.py` - API middleware utilities
- `src/deployment/api/startup.py` - API startup utilities
- `src/deployment/api/routes/health.py` - Health check utilities
- `src/deployment/api/routes/predictions.py` - Prediction route utilities
- `src/deployment/api/inference/engine.py` - Inference engine utilities
- `src/deployment/api/inference/decoder.py` - Decoder utilities
- `src/deployment/api/config.py` - API configuration utilities
- `src/deployment/api/exception_handlers.py` - Exception handling utilities

### Orchestration Utilities (Domain: orchestration)
- `src/orchestration/jobs/tracking/utils/mlflow_utils.py` - **RE-EXPORT LAYER** (backward compat)
- `src/orchestration/jobs/tracking/mlflow_utils.py` - **RE-EXPORT LAYER** (nested re-export)
- `src/orchestration/mlflow_utils.py` - **DEPRECATED RE-EXPORT LAYER**
- `src/orchestration/jobs/tracking/mlflow_helpers.py` - **RE-EXPORT LAYER** (backward compat)
- `src/orchestration/jobs/tracking/utils/helpers.py` - **RE-EXPORT LAYER** (backward compat)
- `src/orchestration/jobs/hpo/local/checkpoint/manager.py` - Checkpoint management utilities
- `src/orchestration/jobs/hpo/local/backup.py` - Backup utilities
- `src/orchestration/jobs/tracking/utils/__init__.py` - **RE-EXPORT LAYER** (convenience exports)

### Workflow Utilities (Domain: workflows)
- `src/evaluation/selection/workflows/benchmarking_workflow.py` - Benchmarking workflow utilities
- `src/evaluation/selection/workflows/selection_workflow.py` - Selection workflow utilities

### Other Utilities
- `src/infrastructure/setup/azure_resources.py` - Azure resource setup utilities
- `src/selection/cache.py` - Selection cache utilities (duplicate of evaluation/selection/cache.py - already consolidated)
- `src/selection/selection.py` - Selection utilities
- `src/selection/selection_logic.py` - Selection logic utilities
- `src/evaluation/selection/selection.py` - Selection utilities (different from selection/selection.py)

**Note**: Many utility scripts are domain-specific and should remain separate. This plan focuses only on MLflow utility re-export layers which are clear DRY violations.

## Analysis

### Identified DRY Violations

#### 1. MLflow Utility Re-Export Layers (Backward Compatibility Shims)

**Current Structure**:
- **Source of Truth**: `src/infrastructure/tracking/mlflow/utils.py`
  - Contains: `retry_with_backoff()`, `get_mlflow_run_id()`, `infer_config_dir_from_path()`
- **Source of Truth**: `src/infrastructure/tracking/mlflow/urls.py`
  - Contains: `get_mlflow_run_url()`
- **Source of Truth**: `src/infrastructure/tracking/mlflow/runs.py`
  - Contains: `create_child_run()`

**Re-Export Layers (Duplication)**:
1. `src/orchestration/jobs/tracking/utils/mlflow_utils.py` (21 lines)
   - Re-exports: `get_mlflow_run_url`, `retry_with_backoff` from infrastructure
   - **Purpose**: Backward compatibility shim
   - **Status**: Active re-export layer

2. `src/orchestration/jobs/tracking/mlflow_utils.py` (18 lines)
   - Re-exports: `get_mlflow_run_url`, `retry_with_backoff` from `orchestration.jobs.tracking.utils.mlflow_utils`
   - **Purpose**: Backward compatibility shim (nested re-export)
   - **Status**: Active re-export layer

3. `src/orchestration/mlflow_utils.py` (21 lines)
   - Re-exports: `setup_mlflow_for_stage` from `infrastructure.tracking.mlflow.setup`
   - **Purpose**: Deprecated backward compatibility shim
   - **Status**: **DEPRECATED** (has deprecation warning)

4. `src/orchestration/jobs/tracking/mlflow_helpers.py` (21 lines)
   - Re-exports: `create_child_run` from `infrastructure.tracking.mlflow.runs`
   - **Purpose**: Backward compatibility shim
   - **Status**: Active re-export layer

5. `src/orchestration/jobs/tracking/utils/helpers.py` (18 lines)
   - Re-exports: `create_child_run` from `infrastructure.tracking.mlflow.runs`
   - **Purpose**: Backward compatibility shim
   - **Status**: Active re-export layer

6. `src/orchestration/jobs/tracking/utils/__init__.py`
   - Re-exports: `create_child_run`, `get_mlflow_run_url`, `retry_with_backoff`
   - **Purpose**: Convenience re-exports
   - **Status**: Active re-export layer

**Impact**: ~120 lines of re-export code, multiple import paths for same functions, confusion about source of truth

**Current Import Patterns**:
- `from infrastructure.tracking.mlflow.utils import retry_with_backoff` (direct - preferred)
- `from orchestration.jobs.tracking.utils.mlflow_utils import retry_with_backoff` (re-export)
- `from orchestration.jobs.tracking.mlflow_utils import retry_with_backoff` (nested re-export)
- `from orchestration.mlflow_utils import setup_mlflow_for_stage` (deprecated)

#### 2. Hash Utilities (Already Consolidated)

**Status**: ✅ Already consolidated in previous refactoring
- `src/common/shared/hash_utils.py` - Basic hash computation (compute_hash_64, compute_hash_16, compute_json_hash)
- `src/infrastructure/tracking/mlflow/hash_utils.py` - MLflow-specific hash retrieval/computation (different purpose, should remain separate)

**No action needed** - these serve different purposes and are correctly separated.

#### 3. HPO Helper Functions (Domain-Specific, Should Remain)

**Status**: ✅ Should remain separate
- `src/training/hpo/utils/helpers.py` - HPO-specific helpers (generate_run_id, setup_checkpoint_storage, create_study_name, etc.)
- These are domain-specific to HPO and used across HPO modules
- **No action needed** - these are not duplicates, they're domain-specific utilities

## Steps

### Step 1: Analyze and document all MLflow utility re-export layers

**Objective**: Create a complete inventory of all re-export layers and their usage.

**Actions**:
1. Search for all imports from orchestration MLflow utility modules:
   ```bash
   grep -r "from orchestration.*mlflow" src/
   grep -r "import.*orchestration.*mlflow" src/
   ```
2. Document each re-export layer:
   - File path
   - Functions re-exported
   - Source module
   - Number of usages in codebase
3. Identify which re-exports are actively used vs. unused
4. Check for any tests that import from re-export layers

**Success criteria**:
- ✅ Complete inventory of all re-export layers documented
- ✅ Usage count for each re-export path identified
- ✅ Tests importing from re-export layers identified

---

### Step 2: Consolidate MLflow utility re-exports

**Objective**: Remove redundant re-export layers, keeping only necessary backward compatibility shims.

**Actions**:
1. **Remove nested re-export**: Delete `src/orchestration/jobs/tracking/mlflow_utils.py`
   - This is a nested re-export (re-exports from another re-export)
   - Update any imports to use `orchestration.jobs.tracking.utils.mlflow_utils` directly
   
2. **Consolidate duplicate re-exports**: Merge `src/orchestration/jobs/tracking/mlflow_helpers.py` into `src/orchestration/jobs/tracking/utils/helpers.py`
   - Both re-export `create_child_run`
   - Keep only one location for backward compatibility
   
3. **Update `src/orchestration/jobs/tracking/utils/__init__.py`**:
   - Ensure it re-exports all needed functions from infrastructure
   - Document that this is a backward compatibility layer

**Success criteria**:
- ✅ `src/orchestration/jobs/tracking/mlflow_utils.py` deleted
- ✅ `src/orchestration/jobs/tracking/mlflow_helpers.py` deleted
- ✅ All functions consolidated in `src/orchestration/jobs/tracking/utils/helpers.py` or `__init__.py`
- ✅ No broken imports from deleted files

---

### Step 3: Remove deprecated orchestration.mlflow_utils module

**Objective**: Remove the deprecated `orchestration.mlflow_utils` module that has explicit deprecation warnings.

**Actions**:
1. Find all imports from `orchestration.mlflow_utils`:
   ```bash
   grep -r "from orchestration.mlflow_utils" src/
   grep -r "import.*orchestration.mlflow_utils" src/
   ```
2. Update all imports to use `infrastructure.tracking.mlflow.setup.setup_mlflow_for_stage` directly
3. Delete `src/orchestration/mlflow_utils.py`
4. Verify no remaining references

**Success criteria**:
- ✅ All imports updated to use `infrastructure.tracking.mlflow.setup.setup_mlflow_for_stage`
- ✅ `src/orchestration/mlflow_utils.py` deleted
- ✅ `grep -r "orchestration.mlflow_utils" src/` returns no matches
- ✅ No deprecation warnings in codebase

---

### Step 4: Update all imports to use infrastructure.tracking.mlflow directly

**Objective**: Migrate all imports to use the source of truth directly, reducing reliance on backward compatibility shims.

**Actions**:
1. Update imports in `src/orchestration/jobs/tracking/trackers/`:
   - Change `from orchestration.jobs.tracking.utils.mlflow_utils import retry_with_backoff`
   - To: `from infrastructure.tracking.mlflow.utils import retry_with_backoff`
   - Change `from orchestration.jobs.tracking.utils.mlflow_utils import get_mlflow_run_url`
   - To: `from infrastructure.tracking.mlflow.urls import get_mlflow_run_url`

2. Update imports in `src/infrastructure/platform/adapters/mlflow_context.py`:
   - Change `from orchestration.jobs.tracking.mlflow_helpers import create_child_run`
   - To: `from infrastructure.tracking.mlflow.runs import create_child_run`

3. Search for any other imports from orchestration MLflow utilities and update them

4. Keep backward compatibility shims in `orchestration.jobs.tracking.utils.*` for now (can be removed in future if unused)

**Success criteria**:
- ✅ All tracker modules import directly from infrastructure
- ✅ All new code uses infrastructure.tracking.mlflow directly
- ✅ Backward compatibility shims remain but are not used by new code
- ✅ `grep -r "from orchestration.*mlflow.*import" src/` shows only backward compat shims

---

### Step 5: Verify no broken imports and run tests

**Objective**: Ensure all imports work correctly and no functionality is broken.

**Actions**:
1. Run import verification:
   ```bash
   python -c "from infrastructure.tracking.mlflow.utils import retry_with_backoff; print('✓ utils')"
   python -c "from infrastructure.tracking.mlflow.urls import get_mlflow_run_url; print('✓ urls')"
   python -c "from infrastructure.tracking.mlflow.runs import create_child_run; print('✓ runs')"
   ```
2. Run tests that use MLflow utilities:
   ```bash
   pytest tests/tracking/ -v
   pytest tests/infrastructure/tracking/ -v
   ```
3. Check for any import errors in linter
4. Verify backward compatibility shims still work (if any code still uses them)

**Success criteria**:
- ✅ All import tests pass
- ✅ All tracking-related tests pass
- ✅ No linter errors related to imports
- ✅ Backward compatibility shims still function (if used)

---

## Success Criteria (Overall)

- ✅ **Code reduction**: ~100+ lines of re-export code removed
- ✅ **Single source of truth**: All MLflow utilities clearly in `infrastructure.tracking.mlflow.*`
- ✅ **Reduced confusion**: Fewer import paths for same functions
- ✅ **Deprecated modules removed**: `orchestration.mlflow_utils` removed
- ✅ **Backward compatibility**: Remaining shims documented and clearly marked
- ✅ **Type safety**: All code passes Mypy type checking
- ✅ **Functionality**: All existing functionality preserved
- ✅ **Maintainability**: Future changes only need to be made in one place

## Notes

### Import Path Strategy

- **Source of Truth**: `infrastructure.tracking.mlflow.*` modules
  - `utils.py` - Retry logic, run ID detection, config inference
  - `urls.py` - MLflow URL generation
  - `runs.py` - Run creation (child runs, etc.)
  - `setup.py` - MLflow setup for stages
  - `hash_utils.py` - MLflow-specific hash retrieval/computation

- **Backward Compatibility**: Keep minimal shims in `orchestration.jobs.tracking.utils.*`
  - Only if actively used
  - Document as backward compatibility layers
  - Encourage migration to infrastructure imports

### Files to Keep Separate

- `src/training/hpo/utils/helpers.py` - HPO-specific helpers (domain-specific, not duplicates)
- `src/infrastructure/tracking/mlflow/hash_utils.py` - MLflow-specific hash retrieval (different purpose from basic hash_utils)
- `src/common/shared/hash_utils.py` - Basic hash computation (already consolidated)

### Risk Assessment

- **Low Risk**: Re-export layers are simple pass-throughs (no logic)
- **Low Risk**: Infrastructure modules are stable and well-tested
- **Medium Risk**: Need to verify all import paths are updated correctly
- **Low Risk**: Backward compatibility shims can remain if needed

### Rollback Plan

If issues arise:
1. Revert commits in reverse order
2. Restore deleted re-export files from git history
3. Revert import changes in affected files

## Related Plans

- `FINISHED-eliminate-tag-parsing-hash-dry-violations.plan.md` - Similar consolidation pattern for naming utilities
- `FINISHED-eliminate-caching-dry-violations.plan.md` - Similar consolidation pattern for caching utilities


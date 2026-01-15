# Utility Scripts Analysis Summary

**Date**: 2025-01-27  
**Purpose**: Comprehensive analysis of all utility scripts tagged with `type: utility` in metadata

## Executive Summary

Found **145+ utility scripts** across the codebase, organized into 7 main categories. Identified **6 major categories of DRY violations** requiring consolidation, with **Category 1 (Selection Module Duplication)** being the highest priority.

## 1. Utility Scripts Inventory

### Category 1: Selection Utilities (20+ files)

#### Active (evaluation.selection - SSOT)
- `src/evaluation/selection/local_selection.py` - Best configuration selection from Optuna studies
- `src/evaluation/selection/local_selection_v2.py` - Improved selection with config-aware discovery
- `src/evaluation/selection/artifact_acquisition.py` - Checkpoint acquisition (SSOT)
- `src/evaluation/selection/trial_finder.py` - Find best trials from studies/disk
- `src/evaluation/selection/disk_loader.py` - Load trial data from disk
- `src/evaluation/selection/cache.py` - Cache management for selection
- `src/evaluation/selection/study_summary.py` - Display and summarize HPO studies
- `src/evaluation/selection/mlflow_selection.py` - MLflow-based best model selection (SSOT)
- `src/evaluation/selection/selection.py` - Selection orchestration
- `src/evaluation/selection/selection_logic.py` - Selection algorithm logic

#### Deprecated Wrappers (selection - TO BE REMOVED)
- `src/selection/local_selection.py` - **DEPRECATED** wrapper around `evaluation.selection.local_selection`
- `src/selection/local_selection_v2.py` - **DEPRECATED** wrapper around `evaluation.selection.local_selection_v2`
- `src/selection/artifact_acquisition.py` - **DEPRECATED** wrapper around `evaluation.selection.artifact_acquisition`
- `src/selection/trial_finder.py` - **DEPRECATED** wrapper around `evaluation.selection.trial_finder`
- `src/selection/disk_loader.py` - **DEPRECATED** wrapper around `evaluation.selection.disk_loader`
- `src/selection/cache.py` - **DEPRECATED** wrapper around `evaluation.selection.cache`
- `src/selection/study_summary.py` - **DEPRECATED** wrapper around `evaluation.selection.study_summary`
- `src/selection/mlflow_selection.py` - **DEPRECATED** wrapper around `evaluation.selection.mlflow_selection`

#### Active (selection - Unique Logic)
- `src/selection/selection.py` - Selection orchestration (may have unique logic)
- `src/selection/selection_logic.py` - Selection algorithm logic (may have unique logic)

### Category 2: MLflow Utilities (30+ files)

#### MLflow Setup
- `src/infrastructure/tracking/mlflow/setup.py` - **SSOT** for MLflow experiment setup
  - `setup_mlflow()` - Main setup function (SSOT)
  - `setup_mlflow_for_stage()` - **DEPRECATED** wrapper (to be removed)
- `src/training/execution/mlflow_setup.py` - Training-specific MLflow run creation
  - `create_training_mlflow_run()` - Run lifecycle management (different responsibility)
  - `setup_mlflow_tracking_env()` - Environment variables for subprocesses (different responsibility)

#### MLflow Tracking
- `src/infrastructure/tracking/mlflow/utils.py` - MLflow utility functions
  - `retry_with_backoff()` - Retry logic for MLflow operations
  - `get_mlflow_run_id()` - Get run ID from active run or env
  - `infer_config_dir_from_path()` - **SSOT** for config directory inference
- `src/infrastructure/tracking/mlflow/hash_utils.py` - Hash retrieval and computation (SSOT)
- `src/infrastructure/tracking/mlflow/finder.py` - MLflow run finding utilities
- `src/infrastructure/tracking/mlflow/queries.py` - MLflow query utilities (SSOT)
- `src/infrastructure/tracking/mlflow/runs.py` - MLflow run lifecycle management
- `src/infrastructure/tracking/mlflow/lifecycle.py` - MLflow run lifecycle utilities
- `src/infrastructure/tracking/mlflow/artifacts.py` - Artifact management
- `src/infrastructure/tracking/mlflow/artifacts/uploader.py` - Artifact upload utilities
- `src/infrastructure/tracking/mlflow/artifacts/manager.py` - Artifact manager
- `src/infrastructure/tracking/mlflow/artifacts/stage_helpers.py` - Artifact staging helpers
- `src/infrastructure/tracking/mlflow/trackers/base_tracker.py` - Base tracker class
- `src/infrastructure/tracking/mlflow/trackers/training_tracker.py` - Training tracker
- `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py` - Sweep tracker
- `src/infrastructure/tracking/mlflow/trackers/benchmark_tracker.py` - Benchmark tracker
- `src/infrastructure/tracking/mlflow/trackers/conversion_tracker.py` - Conversion tracker
- `src/infrastructure/tracking/mlflow/urls.py` - MLflow URL construction
- `src/infrastructure/tracking/mlflow/compatibility.py` - MLflow compatibility utilities

#### MLflow Tags
- `src/infrastructure/naming/mlflow/tags.py` - MLflow tag construction (SSOT)
- `src/infrastructure/naming/mlflow/tag_keys.py` - Tag key definitions and helpers (SSOT)
- `src/infrastructure/naming/mlflow/tags_registry.py` - Tags registry management
- `src/training/execution/tags.py` - Training-specific lineage tags
- `src/training/execution/tag_helpers.py` - Training tag building helpers

### Category 3: Path Utilities (10+ files)

- `src/infrastructure/paths/utils.py` - **SSOT** for path utilities
  - `find_project_root()` - Find project root directory (SSOT)
- `src/infrastructure/paths/config.py` - Path configuration
- `src/orchestration/jobs/hpo/local/trial/execution.py` - Contains duplicate `_find_project_root()` method

### Category 4: Naming Utilities (25+ files)

#### Core Naming
- `src/core/normalize.py` - Normalization for names and paths (SSOT)
- `src/core/placeholders.py` - Placeholder extraction utilities (SSOT)
- `src/core/tokens.py` - Token validation utilities

#### Naming Infrastructure
- `src/infrastructure/naming/display_policy.py` - Naming policy loading and display name formatting
- `src/infrastructure/naming/mlflow/policy.py` - **DEPRECATED** backward-compatibility wrapper
- `src/infrastructure/naming/mlflow/run_names.py` - MLflow run name generation (SSOT)
- `src/infrastructure/naming/mlflow/config.py` - Naming configuration
- `src/infrastructure/naming/mlflow/tag_keys.py` - Tag key definitions (SSOT)
- `src/infrastructure/naming/mlflow/tags.py` - Tag construction (SSOT)
- `src/infrastructure/naming/mlflow/tags_registry.py` - Tags registry
- `src/infrastructure/naming/mlflow/hpo_keys.py` - HPO key building
- `src/infrastructure/naming/mlflow/run_keys.py` - Run key building
- `src/infrastructure/naming/mlflow/refit_keys.py` - Refit key building
- `src/infrastructure/naming/context.py` - Naming context
- `src/infrastructure/naming/context_tokens.py` - Context token building
- `src/infrastructure/naming/experiments.py` - Experiment naming

#### Training Naming
- `src/training/execution/run_names.py` - Training run name building (uses infrastructure.naming internally)
  - Contains duplicate `_infer_config_dir_from_output()` function

### Category 5: Training Utilities (15+ files)

- `src/training/core/trainer.py` - Training core utilities
- `src/training/core/evaluator.py` - Evaluation utilities
- `src/training/core/model.py` - Model utilities
- `src/training/core/cv_utils.py` - Cross-validation utilities
- `src/training/core/metrics.py` - Metrics utilities
- `src/training/core/checkpoint_loader.py` - Checkpoint loading
- `src/training/execution/tags.py` - Lineage tag application
- `src/training/execution/tag_helpers.py` - Tag building helpers
- `src/training/execution/run_names.py` - Run name building
- `src/training/execution/mlflow_setup.py` - MLflow run creation
- `src/training/execution/subprocess_runner.py` - Subprocess execution
- `src/training/execution/distributed.py` - Distributed training utilities
- `src/training/execution/distributed_launcher.py` - Distributed launcher
- `src/training/execution/lineage.py` - Lineage extraction
- `src/training/execution/jobs.py` - Training job utilities

### Category 6: HPO Utilities (10+ files)

- `src/training/hpo/core/study.py` - Optuna study utilities
- `src/training/hpo/core/optuna_integration.py` - Optuna integration
- `src/training/hpo/core/search_space.py` - Search space utilities
- `src/training/hpo/checkpoint/cleanup.py` - **SSOT** for checkpoint cleanup
- `src/training/hpo/checkpoint/storage.py` - Checkpoint storage utilities
- `src/training/hpo/execution/azureml/sweeps.py` - AzureML sweep utilities
- `src/orchestration/jobs/hpo/local/checkpoint/cleanup.py` - **DEPRECATED** wrapper around `training.hpo.checkpoint.cleanup`
- `src/orchestration/jobs/hpo/local/checkpoint/manager.py` - **DEPRECATED** wrapper around `training.hpo.checkpoint.storage`

### Category 7: Other Utilities (30+ files)

- `src/infrastructure/config/selection.py` - Selection configuration
- `src/infrastructure/config/variants.py` - Variant configuration
- `src/infrastructure/config/run_decision.py` - Run decision utilities
- `src/infrastructure/config/run_mode.py` - Run mode utilities
- `src/infrastructure/platform/adapters/mlflow_context.py` - MLflow context adapters
- `src/infrastructure/platform/azureml/data_assets.py` - AzureML data assets
- `src/infrastructure/platform/azureml/jobs.py` - AzureML job utilities
- `src/infrastructure/setup/azure_resources.py` - Azure resource setup
- `src/common/shared/notebook_setup.py` - Notebook setup utilities
- `src/deployment/api/*` - Deployment API utilities (20+ files)
- `src/evaluation/benchmarking/utils.py` - Benchmarking utilities
- `src/evaluation/benchmarking/formatting.py` - Benchmark formatting
- `src/evaluation/benchmarking/execution.py` - Benchmark execution
- And more...

## 2. Overlapping Responsibilities Analysis

### Category 1: Selection Module Duplication (🔴 CRITICAL)

**Files Affected**: 8 deprecated wrapper files in `selection/`

**Overlap**: Complete duplication - all wrappers delegate to `evaluation.selection.*` equivalents

**Impact**: 
- Maintenance burden (8 files to maintain)
- Confusion about which module to use
- Deprecation warnings in all wrapper usage

**Consolidation**: Remove all deprecated wrappers, update imports to use `evaluation.selection.*` directly

### Category 2: Config Directory Inference (🟠 HIGH)

**Files Affected**:
- `src/infrastructure/tracking/mlflow/utils.py::infer_config_dir_from_path()` (SSOT)
- `src/training/execution/run_names.py::_infer_config_dir_from_output()` (duplicate)

**Overlap**: Similar logic for inferring config directory from output/path

**Impact**: 
- Code duplication
- Potential inconsistencies in inference logic

**Consolidation**: Use `infrastructure.tracking.mlflow.utils.infer_config_dir_from_path()` as SSOT

### Category 3: MLflow Setup Duplication (🟠 HIGH)

**Files Affected**:
- `src/infrastructure/tracking/mlflow/setup.py::setup_mlflow()` (SSOT)
- `src/infrastructure/tracking/mlflow/setup.py::setup_mlflow_for_stage()` (deprecated wrapper)

**Overlap**: Deprecated wrapper delegates to main setup function

**Impact**: 
- Unnecessary wrapper function
- Confusion about which function to use

**Consolidation**: Remove deprecated `setup_mlflow_for_stage()` wrapper

### Category 4: Path Resolution Utilities (🟡 MEDIUM)

**Files Affected**:
- `src/infrastructure/paths/utils.py::find_project_root()` (SSOT)
- `src/orchestration/jobs/hpo/local/trial/execution.py::_find_project_root()` (duplicate)

**Overlap**: Similar logic for finding project root directory

**Impact**: 
- Code duplication
- Potential inconsistencies

**Consolidation**: Use `infrastructure.paths.utils.find_project_root()` as SSOT

### Category 5: Checkpoint Path Resolution (🟡 MEDIUM)

**Files Affected**:
- `src/evaluation/selection/local_selection_v2.py::_get_checkpoint_path_from_trial_dir()` (SSOT)
- `src/orchestration/jobs/local_selection_v2.py::_get_checkpoint_path_from_trial_dir()` (duplicate)

**Overlap**: Identical logic for resolving checkpoint paths from trial directories

**Impact**: 
- Code duplication
- Maintenance burden

**Consolidation**: Use `evaluation.selection.local_selection_v2._get_checkpoint_path_from_trial_dir()` as SSOT

### Category 6: Run Name Building (🟢 LOW - Already Consolidated)

**Status**: Already consolidated - `training.execution.run_names` uses `infrastructure.naming.mlflow.run_names` internally

**Action**: Verify no remaining duplication

## 3. Grouped Overlaps

### Group A: Deprecated Wrapper Modules
- **Selection wrappers** (8 files) - All delegate to `evaluation.selection.*`
- **HPO checkpoint wrappers** (2 files) - Delegate to `training.hpo.checkpoint.*`
- **Naming policy wrapper** (1 file) - Delegates to `orchestration.jobs.tracking.naming.policy`

**Consolidation Strategy**: Remove all deprecated wrappers, update imports

### Group B: Path/Config Inference
- **Config directory inference** (2 implementations)
- **Project root finding** (2 implementations)

**Consolidation Strategy**: Use existing SSOT functions, remove duplicates

### Group C: MLflow Setup
- **MLflow setup wrapper** (1 deprecated function)

**Consolidation Strategy**: Remove deprecated wrapper, use main setup function

### Group D: Checkpoint Resolution
- **Checkpoint path resolution** (2 implementations)

**Consolidation Strategy**: Use SSOT from `evaluation.selection.local_selection_v2`

## 4. Consolidation Approach

### Principle 1: Reuse-First
- Identify existing SSOT modules
- Extend or reuse existing utilities rather than creating new ones
- Remove deprecated wrappers that add no value

### Principle 2: SRP Pragmatically
- Keep utilities focused on single responsibilities
- Don't split unnecessarily, but consolidate clear duplicates
- Maintain clear separation: setup vs run creation vs env vars

### Principle 3: Minimize Breaking Changes
- Update imports rather than changing function signatures
- Maintain backward compatibility during transition
- Remove deprecated code only after all imports updated

## 5. Implementation Priority

1. **🔴 CRITICAL**: Remove deprecated selection module wrappers (Step 1)
2. **🟠 HIGH**: Consolidate config directory inference (Step 2)
3. **🟠 HIGH**: Remove MLflow setup deprecated wrapper (Step 3)
4. **🟡 MEDIUM**: Consolidate path resolution utilities (Step 4)
5. **🟡 MEDIUM**: Consolidate checkpoint path resolution (Step 5)
6. **🟢 LOW**: Verify run name building consolidation (Step 6)

## 6. Expected Outcomes

After consolidation:
- **8 deprecated wrapper files removed** (selection modules)
- **3 duplicate functions removed** (config inference, project root, checkpoint path)
- **1 deprecated wrapper function removed** (MLflow setup)
- **All imports updated** to use SSOT modules
- **Codebase follows reuse-first principles**
- **No breaking changes** (import updates only)

## 7. Verification Commands

```bash
# Verify no deprecated selection imports remain
grep -r "from selection\.local_selection\|from selection\.artifact_acquisition" --include="*.py" src/ tests/

# Verify no duplicate config inference functions
grep -r "def.*infer.*config.*dir\|def.*find.*config.*dir" --include="*.py" src/ | grep -v "infrastructure/tracking/mlflow/utils.py"

# Verify no deprecated MLflow setup wrapper usage
grep -r "setup_mlflow_for_stage" --include="*.py" src/ tests/

# Verify no duplicate project root functions
grep -r "def.*find.*project.*root\|def.*get.*project.*root" --include="*.py" src/ | grep -v "infrastructure/paths/utils.py"

# Verify no duplicate checkpoint path functions
grep -r "def.*_get_checkpoint_path_from_trial_dir" --include="*.py" src/ | grep -v "evaluation/selection/local_selection_v2.py"
```

## 8. Related Documentation

- Implementation Plan: `docs/implementation_plans/consolidate-utility-scripts-dry-violations.plan.md`
- Previous Consolidations:
  - `FINISHED-consolidate-selection-utilities-dry-violations.plan.md`
  - `FINISHED-consolidate-mlflow-utilities-duplication.plan.md`
  - `FINISHED-consolidate-tracking-utilities-dry-violations.plan.md`


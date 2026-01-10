<!-- 0d75dc85-b0c0-4bc3-98c0-0a2c993873eb 4394032a-17e9-4db0-beb7-c6ea438fb2e7 -->
# Remaining src Reorganization Plan

## Overview

Reorganize remaining scripts in `src/orchestration` and `src/orchestration/jobs` into modular modules, eliminating duplicates and consolidating related functionality following DRY principles.

## Current State Analysis

### Already Consolidated Modules

- `config/` - Configuration management
- `fingerprints/` - Fingerprint computation
- `metadata/` - Metadata and index management
- `constants/` - Shared constants
- `azureml/` - Azure ML utilities
- `storage/` - Storage and backup
- `selection/` - Best config selection (partially - has duplicates)
- `benchmarking/` - Benchmarking (partially - has duplicates)
- `conversion/` - Conversion execution (partially - has duplicates)
- `training_exec/` - Final training execution (partially - has duplicates)
- `hpo/` - HPO execution (partially - has remaining files)
- `tracking/` - MLflow tracking (partially - has overlaps)
- `paths/` - Path resolution
- `naming/` - Naming utilities
- `core/` - Core utilities

### Remaining Files to Reorganize

#### 1. Duplicate Files in `orchestration/jobs/`

- `orchestration/jobs/selection/` - **DUPLICATES** `src/selection/`:
  - `study_summary.py` (duplicate)
  - `trial_finder.py` (duplicate)
  - `artifact_acquisition.py` (duplicate)
  - `cache.py` (duplicate)
  - `disk_loader.py` (duplicate)
  - `local_selection.py` (duplicate)
  - `mlflow_selection.py` (duplicate)
  - `selection_logic.py` (duplicate)
  - `selection.py` (duplicate)

- `orchestration/jobs/benchmarking/orchestrator.py` - **DUPLICATE** of `src/benchmarking/orchestrator.py`

- `orchestration/jobs/conversion/executor.py` - **DUPLICATE** of `src/conversion/executor.py`

- `orchestration/jobs/final_training/executor.py` - **DUPLICATE** of `src/training_exec/executor.py`
- `orchestration/jobs/final_training/tags.py` - Should be in `src/training_exec/`

#### 2. Remaining HPO Files

- `orchestration/jobs/hpo/local_sweeps.py` - Should be in `src/hpo/execution/local/`
- `orchestration/jobs/hpo/hpo_helpers.py` - Should be in `src/hpo/utils/`
- `orchestration/jobs/hpo/search_space.py` - Should be in `src/hpo/core/`
- `orchestration/jobs/hpo/study_extractor.py` - Should be in `src/hpo/core/`
- `orchestration/jobs/hpo/local/refit/executor.py` - Should be in `src/hpo/execution/local/refit/`
- `orchestration/jobs/hpo/local/cv/orchestrator.py` - Should be in `src/hpo/execution/local/cv/`
- `orchestration/jobs/hpo/local/trial/run_manager.py` - Should be in `src/hpo/trial/`
- `orchestration/jobs/hpo/local/trial/metrics.py` - Should be in `src/hpo/trial/`
- `orchestration/jobs/hpo/local/trial_meta_generator.py` - Should be in `src/hpo/trial/`
- `orchestration/jobs/hpo/local/mlflow/run_setup.py` - Should be in `src/hpo/tracking/`
- `orchestration/jobs/hpo/local/mlflow/cleanup.py` - Should be in `src/hpo/tracking/`

#### 3. Tracking/Naming Overlaps

- `orchestration/jobs/tracking/naming/` - **OVERLAPS** with `src/naming/mlflow/`:
  - `tags.py` (overlap)
  - `run_names.py` (overlap)
  - `tag_keys.py` (overlap)
  - `tags_registry.py` (overlap)
  - `policy.py` (overlap)
  - `run_keys.py` (overlap)

- `orchestration/jobs/tracking/utils/` - **OVERLAPS** with `src/tracking/mlflow/`:
  - `helpers.py` (overlap)
  - `mlflow_utils.py` (overlap)

- `orchestration/jobs/tracking/trackers/` - Should be in `src/tracking/mlflow/trackers/`:
  - `sweep_tracker.py`
  - `benchmark_tracker.py`
  - `training_tracker.py`
  - `conversion_tracker.py`

- `orchestration/jobs/tracking/finder/run_finder.py` - Should be in `src/tracking/mlflow/`
- `orchestration/jobs/tracking/mlflow_*.py` - Should be consolidated into `src/tracking/mlflow/`

#### 4. Top-Level Job Files

- `orchestration/jobs/errors.py` - Should be in `src/hpo/exceptions.py` or `src/shared/exceptions.py`
- `orchestration/jobs/runtime.py` - Should be in `src/azureml/jobs.py` (Azure ML job utilities)
- `orchestration/jobs/training.py` - Should be in `src/training_exec/jobs.py` (Azure ML job creation)
- `orchestration/jobs/sweeps.py` - Should be in `src/hpo/execution/azureml/` (Azure ML sweep job creation)
- `orchestration/jobs/conversion.py` - Should be in `src/conversion/jobs.py` (Azure ML job creation)
- `orchestration/jobs/local_selection.py` - **DUPLICATE** of `src/selection/local_selection.py`
- `orchestration/jobs/local_selection_v2.py` - Should be in `src/selection/` (improved selection logic)

#### 5. Remaining Orchestration Files

- `orchestration/benchmark_utils.py` - Should be in `src/benchmarking/utils.py` (already moved, check for duplicates)
- `orchestration/config_loader.py` - **DUPLICATE** of `src/config/loader.py` (facade should remain)
- `orchestration/conversion_config.py` - **DUPLICATE** of `src/config/conversion.py` (facade should remain)
- `orchestration/final_training_config.py` - **DUPLICATE** of `src/config/training.py` (facade should remain)
- `orchestration/config_compat.py` - **DUPLICATE** of `src/config/validation.py` (facade should remain)
- `orchestration/environment.py` - **DUPLICATE** of `src/config/environment.py` (facade should remain)
- `orchestration/fingerprints.py` - **DUPLICATE** of `src/fingerprints/compute.py` (facade should remain)
- `orchestration/index_manager.py` - **DUPLICATE** of `src/metadata/index.py` (facade should remain)
- `orchestration/metadata_manager.py` - **DUPLICATE** of `src/metadata/training.py` (facade should remain)
- `orchestration/constants.py` - **DUPLICATE** of `src/constants/orchestration.py` (facade should remain)
- `orchestration/data_assets.py` - **DUPLICATE** of `src/azureml/data_assets.py` (facade should remain)
- `orchestration/drive_backup.py` - **DUPLICATE** of `src/storage/drive.py` (facade should remain)
- `orchestration/mlflow_utils.py` - **DUPLICATE** of `src/tracking/mlflow/setup.py` (facade should remain)
- `orchestration/path_resolution.py` - **DUPLICATE** of `src/paths/` (facade should remain)
- `orchestration/naming*.py` - **DUPLICATES** of `src/naming/` (facades should remain)

## Proposed Module Structure

```
src/
├── hpo/
│   ├── execution/
│   │   ├── local/
│   │   │   ├── sweep.py (from orchestration/jobs/hpo/local_sweeps.py)
│   │   │   ├── refit/
│   │   │   │   └── executor.py (from orchestration/jobs/hpo/local/refit/executor.py)
│   │   │   └── cv/
│   │   │       └── orchestrator.py (from orchestration/jobs/hpo/local/cv/orchestrator.py)
│   │   └── azureml/
│   │       └── sweeps.py (from orchestration/jobs/sweeps.py)
│   ├── trial/
│   │   ├── run_manager.py (from orchestration/jobs/hpo/local/trial/run_manager.py)
│   │   ├── metrics.py (already exists, check for duplicates)
│   │   └── meta_generator.py (from orchestration/jobs/hpo/local/trial_meta_generator.py)
│   ├── tracking/
│   │   ├── setup.py (from orchestration/jobs/hpo/local/mlflow/run_setup.py)
│   │   └── cleanup.py (already exists, merge orchestration/jobs/hpo/local/mlflow/cleanup.py)
│   ├── core/
│   │   ├── search_space.py (from orchestration/jobs/hpo/search_space.py)
│   │   └── study_extractor.py (from orchestration/jobs/hpo/study_extractor.py)
│   ├── utils/
│   │   └── helpers.py (from orchestration/jobs/hpo/hpo_helpers.py)
│   └── exceptions.py (from orchestration/jobs/errors.py)
│
├── tracking/
│   └── mlflow/
│       ├── trackers/
│       │   ├── sweep_tracker.py (from orchestration/jobs/tracking/trackers/)
│       │   ├── benchmark_tracker.py
│       │   ├── training_tracker.py
│       │   └── conversion_tracker.py
│       ├── finder.py (from orchestration/jobs/tracking/finder/run_finder.py)
│       └── [consolidate orchestration/jobs/tracking/mlflow_*.py files]
│
├── naming/
│   └── mlflow/
│       └── [consolidate orchestration/jobs/tracking/naming/ files]
│
├── training_exec/
│   ├── jobs.py (from orchestration/jobs/training.py)
│   └── tags.py (from orchestration/jobs/final_training/tags.py)
│
├── conversion/
│   └── jobs.py (from orchestration/jobs/conversion.py)
│
├── azureml/
│   └── jobs.py (from orchestration/jobs/runtime.py)
│
├── selection/
│   └── local_selection_v2.py (from orchestration/jobs/local_selection_v2.py)
│
└── orchestration/ (legacy facades only)
    ├── __init__.py
    └── jobs/ (remove after migration)
```

## Implementation Phases

### Phase 1: Remove Duplicate Files

1. Delete duplicate files in `orchestration/jobs/selection/` (all files)
2. Delete duplicate `orchestration/jobs/benchmarking/orchestrator.py`
3. Delete duplicate `orchestration/jobs/conversion/executor.py`
4. Delete duplicate `orchestration/jobs/final_training/executor.py`
5. Delete duplicate `orchestration/jobs/local_selection.py`

### Phase 2: Move HPO Files

1. Move `orchestration/jobs/hpo/local_sweeps.py` → `src/hpo/execution/local/sweep.py` (merge with existing)
2. Move `orchestration/jobs/hpo/hpo_helpers.py` → `src/hpo/utils/helpers.py` (merge with existing)
3. Move `orchestration/jobs/hpo/search_space.py` → `src/hpo/core/search_space.py` (merge with existing)
4. Move `orchestration/jobs/hpo/study_extractor.py` → `src/hpo/core/study_extractor.py`
5. Move `orchestration/jobs/hpo/local/refit/executor.py` → `src/hpo/execution/local/refit/executor.py` (merge with existing)
6. Move `orchestration/jobs/hpo/local/cv/orchestrator.py` → `src/hpo/execution/local/cv/orchestrator.py` (merge with existing)
7. Move `orchestration/jobs/hpo/local/trial/run_manager.py` → `src/hpo/trial/run_manager.py`
8. Move `orchestration/jobs/hpo/local/trial/metrics.py` → `src/hpo/trial/metrics.py` (merge with existing)
9. Move `orchestration/jobs/hpo/local/trial_meta_generator.py` → `src/hpo/trial/meta_generator.py`
10. Move `orchestration/jobs/hpo/local/mlflow/run_setup.py` → `src/hpo/tracking/setup.py` (merge with existing)
11. Move `orchestration/jobs/hpo/local/mlflow/cleanup.py` → `src/hpo/tracking/cleanup.py` (merge with existing)

### Phase 3: Move Tracking Files

1. Move `orchestration/jobs/tracking/trackers/*` → `src/tracking/mlflow/trackers/`
2. Move `orchestration/jobs/tracking/finder/run_finder.py` → `src/tracking/mlflow/finder.py`
3. Consolidate `orchestration/jobs/tracking/mlflow_*.py` into `src/tracking/mlflow/`
4. Consolidate `orchestration/jobs/tracking/utils/*` into `src/tracking/mlflow/utils/` (check for duplicates)

### Phase 4: Move Naming Files

1. Consolidate `orchestration/jobs/tracking/naming/*` into `src/naming/mlflow/` (check for duplicates with existing files)

### Phase 5: Move Job Creation Files

1. Move `orchestration/jobs/training.py` → `src/training_exec/jobs.py`
2. Move `orchestration/jobs/sweeps.py` → `src/hpo/execution/azureml/sweeps.py` (merge with existing)
3. Move `orchestration/jobs/conversion.py` → `src/conversion/jobs.py`
4. Move `orchestration/jobs/runtime.py` → `src/azureml/jobs.py`
5. Move `orchestration/jobs/errors.py` → `src/hpo/exceptions.py` (merge with existing if any)
6. Move `orchestration/jobs/final_training/tags.py` → `src/training_exec/tags.py` (merge with existing)
7. Move `orchestration/jobs/local_selection_v2.py` → `src/selection/local_selection_v2.py`

### Phase 6: Update Imports

1. Update all imports from `orchestration.jobs.*` to new module locations
2. Update imports in notebooks
3. Update imports in tests

### Phase 7: Create/Update Facades

1. Update `orchestration/__init__.py` to re-export from new locations with deprecation warnings
2. Create facades in `orchestration/jobs/` if needed for backward compatibility

### Phase 8: Remove Empty Directories

1. Remove `orchestration/jobs/` directory structure after migration
2. Keep only facades in `orchestration/` for backward compatibility

## DRY Principles Applied

1. **Eliminate Duplicates**: Remove all duplicate files, keeping only the consolidated versions
2. **Consolidate Related Functionality**: Group related functions into logical modules (HPO, tracking, naming, etc.)
3. **Single Source of Truth**: Each piece of functionality exists in exactly one location
4. **Clear Module Boundaries**: Each module has a clear, single responsibility
5. **Backward Compatibility**: Maintain facades in `orchestration/` for existing code

## Key Decisions

1. **HPO Module**: All HPO-related code goes into `src/hpo/` with clear sub-modules (execution, trial, tracking, core, utils)
2. **Tracking Module**: All MLflow tracking code goes into `src/tracking/mlflow/` with trackers as sub-modules
3. **Naming Module**: All naming utilities go into `src/naming/mlflow/` (already consolidated)
4. **Job Creation**: Azure ML job creation utilities go into respective modules (`training_exec/jobs.py`, `conversion/jobs.py`, `hpo/execution/azureml/sweeps.py`, `azureml/jobs.py`)
5. **Exceptions**: HPO-specific exceptions go into `src/hpo/exceptions.py`
6. **Facades**: Keep `orchestration/` as legacy facades only, remove `orchestration/jobs/` after migration

## Testing Strategy

1. Run existing tests to ensure no regressions
2. Update test imports to use new module locations
3. Verify backward compatibility through facades
4. Check for any remaining `orchestration.jobs.*` imports
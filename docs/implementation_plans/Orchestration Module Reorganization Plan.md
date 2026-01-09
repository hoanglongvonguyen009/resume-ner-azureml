<!-- 5b2f95d0-62fc-4463-9a09-d01434a2e640 f8784dd0-b2c3-41dc-97e4-ee9260d25619 -->
# Orchestration Module Reorganization Plan

## Overview

Reorganize the `orchestration` module into big modular modules following DRY principles. Check for overlaps with existing `naming`, `paths`, `tracking`, and `hpo` modules, and consolidate remaining orchestration code into logical, reusable modules.

## Current State Analysis

### Already Consolidated

- **Paths**: `orchestration/paths.py`, `orchestration/naming_centralized.py` → `src/paths/` (facades remain)
- **Naming**: `orchestration/naming.py`, `orchestration/tokens.py`, `orchestration/normalize.py` → `src/naming/`, `src/core/` (facades remain)
- **Tracking**: `orchestration/jobs/tracking/utils/*` → `src/tracking/mlflow/` (facades remain)
- **HPO**: `orchestration/jobs/hpo/*` → `src/hpo/` (partially moved, some remains)

### Remaining in Orchestration

**Config Management:**

- `config_loader.py` - Experiment config loading (`ExperimentConfig`, `load_experiment_config`, `load_all_configs`, config hashing)
- `conversion_config.py` - Conversion config loading
- `final_training_config.py` - Final training config loading
- `config_compat.py` - Config compatibility validation
- `environment.py` - Azure ML environment config

**Fingerprints:**

- `fingerprints.py` - Fingerprint computation (`compute_spec_fp`, `compute_exec_fp`, `compute_conv_fp`, `compute_bench_fp`, `compute_hardware_fp`)

**Index/Metadata:**

- `index_manager.py` - Index file management for fast lookup
- `metadata_manager.py` - Persistent metadata for training/conversion stages

**Utilities:**

- `constants.py` - Shared constants
- `mlflow_utils.py` - MLflow setup (`setup_mlflow_for_stage`) - **CHECK OVERLAP with tracking**
- `benchmark_utils.py` - Benchmarking utilities
- `data_assets.py` - Azure ML data asset management
- `drive_backup.py` - Google Drive backup/restore
- `path_resolution.py` - Path resolution utilities - **CHECK OVERLAP with paths**

**Jobs (orchestration/jobs/):**

- `jobs/tracking/` - MLflow tracking utilities - **CHECK OVERLAP with tracking**
- `jobs/selection/` - Best configuration selection logic
- `jobs/benchmarking/` - Benchmarking orchestrator
- `jobs/conversion/` - Conversion executor
- `jobs/final_training/` - Final training executor
- `jobs/hpo/` - HPO code (should move to `hpo/` module)
- Various other job-related files

## Proposed Module Structure

```
src/
├── config/                          # Configuration management
│   ├── __init__.py
│   ├── loader.py                    # Experiment config loading (from config_loader.py)
│   ├── conversion.py                # Conversion config (from conversion_config.py)
│   ├── training.py                  # Final training config (from final_training_config.py)
│   ├── environment.py               # Azure ML environment (from environment.py)
│   └── validation.py                # Config compatibility (from config_compat.py)
├── fingerprints/                    # Fingerprint computation
│   ├── __init__.py
│   └── compute.py                   # All fingerprint functions (from fingerprints.py)
├── metadata/                        # Metadata and index management
│   ├── __init__.py
│   ├── index.py                     # Index management (from index_manager.py)
│   └── training.py                  # Training metadata (from metadata_manager.py)
├── constants/                       # Shared constants
│   ├── __init__.py
│   └── orchestration.py             # Orchestration constants (from constants.py)
├── azureml/                        # Azure ML specific utilities
│   ├── __init__.py
│   ├── data_assets.py              # Data asset management (from data_assets.py)
│   └── environment.py               # (moved from orchestration/environment.py)
├── storage/                         # Storage and backup utilities
│   ├── __init__.py
│   └── drive.py                     # Google Drive backup (from drive_backup.py)
├── selection/                       # Best config selection (from orchestration/jobs/selection/)
│   ├── __init__.py
│   └── [selection logic files]
├── benchmarking/                    # Benchmarking (from orchestration/jobs/benchmarking/)
│   ├── __init__.py
│   └── [benchmarking files]
├── conversion/                      # Conversion (from orchestration/jobs/conversion/)
│   ├── __init__.py
│   └── [conversion files]
├── training/                        # Final training (from orchestration/jobs/final_training/)
│   ├── __init__.py
│   └── [training files]
├── hpo/                             # HPO (already exists, complete migration)
│   └── [hpo files]
└── orchestration/                    # Legacy facades (backward compatibility)
    ├── __init__.py                  # Re-exports from new modules
    └── [facade files for deprecated imports]
```

## DRY Checks and Consolidation

### 1. Path Resolution Overlap

- **Check**: `orchestration/path_resolution.py` vs `paths/validation.py`
- **Action**: Review `path_resolution.py` functions:
  - `validate_path_before_mkdir()` - already in `paths/validation.py`
  - `resolve_hpo_output_dir()` - HPO-specific, move to `hpo/` or `paths/` if generic
- **Decision**: Move HPO-specific path resolution to `hpo/utils/paths.py` or consolidate into `paths/` if generic

### 2. MLflow Utilities Overlap

- **Check**: `orchestration/mlflow_utils.py` vs `tracking/mlflow/`
- **Action**: Review `setup_mlflow_for_stage()`:
  - If it's a thin wrapper around `tracking.mlflow`, consolidate into `tracking/mlflow/setup.py`
  - If it has stage-specific logic, keep in `orchestration/` facade or move to `jobs/`
- **Decision**: Consolidate into `tracking/mlflow/setup.py` if generic, or keep as job-specific utility

### 3. Tracking Module Overlap

- **Check**: `orchestration/jobs/tracking/` vs `tracking/mlflow/`
- **Action**: Review remaining files in `jobs/tracking/`:
  - `trackers/` - Job-specific trackers (keep in `jobs/`)
  - `naming/` - Already moved to `naming/mlflow/` (verify)
  - `config/` - MLflow config loading (check if in `naming/mlflow/config.py`)
  - `artifacts/` - Artifact management (check overlap with `tracking/mlflow/artifacts.py`)
  - `index/` - Run indexing (might be job-specific)
  - `finder/` - Run finding (might be job-specific)
- **Decision**: Keep job-specific trackers in `jobs/tracking/trackers/`, move generic utilities to `tracking/`

### 4. HPO Module Overlap

- **Check**: `orchestration/jobs/hpo/` vs `hpo/`
- **Action**: Move remaining HPO code from `orchestration/jobs/hpo/` to `hpo/`:
  - `local_sweeps.py` → `hpo/execution/local/sweep.py` (verify if already moved)
  - `hpo_helpers.py` → `hpo/utils/helpers.py`
  - `search_space.py` → `hpo/core/search_space.py`
  - `study_extractor.py` → `hpo/core/study.py`
  - `azureml/sweeps.py` → `hpo/execution/azureml/sweeps.py`
- **Decision**: Complete HPO migration, remove from `orchestration/jobs/hpo/`

### 5. Benchmarking Utilities Overlap

- **Check**: `orchestration/benchmark_utils.py` vs `jobs/benchmarking/`
- **Action**: Review if `benchmark_utils.py` is generic or job-specific:
  - If generic (can be used outside jobs), move to `benchmarking/` module
  - If job-specific, move to `jobs/benchmarking/utils.py`
- **Decision**: Move to `jobs/benchmarking/utils.py` if job-specific, or create `benchmarking/` module if generic

## Implementation Phases

### Phase 1: Pre-Implementation Analysis

- [ ] Audit all functions in `orchestration/` for overlaps with `naming/`, `paths/`, `tracking/`, `hpo/`
- [ ] Document which functions are generic vs job-specific
- [ ] Identify circular dependencies
- [ ] List all import sites that need updating

### Phase 2: Create Config Module

- [ ] Create `src/config/` directory
- [ ] Move `config_loader.py` → `config/loader.py`
- [ ] Move `conversion_config.py` → `config/conversion.py`
- [ ] Move `final_training_config.py` → `config/training.py`
- [ ] Move `environment.py` → `config/environment.py` (or `azureml/environment.py`)
- [ ] Move `config_compat.py` → `config/validation.py`
- [ ] Update imports, ensure no circular dependencies

### Phase 3: Create Fingerprints Module

- [ ] Create `src/fingerprints/` directory
- [ ] Move `fingerprints.py` → `fingerprints/compute.py`
- [ ] Update imports

### Phase 4: Create Metadata Module

- [ ] Create `src/metadata/` directory
- [ ] Move `index_manager.py` → `metadata/index.py`
- [ ] Move `metadata_manager.py` → `metadata/training.py`
- [ ] Update imports

### Phase 5: Create Constants Module

- [ ] Create `src/constants/` directory
- [ ] Move `constants.py` → `constants/orchestration.py`
- [ ] Update imports

### Phase 6: Create Azure ML Module

- [ ] Create `src/azureml/` directory
- [ ] Move `data_assets.py` → `azureml/data_assets.py`
- [ ] Move `environment.py` → `azureml/environment.py` (if Azure-specific)
- [ ] Update imports

### Phase 7: Create Storage Module

- [ ] Create `src/storage/` directory
- [ ] Move `drive_backup.py` → `storage/drive.py`
- [ ] Update imports

### Phase 8: Reorganize Jobs

- [ ] Create `src/selection/` module
  - [ ] Move `orchestration/jobs/selection/` → `selection/` (keep internal structure)
  - [ ] Update `selection/__init__.py` to export public functions
  - [ ] Update imports in files that use selection logic
- [ ] Create `src/benchmarking/` module
  - [ ] Move `orchestration/jobs/benchmarking/` → `benchmarking/` (keep internal structure)
  - [ ] Move `orchestration/benchmark_utils.py` → `benchmarking/utils.py` (if generic) or keep in `benchmarking/` if job-specific
  - [ ] Update `benchmarking/__init__.py` to export public functions
  - [ ] Update imports in files that use benchmarking
- [ ] Create `src/conversion/` module
  - [ ] Move `orchestration/jobs/conversion/` → `conversion/` (keep internal structure)
  - [ ] Update `conversion/__init__.py` to export public functions
  - [ ] Update imports in files that use conversion
- [ ] Create `src/training/` module
  - [ ] Move `orchestration/jobs/final_training/` → `training/` (rename from final_training)
  - [ ] Update `training/__init__.py` to export public functions
  - [ ] Update imports in files that use training
- [ ] Complete HPO migration
  - [ ] Move remaining `orchestration/jobs/hpo/` → `hpo/` (verify what's already moved)
  - [ ] Update any remaining imports
  - [ ] Remove empty `orchestration/jobs/hpo/` directory
- [ ] Review `orchestration/jobs/tracking/` for overlaps with `tracking/`
  - [ ] Identify job-specific trackers (keep in appropriate module or create `tracking/trackers/`)
  - [ ] Move generic utilities to `tracking/` if not already there
  - [ ] Update imports accordingly

### Phase 9: Consolidate Overlaps

- [ ] Resolve path resolution overlaps (`path_resolution.py` vs `paths/`)
- [ ] Resolve MLflow utility overlaps (`mlflow_utils.py` vs `tracking/mlflow/`)
- [ ] Resolve tracking overlaps (`jobs/tracking/` vs `tracking/`)
- [ ] Complete HPO migration
- [ ] Resolve benchmarking overlaps

### Phase 10: Create Legacy Facades

- [ ] Create `orchestration/__init__.py` facade re-exporting from new modules
- [ ] Add deprecation warnings
- [ ] Maintain backward compatibility for notebooks

### Phase 11: Update Internal Imports

- [ ] Update all imports in `src/` to use new modules
- [ ] Update imports in `tests/`
- [ ] Keep notebooks using `orchestration.*` imports (via facades)

### Phase 12: Testing and Verification

- [ ] Run all tests
- [ ] Verify no circular dependencies
- [ ] Verify backward compatibility
- [ ] Check for remaining duplicates

## Key Decisions

1. **Config Module**: Consolidate all config loading into `config/` module
2. **Fingerprints**: Standalone module (used by multiple modules)
3. **Metadata**: Separate from config (different concerns)
4. **Constants**: Centralized constants module
5. **Azure ML**: Separate module for Azure-specific code
6. **Storage**: Separate module for storage/backup utilities
7. **Jobs**: Keep job execution code in `jobs/` but reorganize structure
8. **Legacy Facades**: Maintain `orchestration/` facades for backward compatibility

## File Mapping

### Config Module

- `orchestration/config_loader.py` → `config/loader.py`
- `orchestration/conversion_config.py` → `config/conversion.py`
- `orchestration/final_training_config.py` → `config/training.py`
- `orchestration/environment.py` → `config/environment.py` or `azureml/environment.py`
- `orchestration/config_compat.py` → `config/validation.py`

### Fingerprints Module

- `orchestration/fingerprints.py` → `fingerprints/compute.py`

### Metadata Module

- `orchestration/index_manager.py` → `metadata/index.py`
- `orchestration/metadata_manager.py` → `metadata/training.py`

### Constants Module

- `orchestration/constants.py` → `constants/orchestration.py`

### Azure ML Module

- `orchestration/data_assets.py` → `azureml/data_assets.py`

### Storage Module

- `orchestration/drive_backup.py` → `storage/drive.py`

### Jobs Module

- `orchestration/jobs/selection/` → `jobs/selection/`
- `orchestration/jobs/benchmarking/` → `jobs/benchmarking/`
- `orchestration/jobs/conversion/` → `jobs/conversion/`
- `orchestration/jobs/final_training/` → `jobs/training/`
- `orchestration/jobs/hpo/` → Complete migration to `hpo/`

## Notes

- All token expansion logic should use `naming/context_tokens.py`
- All path resolution should use `paths/` module
- All MLflow utilities should use `tracking/mlflow/` module
- All HPO code should be in `hpo/` module
- Maintain backward compatibility via facades in `orchestration/`
- Check for circular dependencies at each phase
- Update tests alongside code moves
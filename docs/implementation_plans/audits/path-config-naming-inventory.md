# Path, Config, and Naming Utilities Inventory

**Date**: 2026-01-18  
**Plan**: `20260118-1131-consolidate-path-config-naming-utilities-comprehensive-master.plan.md`

## Summary

This document catalogs all path resolution, configuration loading, and naming utilities, their usage patterns, and call sites.

## Import Statistics

### Config Loading Functions

**Infrastructure SSOT** (`infrastructure.naming.mlflow.config`):
- `get_naming_config`: 5 import sites
- `load_mlflow_config`: 5 import sites

**Orchestration Duplicate** (`orchestration.jobs.tracking.config.loader`):
- `get_naming_config`: 12 import sites
- `get_index_config`: 1 import site
- `get_auto_increment_config`: 3 import sites
- `get_tracking_config`: 5 import sites
- `get_run_finder_config`: 1 import site

### Path Resolution Functions

**SSOT** (`infrastructure.paths.utils`):
- `resolve_project_paths_with_fallback`: 25+ files using it
- `infer_config_dir`: 5+ files using it
- `resolve_project_paths`: 3 files using it (should migrate to `_with_fallback`)

### Hardcoded Patterns

- `Path.cwd() / "config"`: 1 file (`src/evaluation/selection/trial_finder.py:1227`)

## Call Sites Catalog

### Files Using Orchestration Config Loader (12 files)

1. `src/training/hpo/tracking/setup.py` - `get_naming_config`, `get_auto_increment_config`
2. `src/infrastructure/tracking/mlflow/trackers/training_tracker.py` - `get_tracking_config`
3. `src/infrastructure/tracking/mlflow/finder.py` - `get_run_finder_config`
4. `src/infrastructure/tracking/mlflow/trackers/benchmark_tracker.py` - `get_tracking_config`
5. `src/orchestration/jobs/tracking/mlflow_config_loader.py` - Re-exports
6. `src/orchestration/jobs/tracking/config/__init__.py` - Re-exports
7. `src/infrastructure/tracking/mlflow/trackers/conversion_tracker.py` - `get_tracking_config`
8. `src/training/hpo/tracking/runs.py` - Multiple functions
9. `src/infrastructure/tracking/mlflow/artifacts/uploader.py` - `get_tracking_config`
10. `src/orchestration/jobs/tracking/index/run_index.py` - `get_index_config`

### Files Using Infrastructure Config Loader (5 files)

1. `src/training/hpo/execution/local/cv.py` - `get_naming_config`
2. `src/training/hpo/tracking/cleanup.py` - `get_naming_config`
3. `src/orchestration/jobs/tracking/mlflow_config_loader.py` - `load_mlflow_config`
4. `src/orchestration/jobs/tracking/config/loader.py` - `load_mlflow_config`
5. `src/orchestration/jobs/tracking/config/__init__.py` - `load_mlflow_config`

### Functions That Re-infer `config_dir`

1. `src/training/hpo/tracking/setup.py:104-111` - `setup_hpo_mlflow_run()` - re-infers for hash computation
2. `src/training/hpo/tracking/setup.py:188-191` - `setup_hpo_mlflow_run()` - re-infers via `resolve_project_paths_with_fallback`
3. `src/training/hpo/tracking/setup.py:220-223` - `setup_hpo_mlflow_run()` - fallback path re-infers
4. `src/training/hpo/tracking/setup.py:302` - `commit_run_name_version()` - re-infers
5. `src/training/hpo/execution/local/cv.py:171-173` - `run_cv_trials()` - re-infers
6. `src/training/hpo/execution/local/refit.py:138-139` - `run_refit()` - re-infers
7. `src/training/hpo/tracking/cleanup.py:160-162` - `cleanup_old_runs()` - re-infers
8. `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py:126` - `start_sweep_run()` - re-infers
9. `src/training/core/checkpoint_loader.py:118-123` - `resolve_from_config()` - has fallback logic

### Functions Using `resolve_project_paths()` (without `_with_fallback`)

1. `src/training/core/trainer.py:525-526` - Should use `_with_fallback`
2. `src/training/core/checkpoint_loader.py:118` - Should use `_with_fallback`
3. `src/training/orchestrator.py:212` - Should use `_with_fallback`

## Duplicate Implementations

### Config Loading

- `_validate_naming_config()`: Duplicated in both `infrastructure.naming.mlflow.config` and `orchestration.jobs.tracking.config.loader`
- `_validate_index_config()`: Duplicated
- `_validate_auto_increment_config()`: Duplicated
- `_validate_run_finder_config()`: Duplicated
- `get_naming_config()`: Duplicated (orchestration version wraps infrastructure)
- `get_index_config()`: Duplicated
- `get_auto_increment_config()`: Duplicated
- `get_tracking_config()`: Duplicated
- `get_run_finder_config()`: Duplicated

## Next Steps

1. Replace orchestration config loader with re-exports
2. Update all call sites to use infrastructure SSOT
3. Fix functions to trust provided `config_dir`
4. Standardize path resolution function usage


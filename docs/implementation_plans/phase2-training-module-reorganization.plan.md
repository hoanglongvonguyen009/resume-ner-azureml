<!-- Phase 2: Training Module Reorganization -->
# Phase 2: Training Module Reorganization - Detailed Implementation Plan

## Overview

This plan consolidates training-related modules (`training/`, `training_exec/`, `hpo/`) into a unified `training/` module following feature-level organization:

- `training/core/` - Core training logic (model training, metrics, evaluation)
- `training/hpo/` - Hyperparameter optimization (moved from top-level `hpo/`)
- `training/execution/` - Training execution (subprocess runners, MLflow setup, distributed training)
- `training/cli/` - Command-line interfaces for training operations

**Prerequisites**: Phase 1 (Infrastructure Reorganization) must be completed first.

**Migration Strategy**: Consolidate modules while maintaining backward compatibility through compatibility shims. Remove shims after 1-2 releases.

## Target Structure

```
src/
├── training/                    # Unified training module
│   ├── __init__.py
│   │
│   ├── core/                   # Core training logic
│   │   ├── __init__.py
│   │   ├── trainer.py          # Main training logic (from training/trainer.py)
│   │   ├── model.py            # Model definitions (from training/model.py)
│   │   ├── metrics.py          # Metrics computation (from training/metrics.py)
│   │   ├── evaluator.py        # Model evaluation (from training/evaluator.py)
│   │   ├── checkpoint_loader.py # Checkpoint loading (from training/checkpoint_loader.py)
│   │   ├── cv_utils.py         # Cross-validation utilities (from training/cv_utils.py)
│   │   └── utils.py            # Training utilities (from training/utils.py)
│   │
│   ├── hpo/                    # Hyperparameter optimization (from top-level hpo/)
│   │   ├── __init__.py
│   │   ├── core/               # HPO core logic
│   │   │   ├── __init__.py
│   │   │   ├── study.py        # Optuna study management
│   │   │   ├── optuna_integration.py
│   │   │   ├── search_space.py
│   │   │   └── study_extractor.py
│   │   ├── execution/          # HPO execution
│   │   │   ├── __init__.py
│   │   │   ├── local/          # Local HPO execution
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sweep.py    # HPO sweep orchestration
│   │   │   │   ├── cv.py       # Cross-validation for HPO
│   │   │   │   ├── refit.py    # Refit training
│   │   │   │   └── trial.py    # Trial execution
│   │   │   └── azureml/        # Azure ML HPO execution
│   │   │       └── __init__.py
│   │   ├── checkpoint/         # HPO checkpoint management
│   │   │   ├── __init__.py
│   │   │   ├── storage.py
│   │   │   └── cleanup.py
│   │   ├── tracking/            # HPO tracking
│   │   │   ├── __init__.py
│   │   │   ├── setup.py
│   │   │   ├── runs.py
│   │   │   └── cleanup.py
│   │   ├── trial/              # Trial management
│   │   │   ├── __init__.py
│   │   │   ├── callback.py
│   │   │   ├── meta.py
│   │   │   └── metrics.py
│   │   ├── utils/              # HPO utilities
│   │   │   ├── __init__.py
│   │   │   ├── helpers.py
│   │   │   └── paths.py
│   │   └── exceptions.py
│   │
│   ├── execution/               # Training execution (from training/execution/ + training_exec/)
│   │   ├── __init__.py
│   │   ├── subprocess_runner.py # Subprocess execution (from training/execution/subprocess_runner.py)
│   │   ├── mlflow_setup.py      # MLflow setup (from training/execution/mlflow_setup.py)
│   │   ├── distributed.py       # Distributed training (from training/distributed.py)
│   │   ├── distributed_launcher.py # Distributed launcher (from training/distributed_launcher.py)
│   │   ├── executor.py         # Final training executor (from training_exec/executor.py)
│   │   ├── jobs.py              # Training jobs (from training_exec/jobs.py)
│   │   ├── lineage.py           # Training lineage (from training_exec/lineage.py)
│   │   └── tags.py              # Training tags (from training_exec/tags.py)
│   │
│   ├── cli/                     # Command-line interfaces
│   │   ├── __init__.py
│   │   ├── train.py            # Training CLI (from training/train.py)
│   │   └── cli.py              # CLI utilities (from training/cli.py)
│   │
│   ├── orchestrator.py          # Training orchestration (from training/orchestrator.py)
│   ├── config.py                # Training configuration (from training/config.py)
│   ├── logging.py               # Training logging (from training/logging.py)
│   └── data.py                  # Training data utilities (deprecated - use data/ module)
│
└── [other modules remain unchanged]
```

## Important Decisions

1. **Consolidate all training-related code** - `training/`, `training_exec/`, and `hpo/` into unified `training/` module
2. **Keep HPO as submodule** - `training/hpo/` maintains its internal structure
3. **Separate execution concerns** - `training/execution/` handles all execution-related code
4. **Maintain backward compatibility** - Create compatibility shims for old imports
5. **Data handling** - Note that data handling has moved to top-level `data/` module (from Phase 1)
6. **Remove shims after 1-2 releases** - Breaking change, plan accordingly

## Phase 1: Pre-Implementation Analysis

- [ ] **Audit training/ module structure**
  - [ ] List all files in `src/training/` and their purposes
  - [ ] Identify core training logic vs execution vs configuration
  - [ ] Document dependencies between training modules
  - [ ] Map files to target structure (core/, execution/, cli/)

- [ ] **Audit training_exec/ module structure**
  - [ ] List all files in `src/training_exec/` and their purposes
  - [ ] Identify which files belong in `training/execution/`
  - [ ] Document dependencies on `training/` and `infrastructure/`
  - [ ] Check for any shared code that should be in `common/`

- [ ] **Audit hpo/ module structure**
  - [ ] List all files in `src/hpo/` and their purposes
  - [ ] Verify internal structure (core/, execution/, checkpoint/, tracking/, trial/, utils/)
  - [ ] Document dependencies on `training/` and `infrastructure/`
  - [ ] Identify any code that should move to `training/core/` or `training/execution/`

- [ ] **Audit external dependencies**
  - [ ] Find all imports of `from training import ...`
  - [ ] Find all imports of `from training_exec import ...`
  - [ ] Find all imports of `from hpo import ...`
  - [ ] Document which modules depend on training functionality
  - [ ] Identify notebooks, scripts, and tests that import training modules

- [ ] **Audit orchestration/jobs/ dependencies**
  - [ ] Review `orchestration/jobs/hpo/` - identify what should move to `training/hpo/`
  - [ ] Review `orchestration/jobs/final_training/` - identify what should move to `training/execution/`
  - [ ] Document orchestration facade patterns that need updating

- [ ] **Create dependency graph**
  - [ ] Map all import relationships within training modules
  - [ ] Map dependencies on infrastructure/, common/, and data/
  - [ ] Identify circular dependencies
  - [ ] Plan import order to avoid cycles

- [ ] **Review data module dependencies**
  - [ ] Verify `training/data.py` and `training/data_combiner.py` have been moved to `data/` (from Phase 1)
  - [ ] Update any remaining references to use `data.*` imports
  - [ ] Document any training-specific data handling that should stay in `training/`

## Phase 2: Create Training Core Module Structure

- [ ] **Create training/core/ directory**
  - [ ] Create `src/training/core/` directory
  - [ ] Create `src/training/core/__init__.py`
  - [ ] Add module docstring explaining core training logic

- [ ] **Move core training files**
  - [ ] Move `src/training/trainer.py` → `training/core/trainer.py`
  - [ ] Move `src/training/model.py` → `training/core/model.py`
  - [ ] Move `src/training/metrics.py` → `training/core/metrics.py`
  - [ ] Move `src/training/evaluator.py` → `training/core/evaluator.py`
  - [ ] Move `src/training/checkpoint_loader.py` → `training/core/checkpoint_loader.py`
  - [ ] Move `src/training/cv_utils.py` → `training/core/cv_utils.py`
  - [ ] Move `src/training/utils.py` → `training/core/utils.py`

- [ ] **Update training/core/ imports**
  - [ ] Update all internal imports within core/ to use relative imports
  - [ ] Update imports to use `infrastructure.*`, `common.*`, and `data.*`
  - [ ] Fix any broken imports
  - [ ] Update `training/core/__init__.py` to export public APIs

- [ ] **Create compatibility shims**
  - [ ] Create `src/training/trainer.py` - shim to `training.core.trainer`
  - [ ] Create `src/training/model.py` - shim to `training.core.model`
  - [ ] Create `src/training/metrics.py` - shim to `training.core.metrics`
  - [ ] Create `src/training/evaluator.py` - shim to `training.core.evaluator`
  - [ ] Create `src/training/checkpoint_loader.py` - shim to `training.core.checkpoint_loader`
  - [ ] Create `src/training/cv_utils.py` - shim to `training.core.cv_utils`
  - [ ] Create `src/training/utils.py` - shim to `training.core.utils`
  - [ ] Add deprecation warnings to all shims

## Phase 3: Move HPO to Training Module

- [ ] **Create training/hpo/ directory**
  - [ ] Create `src/training/hpo/` directory
  - [ ] Create `src/training/hpo/__init__.py`
  - [ ] Add module docstring explaining HPO functionality

- [ ] **Move hpo/ to training/hpo/**
  - [ ] Move entire `src/hpo/` directory → `src/training/hpo/`
  - [ ] Preserve internal structure (core/, execution/, checkpoint/, tracking/, trial/, utils/)
  - [ ] Update all internal imports within hpo/ to use relative imports
  - [ ] Update imports to use `infrastructure.*`, `common.*`, and `data.*`
  - [ ] Update `training/hpo/__init__.py` to export public APIs

- [ ] **Update HPO imports**
  - [ ] Update imports from `from hpo import ...` to `from training.hpo import ...`
  - [ ] Update imports from `from hpo.core import ...` to `from training.hpo.core import ...`
  - [ ] Update imports from `from hpo.execution import ...` to `from training.hpo.execution import ...`
  - [ ] Fix any broken imports

- [ ] **Create compatibility shim**
  - [ ] Create `src/hpo/__init__.py` - shim to `training.hpo`
  - [ ] Create compatibility shims for submodules:
    - [ ] `src/hpo/core/__init__.py` - shim to `training.hpo.core`
    - [ ] `src/hpo/execution/__init__.py` - shim to `training.hpo.execution`
    - [ ] `src/hpo/checkpoint/__init__.py` - shim to `training.hpo.checkpoint`
    - [ ] `src/hpo/tracking/__init__.py` - shim to `training.hpo.tracking`
    - [ ] `src/hpo/trial/__init__.py` - shim to `training.hpo.trial`
    - [ ] `src/hpo/utils/__init__.py` - shim to `training.hpo.utils`
  - [ ] Add deprecation warnings to all shims

- [ ] **Update orchestration/jobs/hpo/**
  - [ ] Update all imports in `orchestration/jobs/hpo/` to use `training.hpo.*`
  - [ ] Keep public API stable for external callers
  - [ ] Add deprecation warnings if needed

## Phase 4: Consolidate Training Execution

- [ ] **Create training/execution/ directory**
  - [ ] Create `src/training/execution/` directory (if not exists)
  - [ ] Create `src/training/execution/__init__.py`
  - [ ] Add module docstring explaining execution functionality

- [ ] **Move training execution files**
  - [ ] Keep `src/training/execution/subprocess_runner.py` in place
  - [ ] Keep `src/training/execution/mlflow_setup.py` in place
  - [ ] Move `src/training/distributed.py` → `training/execution/distributed.py`
  - [ ] Move `src/training/distributed_launcher.py` → `training/execution/distributed_launcher.py`

- [ ] **Move training_exec/ files**
  - [ ] Move `src/training_exec/executor.py` → `training/execution/executor.py`
  - [ ] Move `src/training_exec/jobs.py` → `training/execution/jobs.py`
  - [ ] Move `src/training_exec/lineage.py` → `training/execution/lineage.py`
  - [ ] Move `src/training_exec/tags.py` → `training/execution/tags.py`

- [ ] **Update training/execution/ imports**
  - [ ] Update all internal imports within execution/ to use relative imports
  - [ ] Update imports to use `training.core.*`, `infrastructure.*`, `common.*`, and `data.*`
  - [ ] Fix any broken imports
  - [ ] Update `training/execution/__init__.py` to export public APIs

- [ ] **Create compatibility shims**
  - [ ] Create `src/training/distributed.py` - shim to `training.execution.distributed`
  - [ ] Create `src/training/distributed_launcher.py` - shim to `training.execution.distributed_launcher`
  - [ ] Create `src/training_exec/__init__.py` - shim to `training.execution`
  - [ ] Create `src/training_exec/executor.py` - shim to `training.execution.executor`
  - [ ] Create `src/training_exec/jobs.py` - shim to `training.execution.jobs`
  - [ ] Create `src/training_exec/lineage.py` - shim to `training.execution.lineage`
  - [ ] Create `src/training_exec/tags.py` - shim to `training.execution.tags`
  - [ ] Add deprecation warnings to all shims

## Phase 5: Create Training CLI Module

- [ ] **Create training/cli/ directory**
  - [ ] Create `src/training/cli/` directory
  - [ ] Create `src/training/cli/__init__.py`
  - [ ] Add module docstring explaining CLI functionality

- [ ] **Move CLI files**
  - [ ] Move `src/training/train.py` → `training/cli/train.py`
  - [ ] Move `src/training/cli.py` → `training/cli/cli.py` (rename to avoid conflict)

- [ ] **Update training/cli/ imports**
  - [ ] Update imports to use `training.core.*`, `training.execution.*`, `infrastructure.*`, etc.
  - [ ] Fix any broken imports
  - [ ] Update `training/cli/__init__.py` to export public APIs

- [ ] **Create compatibility shims**
  - [ ] Create `src/training/train.py` - shim to `training.cli.train`
  - [ ] Create `src/training/cli.py` - shim to `training.cli.cli` (if needed)
  - [ ] Add deprecation warnings to shims

- [ ] **Update entry points**
  - [ ] Update any `setup.py` or `pyproject.toml` entry points
  - [ ] Update scripts that call training CLI
  - [ ] Update documentation for CLI usage

## Phase 6: Update Remaining Training Files

- [ ] **Update training/ top-level files**
  - [ ] Update `src/training/orchestrator.py` - update imports to use `training.core.*`, `training.execution.*`
  - [ ] Update `src/training/config.py` - update imports to use `infrastructure.*`
  - [ ] Update `src/training/logging.py` - update imports to use `infrastructure.*`
  - [ ] Update `src/training/data.py` - mark as deprecated, redirect to `data.*` imports

- [ ] **Update training/__init__.py**
  - [ ] Export public APIs from submodules:
    - [ ] `from training.core import *`
    - [ ] `from training.hpo import *`
    - [ ] `from training.execution import *`
    - [ ] `from training.cli import *`
  - [ ] Maintain backward compatibility signatures
  - [ ] Add deprecation timeline documentation

## Phase 7: Update External Imports

- [ ] **Update imports in feature modules**
  - [ ] Update `src/benchmarking/` imports to use `training.*` instead of `hpo.*`
  - [ ] Update `src/selection/` imports to use `training.*` instead of `hpo.*`
  - [ ] Update `src/conversion/` imports if they reference training modules
  - [ ] Update `src/api/` imports if they reference training modules
  - [ ] Update `src/testing/` imports to use `training.*` instead of `hpo.*`

- [ ] **Update imports in orchestration/**
  - [ ] Update `orchestration/jobs/hpo/` to use `training.hpo.*`
  - [ ] Update `orchestration/jobs/final_training/` to use `training.execution.*`
  - [ ] Keep public API stable for external callers
  - [ ] Add deprecation warnings where appropriate

- [ ] **Update imports in tests/**
  - [ ] Update test imports to use new module paths
  - [ ] Keep tests working with both old and new imports during transition
  - [ ] Update test fixtures if needed
  - [ ] Update test paths and imports in test files

- [ ] **Update imports in notebooks**
  - [ ] Update notebooks to use new `training.*` imports
  - [ ] Test notebooks work with new structure
  - [ ] Update notebook documentation if needed

- [ ] **Update src/__init__.py**
  - [ ] Update exports to use new training module structure
  - [ ] Maintain backward compatibility
  - [ ] Add deprecation warnings for old imports

## Phase 8: Testing and Verification

- [ ] **Run existing tests**
  - [ ] Run all training tests
  - [ ] Run all HPO tests
  - [ ] Run all training_exec tests
  - [ ] Run all integration tests that use training modules
  - [ ] Fix any test failures

- [ ] **Test backward compatibility**
  - [ ] Test that `from training import ...` still works (via shims)
  - [ ] Test that `from hpo import ...` still works (via shims)
  - [ ] Test that `from training_exec import ...` still works (via shims)
  - [ ] Test that deprecation warnings are shown
  - [ ] Test that notebooks work without changes (if using shims)
  - [ ] Verify no breaking changes for external users during transition

- [ ] **Verify no circular dependencies**
  - [ ] Run dependency checker
  - [ ] Verify `training/core/` depends only on `infrastructure/`, `common/`, and `data/`
  - [ ] Verify `training/hpo/` depends on `training/core/`, `infrastructure/`, `common/`, and `data/`
  - [ ] Verify `training/execution/` depends on `training/core/`, `infrastructure/`, `common/`, and `data/`
  - [ ] Verify `training/cli/` depends on `training/core/`, `training/execution/`, `infrastructure/`, etc.
  - [ ] Verify no cycles between training submodules

- [ ] **Test import performance**
  - [ ] Verify no significant import time regressions
  - [ ] Test that training modules load efficiently
  - [ ] Test that HPO modules load efficiently

- [ ] **Verify module isolation**
  - [ ] Test each training submodule independently
  - [ ] Test that core training logic is isolated from execution
  - [ ] Test that HPO is properly isolated but can use training core
  - [ ] Verify SRP (Single Responsibility Principle) is maintained

- [ ] **Test training workflows**
  - [ ] Test basic training workflow
  - [ ] Test HPO workflow
  - [ ] Test distributed training workflow
  - [ ] Test final training execution workflow
  - [ ] Test CLI commands

## Phase 9: Documentation and Cleanup

- [ ] **Update documentation**
  - [ ] Document new import patterns in README
  - [ ] Document deprecation timeline for old imports (`hpo.*`, `training_exec.*`)
  - [ ] Update architecture diagrams to show new training module structure
  - [ ] Document migration path for internal code
  - [ ] Update API documentation

- [ ] **Code cleanup**
  - [ ] Remove unused imports
  - [ ] Fix any linter warnings
  - [ ] Ensure consistent code style
  - [ ] Update type hints if needed
  - [ ] Remove any dead code

- [ ] **Final verification**
  - [ ] Run full test suite
  - [ ] Verify no regressions
  - [ ] Check code coverage
  - [ ] Verify all compatibility shims work
  - [ ] Verify all training workflows function correctly

## Phase 10: Remove Compatibility Shims (Future - After 1-2 Releases)

- [ ] **Remove top-level hpo/ shims**
  - [ ] Remove `src/hpo/` directory and all shims
  - [ ] Update all remaining imports to use `training.hpo.*`
  - [ ] Update documentation

- [ ] **Remove training_exec/ shims**
  - [ ] Remove `src/training_exec/` directory and all shims
  - [ ] Update all remaining imports to use `training.execution.*`
  - [ ] Update documentation

- [ ] **Remove training/ top-level shims**
  - [ ] Remove shims for `trainer.py`, `model.py`, `metrics.py`, etc.
  - [ ] Update all remaining imports to use `training.core.*`
  - [ ] Update documentation

- [ ] **Final cleanup**
  - [ ] Remove all deprecation warnings
  - [ ] Update all notebooks to use new imports
  - [ ] Final test run
  - [ ] Update migration documentation

## Quick Reference: File Mapping

### Training Core Module

- `src/training/trainer.py` → `training/core/trainer.py`
- `src/training/model.py` → `training/core/model.py`
- `src/training/metrics.py` → `training/core/metrics.py`
- `src/training/evaluator.py` → `training/core/evaluator.py`
- `src/training/checkpoint_loader.py` → `training/core/checkpoint_loader.py`
- `src/training/cv_utils.py` → `training/core/cv_utils.py`
- `src/training/utils.py` → `training/core/utils.py`

### Training HPO Module

- `src/hpo/` → `training/hpo/` (entire directory, preserve structure)
  - `src/hpo/core/` → `training/hpo/core/`
  - `src/hpo/execution/` → `training/hpo/execution/`
  - `src/hpo/checkpoint/` → `training/hpo/checkpoint/`
  - `src/hpo/tracking/` → `training/hpo/tracking/`
  - `src/hpo/trial/` → `training/hpo/trial/`
  - `src/hpo/utils/` → `training/hpo/utils/`

### Training Execution Module

- `src/training/execution/subprocess_runner.py` → `training/execution/subprocess_runner.py` (stays)
- `src/training/execution/mlflow_setup.py` → `training/execution/mlflow_setup.py` (stays)
- `src/training/distributed.py` → `training/execution/distributed.py`
- `src/training/distributed_launcher.py` → `training/execution/distributed_launcher.py`
- `src/training_exec/executor.py` → `training/execution/executor.py`
- `src/training_exec/jobs.py` → `training/execution/jobs.py`
- `src/training_exec/lineage.py` → `training/execution/lineage.py`
- `src/training_exec/tags.py` → `training/execution/tags.py`

### Training CLI Module

- `src/training/train.py` → `training/cli/train.py`
- `src/training/cli.py` → `training/cli/cli.py`

### Training Top-Level Files

- `src/training/orchestrator.py` → Stays (update imports)
- `src/training/config.py` → Stays (update imports)
- `src/training/logging.py` → Stays (update imports)
- `src/training/data.py` → Deprecated (use `data.*` module)

## Notes

- **Prerequisites**: Phase 1 (Infrastructure Reorganization) must be completed
- **Data handling**: Data handling has moved to top-level `data/` module (from Phase 1)
- **Backward compatibility**: Maintain compatibility shims for 1-2 releases
- **Breaking change**: Removing shims will be a breaking change - plan accordingly
- **Testing**: Test thoroughly after each phase before proceeding
- **HPO structure**: HPO maintains its internal structure when moved to `training/hpo/`
- **Execution separation**: Execution code is clearly separated from core training logic

## Dependencies

- **Requires**: Phase 1 (Infrastructure Reorganization) completion
- **Depends on**: `infrastructure/`, `common/`, `data/` modules
- **Used by**: `benchmarking/`, `selection/`, `conversion/`, `api/`, `testing/` modules

## Migration Checklist

- [ ] Phase 1: Pre-Implementation Analysis
- [ ] Phase 2: Create Training Core Module Structure
- [ ] Phase 3: Move HPO to Training Module
- [ ] Phase 4: Consolidate Training Execution
- [ ] Phase 5: Create Training CLI Module
- [ ] Phase 6: Update Remaining Training Files
- [ ] Phase 7: Update External Imports
- [ ] Phase 8: Testing and Verification
- [ ] Phase 9: Documentation and Cleanup
- [ ] Phase 10: Remove Compatibility Shims (Future)


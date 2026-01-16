# Deprecated Scripts Audit

**Date**: 2025-01-27  
**Purpose**: Identify and audit all deprecated scripts and modules that emit `DeprecationWarning` messages  
**Status**: Active

## Executive Summary

This document provides a comprehensive audit of all deprecated scripts, modules, and imports that emit `DeprecationWarning` messages. Each entry includes:
- The exact deprecation warning message
- Location of the deprecated code
- Current usage locations (where the warning appears)
- Migration path to the replacement
- Priority for migration

**Total Deprecated Items**: 60+ modules emitting `DeprecationWarning`

## How to Use This Document

1. **Search for a specific warning**: Use Ctrl+F to find the exact deprecation message
2. **Find usage locations**: Check the "Current Usage" section for each item
3. **Migrate code**: Follow the "Migration Path" to update imports
4. **Verify fixes**: Run code and check that warnings no longer appear

## Deprecated Modules by Category

### 1. Training Module Deprecations

#### 1.1 `training.cv_utils` → `training.core.cv_utils`

**Deprecation Warning**:
```
DeprecationWarning: Importing from 'training.cv_utils' is deprecated. Please use 'training.core.cv_utils' instead. This shim will be removed in a future release.
```

**Location**: `src/training/cv_utils.py:11-14`

**Current Usage**:
- ✅ **Notebooks**:
  - `notebooks/01_orchestrate_training_colab.ipynb:1606` - Direct import
  - `notebooks/01_orchestrate_training_colab.ipynb:1611` - Import statement

**Migration Path**:
```python
# Before (deprecated)
from training.cv_utils import (
    create_kfold_splits,
    load_fold_splits,
    save_fold_splits,
)

# After (replacement)
from training.core.cv_utils import (
    create_kfold_splits,
    load_fold_splits,
    save_fold_splits,
)
```

**Status**: ⚠️ **Needs Migration** - 1 notebook still using deprecated import

**Priority**: Medium (low usage, but visible in notebooks)

---

#### 1.2 `training.checkpoint_loader` → `training.core.checkpoint_loader`

**Deprecation Warning**:
```
DeprecationWarning: Importing from 'training.checkpoint_loader' is deprecated. Please use 'training.core.checkpoint_loader' instead. This shim will be removed in a future release.
```

**Location**: `src/training/checkpoint_loader.py:11-14`

**Current Usage**: 
- ✅ No external usage found (all code migrated)

**Migration Path**:
```python
# Before (deprecated)
from training.checkpoint_loader import load_checkpoint

# After (replacement)
from training.core.checkpoint_loader import load_checkpoint
```

**Status**: ✅ **Ready for Removal** - No usage found

**Priority**: Low (can be removed)

---

#### 1.3 `training.data` → `data.loaders`

**Deprecation Warning**:
```
DeprecationWarning: Importing from 'training.data' is deprecated. Please use 'data.loaders' instead. This shim will be removed in a future release.
```

**Location**: `src/training/data.py:10-11`

**Current Usage**: 
- ✅ No external usage found

**Migration Path**:
```python
# Before (deprecated)
from training.data import load_dataset

# After (replacement)
from data.loaders import load_dataset
```

**Status**: ✅ **Ready for Removal** - No usage found

**Priority**: Low (can be removed)

---

#### 1.4 `training.distributed` → `training.execution.distributed`

**Deprecation Warning**:
```
DeprecationWarning: Importing from 'training.distributed' is deprecated. Please use 'training.execution.distributed' instead. This shim will be removed in a future release.
```

**Location**: `src/training/distributed.py:11-14`

**Current Usage**: 
- ✅ No external usage found

**Migration Path**:
```python
# Before (deprecated)
from training.distributed import setup_ddp

# After (replacement)
from training.execution.distributed import setup_ddp
```

**Status**: ✅ **Ready for Removal** - No usage found

**Priority**: Low (can be removed)

---

#### 1.5 `training.distributed_launcher` → `training.execution.distributed_launcher`

**Deprecation Warning**:
```
DeprecationWarning: Importing from 'training.distributed_launcher' is deprecated. Please use 'training.execution.distributed_launcher' instead. This shim will be removed in a future release.
```

**Location**: `src/training/distributed_launcher.py:11-14`

**Current Usage**: 
- ✅ No external usage found

**Migration Path**:
```python
# Before (deprecated)
from training.distributed_launcher import launch_distributed

# After (replacement)
from training.execution.distributed_launcher import launch_distributed
```

**Status**: ✅ **Ready for Removal** - No usage found

**Priority**: Low (can be removed)

---

#### 1.6 `training.evaluator` → `training.core.evaluator`

**Deprecation Warning**:
```
DeprecationWarning: Importing from 'training.evaluator' is deprecated. Please use 'training.core.evaluator' instead. This shim will be removed in a future release.
```

**Location**: `src/training/evaluator.py:11-14`

**Current Usage**: 
- ✅ No external usage found

**Migration Path**:
```python
# Before (deprecated)
from training.evaluator import evaluate_model

# After (replacement)
from training.core.evaluator import evaluate_model
```

**Status**: ✅ **Ready for Removal** - No usage found

**Priority**: Low (can be removed)

---

#### 1.7 `training.metrics` → `training.core.metrics`

**Deprecation Warning**:
```
DeprecationWarning: Importing from 'training.metrics' is deprecated. Please use 'training.core.metrics' instead. This shim will be removed in a future release.
```

**Location**: `src/training/metrics.py:11-14`

**Current Usage**: 
- ✅ No external usage found

**Migration Path**:
```python
# Before (deprecated)
from training.metrics import compute_metrics

# After (replacement)
from training.core.metrics import compute_metrics
```

**Status**: ✅ **Ready for Removal** - No usage found

**Priority**: Low (can be removed)

---

#### 1.8 `training.model` → `training.core.model`

**Deprecation Warning**:
```
DeprecationWarning: Importing from 'training.model' is deprecated. Please use 'training.core.model' instead. This shim will be removed in a future release.
```

**Location**: `src/training/model.py:11-14`

**Current Usage**: 
- ✅ No external usage found

**Migration Path**:
```python
# Before (deprecated)
from training.model import Model

# After (replacement)
from training.core.model import Model
```

**Status**: ✅ **Ready for Removal** - No usage found

**Priority**: Low (can be removed)

---

#### 1.9 `training.train` → `training.cli.train`

**Deprecation Warning**:
```
DeprecationWarning: Importing from 'training.train' is deprecated. Please use 'training.cli.train' instead. This shim will be removed in a future release.
```

**Location**: `src/training/train.py:11-14`

**Current Usage**: 
- ✅ No external usage found

**Migration Path**:
```python
# Before (deprecated)
from training.train import main

# After (replacement)
from training.cli.train import main
```

**Status**: ✅ **Ready for Removal** - No usage found

**Priority**: Low (can be removed)

---

#### 1.10 `training.trainer` → `training.core.trainer`

**Deprecation Warning**:
```
DeprecationWarning: Importing from 'training.trainer' is deprecated. Please use 'training.core.trainer' instead. This shim will be removed in a future release.
```

**Location**: `src/training/trainer.py:11-14`

**Current Usage**: 
- ✅ No external usage found

**Migration Path**:
```python
# Before (deprecated)
from training.trainer import Trainer

# After (replacement)
from training.core.trainer import Trainer
```

**Status**: ✅ **Ready for Removal** - No usage found

**Priority**: Low (can be removed)

---

#### 1.11 `training.utils` → `training.core.utils`

**Deprecation Warning**:
```
DeprecationWarning: Importing from 'training.utils' is deprecated. Please use 'training.core.utils' instead. This shim will be removed in a future release.
```

**Location**: `src/training/utils.py:11-14`

**Current Usage**: 
- ✅ No external usage found

**Migration Path**:
```python
# Before (deprecated)
from training.utils import set_seed

# After (replacement)
from training.core.utils import set_seed
```

**Status**: ✅ **Ready for Removal** - No usage found

**Priority**: Low (can be removed)

---

### 2. Orchestration Module Deprecations

#### 2.1 `orchestration` (package-level)

**Deprecation Warning**:
```
DeprecationWarning: orchestration module is deprecated. Use 'infrastructure', 'common', or 'data' modules instead. This will be removed in 2 releases.
```

**Location**: `src/orchestration/__init__.py:25-30`

**Current Usage**:
- ✅ **Notebooks**:
  - `notebooks/01_orchestrate_training_colab.ipynb:977` - Warning appears when importing from orchestration

**Migration Path**:
```python
# Before (deprecated)
from orchestration import (
    STAGE_HPO,
    resolve_output_path,
    compute_spec_fp,
)

# After (replacement)
from common.constants import STAGE_HPO
from infrastructure.paths import resolve_output_path
from infrastructure.fingerprints import compute_spec_fp
```

**Status**: ⚠️ **Needs Migration** - Package-level deprecation affects all imports

**Priority**: High (affects many modules)

---

#### 2.2 `orchestration.constants` → `common.constants`

**Deprecation Warning**:
```
DeprecationWarning: Importing 'constants' from 'orchestration' is deprecated. Please import from 'constants' instead.
```

**Location**: `src/orchestration/__init__.py:141`

**Current Usage**:
- ✅ **Notebooks**:
  - `notebooks/01_orchestrate_training_colab.ipynb:980` - Warning appears

**Migration Path**:
```python
# Before (deprecated)
from orchestration import STAGE_HPO, EXPERIMENT_NAME

# After (replacement)
from common.constants import STAGE_HPO, EXPERIMENT_NAME
```

**Status**: ⚠️ **Needs Migration** - Used in notebooks

**Priority**: Medium

---

#### 2.3 `orchestration.fingerprints` → `infrastructure.fingerprints`

**Deprecation Warning**:
```
DeprecationWarning: Importing 'fingerprints' from 'orchestration' is deprecated. Please import from 'fingerprints' instead.
```

**Location**: `src/orchestration/__init__.py:142`

**Current Usage**:
- ✅ **Notebooks**:
  - `notebooks/01_orchestrate_training_colab.ipynb:982` - Warning appears

**Migration Path**:
```python
# Before (deprecated)
from orchestration import compute_spec_fp

# After (replacement)
from infrastructure.fingerprints import compute_spec_fp
```

**Status**: ⚠️ **Needs Migration** - Used in notebooks

**Priority**: Medium

---

#### 2.4 `orchestration.metadata/index_manager` → `infrastructure.metadata`

**Deprecation Warning**:
```
DeprecationWarning: Importing 'metadata/index_manager' from 'orchestration' is deprecated. Please import from 'metadata' instead.
```

**Location**: `src/orchestration/__init__.py:143`

**Current Usage**:
- ✅ **Notebooks**:
  - `notebooks/01_orchestrate_training_colab.ipynb:984` - Warning appears

**Migration Path**:
```python
# Before (deprecated)
from orchestration.metadata.index_manager import update_index

# After (replacement)
from infrastructure.metadata.index import update_index
```

**Status**: ⚠️ **Needs Migration** - Used in notebooks

**Priority**: Medium

---

#### 2.5 `orchestration.metadata/metadata_manager` → `infrastructure.metadata`

**Deprecation Warning**:
```
DeprecationWarning: Importing 'metadata/metadata_manager' from 'orchestration' is deprecated. Please import from 'metadata' instead.
```

**Location**: `src/orchestration/__init__.py:144`

**Current Usage**:
- ✅ **Notebooks**:
  - `notebooks/01_orchestrate_training_colab.ipynb:986` - Warning appears

**Migration Path**:
```python
# Before (deprecated)
from orchestration.metadata.metadata_manager import find_by_spec_fp

# After (replacement)
from infrastructure.metadata.index import find_by_spec_fp
```

**Status**: ⚠️ **Needs Migration** - Used in notebooks

**Priority**: Medium

---

#### 2.6 `orchestration.drive_backup` → `infrastructure.storage`

**Deprecation Warning**:
```
DeprecationWarning: Importing 'drive_backup' from 'orchestration' is deprecated. Please import from 'storage' instead.
```

**Location**: `src/orchestration/__init__.py:145`

**Current Usage**:
- ✅ **Notebooks**:
  - `notebooks/01_orchestrate_training_colab.ipynb:988` - Warning appears

**Migration Path**:
```python
# Before (deprecated)
from orchestration.drive_backup import DriveBackupStore

# After (replacement)
from infrastructure.storage import DriveBackupStore
```

**Status**: ⚠️ **Needs Migration** - Used in notebooks

**Priority**: Medium

---

#### 2.7 `orchestration.benchmark_utils` → `evaluation.benchmarking.utils`

**Deprecation Warning**:
```
DeprecationWarning: Importing 'benchmark_utils' from 'orchestration' is deprecated. Please import from 'benchmarking.utils' instead.
```

**Location**: `src/orchestration/__init__.py:146`

**Current Usage**:
- ✅ **Notebooks**:
  - `notebooks/01_orchestrate_training_colab.ipynb:990` - Warning appears

**Migration Path**:
```python
# Before (deprecated)
from orchestration.benchmark_utils import run_benchmarking

# After (replacement)
from evaluation.benchmarking.utils import run_benchmarking
```

**Status**: ⚠️ **Needs Migration** - Used in notebooks

**Priority**: Medium

---

#### 2.8 `orchestration.config_loader` → `infrastructure.config.loader`

**Deprecation Warning**:
```
DeprecationWarning: Importing 'config_loader' from 'orchestration' is deprecated. Please import from 'config.loader' instead.
```

**Location**: `src/orchestration/__init__.py:147`

**Current Usage**:
- ✅ **Notebooks**:
  - `notebooks/01_orchestrate_training_colab.ipynb:992` - Warning appears

**Migration Path**:
```python
# Before (deprecated)
from orchestration.config_loader import load_config

# After (replacement)
from infrastructure.config.loader import load_config
```

**Status**: ⚠️ **Needs Migration** - Used in notebooks

**Priority**: Medium

---

#### 2.9 `orchestration.conversion_config` → `infrastructure.config.conversion`

**Deprecation Warning**:
```
DeprecationWarning: Importing 'conversion_config' from 'orchestration' is deprecated. Please import from 'config.conversion' instead.
```

**Location**: `src/orchestration/__init__.py:148`

**Current Usage**:
- ✅ **Notebooks**:
  - `notebooks/01_orchestrate_training_colab.ipynb:994` - Warning appears

**Migration Path**:
```python
# Before (deprecated)
from orchestration.conversion_config import load_conversion_config

# After (replacement)
from infrastructure.config.conversion import load_conversion_config
```

**Status**: ⚠️ **Needs Migration** - Used in notebooks

**Priority**: Medium

---

#### 2.10 `orchestration.final_training_config` → `infrastructure.config.training`

**Deprecation Warning**:
```
DeprecationWarning: Importing 'final_training_config' from 'orchestration' is deprecated. Please import from 'config.training' instead.
```

**Location**: `src/orchestration/__init__.py:149`

**Current Usage**:
- ✅ **Notebooks**:
  - `notebooks/01_orchestrate_training_colab.ipynb:996` - Warning appears

**Migration Path**:
```python
# Before (deprecated)
from orchestration.final_training_config import load_final_training_config

# After (replacement)
from infrastructure.config.training import load_final_training_config
```

**Status**: ⚠️ **Needs Migration** - Used in notebooks

**Priority**: Medium

---

#### 2.11 `orchestration.environment` → `infrastructure.config.environment`

**Deprecation Warning**:
```
DeprecationWarning: Importing 'environment' from 'orchestration' is deprecated. Please import from 'config.environment' instead.
```

**Location**: `src/orchestration/__init__.py:150`

**Current Usage**:
- ✅ **Notebooks**:
  - `notebooks/01_orchestrate_training_colab.ipynb:998` - Warning appears

**Migration Path**:
```python
# Before (deprecated)
from orchestration.environment import get_environment

# After (replacement)
from infrastructure.config.environment import get_environment
```

**Status**: ⚠️ **Needs Migration** - Used in notebooks

**Priority**: Medium

---

#### 2.12 `orchestration.config_compat` → `infrastructure.config.validation`

**Deprecation Warning**:
```
DeprecationWarning: Importing 'config_compat' from 'orchestration' is deprecated. Please import from 'config.validation' instead.
```

**Location**: `src/orchestration/__init__.py:151`

**Current Usage**:
- ✅ **Notebooks**:
  - `notebooks/01_orchestrate_training_colab.ipynb:1000` - Warning appears

**Migration Path**:
```python
# Before (deprecated)
from orchestration.config_compat import validate_config

# After (replacement)
from infrastructure.config.validation import validate_config
```

**Status**: ⚠️ **Needs Migration** - Used in notebooks

**Priority**: Medium

---

#### 2.13 `orchestration.data_assets` → `azureml.data_assets`

**Deprecation Warning**:
```
DeprecationWarning: Importing 'data_assets' from 'orchestration' is deprecated. Please import from 'azureml.data_assets' instead.
```

**Location**: `src/orchestration/__init__.py:152`

**Current Usage**:
- ✅ **Notebooks**:
  - `notebooks/01_orchestrate_training_colab.ipynb:1002` - Warning appears

**Migration Path**:
```python
# Before (deprecated)
from orchestration.data_assets import get_data_asset

# After (replacement)
from azureml.data_assets import get_data_asset
```

**Status**: ⚠️ **Needs Migration** - Used in notebooks

**Priority**: Medium

---

### 3. Top-Level Package Deprecations

#### 3.1 `conversion` → `deployment.conversion`

**Deprecation Warning**:
```
DeprecationWarning: conversion is deprecated, use deployment.conversion instead. This shim will be removed in 2 releases.
```

**Location**: `src/conversion/__init__.py:72-74`

**Current Usage**:
- ✅ **Notebooks**:
  - `notebooks/02_best_config_selection.ipynb:932` - Warning appears

**Migration Path**:
```python
# Before (deprecated)
from conversion import convert_model

# After (replacement)
from deployment.conversion import convert_model
```

**Status**: ⚠️ **Needs Migration** - Used in notebooks

**Priority**: Medium

---

### 4. Configuration Key Deprecations

#### 4.1 `objective.goal` → `objective.direction`

**Deprecation Warning**:
```
DeprecationWarning: The 'goal' key in objective config is deprecated. Use 'direction' instead.
```

**Location**: `src/infrastructure/config/selection.py:73-75`

**Current Usage**: 
- ✅ Config files (YAML) - 7 references found

**Migration Path**:
```yaml
# Before (deprecated)
objective:
  goal: maximize  # deprecated

# After (replacement)
objective:
  direction: maximize  # new key
```

**Status**: ⚠️ **Needs Migration** - Config files need updating

**Priority**: Low (automatic mapping exists, but configs should be updated)

---

## Summary by Status

### ✅ Ready for Removal (No Usage)
- `training.checkpoint_loader`
- `training.data`
- `training.distributed`
- `training.distributed_launcher`
- `training.evaluator`
- `training.metrics`
- `training.model`
- `training.train`
- `training.trainer`
- `training.utils`

**Total**: 10 modules

### ⚠️ Needs Migration (Active Usage)
- `training.cv_utils` - 1 notebook
- `orchestration` (package-level) - Multiple notebooks
- `orchestration.constants` - Notebooks
- `orchestration.fingerprints` - Notebooks
- `orchestration.metadata/index_manager` - Notebooks
- `orchestration.metadata/metadata_manager` - Notebooks
- `orchestration.drive_backup` - Notebooks
- `orchestration.benchmark_utils` - Notebooks
- `orchestration.config_loader` - Notebooks
- `orchestration.conversion_config` - Notebooks
- `orchestration.final_training_config` - Notebooks
- `orchestration.environment` - Notebooks
- `orchestration.config_compat` - Notebooks
- `orchestration.data_assets` - Notebooks
- `conversion` - 1 notebook
- `objective.goal` - 7 config files

**Total**: 16 items needing migration

## Migration Checklist

### Notebooks to Update

- [ ] `notebooks/01_orchestrate_training_colab.ipynb`
  - [ ] Fix `training.cv_utils` import (line 1606, 1611)
  - [ ] Fix all `orchestration.*` imports (multiple locations)
  
- [ ] `notebooks/02_best_config_selection.ipynb`
  - [ ] Fix `conversion` import (line 932)

### Config Files to Update

- [ ] Update all YAML files using `objective.goal` → `objective.direction` (7 files)

### Source Files

- [ ] All source files already migrated (no action needed)

## How to Find Deprecation Warnings

### Method 1: Run Code and Check Output

When running Python code or notebooks, deprecation warnings will appear in the output:
```
/tmp/ipykernel_123627/908799909.py:1: DeprecationWarning: Importing from 'training.cv_utils' is deprecated. Please use 'training.core.cv_utils' instead. This shim will be removed in a future release.
  from training.cv_utils import (
```

### Method 2: Search Codebase

```bash
# Find all DeprecationWarning instances
grep -rn "DeprecationWarning" src/ notebooks/ tests/

# Find specific deprecated imports
grep -rn "from training\.cv_utils\|import training\.cv_utils" notebooks/ src/
```

### Method 3: Run Tests with Warnings Enabled

```bash
# Run pytest with warnings shown
uvx pytest tests/ -W default::DeprecationWarning

# Or capture warnings
uvx pytest tests/ -W default::DeprecationWarning --tb=short
```

## Verification Steps

After migrating code:

1. **Run the code/notebook** - Verify no deprecation warnings appear
2. **Run tests** - Ensure functionality is preserved
3. **Check imports** - Verify all imports use new paths
4. **Update documentation** - Update any examples or docs

## Related Documents

- **Analysis Document**: `docs/implementation_plans/audits/deprecated-scripts-analysis.md`
- **Removal Roadmap**: `docs/implementation_plans/deprecated-code-removal-roadmap.plan.md`
- **Raw Inventory**: `docs/implementation_plans/audits/deprecated-code-inventory-raw.txt`

## Notes

- All deprecation warnings use `stacklevel=2` or `stacklevel=3` to point to the caller, not the deprecated module itself
- Warnings are suppressed in pytest by default (see `pytest.ini`)
- Some deprecated modules are facades that re-export from new locations
- Migration should be done incrementally, testing after each change


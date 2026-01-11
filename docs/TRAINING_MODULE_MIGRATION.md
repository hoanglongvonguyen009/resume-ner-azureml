# Training Module Migration Guide

## Overview

The training module has been reorganized into a clearer structure with better separation of concerns. This guide helps you migrate from old import paths to the new structure.

## New Module Structure

```
training/
├── core/          # Core training logic (trainer, model, metrics, evaluator)
├── hpo/           # Hyperparameter optimization
├── execution/     # Training execution infrastructure (distributed, subprocess, jobs)
└── cli/           # Command-line interfaces
```

## Migration Guide

### Core Training Functions

**Old (deprecated):**
```python
from training.trainer import train_model
from training.model import create_model_and_tokenizer
from training.metrics import compute_metrics
from training.evaluator import evaluate_model
```

**New (preferred):**
```python
from training.core import train_model
from training.core import create_model_and_tokenizer
from training.core import compute_metrics
from training.core import evaluate_model
```

### Hyperparameter Optimization

**Old (deprecated):**
```python
from hpo import run_local_hpo_sweep
from hpo import extract_best_config_from_study
from hpo import create_search_space
```

**New (preferred):**
```python
from training.hpo import run_local_hpo_sweep
from training.hpo import extract_best_config_from_study
from training.hpo import create_search_space
```

### Training Execution

**Old (deprecated):**
```python
from training_exec import execute_final_training
from training_exec import extract_lineage_from_best_model
from training.distributed import create_run_context
```

**New (preferred):**
```python
from training.execution import execute_final_training
from training.execution import extract_lineage_from_best_model
from training.execution import create_run_context
```

### Cross-Validation Utilities

**Old (deprecated):**
```python
from training.cv_utils import create_kfold_splits
```

**New (preferred):**
```python
from training.core.cv_utils import create_kfold_splits
```

### Data Utilities

**Old (deprecated):**
```python
from training.data import load_dataset
```

**New (preferred):**
```python
from data.loaders import load_dataset
```

## Backward Compatibility

All old import paths continue to work via compatibility shims, but they will show deprecation warnings. The shims will be removed in a future release (1-2 releases after the reorganization).

### Deprecation Warnings

When using old import paths, you'll see warnings like:
```
DeprecationWarning: Importing from 'training.model' is deprecated. 
Please use 'training.core.model' instead. This shim will be removed in a future release.
```

## Top-Level Imports

For backward compatibility, you can still import from the top-level `training` module:

```python
from training import train_model
from training import create_model_and_tokenizer
from training import run_local_hpo_sweep
```

However, for new code, prefer the explicit submodule imports for clarity.

## Module Dependencies

### Dependency Structure

- `training.core` - Depends only on `infrastructure/`, `common/`, `data/`, and standard library
- `training.hpo` - Depends on `training.core/`, `infrastructure/`, `common/`, `data/`
- `training.execution` - Depends on `training.core/`, `infrastructure/`, `common/`, `data/`
- `training.cli` - Depends on `training.core/`, `training.execution/`, `infrastructure/`

### No Circular Dependencies

The module structure is designed to avoid circular dependencies:
- Core does not import execution (except via lazy import in trainer)
- Execution can import core (one-way dependency)
- HPO can import core and execution (one-way dependencies)
- CLI can import core and execution (one-way dependencies)

## Lazy Imports

To avoid requiring heavy dependencies (torch, azure) at module import time, many functions are imported lazily:

- Torch-dependent functions in `training.core` are lazy
- Azure-dependent functions in `training.execution` are lazy
- Optuna-dependent functions in `training.hpo` are lazy

This allows importing the modules without requiring all dependencies to be installed.

## Examples

### Basic Training

```python
from training.core import train_model, create_model_and_tokenizer
from training.config import build_training_config
from data.loaders import load_dataset

config = build_training_config(args, config_dir)
dataset = load_dataset(data_asset)
model, tokenizer = create_model_and_tokenizer(config)
metrics = train_model(config, dataset, output_dir)
```

### HPO Sweep

```python
from training.hpo import run_local_hpo_sweep, extract_best_config_from_study
from training.hpo import create_search_space

search_space = create_search_space(hpo_config)
study = run_local_hpo_sweep(backbone, search_space, ...)
best_config = extract_best_config_from_study(study)
```

### Final Training Execution

```python
from training.execution import execute_final_training
from training.execution import extract_lineage_from_best_model

job = execute_final_training(best_config, ...)
lineage = extract_lineage_from_best_model(job)
```

## Timeline

- **Current**: Old imports work with deprecation warnings
- **Next 1-2 releases**: Shims remain, warnings continue
- **After 1-2 releases**: Shims will be removed (breaking change)

## Questions?

If you encounter issues during migration, please:
1. Check this guide first
2. Review the deprecation warnings for suggested replacements
3. Check the module `__init__.py` files for available exports
4. Open an issue if you find a missing migration path


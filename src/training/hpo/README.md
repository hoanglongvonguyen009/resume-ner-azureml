# Training HPO

Hyperparameter optimization for training workflows using Optuna (local) and AzureML (cloud).

## TL;DR / Quick Start

Run HPO sweeps to find optimal hyperparameters for your models.

```python
from src.training.hpo import run_local_hpo_sweep, extract_best_config_from_study

# Run HPO sweep
study = run_local_hpo_sweep(
    config={
        "model": {"backbone": "distilbert-base-uncased"},
        "hpo": {
            "search_space": {
                "learning_rate": {"type": "log_uniform", "min": 1e-5, "max": 1e-3},
                "batch_size": {"type": "choice", "values": [8, 16, 32]}
            },
            "n_trials": 50
        }
    },
    study_name="my_study",
    n_trials=50
)

# Extract best configuration
best_config = extract_best_config_from_study(study)
```

## Overview

The `hpo` module provides hyperparameter optimization capabilities:

- **Local HPO**: Optuna-based sweeps for local execution
- **AzureML HPO**: AzureML sweep job creation and management
- **Search space management**: Define and translate search spaces between formats
- **Trial execution**: Execute individual trials with checkpointing
- **Study management**: Manage Optuna studies, extract best configurations
- **Checkpoint management**: Store and clean up trial checkpoints
- **MLflow integration**: Track HPO runs and trial metrics

## Module Structure

- `core/`: Core HPO functionality
  - `search_space.py`: Search space translation (Optuna, AzureML)
  - `optuna_integration.py`: Optuna integration utilities
  - `study.py`: Study management and best config extraction
  - `types.py`: Shared HPO type definitions (e.g., `HPOParentContext`)
- `execution/`: Trial execution
  - `local/`: Local execution (sweeps, trials, CV, refit)
  - `azureml/`: AzureML sweep job creation
- `checkpoint/`: Checkpoint storage and cleanup
- `tracking/`: MLflow tracking for HPO runs
- `trial/`: Trial-specific utilities (metrics, callbacks)
- `utils/`: HPO helper utilities

## Usage

### Basic Example: Local HPO Sweep

```python
from src.training.hpo import run_local_hpo_sweep

# Run HPO sweep
study = run_local_hpo_sweep(
    config={
        "model": {"backbone": "distilbert-base-uncased"},
        "hpo": {
            "search_space": {
                "learning_rate": {"type": "log_uniform", "min": 1e-5, "max": 1e-3},
                "batch_size": {"type": "choice", "values": [8, 16, 32]},
                "dropout": {"type": "uniform", "min": 0.1, "max": 0.5}
            },
            "n_trials": 50,
            "objective_metric": "macro-f1"
        }
    },
    study_name="my_study",
    n_trials=50
)
```

### Basic Example: Extract Best Config

```python
# Canonical import path
from src.training.hpo.core.study import extract_best_config_from_study

# Or use convenience import from training.hpo
from src.training.hpo import extract_best_config_from_study

# Extract best configuration from study
best_config = extract_best_config_from_study(study)
print(f"Best learning rate: {best_config['training']['learning_rate']}")
print(f"Best batch size: {best_config['training']['batch_size']}")
```

### Basic Example: Create Search Space

```python
from src.training.hpo.core.search_space import create_search_space

# Create search space from config
search_space = create_search_space({
    "learning_rate": {"type": "log_uniform", "min": 1e-5, "max": 1e-3},
    "batch_size": {"type": "choice", "values": [8, 16, 32]}
})
```

## API Reference

- `run_local_hpo_sweep(...)`: Run local HPO sweep using Optuna
- `extract_best_config_from_study(...)`: Extract best configuration from Optuna study
- `create_search_space(...)`: Create search space from configuration
- `StudyManager`: Manage Optuna study creation, loading, and resume logic (requires `study_key_hash` for v2 path resolution)
- `HPOParentContext`: TypedDict for HPO parent run context (`hpo_parent_run_id`, `study_key_hash`, `study_family_hash`)
- `resolve_storage_path(...)`: Resolve checkpoint storage path with platform awareness (requires `study_key_hash`, uses v2 hash-based paths)
- `setup_checkpoint_storage(...)`: Set up checkpoint storage with Drive restore support (requires `study_key_hash`)
- `TrialExecutor`: Execute individual HPO trials
- `SearchSpaceTranslator`: Search space translation utilities
- `CheckpointCleanupManager`: Manage checkpoint cleanup

**Checkpoint Management Layering**:
- **Low-level**: `common.shared.platform_detection.resolve_platform_checkpoint_path()` - Platform-specific path resolution
- **Mid-level**: `training.hpo.checkpoint.storage.resolve_storage_path()` - HPO-specific checkpoint storage (uses v2 hash-based paths)
- **High-level**: `training.hpo.utils.helpers.setup_checkpoint_storage()` - Complete checkpoint setup orchestration

**Backup System**: Uses `infrastructure.shared.backup` for centralized backup utilities. `study.db` is backed up immediately after creation/loading and incrementally after each trial.

For detailed signatures and additional utilities, see source code.

## Integration Points

### Used By

- **Orchestration modules**: Use HPO for automated hyperparameter tuning
- **Evaluation modules**: Extract best configs from HPO studies
- **Testing modules**: Use HPO for test execution

### Depends On

- `optuna`: For local HPO sweeps
- `training/core/`: For trial execution
- `infrastructure/`: For MLflow tracking and checkpoint storage

## Search Space Types

Supported search space parameter types:

- `log_uniform`: Log-uniform distribution (min, max)
- `uniform`: Uniform distribution (min, max)
- `choice`: Categorical choice (values list)
- `int_uniform`: Integer uniform distribution (min, max)

## Best Practices

1. **Use consolidated utilities**: Use consolidated utilities from infrastructure modules instead of implementing inline patterns:
   - **Path resolution**: Use `resolve_project_paths_with_fallback()` from `infrastructure.paths.utils` for path resolution with standardized fallback logic
   - **Hash computation**: Use `get_or_compute_study_key_hash()` and `get_or_compute_trial_key_hash()` from `infrastructure.tracking.mlflow.hash_utils` instead of implementing inline hash computation patterns
2. **Trust provided parameters**: When calling utilities that accept `config_dir`, trust the provided value - inference only occurs when explicitly `None` (DRY principle)
3. **Use SSOT for MLflow**: Always use `infrastructure.tracking.mlflow.setup.setup_mlflow()` for MLflow configuration. Call this **first** before using `setup_hpo_mlflow_run()`
4. **Explicit path parameters**: Pass explicit `config_dir` parameter to avoid path inference issues in Colab where checkpoints may be in Drive while project code is elsewhere
5. **Prefer v2 hash computation**: When `train_config` is available, pass it to `setup_hpo_mlflow_run()` to enable v2 hash computation (more accurate than v1)

**See Also**: 
- [`docs/architecture/mlflow-utilities.md`](../../../docs/architecture/mlflow-utilities.md) - Consolidated patterns, SSOT functions, and usage examples
- [`docs/design/mlflow-layering.md`](../../../docs/design/mlflow-layering.md) - Detailed MLflow setup layering documentation

## Testing

```bash
uvx pytest tests/training/hpo/
```

## Related Modules

- [`../README.md`](../README.md) - Main training module
- [`../core/README.md`](../core/README.md) - Core training used by HPO
- [`../execution/README.md`](../execution/README.md) - Execution infrastructure


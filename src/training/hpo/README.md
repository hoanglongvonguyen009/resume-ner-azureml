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
from src.training.hpo.core.study import extract_best_config_from_study

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

### HPO Execution

- `run_local_hpo_sweep(...)`: Run local HPO sweep using Optuna
- `TrialExecutor`: Execute individual HPO trials

### Search Space

- `create_search_space(...)`: Create search space from configuration
- `translate_search_space_to_optuna(...)`: Translate search space to Optuna format
- `SearchSpaceTranslator`: Search space translation utilities

### Study Management

- `extract_best_config_from_study(...)`: Extract best configuration from Optuna study
- `create_study_name(...)`: Create study name from configuration

### Checkpoint Management

- `resolve_storage_path(...)`: Resolve checkpoint storage path with platform awareness
  - **V2 mode**: When `study_key_hash` is provided, uses v2 hash-based folder structure: `{backbone}/study-{study8}/study.db`
    - `study8` is the first 8 characters of `study_key_hash`
    - Example: `distilbert/study-c3659fea/study.db`
  - **Legacy mode**: When `study_key_hash` is None, falls back to legacy `study_name` format: `{backbone}/{study_name}/study.db`
    - Maintains backward compatibility with existing configurations
- `get_storage_uri(...)`: Get checkpoint storage URI
- `setup_checkpoint_storage(...)`: Set up checkpoint storage with Drive restore support
  - Accepts optional `study_key_hash` parameter for v2 path resolution
- `CheckpointCleanupManager`: Manage checkpoint cleanup

**Note**: When checkpoints are stored in Google Drive (Colab), the system automatically detects Drive paths and skips redundant `restore_from_drive()` calls to prevent path resolution errors.

**Path Resolution**: The system prioritizes v2 hash-based paths when `study_key_hash` is available, ensuring deterministic study folder names based on study configuration. Legacy `study_name` format is supported for backward compatibility.

For detailed signatures, see source code.

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

## Testing

```bash
uvx pytest tests/training/hpo/
```

## Related Modules

- [`../README.md`](../README.md) - Main training module
- [`../core/README.md`](../core/README.md) - Core training used by HPO
- [`../execution/README.md`](../execution/README.md) - Execution infrastructure


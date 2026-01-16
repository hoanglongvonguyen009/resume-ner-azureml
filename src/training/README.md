# Training

Model training, hyperparameter optimization, and execution infrastructure for Resume NER models.

## TL;DR / Quick Start

Train models, run HPO sweeps, and execute training workflows with MLflow tracking.

```python
from src.training.core.trainer import train_model
from src.training.hpo import run_local_hpo_sweep
from src.training.execution import execute_final_training

# Train a model
train_model(
    config=training_config,
    train_data=train_samples,
    val_data=val_samples,
    output_dir=Path("outputs/checkpoint")
)

# Run HPO sweep
run_local_hpo_sweep(
    config=config,
    study_name="my_study",
    n_trials=50
)

# Execute final training
execute_final_training(
    config=best_config,
    output_dir=Path("outputs/final_model")
)
```

## Overview

The `training` module provides a unified interface for training operations:

- **Core training**: Model training, evaluation, metrics computation, checkpoint management
- **Hyperparameter optimization**: Local (Optuna) and AzureML HPO sweeps, trial execution, study management
- **Execution infrastructure**: Subprocess execution, distributed training, MLflow setup, lineage tracking
- **CLI interfaces**: Command-line tools for training workflows

This module is organized into submodules that handle specific aspects of training. See individual submodule READMEs for detailed documentation.

## Key Concepts

- **Training workflow**: Load data → Train model → Evaluate → Save checkpoint → Log metrics
- **HPO sweeps**: Automated hyperparameter search using Optuna (local) or AzureML (cloud)
- **Distributed training**: Support for DataParallel (DDP) for multi-GPU training
- **MLflow integration**: Automatic tracking of metrics, parameters, and artifacts
- **Lineage tracking**: Track model provenance from HPO trials to final models

**MLflow Setup Layering**: Training modules use `infrastructure.tracking.mlflow.setup.setup_mlflow()` (SSOT) for MLflow configuration, then extend with training-specific run lifecycle management via `training.execution.mlflow_setup`.

**Naming Hierarchy**: Training run names use `infrastructure.naming` as the primary system, with training-specific fallbacks when systematic naming is unavailable.

## Module Structure

This module is organized into the following submodules:

- `core/`: Core training components (trainer, model, evaluator, metrics)
- `hpo/`: Hyperparameter optimization (Optuna integration, search spaces, trial execution)
- `execution/`: Training execution (subprocess runner, distributed training, MLflow setup)
- `cli/`: Command-line interfaces for training operations
- `orchestrator.py`: High-level training orchestration
- `config.py`: Training configuration building and resolution

See individual submodule READMEs for detailed documentation:
- [`core/README.md`](core/README.md) - Core training components
- [`hpo/README.md`](hpo/README.md) - Hyperparameter optimization
- [`execution/README.md`](execution/README.md) - Execution backends

## Usage

### Basic Workflow: Training a Model

```python
from pathlib import Path
from src.training.core.trainer import train_model
from src.data.loaders.dataset_loader import load_dataset

# Load dataset
dataset = load_dataset("dataset/")
train_data = dataset["train"]
val_data = dataset["validation"]

# Train model
train_model(
    config={
        "model": {"backbone": "distilbert-base-uncased", "num_labels": 5},
        "training": {
            "learning_rate": 2e-5,
            "batch_size": 16,
            "epochs": 3,
            "random_seed": 42
        }
    },
    train_data=train_data,
    val_data=val_data,
    output_dir=Path("outputs/checkpoint")
)
```

### Basic Workflow: Running HPO

```python
from src.training.hpo import run_local_hpo_sweep

# Run HPO sweep
best_config = run_local_hpo_sweep(
    config={
        "model": {"backbone": "distilbert-base-uncased"},
        "hpo": {
            "search_space": {
                "learning_rate": {"type": "log_uniform", "min": 1e-5, "max": 1e-3},
                "batch_size": {"type": "choice", "values": [8, 16, 32]}
            },
            "n_trials": 50,
            "study_name": "my_study"
        }
    },
    study_name="my_study",
    n_trials=50
)
```

### CLI Usage

Train a model from command line:

```bash
python -m src.training.cli.train \
  --config-dir config/ \
  --data-asset dataset/ \
  --output-dir outputs/checkpoint
```

## API Reference

### Main Functions

- `train_model(...)`: Train a model with given configuration and data
- `evaluate_model(...)`: Evaluate a trained model on validation data
- `create_model_and_tokenizer(...)`: Create model and tokenizer from config
- `compute_metrics(...)`: Compute evaluation metrics from predictions
- `run_local_hpo_sweep(...)`: Run local HPO sweep using Optuna
- `execute_final_training(...)`: Execute final training with best config
- `extract_lineage_from_best_model(...)`: Extract lineage information from best model

### Configuration

Training configuration is built from YAML files and command-line arguments. See `config.py` for details.

For detailed signatures, see source code or submodule documentation.

## Integration Points

### Dependencies

- `data/`: Data loading utilities (`load_dataset`, `ResumeNERDataset`)
- `infrastructure/`: Platform adapters, MLflow tracking, path resolution
- `common/`: Shared utilities (logging, hashing, platform detection)

### Used By

- **Orchestration modules**: Use training workflows for job execution
- **Evaluation modules**: Use training components for model evaluation
- **Testing modules**: Use training utilities for test execution

## Examples

### Example 1: Simple Training

```python
from pathlib import Path
from src.training.core.trainer import train_model
from src.data.loaders.dataset_loader import load_dataset

# Load data
dataset = load_dataset("dataset/")

# Train
train_model(
    config={
        "model": {"backbone": "distilbert-base-uncased", "num_labels": 5},
        "training": {"learning_rate": 2e-5, "batch_size": 16, "epochs": 3}
    },
    train_data=dataset["train"],
    val_data=dataset["validation"],
    output_dir=Path("outputs/checkpoint")
)
```

### Example 2: HPO Sweep

```python
from src.training.hpo import run_local_hpo_sweep

# Run HPO
best_config = run_local_hpo_sweep(
    config={
        "model": {"backbone": "distilbert-base-uncased"},
        "hpo": {
            "search_space": {
                "learning_rate": {"type": "log_uniform", "min": 1e-5, "max": 1e-3},
                "batch_size": {"type": "choice", "values": [8, 16, 32]}
            }
        }
    },
    study_name="my_study",
    n_trials=50
)
```

## Best Practices

1. **Use configuration files**: Define training configs in YAML files rather than hardcoding
2. **Enable MLflow tracking**: Always use MLflow for experiment tracking and reproducibility
   - Call `infrastructure.tracking.mlflow.setup.setup_mlflow()` first (SSOT)
   - Then use `training.execution.mlflow_setup` for run lifecycle management
3. **Use infrastructure naming**: Run names use `infrastructure.naming` as primary, with training fallbacks
4. **Set random seeds**: Use consistent random seeds for reproducibility
5. **Validate checkpoints**: Always validate checkpoints after training
6. **Use HPO for hyperparameter tuning**: Don't manually tune hyperparameters; use HPO sweeps

## Notes

- Training functions use lazy imports to avoid requiring torch/optuna at module level
- Distributed training (DDP) is automatically detected and configured
- MLflow tracking is integrated throughout training workflows
- Checkpoints are saved in standard format for compatibility

## Testing

```bash
uvx pytest tests/training/
```

## Related Modules

- [`../data/README.md`](../data/README.md) - Data loading utilities
- [`../infrastructure/README.md`](../infrastructure/README.md) - Infrastructure layer (MLflow, paths)
- [`../evaluation/README.md`](../evaluation/README.md) - Model evaluation
- [`core/README.md`](core/README.md) - Core training components
- [`hpo/README.md`](hpo/README.md) - Hyperparameter optimization
- [`execution/README.md`](execution/README.md) - Execution backends


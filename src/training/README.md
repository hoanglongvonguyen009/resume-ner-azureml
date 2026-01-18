# Training

Model training, hyperparameter optimization, and execution infrastructure for Resume NER models.

## TL;DR / Quick Start

Train models, run HPO sweeps, and execute training workflows with MLflow tracking.

```python
from src.training.core.trainer import train_model
from src.training.hpo import run_local_hpo_sweep
from src.training.execution import run_final_training_workflow

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
run_final_training_workflow(
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

**MLflow Setup Layering**: 
- **SSOT**: `infrastructure.tracking.mlflow.setup.setup_mlflow()` - Use this for MLflow configuration
- **Internal**: `common.shared.mlflow_setup.setup_mlflow_cross_platform()` - Internal implementation detail, do not call directly
- **Training-specific**: `training.execution.mlflow_setup` - Extends SSOT with training-specific run lifecycle management

Training modules should call `infrastructure.tracking.mlflow.setup.setup_mlflow()` first, then use `training.execution.mlflow_setup` for run lifecycle management.

**Naming Hierarchy**: Training run names use `infrastructure.naming` as the primary system, with training-specific fallbacks when systematic naming is unavailable.

## Module Structure

This module is organized into the following submodules:

- `core/`: Core training components (trainer, model, evaluator, metrics)
- `hpo/`: Hyperparameter optimization (Optuna integration, search spaces, trial execution)
  - `azureml/`: AzureML HPO sweep job creation
- `execution/`: Training execution (subprocess runner, distributed training, MLflow setup)
- `azureml/`: AzureML training job creation
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

### Basic Workflow: AzureML Training Jobs

```python
from pathlib import Path
from training.azureml import (
    build_final_training_config,
    create_final_training_job,
    validate_final_training_job,
)
from infrastructure.azureml import submit_and_wait_for_job

# Build final training config from best HPO config
final_config = build_final_training_config(
    best_config=best_hpo_config,
    train_config=train_config,
    random_seed=42
)

# Create AzureML training job
training_job = create_final_training_job(
    script_path=Path("src/training/cli/train.py"),
    data_asset=data_asset,
    environment=environment,
    compute_cluster="gpu-cluster",
    final_config=final_config,
    aml_experiment_name="my_experiment",
    tags={"backbone": "distilbert", "stage": "final_training"}
)

# Submit and wait for completion
completed_job = submit_and_wait_for_job(ml_client, training_job)
validate_final_training_job(completed_job)
```

### Basic Workflow: AzureML HPO Sweeps

```python
from pathlib import Path
from training.hpo.azureml import (
    create_hpo_sweep_job_for_backbone,
    create_dry_run_sweep_job_for_backbone,
    validate_sweep_job,
)
from infrastructure.azureml import submit_and_wait_for_job

# Create AzureML HPO sweep job
sweep_job = create_hpo_sweep_job_for_backbone(
    script_path=Path("src/training/cli/train.py"),
    data_asset=data_asset,
    environment=environment,
    compute_cluster="gpu-cluster",
    hpo_config=hpo_config,
    backbone="distilbert",
    configs=configs,
    config_metadata=config_metadata,
    aml_experiment_name="my_experiment",
    stage="hpo"
)

# Submit and wait for completion
completed_sweep = submit_and_wait_for_job(ml_client, sweep_job)
validate_sweep_job(completed_sweep, backbone="distilbert")
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
- `run_final_training_workflow(...)`: Execute final training with best config
- `extract_lineage_from_best_model(...)`: Extract lineage information from best model

### AzureML Job Creation

- `training.execution.jobs.build_final_training_config(...)`: Build final training config from best HPO config
- `training.execution.jobs.create_final_training_job(...)`: Create AzureML final training job
- `training.execution.jobs.validate_final_training_job(...)`: Validate training job completion

**Note**: The `training.azureml` import path is deprecated but still works for backward compatibility. Use `training.execution.jobs` for new code.
- `training.hpo.execution.azureml.create_hpo_sweep_job_for_backbone(...)`: Create AzureML HPO sweep job
- `training.hpo.execution.azureml.create_dry_run_sweep_job_for_backbone(...)`: Create dry-run HPO sweep job
- `training.hpo.execution.azureml.validate_sweep_job(...)`: Validate sweep job completion

**Note**: The `training.hpo.azureml` import path is deprecated but still works for backward compatibility. Use `training.hpo.execution.azureml` for new code.

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


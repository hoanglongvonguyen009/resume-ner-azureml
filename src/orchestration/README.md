# Orchestration

Job orchestration and workflow management for HPO, training, conversion, benchmarking, and tracking.

## TL;DR / Quick Start

Orchestrate job execution for HPO sweeps, training, conversion, and benchmarking workflows.

```python
from src.orchestration.jobs.hpo.azureml.sweeps import create_hpo_sweep_job_for_backbone
from src.orchestration.jobs.training import build_final_training_config
from src.orchestration.jobs.runtime import submit_and_wait_for_job

# Create HPO sweep job
sweep_job = create_hpo_sweep_job_for_backbone(
    script_path=Path("src/training/cli/train.py"),
    data_asset=data_asset,
    environment=environment,
    compute_cluster="gpu-cluster",
    backbone="distilbert",
    hpo_config=hpo_config,
    configs=configs
)

# Submit and wait for job
completed_job = submit_and_wait_for_job(ml_client, sweep_job)
```

## Overview

The `orchestration` module provides job orchestration and workflow management:

- **HPO orchestration**: Create and manage HPO sweep jobs (local Optuna, AzureML)
- **Training orchestration**: Create and manage final training jobs
- **Conversion orchestration**: Create and manage model conversion jobs
- **Benchmarking orchestration**: Create and manage benchmarking jobs
- **Tracking orchestration**: MLflow tracking, indexing, and run finding
- **Job runtime**: Job submission and monitoring utilities

**Note**: The top-level `orchestration` module (`orchestration/__init__.py`) is deprecated and acts as a facade for backward compatibility. New code should import directly from:
- `infrastructure.*` for configuration, paths, naming, tracking
- `common.constants` for constants
- `orchestration.jobs.*` for job orchestration

The `jobs/` submodule is active and contains the job orchestration logic.

## Key Concepts

- **Job orchestration**: Create AzureML jobs or local execution workflows
- **HPO sweeps**: Automated hyperparameter search across multiple trials
- **Job dependencies**: Manage job dependencies and workflows
- **MLflow indexing**: Index MLflow runs for efficient querying
- **Run finding**: Find and query MLflow runs

## Module Structure

This module is organized into the following submodules:

- `jobs/`: Job orchestration (active)
  - `hpo/`: HPO job orchestration (local, AzureML)
    - `local/`: Local HPO orchestration (Optuna sweeps, Drive backup)
      - `backup.py`: HPO study.db and study folder backup to Google Drive
        - Correctly handles v2 study folders (`study-{hash}/study.db`)
        - Verifies actual file existence in Drive (not just path mapping)
        - Supports both v2 and legacy folder structures
  - `tracking/`: Tracking job orchestration (MLflow indexing, finding)
  - `benchmarking/`: Benchmarking job orchestration
  - `conversion/`: Conversion job orchestration
  - `training.py`: Training job orchestration
  - `sweeps.py`: Sweep job utilities
  - `runtime.py`: Job runtime utilities
- `naming.py`: Removed (use `infrastructure.naming` instead)

See individual submodule READMEs for detailed documentation:
- [`jobs/README.md`](jobs/README.md) - Job orchestration

## Usage

### Basic Workflow: HPO Sweep Job

```python
from pathlib import Path
from src.orchestration.jobs.hpo.azureml.sweeps import create_hpo_sweep_job_for_backbone
from src.orchestration.jobs.runtime import submit_and_wait_for_job

# Create HPO sweep job
sweep_job = create_hpo_sweep_job_for_backbone(
    script_path=Path("src/training/cli/train.py"),
    data_asset=data_asset,
    environment=environment,
    compute_cluster="gpu-cluster",
    backbone="distilbert",
    hpo_config=hpo_config,
    configs=configs,
    config_metadata=config_metadata,
    aml_experiment_name="my_experiment",
    stage="hpo"
)

# Submit and wait for completion
completed_job = submit_and_wait_for_job(ml_client, sweep_job)
```

### Basic Workflow: Final Training Job

```python
from src.orchestration.jobs.training import (
    build_final_training_config,
    create_final_training_job
)

# Build final training config from best HPO config
final_config = build_final_training_config(
    best_config=best_hpo_config,
    train_config=train_config,
    random_seed=42
)

# Create training job
training_job = create_final_training_job(
    script_path=Path("src/training/cli/train.py"),
    data_asset=data_asset,
    environment=environment,
    compute_cluster="gpu-cluster",
    config=final_config,
    aml_experiment_name="my_experiment"
)
```

### Basic Workflow: Conversion Job

```python
from src.orchestration.jobs.conversion import create_conversion_job

# Create conversion job from training job output
conversion_job = create_conversion_job(
    script_path=Path("src/deployment/conversion/orchestration.py"),
    training_job=completed_training_job,
    environment=environment,
    compute_cluster="cpu-cluster"
)
```

## API Reference

### HPO Jobs

- `create_hpo_sweep_job_for_backbone(...)`: Create AzureML HPO sweep job
- `create_dry_run_sweep_job_for_backbone(...)`: Create dry-run HPO sweep job
- `backup_hpo_study_to_drive(...)`: Backup HPO study.db and study folders to Google Drive (Colab)
  - Automatically detects v2 study folders (`study-{hash}/study.db`)
  - Verifies actual file existence in Drive (not just path mapping)
  - Supports both v2 and legacy folder structures
  - See `jobs/hpo/local/backup.py` for implementation details
- See `jobs/hpo/` for local HPO orchestration

### Training Jobs

- `build_final_training_config(...)`: Build final training config from best HPO config
- `create_final_training_job(...)`: Create AzureML final training job
- `validate_final_training_job(...)`: Validate training job completion

### Conversion Jobs

- `create_conversion_job(...)`: Create AzureML conversion job
- `get_checkpoint_output_from_training_job(...)`: Extract checkpoint from training job

### Job Runtime

- `submit_and_wait_for_job(...)`: Submit job and wait for completion

For detailed signatures, see source code or submodule documentation.

## Integration Points

### Dependencies

- `training/`: Training execution and HPO
- `infrastructure/`: Configuration, paths, naming, tracking
- `common/`: Shared utilities and constants
- `azure.ai.ml`: AzureML SDK for job creation

### Used By

- **Notebooks**: Use orchestration for workflow execution
- **Scripts**: Use orchestration for job submission

## Examples

### Example 1: Complete HPO to Training Workflow

```python
from src.orchestration.jobs.hpo.azureml.sweeps import create_hpo_sweep_job_for_backbone
from src.orchestration.jobs.training import build_final_training_config, create_final_training_job
from src.orchestration.jobs.runtime import submit_and_wait_for_job

# 1. Run HPO sweep
sweep_job = create_hpo_sweep_job_for_backbone(...)
completed_sweep = submit_and_wait_for_job(ml_client, sweep_job)

# 2. Extract best config (from evaluation/selection)
from src.evaluation.selection import select_best_configuration
best_config = select_best_configuration(
    sweep_job=completed_sweep,
    ml_client=ml_client,
    objective_metric="macro-f1"
)

# 3. Run final training
final_config = build_final_training_config(best_config, train_config)
training_job = create_final_training_job(...)
completed_training = submit_and_wait_for_job(ml_client, training_job)
```

## Best Practices

1. **Use job orchestration**: Always use orchestration functions instead of creating jobs directly
2. **Validate jobs**: Always validate job completion before using outputs
3. **Handle dependencies**: Manage job dependencies explicitly
4. **Use runtime utilities**: Use `submit_and_wait_for_job` for job submission

## Notes

- Top-level `orchestration` module is deprecated (use `infrastructure.*` or `orchestration.jobs.*`)
- `jobs/` submodule is active and contains all job orchestration logic
- Job orchestration supports both local (Optuna) and AzureML execution
- MLflow indexing is used for efficient run querying

## Testing

```bash
uvx pytest tests/orchestration/
```

## Related Modules

- [`jobs/README.md`](jobs/README.md) - Job orchestration details
- [`../training/README.md`](../training/README.md) - Training workflows
- [`../infrastructure/README.md`](../infrastructure/README.md) - Infrastructure layer
- [`../evaluation/README.md`](../evaluation/README.md) - Model evaluation and selection


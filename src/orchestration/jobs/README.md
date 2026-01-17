# Orchestration Jobs

Job orchestration for HPO, training, conversion, benchmarking, and tracking workflows.

## TL;DR / Quick Start

Create and manage jobs for different workflow stages.

```python
from src.orchestration.jobs.hpo.azureml.sweeps import create_hpo_sweep_job_for_backbone
from src.orchestration.jobs.training import build_final_training_config
from src.orchestration.jobs.runtime import submit_and_wait_for_job

# Create HPO sweep job
sweep_job = create_hpo_sweep_job_for_backbone(...)

# Submit and wait
completed = submit_and_wait_for_job(ml_client, sweep_job)
```

## Overview

The `jobs` module provides job orchestration for:

- **HPO jobs**: Create and manage HPO sweep jobs (local Optuna, AzureML)
- **Training jobs**: Create and manage final training jobs
- **Conversion jobs**: Create and manage model conversion jobs
- **Benchmarking jobs**: Create and manage benchmarking jobs
- **Tracking jobs**: MLflow tracking, indexing, and run finding
- **Job runtime**: Job submission, monitoring, and validation

## Module Structure

- `hpo/`: HPO job orchestration
  - `local/`: Local HPO orchestration (Optuna)
    - `backup.py`: Centralized backup utilities for HPO and all workflows
      - **Immediate backup**: `immediate_backup_if_needed()` for immediate post-creation backup (standardized)
      - **Incremental backup**: Optuna callbacks for `study.db` backup after each trial
      - **Standardized pattern**: Used by HPO, training, conversion, and benchmarking workflows
  - `azureml/`: AzureML HPO sweep job creation
- `tracking/`: Tracking job orchestration
  - MLflow indexing, run finding, artifact management
- `benchmarking/`: Benchmarking job orchestration
- `conversion/`: Conversion job orchestration
- `training.py`: Training job orchestration
- `sweeps.py`: Sweep job utilities
- `runtime.py`: Job runtime utilities
- `conversion.py`: Conversion job utilities

## Usage

### Basic Example: HPO Sweep Job

```python
from src.orchestration.jobs.hpo.azureml.sweeps import create_hpo_sweep_job_for_backbone

# Create AzureML HPO sweep job
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
```

### Basic Example: Final Training Job

```python
from src.orchestration.jobs.training import (
    build_final_training_config,
    create_final_training_job
)

# Build final training config
final_config = build_final_training_config(
    best_config=best_hpo_config,
    train_config=train_config
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

### Basic Example: Job Submission

```python
from src.orchestration.jobs.runtime import submit_and_wait_for_job

# Submit job and wait for completion
completed_job = submit_and_wait_for_job(ml_client, job)

# Check job status
if completed_job.status == "Completed":
    # Process outputs
    pass
```

## API Reference

### HPO Jobs

- `create_hpo_sweep_job_for_backbone(...)`: Create AzureML HPO sweep job
- `create_dry_run_sweep_job_for_backbone(...)`: Create dry-run HPO sweep job
- See `hpo/local/` for local HPO orchestration
  - `backup.py`: Centralized backup utilities (standardized across all workflows)
    - **Immediate Backup**:
      - `immediate_backup_if_needed(...)`: Generic immediate backup utility (file/directory)
      - Used by HPO, training, conversion, and benchmarking workflows
      - Checks: backup_enabled, path exists, path not in Drive
    - **Incremental Backup** (HPO-specific):
      - `backup_hpo_study_to_drive(...)`: Backup HPO study database and folder to Drive
      - `create_incremental_backup_callback(...)`: Create Optuna callback for incremental backup
      - `create_study_db_backup_callback(...)`: Convenience wrapper for `study.db` backup callback

### Training Jobs

- `build_final_training_config(...)`: Build final training config from best HPO config
- `create_final_training_job(...)`: Create AzureML final training job
- `validate_final_training_job(...)`: Validate training job completion

### Conversion Jobs

- `create_conversion_job(...)`: Create AzureML conversion job
- `get_checkpoint_output_from_training_job(...)`: Extract checkpoint from training job

### Job Runtime

- `submit_and_wait_for_job(ml_client: MLClient, job: Any) -> Job`: Submit job and wait for completion

### Tracking

- See `tracking/` for MLflow indexing, run finding, and artifact management

For detailed signatures, see source code.

## Integration Points

### Used By

- **Notebooks**: Use job orchestration for workflow execution
- **Scripts**: Use job orchestration for job submission

### Depends On

- `training/`: Training execution and HPO
- `infrastructure/`: Configuration, paths, naming, tracking
- `azure.ai.ml`: AzureML SDK for job creation

## Job Types

### HPO Jobs

HPO jobs run hyperparameter optimization sweeps:
- **Local**: Uses Optuna for local execution
- **AzureML**: Uses AzureML sweep jobs for cloud execution

### Training Jobs

Training jobs run final model training with best hyperparameters from HPO.

### Conversion Jobs

Conversion jobs convert trained models to deployment format (ONNX).

### Benchmarking Jobs

Benchmarking jobs measure inference performance.

## Testing

```bash
uvx pytest tests/orchestration/jobs/
```

## Related Modules

- [`../README.md`](../README.md) - Main orchestration module
- [`../../training/README.md`](../../training/README.md) - Training workflows
- [`../../infrastructure/README.md`](../../infrastructure/README.md) - Infrastructure layer


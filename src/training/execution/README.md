# Training Execution

Training execution infrastructure: subprocess execution, distributed training, MLflow setup, and lineage tracking.

## TL;DR / Quick Start

Execute training as subprocesses, set up MLflow tracking, and manage distributed training.

```python
from src.training.execution.subprocess_runner import execute_training_subprocess
from src.training.execution.mlflow_setup import create_training_mlflow_run
from src.training.execution.distributed import create_run_context

# Create MLflow run
with create_training_mlflow_run(config) as run:
    # Execute training subprocess
    execute_training_subprocess(
        config=config,
        output_dir=Path("outputs/checkpoint")
    )
```

## Overview

The `execution` module provides infrastructure for training execution:

- **Subprocess execution**: Execute training as subprocesses with proper environment setup
- **Distributed training**: Support for DataParallel (DDP) multi-GPU training
- **MLflow setup**: Create and configure MLflow runs for training tracking
- **Lineage tracking**: Track model provenance and lineage information
- **Run management**: Build run names, apply tags, manage run lifecycle

## Module Structure

- `subprocess_runner.py`: Subprocess execution and environment setup
- `distributed.py`: Distributed training (DDP) support
- `mlflow_setup.py`: MLflow run creation and configuration
- `lineage.py`: Lineage extraction and tracking
- `run_names.py`: Training run name generation
- `tags.py`: Tag management and lineage tags
- `tag_helpers.py`: Tag helper utilities
- `executor.py`: High-level training execution
- `jobs.py`: AzureML job creation (optional)
- `distributed_launcher.py`: Distributed training launcher

## Usage

### Basic Example: Subprocess Execution

```python
from pathlib import Path
from src.training.execution.subprocess_runner import execute_training_subprocess

# Execute training as subprocess
execute_training_subprocess(
    config={
        "model": {"backbone": "distilbert-base-uncased"},
        "training": {"learning_rate": 2e-5, "batch_size": 16}
    },
    output_dir=Path("outputs/checkpoint"),
    data_path=Path("dataset/")
)
```

### Basic Example: MLflow Setup

```python
from src.training.execution.mlflow_setup import create_training_mlflow_run

# Create MLflow run
with create_training_mlflow_run(config) as run:
    # Training code here
    # Metrics automatically logged to MLflow
    pass
```

### Basic Example: Distributed Training

```python
from src.training.execution.distributed import create_run_context, should_use_ddp

# Check if DDP should be used
if should_use_ddp(config):
    # Create distributed run context
    context = create_run_context(distributed_config)
    # Initialize process group
    init_process_group_if_needed(context)
```

### Basic Example: Lineage Tracking

```python
from src.training.execution.lineage import extract_lineage_from_best_model

# Extract lineage from best model
lineage = extract_lineage_from_best_model(
    best_model_path=Path("outputs/best_model"),
    hpo_study_path=Path("outputs/hpo/study.db")
)

# Apply lineage tags
from src.training.execution.tags import apply_lineage_tags
apply_lineage_tags(lineage, mlflow_run)
```

## API Reference

### Subprocess Execution

- `execute_training_subprocess(...)`: Execute training as subprocess
- `build_training_command(...)`: Build training command from config
- `setup_training_environment(...)`: Setup training environment
- `verify_training_environment(...)`: Verify training environment

### MLflow Setup

**Layering**: This module handles training-specific run creation and lifecycle management. It does NOT handle MLflow setup/configuration.

**Prerequisites**: Always call `infrastructure.tracking.mlflow.setup.setup_mlflow()` (SSOT) **first** before using these functions.

- `create_training_mlflow_run(...)`: Create MLflow run for training
- `create_training_child_run(...)`: Create child MLflow run
- `setup_mlflow_tracking_env(...)`: Setup MLflow tracking environment

**See Also**: 
- [`docs/design/mlflow-layering.md`](../../../docs/design/mlflow-layering.md) - Detailed MLflow setup layering documentation
- [`docs/architecture/mlflow-utilities.md`](../../../docs/architecture/mlflow-utilities.md) - Consolidated patterns and best practices

### Distributed Training

- `create_run_context(...)`: Create distributed run context
- `should_use_ddp(...)`: Check if DDP should be used
- `detect_hardware(...)`: Detect available hardware
- `init_process_group_if_needed(...)`: Initialize process group for DDP

### Lineage and Tags

- `extract_lineage_from_best_model(...)`: Extract lineage from best model
- `apply_lineage_tags(...)`: Apply lineage tags to MLflow run
- `add_training_tags(...)`: Add training tags to MLflow run
- `build_training_run_name_with_fallback(..., config_dir: Optional[Path] = None)`: Build training run name with fallback logic
  - **Accepts `config_dir` parameter**: Pass `config_dir` explicitly when available (follows "trust provided parameter" pattern)
  - **Trusts provided `config_dir`**: Only infers when parameter is `None`
  - Uses infrastructure naming as primary, falls back to policy-based or legacy naming

### High-Level Execution

- `run_final_training_workflow(...)`: Execute final training with best config
  - **Backup support**: Accepts `backup_to_drive` and `backup_enabled` parameters
  - Uses standardized immediate backup pattern (`immediate_backup_if_needed()` from `orchestration.jobs.hpo.local.backup`)
  - Backs up final checkpoint directory immediately after training completion
  - Consistent backup behavior with HPO, conversion, and benchmarking workflows

For detailed signatures, see source code.

## Integration Points

### Used By

- **Training orchestrator**: Uses execution infrastructure for training workflows
- **HPO modules**: Uses subprocess execution for trial execution
- **Orchestration modules**: Uses execution for job orchestration

### Depends On

- `torch`: For distributed training (DDP)
- `mlflow`: For MLflow tracking
- `training/core/`: For training execution
- `infrastructure/`: For platform adapters and MLflow setup

## Testing

```bash
uvx pytest tests/training/execution/
```

## Best Practices

1. **MLflow setup layering**: Always call `infrastructure.tracking.mlflow.setup.setup_mlflow()` first, then use functions from this module for run creation
2. **Trust provided parameters**: When calling functions that accept `config_dir`, trust the provided value - inference only occurs when explicitly `None` (DRY principle)
3. **Use consolidated utilities**: Use centralized hash utilities (`get_or_compute_study_key_hash()`, `get_or_compute_trial_key_hash()`) instead of manually retrieving hashes from MLflow runs

**See Also**: 
- [`docs/architecture/mlflow-utilities.md`](../../../docs/architecture/mlflow-utilities.md) - Consolidated patterns, SSOT functions, and usage examples
- [`docs/design/mlflow-layering.md`](../../../docs/design/mlflow-layering.md) - Detailed MLflow setup layering documentation

## Related Modules

- [`../README.md`](../README.md) - Main training module
- [`../core/README.md`](../core/README.md) - Core training components
- [`../hpo/README.md`](../hpo/README.md) - HPO uses execution infrastructure


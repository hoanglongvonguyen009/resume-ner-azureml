# Infrastructure Tracking

MLflow tracking integration and utilities for experiment tracking.

## TL;DR / Quick Start

Setup MLflow tracking and manage MLflow runs, artifacts, and queries.

```python
from src.infrastructure.tracking.mlflow.setup import setup_mlflow
from src.infrastructure.tracking.mlflow.runs import create_mlflow_run
from src.infrastructure.tracking.mlflow.finder import find_mlflow_runs

# Setup MLflow
tracking_uri = setup_mlflow(
    experiment_name="my_experiment",
    tracking_uri="file:./mlruns"
)

# Create MLflow run
with create_mlflow_run(run_name="my_run") as run:
    # Log metrics, parameters, artifacts
    pass

# Find runs
runs = find_mlflow_runs(experiment_name="my_experiment", filter_string="tags.stage='hpo'")
```

## Overview

The `tracking` module provides MLflow tracking integration:

- **MLflow setup**: Single source of truth (SSOT) for MLflow configuration via `setup_mlflow()`
- **Run management**: Create and manage MLflow runs
- **Run finding**: Query and find MLflow runs
- **Artifact management**: Upload and download artifacts
- **Tracking utilities**: Hash computation, URL generation, lifecycle management
- **Trackers**: Specialized trackers for different process types (sweep, training, benchmark, conversion)

**Layering**: This module provides the SSOT for MLflow setup. The layering is:
- **SSOT (High-level)**: `infrastructure.tracking.mlflow.setup.setup_mlflow()` - Use this for all MLflow setup
- **Low-level (Internal)**: `common.shared.mlflow_setup.setup_mlflow_cross_platform()` - Internal implementation detail, do not call directly

Training, deployment, and other modules should call `infrastructure.tracking.mlflow.setup.setup_mlflow()` first, then use domain-specific extensions (e.g., `training.execution.mlflow_setup` for run lifecycle management).

## Module Structure

- `mlflow/`: MLflow integration
  - `setup.py`: MLflow setup (SSOT for configuration)
  - `runs.py`: Run creation and management
  - `finder.py`: Run finding and querying
  - `artifacts/`: Artifact upload and download
  - `trackers/`: Specialized trackers (sweep, training, benchmark, conversion)
  - `hash_utils.py`: Hash computation for tracking (includes consolidated hash computation utilities)
  - `urls.py`: URL generation for MLflow runs
  - `lifecycle.py`: Run lifecycle management
  - `queries.py`: Query utilities
  - `utils.py`: Tracking utilities

## Usage

### Basic Example: Setup MLflow

```python
from src.infrastructure.tracking.mlflow.setup import setup_mlflow

# Setup MLflow for local tracking
tracking_uri = setup_mlflow(
    experiment_name="my_experiment",
    tracking_uri="file:./mlruns"
)

# Setup MLflow for AzureML
from src.common.shared.mlflow_setup import create_ml_client_from_config
ml_client = create_ml_client_from_config(config)
tracking_uri = setup_mlflow(
    experiment_name="my_experiment",
    ml_client=ml_client
)
```

### Basic Example: Create Run

```python
from src.infrastructure.tracking.mlflow.runs import create_mlflow_run

# Create MLflow run
with create_mlflow_run(
    run_name="my_training_run",
    tags={"stage": "training", "backbone": "distilbert"}
) as run:
    # Log metrics
    import mlflow
    mlflow.log_metric("f1", 0.85)
    mlflow.log_param("learning_rate", 2e-5)
```

### Basic Example: Find Runs

```python
from src.infrastructure.tracking.mlflow.finder import find_mlflow_runs

# Find runs by experiment and filter
runs = find_mlflow_runs(
    experiment_name="my_experiment",
    filter_string="tags.stage='hpo' AND metrics.f1 > 0.8"
)

# Access run information
for run in runs:
    print(f"Run: {run.info.run_name}, F1: {run.data.metrics.get('f1')}")
```

## API Reference

### MLflow Setup

- `setup_mlflow(...)`: Setup MLflow tracking (SSOT for configuration)

### Run Management

- `create_mlflow_run(...)`: Create MLflow run
- See `mlflow/runs.py` for detailed run management functions

### Run Finding

- `find_mlflow_runs(...)`: Find MLflow runs by query
- See `mlflow/finder.py` for detailed finding functions

### Artifacts

- See `mlflow/artifacts/` for artifact upload and download utilities

### Trackers

- `MLflowSweepTracker`: Tracker for HPO sweeps
- `MLflowTrainingTracker`: Tracker for training runs
- `MLflowBenchmarkTracker`: Tracker for benchmarking runs
- `MLflowConversionTracker`: Tracker for conversion runs

### Hash Computation Utilities

Consolidated utilities for hash computation with fallback hierarchy:

- `get_or_compute_study_key_hash(...)`: **Consolidated utility for study key hash computation**. Implements fallback hierarchy:
  1. Use provided `study_key_hash` (if available)
  2. Retrieve from MLflow run tags (SSOT) - if `hpo_parent_run_id` provided
  3. Compute from configs (fallback) - if `data_config`, `hpo_config`, `train_config`, `backbone` available
  
  This function consolidates the common pattern used across HPO and training execution scripts.

- `get_or_compute_trial_key_hash(...)`: **Consolidated utility for trial key hash computation**. Implements fallback hierarchy:
  1. Use provided `trial_key_hash` (if available)
  2. Retrieve from MLflow run tags (SSOT) - if `trial_run_id` provided
  3. Compute from configs (fallback) - if `study_key_hash` and `hyperparameters` available

**Usage Example**:
```python
from infrastructure.tracking.mlflow.hash_utils import (
    get_or_compute_study_key_hash,
    get_or_compute_trial_key_hash,
)

# Get or compute study key hash
study_key_hash = get_or_compute_study_key_hash(
    study_key_hash=None,  # Not provided
    hpo_parent_run_id="parent-run-123",  # Try to retrieve from parent
    data_config=data_config,
    hpo_config=hpo_config,
    train_config=train_config,
    backbone="distilbert-base-uncased",
    config_dir=config_dir,
)

# Get or compute trial key hash
trial_key_hash = get_or_compute_trial_key_hash(
    trial_key_hash=None,  # Not provided
    trial_run_id=None,  # Not available
    study_key_hash=study_key_hash,
    hyperparameters={"learning_rate": 3e-5, "batch_size": 16},
    config_dir=config_dir,
)
```

**Best Practice**: Use these consolidated utilities instead of implementing inline hash computation patterns. They follow the SSOT pattern and provide consistent fallback behavior across all execution scripts.

For detailed signatures, see source code.

**See Also**: 
- [`docs/architecture/mlflow-utilities.md`](../../../docs/architecture/mlflow-utilities.md) - Consolidated patterns and best practices
- [`docs/design/mlflow-layering.md`](../../../docs/design/mlflow-layering.md) - MLflow setup layering documentation

## Integration Points

### Used By

- **Training modules**: Use tracking for training run tracking
- **HPO modules**: Use tracking for HPO sweep tracking
- **Orchestration modules**: Use tracking for job tracking
- **Evaluation modules**: Use tracking for evaluation tracking

### Depends On

- `mlflow`: MLflow library
- `common/`: MLflow setup utilities, logging

## Best Practices

1. **Use setup_mlflow()**: Always use `setup_mlflow()` from this module (SSOT), don't call `mlflow.set_tracking_uri()` or `mlflow.set_experiment()` directly
2. **Layering**: Training and other modules should call `setup_mlflow()` first, then use domain-specific extensions for run lifecycle management
3. **Use trackers**: Use specialized trackers for different process types
4. **Consistent naming**: Use naming utilities for consistent run names
5. **Tag management**: Use tag utilities for consistent tagging
6. **Explicit path parameters**: When calling tracker methods that upload artifacts (e.g., `log_best_checkpoint()`), pass explicit `config_dir` parameter to avoid path inference issues in Colab where checkpoints may be in Drive while project code is elsewhere
7. **Trust provided parameters**: When calling utilities that accept `config_dir`, trust the provided value - inference only occurs when explicitly `None` (DRY principle)
8. **Use centralized hash utilities**: Always use `get_or_compute_study_key_hash()` and `get_or_compute_trial_key_hash()` instead of manually retrieving hashes from MLflow runs

**Note**: Training modules (e.g., `training.execution.mlflow_setup`) extend this module's setup with training-specific run lifecycle management. They assume MLflow has already been configured via `setup_mlflow()`.

**See Also**: 
- [`docs/architecture/mlflow-utilities.md`](../../../docs/architecture/mlflow-utilities.md) - Consolidated patterns, SSOT functions, and usage examples
- [`docs/design/mlflow-layering.md`](../../../docs/design/mlflow-layering.md) - Detailed MLflow setup layering documentation

### Colab-Specific Considerations

When running in Colab, checkpoints are often stored in Google Drive (`/content/drive/MyDrive/...`) while the project code is at `/content/resume-ner-azureml/`. To avoid path inference warnings:

- **Pass explicit `config_dir`**: When calling `MLflowSweepTracker.log_best_checkpoint()`, pass `config_dir` explicitly (e.g., `config_dir=root_dir / "config"`)
- **Use known paths**: Prefer passing `root_dir` and `config_dir` that are already known in the calling context rather than inferring from checkpoint paths

This prevents warnings like "Could not find project root. Using /content as fallback" during checkpoint upload.

## Testing

```bash
uvx pytest tests/infrastructure/tracking/
```

## Related Modules

- [`../README.md`](../README.md) - Main infrastructure module
- [`../naming/README.md`](../naming/README.md) - Naming uses tracking for run names
- [`../../common/README.md`](../../common/README.md) - Shared MLflow utilities


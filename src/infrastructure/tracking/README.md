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

**Layering**: This module provides the SSOT for MLflow setup. Training, deployment, and other modules should call `infrastructure.tracking.mlflow.setup.setup_mlflow()` first, then use domain-specific extensions (e.g., `training.execution.mlflow_setup` for run lifecycle management).

## Module Structure

- `mlflow/`: MLflow integration
  - `setup.py`: MLflow setup (SSOT for configuration)
  - `runs.py`: Run creation and management
  - `finder.py`: Run finding and querying
  - `artifacts/`: Artifact upload and download
  - `trackers/`: Specialized trackers (sweep, training, benchmark, conversion)
  - `hash_utils.py`: Hash computation for tracking
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

For detailed signatures, see source code.

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

**Note**: Training modules (e.g., `training.execution.mlflow_setup`) extend this module's setup with training-specific run lifecycle management. They assume MLflow has already been configured via `setup_mlflow()`.

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


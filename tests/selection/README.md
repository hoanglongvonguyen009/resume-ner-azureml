# Selection Tests

Model selection tests covering best model selection logic, artifact acquisition, cache tests, and workflow execution.

## TL;DR / Quick Start

Selection tests validate best model selection logic, artifact acquisition from multiple sources (local, drive, MLflow), cache functionality, and selection workflow execution. Tests cover both unit-level config validation and integration-level workflow execution.

```bash
# Run all selection tests
uvx pytest tests/selection/ -v

# Run specific category
uvx pytest tests/selection/unit/ -v
uvx pytest tests/selection/integration/ -v
```

## Overview

The `selection/` module provides tests for best model selection functionality:

- **Unit tests**: Config options, cache tests, study summary
- **Integration tests**: MLflow selection, artifact acquisition, workflow, edge cases, cache config

These tests validate best model selection logic, artifact acquisition from multiple sources (local, Google Drive, MLflow), cache functionality, and selection workflow execution.

## Test Structure

This test module is organized into the following categories:

- `unit/`: Unit tests for selection config and options
- `integration/`: Integration tests for selection workflow and artifact acquisition
- `conftest.py`: Module-specific fixtures

## Test Categories

- **Unit Tests** (`unit/`): Fast, isolated tests for selection configuration
  - Best model selection config
  - Artifact acquisition config
  - Artifact acquisition options
  - Study summary

- **Integration Tests** (`integration/`): Tests with real components
  - Best model selection workflow
  - Artifact acquisition logic
  - Artifact acquisition workflow
  - Artifact acquisition unified config
  - Artifact acquisition edge cases
  - Best model cache
  - Selection cache config
  - MLflow selection config
  - Selection edge cases

## Running Tests

### Basic Execution

```bash
# Run all selection tests
uvx pytest tests/selection/ -v

# Run with coverage
uvx pytest tests/selection/ --cov=src.evaluation.selection --cov-report=html

# Run specific category
uvx pytest tests/selection/unit/ -v
uvx pytest tests/selection/integration/ -v

# Run specific test file
uvx pytest tests/selection/unit/test_best_model_selection_config.py -v
uvx pytest tests/selection/integration/test_selection_workflow.py -v
```

### Advanced Execution

```bash
# Run specific test
uvx pytest tests/selection/integration/test_selection_workflow.py::test_selection_workflow_execution -v

# Run with markers (if defined)
uvx pytest tests/selection/ -m "slow" -v
```

## Test Fixtures and Helpers

### Available Fixtures

#### Shared Fixtures (from `fixtures/`)

- `tiny_dataset`: Creates minimal test dataset (from `fixtures.datasets`)
- `mock_mlflow_tracking`: Sets up local file-based MLflow tracking (from `fixtures.mlflow`)
  - Configures MLflow to use local file-based tracking
  - Mocks Azure ML client creation
- `mock_mlflow_run`: Creates a basic MLflow run with common tags and metrics (from `fixtures.mlflow`)
- `mock_hpo_trial_run`: Creates an HPO trial run with macro-f1 metric and HPO tags (from `fixtures.mlflow`)
  - Includes `tags.process.stage: "hpo"` and `tags.process.type: "trial"`
  - Includes `macro-f1` metric
- `mock_benchmark_run`: Creates a benchmark run with latency and throughput metrics (from `fixtures.mlflow`)
  - Includes latency and throughput metrics
  - Includes benchmark-specific tags
- `mock_refit_run`: Creates a refit run with checkpoint tags (from `fixtures.mlflow`)
  - Includes checkpoint tags (no macro-f1 metric)
- `clean_mlflow_db`: Cleans MLflow SQLite database between tests to prevent state pollution (from `fixtures.mlflow`)
  - Automatically used in `tests/selection/integration/conftest.py` with `autouse=True`
  - Prevents Alembic migration errors and database locking issues

### Usage Example

```python
from fixtures.mlflow import (
    mock_mlflow_tracking,
    mock_hpo_trial_run,
    mock_benchmark_run,
    mock_refit_run,
)

def test_selection_with_runs(mock_mlflow_tracking, mock_hpo_trial_run, mock_benchmark_run):
    # Use mock runs for selection tests
    trial_run = mock_hpo_trial_run
    benchmark_run = mock_benchmark_run
    # Test selection logic with these runs
```

See [`../fixtures/README.md`](../fixtures/README.md) for complete fixture documentation and usage examples.

## What Is Tested

### Unit Tests

- ✅ Best model selection config loading and validation
- ✅ Artifact acquisition config
- ✅ Artifact acquisition options
- ✅ Study summary

### Integration Tests

- ✅ Best model selection workflow execution
- ✅ Artifact acquisition logic (local, drive, MLflow)
- ✅ Artifact acquisition workflow
- ✅ Artifact acquisition unified config
- ✅ Artifact acquisition edge cases
- ✅ Best model cache functionality
- ✅ Selection cache config
- ✅ MLflow selection config
- ✅ Selection edge cases

## What Is Not Tested

- ❌ Real Google Drive API calls (mocked in tests)
- ❌ Real MLflow artifact downloads (mocked for CI speed)
- ❌ Large-scale selection with many models (only small selections tested for CI speed)

## Related Test Modules

- **Upstream dependencies** (test modules this depends on):
  - [`../fixtures/README.md`](../fixtures/README.md) - Shared fixtures used by these tests

- **Related test modules** (similar functionality):
  - [`../hpo/README.md`](../hpo/README.md) - HPO tests (selection uses HPO results)
  - [`../benchmarking/README.md`](../benchmarking/README.md) - Benchmarking tests (selection uses benchmark results)
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests use selection components

- **Downstream consumers** (test modules that use this):
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests use selection components
  - [`../final_training/README.md`](../final_training/README.md) - Final training tests use selected models


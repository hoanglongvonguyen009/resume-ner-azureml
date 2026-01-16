# Fixtures Tests

Shared test fixtures and helpers used across all test modules.

## TL;DR / Quick Start

This module provides reusable pytest fixtures for datasets, MLflow mocking, configs, and validation helpers. Import fixtures directly from the `fixtures` module.

```bash
# No tests to run - this is a fixtures module
# Import fixtures in your tests:
from fixtures import tiny_dataset, mock_mlflow_tracking, validate_path_structure
```

## Overview

The `fixtures/` module provides foundational test infrastructure that other tests depend on. It includes:

- **Dataset fixtures**: Create minimal test datasets for training and evaluation
- **MLflow fixtures**: Mock MLflow tracking for isolated testing
- **Config fixtures**: Pre-configured test configs for HPO, selection, acquisition, and conversion
- **Validation helpers**: Functions to validate paths, run names, and tags against config patterns

All fixtures are designed to be reusable and work with pytest's dependency injection system.

## Test Structure

- `datasets.py`: Dataset fixtures (`tiny_dataset`, `create_dataset_structure`)
- `mlflow.py`: MLflow mocking fixtures (`mock_mlflow_tracking`, `mock_mlflow_client`, `mock_mlflow_run`)
- `configs.py`: Config fixtures (HPO, selection, acquisition, conversion configs)
- `validators.py`: Validation helpers (`validate_path_structure`, `validate_run_name`, `validate_tags`)

## Running Tests

This module does not contain tests - it provides fixtures for other test modules. To verify fixtures work correctly, run tests that use them:

```bash
# Run tests that use fixtures
uvx pytest tests/workflows/ -v
uvx pytest tests/hpo/ -v
```

## Test Fixtures and Helpers

### Available Fixtures

#### Dataset Fixtures

- `tiny_dataset`: Pytest fixture that creates a minimal dataset structure with train.json, validation.json, and test.json in a temporary directory
- `create_dataset_structure()`: Helper function to create datasets with configurable sizes (train_size, val_size, test_size)

#### MLflow Fixtures

- `mock_mlflow_tracking`: Pytest fixture that sets up local file-based MLflow tracking and mocks Azure ML client creation
- `mock_mlflow_client()`: Helper function that creates a mock MLflow client with common operations
- `mock_mlflow_run()`: Helper function that creates a mock MLflow run with specified attributes (run_id, tags, metrics, params)

#### Config Fixtures

- `hpo_config_smoke`: Pytest fixture with full HPO config structure (search space, sampling, checkpoint, mlflow, early_termination, objective, selection, k_fold, refit, cleanup)
- `hpo_config_minimal`: Pytest fixture with minimal HPO config for simple tests
- `selection_config_default`: Pytest fixture with default best_model_selection.yaml configuration
- `acquisition_config_default`: Pytest fixture with default artifact_acquisition.yaml configuration
- `conversion_config_default`: Pytest fixture with default conversion.yaml configuration

#### Validation Helpers

- `validate_path_structure(path, pattern_type, config_dir)`: Validates that a path matches expected v2 pattern from infrastructure.paths.yaml
- `validate_run_name(run_name, process_type, config_dir)`: Validates that a run name matches naming.yaml patterns
- `validate_tags(tags, process_type, config_dir)`: Validates that tags match tags.yaml definitions, returns (is_valid, missing_tags_list)

### Usage Examples

```python
# Using dataset fixture
def test_training_with_dataset(tiny_dataset):
    dataset_path = tiny_dataset
    # Use dataset_path in your test
    assert dataset_path.exists()

# Using MLflow fixture
def test_mlflow_tracking(mock_mlflow_tracking):
    tracking_uri = mock_mlflow_tracking
    # MLflow is now configured to use local tracking
    import mlflow
    mlflow.start_run()
    mlflow.log_metric("test_metric", 1.0)

# Using config fixture
def test_hpo_with_config(hpo_config_smoke):
    config = hpo_config_smoke
    assert "search_space" in config
    assert "backbone" in config["search_space"]

# Using validation helpers
def test_path_validation(tmp_path, config_dir):
    test_path = tmp_path / "outputs" / "hpo_v2" / "study-123"
    is_valid = validate_path_structure(test_path, "hpo_v2", config_dir)
    assert is_valid
```

## What Is Tested

This module does not contain tests - it provides fixtures. However, fixtures are validated through their usage in other test modules:

- ✅ Dataset fixtures create valid dataset structures
- ✅ MLflow fixtures properly mock MLflow tracking
- ✅ Config fixtures provide valid config structures
- ✅ Validation helpers correctly validate paths, run names, and tags

## Related Test Modules

- **Downstream consumers** (test modules that use these fixtures):
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests use these fixtures
  - [`../hpo/README.md`](../hpo/README.md) - HPO tests use dataset and MLflow fixtures
  - [`../tracking/README.md`](../tracking/README.md) - Tracking tests use MLflow fixtures
  - [`../selection/README.md`](../selection/README.md) - Selection tests use config fixtures


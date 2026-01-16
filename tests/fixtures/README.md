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
- **Config directory fixtures**: Create temporary config directories with YAML files (paths.yaml, naming.yaml, tags.yaml, etc.)
- **Validation helpers**: Functions to validate paths, run names, and tags against config patterns

All fixtures are designed to be reusable and work with pytest's dependency injection system.

## Test Structure

- `datasets.py`: Dataset fixtures (`tiny_dataset`, `create_dataset_structure`)
- `mlflow.py`: MLflow mocking fixtures (`mock_mlflow_tracking`, `mock_mlflow_client`, `mock_mlflow_setup`, `mock_mlflow_run`, `mock_hpo_trial_run`, `mock_benchmark_run`, `mock_refit_run`, `mock_final_training_run`, `clean_mlflow_db`, `create_mock_run`, `create_mock_mlflow_client`)
- `configs.py`: Config fixtures (HPO, selection, acquisition, conversion configs)
- `config_dirs.py`: Config directory fixtures (`config_dir`, `config_dir_minimal`, `config_dir_full`, `create_config_dir_files`)
- `config_helpers.py`: Config helper functions (`create_minimal_training_config`, `create_minimal_data_config`, `create_minimal_experiment_config`, `create_minimal_model_config`)
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
- `mock_mlflow_client`: Pytest fixture that creates a mock MLflow client with common operations (returns tuple of `(mock_client, mock_parent_run)`)
- `mock_mlflow_setup`: Pytest fixture that combines `mock_mlflow_client` and returns a dictionary with `{"client": ..., "parent_run": ...}`
- `mock_mlflow_run`: Pytest fixture that creates a basic MLflow run with common tags and metrics
- `mock_hpo_trial_run`: Pytest fixture that creates an HPO trial run with macro-f1 metric and HPO tags
- `mock_benchmark_run`: Pytest fixture that creates a benchmark run with latency and throughput metrics
- `mock_refit_run`: Pytest fixture that creates a refit run with checkpoint tags (no macro-f1 metric)
- `mock_final_training_run`: Pytest fixture that creates a final training run with spec and exec hash tags
- `clean_mlflow_db`: Pytest fixture that cleans the MLflow SQLite database between tests to prevent state pollution and Alembic migration errors
- `create_mock_run(run_id, tags, metrics, params, experiment_id, status)`: Helper function to create custom mock runs
- `create_mock_mlflow_client()`: Helper function version of `mock_mlflow_client` fixture (use when you need to create a mock client outside of pytest fixtures)

#### Config Fixtures

- `hpo_config_smoke`: Pytest fixture with full HPO config structure (search space, sampling, checkpoint, mlflow, early_termination, objective, selection, k_fold, refit, cleanup)
- `hpo_config_minimal`: Pytest fixture with minimal HPO config for simple tests
- `selection_config_default`: Pytest fixture with default best_model_selection.yaml configuration
- `acquisition_config_default`: Pytest fixture with default artifact_acquisition.yaml configuration
- `conversion_config_default`: Pytest fixture with default conversion.yaml configuration

#### Config Directory Fixtures

- `config_dir`: Pytest fixture that creates a config directory with all commonly required YAML files (paths.yaml, naming.yaml, tags.yaml, mlflow.yaml, data.yaml)
- `config_dir_minimal`: Pytest fixture that creates a minimal config directory with only essential files (paths.yaml, naming.yaml, tags.yaml)
- `config_dir_full`: Pytest fixture that creates a full config directory with complete configuration structure including all options
- `create_config_dir_files(config_dir, files_dict)`: Helper function to programmatically create config files from a dictionary mapping filenames to YAML content

#### Config Helper Functions

- `create_minimal_training_config(config_dir)`: Creates minimal training config files (train.yaml, model/distilbert.yaml, data/resume_v1.yaml) needed for training subprocess
- `create_minimal_data_config(config_dir, dataset_name, dataset_version)`: Creates minimal data.yaml config file
- `create_minimal_experiment_config(config_dir, experiment_name)`: Creates minimal experiment.yaml config file
- `create_minimal_model_config(config_dir, model_name)`: Creates minimal model config file

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

# Using config directory fixture
def test_with_config_dir(config_dir):
    # config_dir is a Path to a temporary config directory with YAML files
    paths_yaml = config_dir / "paths.yaml"
    assert paths_yaml.exists()
    
# Using config_dir_minimal for simple tests
def test_minimal_config(config_dir_minimal):
    # Only essential files are created
    assert (config_dir_minimal / "paths.yaml").exists()
    
# Using create_config_dir_files helper
from fixtures import create_config_dir_files

def test_custom_config(tmp_path):
    config_dir = tmp_path / "config"
    create_config_dir_files(
        config_dir,
        {
            "paths.yaml": "schema_version: 2\nbase:\n  outputs: outputs",
            "custom.yaml": "custom_key: custom_value"
        }
    )
    assert (config_dir / "custom.yaml").exists()

# Using MLflow run fixtures
def test_with_hpo_trial_run(mock_hpo_trial_run):
    run = mock_hpo_trial_run
    assert run.data.metrics["macro-f1"] == 0.75
    assert run.data.tags["tags.process.stage"] == "hpo"

# Using clean_mlflow_db fixture to prevent state pollution
def test_mlflow_with_clean_db(clean_mlflow_db, mock_mlflow_tracking):
    # MLflow database is clean here - no Alembic errors
    tracking_uri = mock_mlflow_tracking
    import mlflow
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("test_experiment")
    # Your test code here

# To enable automatic cleanup for all tests in a module, add to conftest.py:
# @pytest.fixture(autouse=True)
# def auto_clean_mlflow_db(clean_mlflow_db):
#     yield

def test_with_benchmark_run(mock_benchmark_run):
    run = mock_benchmark_run
    assert "latency_batch_1_ms" in run.data.metrics

# Using config helpers
from fixtures.config_helpers import create_minimal_training_config

def test_with_minimal_config(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    create_minimal_training_config(config_dir)
    assert (config_dir / "train.yaml").exists()

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


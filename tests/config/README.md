# Config Tests

Configuration loading tests covering config loader, YAML configs, fingerprints, and path/naming/mlflow configuration.

## TL;DR / Quick Start

Config tests validate configuration loading functionality including experiment configs, data/model configs, paths/naming/mlflow YAML tests, fingerprints, and run mode. Tests cover both unit-level validation and integration-level behavior.

```bash
# Run all config tests
uvx pytest tests/config/ -v

# Run specific category
uvx pytest tests/config/unit/ -v
uvx pytest tests/config/integration/ -v
```

## Overview

The `config/` module provides tests for configuration loading functionality:

- **Unit tests**: Config loader, experiment/data/model configs, paths/naming/mlflow YAML tests, fingerprints, run mode, variants
- **Integration tests**: Config integration tests

These tests validate configuration loading, YAML config parsing, fingerprint computation, path/naming/mlflow configuration, and run mode decision logic.

## Test Structure

This test module is organized into the following categories:

- `unit/`: Unit tests for config loading components
- `integration/`: Integration tests for config behavior

## Test Categories

- **Unit Tests** (`unit/`): Fast, isolated tests for config components
  - Config loader and hashing
  - Experiment config loading
  - Data config loading
  - Model config loading
  - Paths YAML tests (including repository root detection configuration)
  - Project path resolution (`resolve_project_paths`)
  - Config directory inference (`infer_config_dir`)
  - Naming YAML tests
  - MLflow YAML tests
  - Fingerprints and placeholder fallback
  - Run mode
  - Variants

- **Integration Tests** (`integration/`): Tests with real components
  - Config integration tests

## Running Tests

### Basic Execution

```bash
# Run all config tests
uvx pytest tests/config/ -v

# Run with coverage
uvx pytest tests/config/ --cov=src.infrastructure.config --cov-report=html

# Run specific category
uvx pytest tests/config/unit/ -v
uvx pytest tests/config/integration/ -v

# Run specific test file
uvx pytest tests/config/unit/test_config_loader.py -v
uvx pytest tests/config/unit/test_paths_yaml.py -v
uvx pytest tests/config/unit/test_paths.py -v
```

### Advanced Execution

```bash
# Run specific test
uvx pytest tests/config/unit/test_config_loader.py::TestConfigHashComputation -v

# Run with markers (if defined)
uvx pytest tests/config/ -m "slow" -v
```

## Test Fixtures and Helpers

### Available Fixtures

#### Shared Fixtures (from `fixtures/`)

- `config_dir`: Creates temporary config directory with required YAML files (from `fixtures.config_dirs`)
  - Provides `paths.yaml`, `naming.yaml`, `tags.yaml`, `mlflow.yaml`, `data.yaml`
  - Used extensively in config tests for YAML validation
- `config_dir_minimal`: Creates minimal config directory with only essential files (from `fixtures.config_dirs`)
  - Provides only `paths.yaml`, `naming.yaml`, `tags.yaml`
  - Use for tests that don't need full config structure
- `config_dir_full`: Creates full config directory with complete configuration structure (from `fixtures.config_dirs`)
  - Provides all config files with complete options
  - Use for tests that need comprehensive config validation

#### Config Helper Functions (from `fixtures.config_helpers`)

- `create_minimal_training_config(config_dir)`: Creates minimal training config files
  - Creates `train.yaml`, `model/distilbert.yaml`, `data/resume_v1.yaml`
- `create_minimal_data_config(config_dir, dataset_name, dataset_version)`: Creates minimal data.yaml config file
- `create_minimal_experiment_config(config_dir, experiment_name)`: Creates minimal experiment.yaml config file
- `create_minimal_model_config(config_dir, model_name)`: Creates minimal model config file

#### Pytest Fixtures

- `tmp_path`: Pytest temporary directory fixture (used for creating test configs)

### Usage Example

```python
from fixtures.config_dirs import config_dir, config_dir_minimal
from fixtures.config_helpers import create_minimal_training_config

def test_config_loading(config_dir):
    # config_dir is a Path to a temporary config directory with YAML files
    paths_yaml = config_dir / "paths.yaml"
    assert paths_yaml.exists()
    
def test_minimal_config(config_dir_minimal):
    # Only essential files are created
    assert (config_dir_minimal / "paths.yaml").exists()
    
def test_custom_config(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    create_minimal_training_config(config_dir)
    assert (config_dir / "train.yaml").exists()
```

See [`../fixtures/README.md`](../fixtures/README.md) for complete fixture documentation and usage examples.

## What Is Tested

### Unit Tests

- ✅ Config loader and hashing
- ✅ Experiment config loading
- ✅ Data config loading
- ✅ Model config loading
- ✅ Paths YAML tests (including repository root detection configuration)
- ✅ Project path resolution (`resolve_project_paths`) - trusts provided config_dir, infers from output_dir/start_path
- ✅ Config directory inference (`infer_config_dir`) - searches up from path, validates with src/ directory
- ✅ Naming YAML tests
- ✅ MLflow YAML tests
- ✅ Fingerprints and placeholder fallback
- ✅ Run mode decision logic
- ✅ Variants

### Integration Tests

- ✅ Config integration tests

## What Is Not Tested

- ❌ Large-scale config loading (only small configs tested for CI speed)
- ❌ Complex config validation (basic validation only)
- ❌ Config migration/versioning (not supported in current implementation)

## Related Test Modules

- **Upstream dependencies** (test modules this depends on):
  - [`../fixtures/README.md`](../fixtures/README.md) - Shared fixtures used by these tests

- **Related test modules** (similar functionality):
  - [`../tracking/README.md`](../tracking/README.md) - Tracking tests (MLflow YAML config)
  - [`../hpo/README.md`](../hpo/README.md) - HPO tests use config loading
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests use config loading

- **Downstream consumers** (test modules that use this):
  - [`../hpo/README.md`](../hpo/README.md) - HPO tests use config loading
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests use config loading
  - [`../infrastructure/README.md`](../infrastructure/README.md) - Infrastructure tests use config components


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
  - Paths YAML tests
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

- `tmp_path`: Pytest temporary directory fixture (used for creating test configs)

See [`../fixtures/README.md`](../fixtures/README.md) for shared fixtures.

## What Is Tested

### Unit Tests

- ✅ Config loader and hashing
- ✅ Experiment config loading
- ✅ Data config loading
- ✅ Model config loading
- ✅ Paths YAML tests
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


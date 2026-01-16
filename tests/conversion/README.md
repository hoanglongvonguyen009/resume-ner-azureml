# Conversion Tests

Model conversion tests covering conversion workflows, configuration validation, and options testing.

## TL;DR / Quick Start

Conversion tests validate model conversion workflows, configuration loading, and conversion options. Tests cover both unit-level config validation and integration-level workflow execution.

```bash
# Run all conversion tests
uvx pytest tests/conversion/ -v

# Run specific category
uvx pytest tests/conversion/unit/ -v
uvx pytest tests/conversion/integration/ -v
```

## Overview

The `conversion/` module provides tests for model conversion functionality:

- **Unit tests**: Config validation, conversion options
- **Integration tests**: Conversion config integration tests

These tests validate conversion configuration loading, conversion options, and conversion workflow execution.

## Test Structure

This test module is organized into the following categories:

- `unit/`: Unit tests for conversion config and options
- `integration/`: Integration tests for conversion config
- `conftest.py`: Module-specific fixtures

## Test Categories

- **Unit Tests** (`unit/`): Fast, isolated tests for conversion configuration
  - Conversion config loading and validation
  - Conversion options

- **Integration Tests** (`integration/`): Tests with real components
  - Conversion config integration tests

## Running Tests

### Basic Execution

```bash
# Run all conversion tests
uvx pytest tests/conversion/ -v

# Run with coverage
uvx pytest tests/conversion/ --cov=src.training.conversion --cov-report=html

# Run specific category
uvx pytest tests/conversion/unit/ -v
uvx pytest tests/conversion/integration/ -v

# Run specific test file
uvx pytest tests/conversion/unit/test_conversion_config.py -v
uvx pytest tests/conversion/integration/test_conversion_config.py -v
```

### Advanced Execution

```bash
# Run specific test
uvx pytest tests/conversion/integration/test_conversion_config.py::test_conversion_workflow -v

# Run with markers (if defined)
uvx pytest tests/conversion/ -m "slow" -v
```

## Test Fixtures and Helpers

### Available Fixtures

#### Shared Fixtures (from `fixtures/`)

- `tiny_dataset`: Creates minimal test dataset (from `fixtures.datasets`)
- `mock_mlflow_tracking`: Sets up local file-based MLflow tracking (from `fixtures.mlflow`)
  - Configures MLflow to use local file-based tracking
  - Mocks Azure ML client creation

See [`../fixtures/README.md`](../fixtures/README.md) for complete fixture documentation and usage examples.

## What Is Tested

### Unit Tests

- ✅ Conversion config loading and validation
- ✅ Conversion options

### Integration Tests

- ✅ Conversion config integration tests

## What Is Not Tested

- ❌ Real ONNX conversion execution (mocked for CI speed)
- ❌ Large-scale conversion (only small conversions tested for CI speed)
- ❌ Production model conversion (uses minimal config for CI speed)

## Related Test Modules

- **Upstream dependencies** (test modules this depends on):
  - [`../fixtures/README.md`](../fixtures/README.md) - Shared fixtures used by these tests

- **Related test modules** (similar functionality):
  - [`../final_training/README.md`](../final_training/README.md) - Final training tests (conversion uses final training outputs)
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests use conversion components

- **Downstream consumers** (test modules that use this):
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests use conversion components


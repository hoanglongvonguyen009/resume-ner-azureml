# Final Training Tests

Final training tests covering final training components, logging intervals, and configuration validation.

## TL;DR / Quick Start

Final training tests validate final training component functionality, logging intervals, and configuration options. Tests cover both unit-level config validation and integration-level component execution.

```bash
# Run all final training tests
uvx pytest tests/final_training/ -v

# Run specific category
uvx pytest tests/final_training/unit/ -v
uvx pytest tests/final_training/integration/ -v
```

## Overview

The `final_training/` module provides tests for final training functionality:

- **Unit tests**: Config validation, critical config options
- **Integration tests**: Final training component execution, logging intervals

These tests validate final training configuration loading, component execution, and logging interval functionality.

## Test Structure

This test module is organized into the following categories:

- `unit/`: Unit tests for final training config
- `integration/`: Integration tests for final training components

## Test Categories

- **Unit Tests** (`unit/`): Fast, isolated tests for final training configuration
  - Final training config loading and validation
  - Critical config options

- **Integration Tests** (`integration/`): Tests with real components
  - Final training component execution
  - Logging intervals

## Running Tests

### Basic Execution

```bash
# Run all final training tests
uvx pytest tests/final_training/ -v

# Run with coverage
uvx pytest tests/final_training/ --cov=src.training.execution --cov-report=html

# Run specific category
uvx pytest tests/final_training/unit/ -v
uvx pytest tests/final_training/integration/ -v

# Run specific test file
uvx pytest tests/final_training/unit/test_final_training_config.py -v
uvx pytest tests/final_training/integration/test_final_training_component.py -v
```

### Advanced Execution

```bash
# Run specific test
uvx pytest tests/final_training/integration/test_final_training_component.py::test_final_training_execution -v

# Run with markers (if defined)
uvx pytest tests/final_training/ -m "slow" -v
```

## Test Fixtures and Helpers

### Available Fixtures

- `tiny_dataset`: Creates minimal test dataset (from `fixtures.datasets`)
- `mock_mlflow_tracking`: Sets up local file-based MLflow tracking (from `fixtures.mlflow`)

See [`../fixtures/README.md`](../fixtures/README.md) for shared fixtures.

## What Is Tested

### Unit Tests

- ✅ Final training config loading and validation
- ✅ Critical config options

### Integration Tests

- ✅ Final training component execution
- ✅ Logging intervals

## What Is Not Tested

- ❌ Real GPU training (mocked in tests)
- ❌ Long-running training jobs (uses minimal config for CI speed)
- ❌ Large-scale final training (only small training tested for CI speed)

## Related Test Modules

- **Upstream dependencies** (test modules this depends on):
  - [`../fixtures/README.md`](../fixtures/README.md) - Shared fixtures used by these tests

- **Related test modules** (similar functionality):
  - [`../selection/README.md`](../selection/README.md) - Selection tests (final training uses selected models)
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests use final training components

- **Downstream consumers** (test modules that use this):
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests use final training components
  - [`../conversion/README.md`](../conversion/README.md) - Conversion tests use final training outputs


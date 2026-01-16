# Benchmarking Tests

Benchmarking tests covering benchmark workflow, orchestrator, edge cases, and configuration options.

## TL;DR / Quick Start

Benchmarking tests validate benchmark workflow execution, orchestrator functionality, MLflow tracking, and edge cases. Tests cover both unit-level config validation and integration-level workflow execution.

```bash
# Run all benchmarking tests
uvx pytest tests/benchmarking/ -v

# Run specific category
uvx pytest tests/benchmarking/unit/ -v
uvx pytest tests/benchmarking/integration/ -v
```

## Overview

The `benchmarking/` module provides tests for benchmarking functionality:

- **Unit tests**: Config option tests, run mode config, trial ID extraction
- **Integration tests**: Benchmark workflow, orchestrator, utils, edge cases, MLflow tracking, run mode idempotency

These tests validate benchmark configuration loading, workflow execution, orchestrator functionality, MLflow tracking integration, and edge case handling.

## Test Structure

This test module is organized into the following categories:

- `unit/`: Unit tests for benchmark config options
- `integration/`: Integration tests for benchmark workflow and orchestrator

## Test Categories

- **Unit Tests** (`unit/`): Fast, isolated tests for benchmark configuration
  - Benchmark config loading and validation
  - Benchmark config options
  - Benchmark run mode config
  - Trial ID extraction

- **Integration Tests** (`integration/`): Tests with real components
  - Benchmark workflow execution
  - Benchmark orchestrator functionality
  - Benchmark utils
  - Edge cases
  - MLflow tracking integration
  - Run mode idempotency

## Running Tests

### Basic Execution

```bash
# Run all benchmarking tests
uvx pytest tests/benchmarking/ -v

# Run with coverage
uvx pytest tests/benchmarking/ --cov=src.evaluation.benchmarking --cov-report=html

# Run specific category
uvx pytest tests/benchmarking/unit/ -v
uvx pytest tests/benchmarking/integration/ -v

# Run specific test file
uvx pytest tests/benchmarking/unit/test_benchmark_config.py -v
uvx pytest tests/benchmarking/integration/test_benchmark_workflow.py -v
```

### Advanced Execution

```bash
# Run specific test
uvx pytest tests/benchmarking/integration/test_benchmark_workflow.py::test_benchmark_workflow_execution -v

# Run with markers (if defined)
uvx pytest tests/benchmarking/ -m "slow" -v
```

## Test Fixtures and Helpers

### Available Fixtures

#### Shared Fixtures (from `fixtures/`)

- `tiny_dataset`: Creates minimal test dataset (from `fixtures.datasets`)
- `mock_mlflow_tracking`: Sets up local file-based MLflow tracking (from `fixtures.mlflow`)
  - Configures MLflow to use local file-based tracking
  - Mocks Azure ML client creation
- `mock_benchmark_run`: Creates a benchmark run with latency and throughput metrics (from `fixtures.mlflow`)
  - Includes latency and throughput metrics
  - Includes benchmark-specific tags
- `config_dir`: Creates temporary config directory with required YAML files (from `fixtures.config_dirs`)
  - May be used for config validation tests
  - Provides `paths.yaml`, `naming.yaml`, `tags.yaml`, `mlflow.yaml`, `data.yaml`

See [`../fixtures/README.md`](../fixtures/README.md) for complete fixture documentation and usage examples.

## What Is Tested

### Unit Tests

- ✅ Benchmark config loading and validation
- ✅ Benchmark config options
- ✅ Benchmark run mode config
- ✅ Trial ID extraction

### Integration Tests

- ✅ Benchmark workflow execution
- ✅ Benchmark orchestrator functionality
- ✅ Benchmark utils
- ✅ Edge cases
- ✅ MLflow tracking integration
- ✅ Run mode idempotency

## What Is Not Tested

- ❌ Large-scale benchmark execution (only small benchmarks tested for CI speed)
- ❌ Real model inference performance (mocked for CI speed)
- ❌ Azure ML compute target provisioning (requires Azure ML workspace)

## Related Test Modules

- **Upstream dependencies** (test modules this depends on):
  - [`../fixtures/README.md`](../fixtures/README.md) - Shared fixtures used by these tests

- **Related test modules** (similar functionality):
  - [`../hpo/README.md`](../hpo/README.md) - HPO tests (similar structure)
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests use benchmarking components

- **Downstream consumers** (test modules that use this):
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests use benchmarking components


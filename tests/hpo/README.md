# HPO Tests

Hyperparameter optimization tests covering search space generation, trial execution, checkpoint resume, and sweep setup.

## TL;DR / Quick Start

HPO tests validate hyperparameter optimization functionality across unit, integration, and E2E levels. Tests cover search space generation, trial selection, checkpoint resume, early termination, and full HPO workflow execution.

```bash
# Run all HPO tests
uvx pytest tests/hpo/ -v

# Run specific category
uvx pytest tests/hpo/unit/ -v
uvx pytest tests/hpo/integration/ -v
uvx pytest tests/hpo/e2e/ -v
```

## Overview

The `hpo/` module provides comprehensive tests for hyperparameter optimization functionality:

- **Unit tests**: Fast, isolated tests for search space generation, trial selection, variant generation
- **Integration tests**: Tests with real components (sweep execution, checkpoint resume, refit training, early termination, path structure)
- **E2E tests**: Full HPO workflow tests with tiny datasets

These tests validate HPO search space configuration, trial execution, checkpoint resume functionality, early termination logic, MLflow tracking integration, and path structure validation.

## Test Structure

This test module is organized into the following categories:

- `unit/`: Unit tests for HPO components (search space, trial selection, variant generation)
- `integration/`: Integration tests with real components (sweep execution, checkpoint resume, refit training, early termination, path structure)
- `e2e/`: Full HPO workflow tests (`test_hpo_workflow.py`)
- `conftest.py`: Module-specific fixtures (tmp_project_structure, tmp_output_dir, train_config_minimal, data_config_minimal, mock_training_subprocess) and imports shared fixtures

## Test Categories

- **Unit Tests** (`unit/`): Fast, isolated tests for HPO components
  - Search space generation and validation
  - Trial selection logic
  - Variant generation

- **Integration Tests** (`integration/`): Tests with real components
  - HPO sweep setup and execution
  - Checkpoint resume functionality
  - Refit training
  - Early termination logic
  - Path structure validation
  - MLflow structure validation
  - Best trial selection component
  - HPO studies dictionary storage
  - Run mode variants
  - Smoke YAML options

- **E2E Tests** (`e2e/`): Full HPO workflow tests
  - Complete HPO workflow with tiny datasets
  - K-fold cross-validation
  - Edge cases (small datasets, k > n_samples)

## Running Tests

### Basic Execution

```bash
# Run all HPO tests
uvx pytest tests/hpo/ -v

# Run with coverage
uvx pytest tests/hpo/ --cov=src.training.hpo --cov-report=html

# Run specific category
uvx pytest tests/hpo/unit/ -v
uvx pytest tests/hpo/integration/ -v
uvx pytest tests/hpo/e2e/ -v

# Run specific test file
uvx pytest tests/hpo/unit/test_search_space.py -v
uvx pytest tests/hpo/integration/test_hpo_sweep_setup.py -v
```

### Advanced Execution

```bash
# Run specific test
uvx pytest tests/hpo/unit/test_search_space.py::test_search_space_generation -v

# Run with markers (if defined)
uvx pytest tests/hpo/ -m "slow" -v

# Run integration tests only
uvx pytest tests/hpo/integration/ -v
```

## Test Fixtures and Helpers

### Available Fixtures

#### Shared Fixtures (from `fixtures/`)

- `tiny_dataset`: Creates minimal test dataset (from `fixtures.datasets`)
- `config_dir` (aliased as `tmp_config_dir`): Creates temporary config directory with required YAML files (from `fixtures.config_dirs`)
  - Provides `paths.yaml`, `naming.yaml`, `tags.yaml`, `mlflow.yaml`, `data.yaml`
  - Use `config_dir_minimal` for tests that only need essential files
  - Use `config_dir_full` for tests that need complete configuration structure
- `mock_mlflow_client`: Provides mocked MLflow client with common operations (from `fixtures.mlflow`)
  - Returns tuple of `(mock_client, mock_parent_run)`
- `mock_mlflow_setup`: Sets up MLflow mocks for HPO tests (from `fixtures.mlflow`)
  - Returns dictionary with `{"client": ..., "parent_run": ...}`
- `clean_mlflow_db`: Cleans MLflow SQLite database between tests to prevent state pollution (from `fixtures.mlflow`)
  - Automatically used in `tests/hpo/integration/conftest.py` with `autouse=True`
  - Prevents Alembic migration errors and database locking issues
- `hpo_config_smoke`: Loads and returns smoke.yaml HPO config structure (from `fixtures.configs`)
  - Full HPO config with all options (search space, sampling, checkpoint, mlflow, early_termination, objective, selection, k_fold, refit, cleanup)
- `hpo_config_minimal`: Minimal HPO config for simple tests (from `fixtures.configs`)

#### Module-Specific Fixtures

- `tmp_project_structure`: Creates temporary project structure with src/training module
- `tmp_output_dir`: Creates temporary output directory for HPO
- `train_config_minimal`: Minimal training config for HPO tests
- `data_config_minimal`: Minimal data config for HPO tests
- `mock_training_subprocess`: Mocks training subprocess to return success and create metrics.json

### Config Helper Functions

- `create_minimal_training_config(config_dir)`: Creates minimal training config files (from `fixtures.config_helpers`)
  - Creates `train.yaml`, `model/distilbert.yaml`, `data/resume_v1.yaml` needed for training subprocess

See [`../fixtures/README.md`](../fixtures/README.md) for complete fixture documentation and usage examples.

## What Is Tested

### Unit Tests

- ✅ HPO search space generation and validation
- ✅ Trial selection logic
- ✅ Variant generation

### Integration Tests

- ✅ HPO sweep setup and execution
- ✅ Checkpoint resume functionality
- ✅ Refit training
- ✅ Early termination logic (bandit policy)
- ✅ Path structure validation (hpo_v2 patterns)
- ✅ MLflow structure validation
- ✅ Best trial selection component
- ✅ HPO studies dictionary storage (prevents indentation bugs)
- ✅ Run mode variants
- ✅ Smoke YAML options
- ✅ Trial execution with real components
- ✅ Error handling
- ✅ Assertions and validation

### E2E Tests

- ✅ Complete HPO workflow with tiny datasets
- ✅ K-fold cross-validation with small datasets
- ✅ Edge cases (minimal k, small validation sets, batch size issues)
- ✅ Random seed variants (seed0, seed1, seed2, ...)
- ✅ Multiple backbones

## What Is Not Tested

- ❌ Large-scale HPO sweeps (only small sweeps tested for CI speed)
- ❌ Distributed training (not supported in current implementation)
- ❌ Azure ML compute target provisioning (requires Azure ML workspace)
- ❌ GPU-specific optimizations (tests run without GPU)

## Configuration

### Test Configuration

Tests use minimal configs for CI compatibility:
- Minimal HPO trials (1-2 trials)
- Minimal dataset sizes (tiny datasets)
- Local file-based MLflow tracking
- Mocked training subprocess

### HPO Config Fixtures

- `hpo_config_smoke`: Full HPO config with all options (search space, sampling, checkpoint, mlflow, early_termination, objective, selection, k_fold, refit, cleanup)
- `hpo_config_minimal`: Minimal HPO config for simple tests

## Related Test Modules

- **Upstream dependencies** (test modules this depends on):
  - [`../fixtures/README.md`](../fixtures/README.md) - Shared fixtures used by these tests
  - [`../shared/README.md`](../shared/README.md) - HPO studies validation utilities

- **Related test modules** (similar functionality):
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests use HPO components
  - [`../benchmarking/README.md`](../benchmarking/README.md) - Benchmarking tests (similar structure)

- **Downstream consumers** (test modules that use this):
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests use HPO components


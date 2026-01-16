# Testing

Testing infrastructure and utilities for HPO pipeline testing, validation, and integration tests.

## TL;DR / Quick Start

Run integration tests for HPO pipeline, validate datasets, and execute test workflows.

```python
from src.testing.orchestrators.test_orchestrator import run_deterministic_hpo
from src.testing.services.kfold_validator import validate_kfold_splits
from src.testing.validators.dataset_validator import check_dataset_exists

# Validate dataset
if check_dataset_exists(dataset_path):
    # Validate K-fold splits
    kfold_results = validate_kfold_splits(dataset_path, k=5)
    
    # Run deterministic HPO test
    hpo_results = run_deterministic_hpo(
        dataset_path=dataset_path,
        config_dir=config_dir,
        hpo_config=hpo_config,
        train_config=train_config,
        output_dir=output_dir
    )
```

## Overview

The `testing` module provides testing infrastructure for HPO pipeline validation:

- **Test orchestration**: Coordinate test execution flow for HPO pipeline tests
- **Testing services**: HPO execution, K-fold validation, edge case detection
- **Data validation**: Validate datasets and data quality
- **Result processing**: Aggregate and compare test results
- **Test fixtures**: Test configuration, helpers, and utilities
- **Environment setup**: Test environment setup and configuration

This module supports integration testing of the HPO pipeline, ensuring deterministic behavior and validating data quality.

## Key Concepts

- **Deterministic testing**: Tests with fixed datasets and seeds for reproducibility
- **Integration tests**: End-to-end HPO pipeline testing
- **K-fold validation**: Validate cross-validation split creation
- **Result aggregation**: Collect and aggregate test results
- **Edge case detection**: Detect edge cases in datasets

## Module Structure

- `orchestrators/`: Test orchestration
  - `test_orchestrator.py`: Main test orchestrator for HPO pipeline tests
- `services/`: Testing services
  - `hpo_executor.py`: HPO execution service for tests
  - `kfold_validator.py`: K-fold cross-validation validation
  - `edge_case_detector.py`: Edge case detection in datasets
- `validators/`: Data validation
  - `dataset_validator.py`: Dataset existence and quality validation
- `aggregators/`: Result aggregation
  - `result_aggregator.py`: Aggregate test results
- `comparators/`: Result comparison
  - `result_comparator.py`: Compare test results
- `fixtures/`: Test fixtures and helpers
  - `config/`: Test configuration loaders
  - `hpo_test_helpers.py`: HPO test helper utilities
  - `presenters/`: Result presentation utilities
- `setup/`: Test environment setup
  - `environment_setup.py`: Test environment configuration

## Usage

### Basic Example: Run Deterministic HPO Test

```python
from pathlib import Path
from src.testing.orchestrators.test_orchestrator import run_deterministic_hpo

# Run deterministic HPO test
results = run_deterministic_hpo(
    dataset_path=Path("tests/fixtures/datasets/deterministic"),
    config_dir=Path("config/"),
    hpo_config={
        "n_trials": 5,
        "objective_metric": "macro-f1"
    },
    train_config={
        "training": {"epochs": 1, "batch_size": 8}
    },
    output_dir=Path("tests/outputs"),
    backbone="distilbert"
)

if results:
    print(f"Trials completed: {results['trials_completed']}")
    print(f"Best value: {results['best_value']}")
```

### Basic Example: Validate K-fold Splits

```python
from src.testing.services.kfold_validator import validate_kfold_splits

# Validate K-fold splits
results = validate_kfold_splits(
    dataset_path=Path("dataset/"),
    k=5,
    random_seed=42,
    shuffle=True
)

if results["success"]:
    print(f"Created {results['splits_created']} splits")
    print(f"All folds non-empty: {results['all_folds_non_empty']}")
```

### Basic Example: Validate Dataset

```python
from src.testing.validators.dataset_validator import check_dataset_exists

# Check if dataset exists
if check_dataset_exists(Path("dataset/")):
    print("Dataset exists and is valid")
else:
    print("Dataset not found or invalid")
```

### Basic Example: Run HPO Sweep for Testing

```python
from src.testing.services.hpo_executor import run_hpo_sweep_for_dataset

# Run HPO sweep for testing
results = run_hpo_sweep_for_dataset(
    dataset_path=Path("dataset/"),
    config_dir=Path("config/"),
    hpo_config=hpo_config,
    train_config=train_config,
    output_dir=Path("tests/outputs"),
    mlflow_experiment_name="test-hpo",
    backbone="distilbert"
)

print(f"Success: {results['success']}")
print(f"Best trial: {results['best_trial']}")
```

## API Reference

### Test Orchestration

- `run_deterministic_hpo(...)`: Run deterministic HPO test
- `run_full_test_suite(...)`: Run full test suite

### Testing Services

- `run_hpo_sweep_for_dataset(...)`: Run HPO sweep for dataset (testing)
- `validate_kfold_splits(...)`: Validate K-fold cross-validation splits
- `detect_edge_cases(...)`: Detect edge cases in dataset

### Data Validation

- `check_dataset_exists(dataset_path: Path) -> bool`: Check if dataset exists and is valid

### Result Processing

- `build_test_details(...)`: Build test details from results
- `collect_test_results(...)`: Collect test results
- `compare_results(...)`: Compare test results

For detailed signatures, see source code.

## Integration Points

### Used By

- **Test suites**: Use testing infrastructure for integration tests
- **CI/CD**: Use testing infrastructure for automated testing

### Depends On

- `training/`: HPO execution, training utilities
- `data/`: Data loading utilities
- `infrastructure/`: Configuration, paths
- `common/`: Shared utilities

## Testing Patterns

### Deterministic Testing

Tests use deterministic datasets and fixed random seeds to ensure reproducible results:
- Fixed dataset with known characteristics
- Fixed random seeds for all random operations
- Expected results validation

### Integration Testing

Integration tests validate end-to-end HPO pipeline:
- Dataset loading
- HPO sweep execution
- Trial execution and results
- Best trial selection

## Testing

```bash
uvx pytest tests/testing/
```

## Related Modules

- [`../training/README.md`](../training/README.md) - Training and HPO used by tests
- [`../data/README.md`](../data/README.md) - Data loading used by tests
- [`../infrastructure/README.md`](../infrastructure/README.md) - Infrastructure used by tests


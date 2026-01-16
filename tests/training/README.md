# Training Tests

Training component tests covering trainer, checkpoint loader, data combiner, CV utils, and HPO-specific training functionality.

## TL;DR / Quick Start

Training tests validate training component functionality including training loop, checkpoint loading, data combination, cross-validation utilities, and HPO-specific training features. Tests require PyTorch and should be run in the resume-ner-training environment.

```bash
# Run all training tests
uvx pytest tests/unit/training/ tests/training/ -v

# Run specific category
uvx pytest tests/unit/training/ -v
uvx pytest tests/training/hpo/ -v
```

## Overview

The `training/` module provides tests for training component functionality:

- **Unit tests** (`tests/unit/training/`): Training component tests
  - Trainer (training loop and data loader)
  - Checkpoint loader (path resolution and validation)
  - Data combiner (dataset combination strategy)
  - CV utils (cross-validation utilities)
  - Train config defaults

- **HPO training tests** (`tests/training/hpo/`): HPO-specific training tests
  - CV hash computation
  - Phase 2 tags
  - Hash consistency

These tests validate training loop functionality, checkpoint path resolution, dataset combination strategies, cross-validation utilities, and HPO-specific training features.

## Test Structure

Training tests are organized in two locations:

- `tests/unit/training/`: Main training component tests
- `tests/training/hpo/`: HPO-specific training tests (unit and integration)

## Test Categories

- **Unit Tests** (`tests/unit/training/`): Training component tests
  - Trainer - training loop and data loader tests
  - Checkpoint loader - checkpoint path resolution and validation tests
  - Data combiner - dataset combination strategy tests
  - CV utils - cross-validation utilities tests
  - Train config defaults

- **HPO Training Tests** (`tests/training/hpo/`): HPO-specific training tests
  - **Unit tests**: CV hash computation, phase 2 tags
  - **Integration tests**: Hash consistency

## Running Tests

### Basic Execution

```bash
# Run all training tests
uvx pytest tests/unit/training/ tests/training/ -v

# Run with coverage
uvx pytest tests/unit/training/ tests/training/ --cov=src.training --cov-report=html

# Run specific category
uvx pytest tests/unit/training/ -v
uvx pytest tests/training/hpo/ -v

# Run specific test file
uvx pytest tests/unit/training/test_trainer.py -v
uvx pytest tests/unit/training/test_checkpoint_loader.py -v
uvx pytest tests/unit/training/test_data_combiner.py -v
uvx pytest tests/unit/training/test_cv_utils.py -v
```

### Advanced Execution

```bash
# Run specific test
uvx pytest tests/unit/training/test_trainer.py::TestPrepareDataLoaders -v

# Run with markers (if defined)
uvx pytest tests/unit/training/ tests/training/ -m "torch" -v
```

## Test Fixtures and Helpers

### Available Fixtures

- `tmp_path`: Pytest temporary directory fixture (used for creating test datasets and checkpoints)
- `old_dataset`: Creates temporary old dataset (data combiner tests)
- `new_dataset`: Creates temporary new dataset (data combiner tests)

### Test Markers

- `@pytest.mark.torch`: Marks tests that require PyTorch

## What Is Tested

### Unit Tests (`tests/unit/training/`)

- ✅ Training loop functionality
- ✅ Data loader preparation
- ✅ Checkpoint path resolution
- ✅ Checkpoint validation
- ✅ Dataset combination strategies
- ✅ Cross-validation split creation
- ✅ Fold split saving and loading
- ✅ Fold data retrieval
- ✅ Split validation
- ✅ Train config defaults

### HPO Training Tests (`tests/training/hpo/`)

- ✅ CV hash computation (priority hierarchy, hash consistency)
- ✅ Phase 2 tags
- ✅ Hash consistency between parent and trial runs

## What Is Not Tested

- ❌ Real GPU training (mocked in tests)
- ❌ Long-running training jobs (uses minimal config for CI speed)
- ❌ Large-scale training (only small-scale tests for CI speed)
- ❌ Distributed training (not supported in current implementation)

## Configuration

### Test Requirements

- **PyTorch**: Required for training tests (tests are marked with `@pytest.mark.torch`)
- **Environment**: Tests should be run in the `resume-ner-training` environment
- **Dependencies**: Transformers, torch, and related ML libraries

### Test Configuration

Tests use minimal configs for CI compatibility:
- Minimal training epochs
- Small dataset sizes
- Mocked model components where possible

## Dependencies

- **PyTorch**: Required for training tests
- **Transformers**: Required for tokenization and model loading
- **Test fixtures**: Uses pytest fixtures for temporary directories and datasets

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:
1. Ensure `src/` is in Python path
2. Install required dependencies: `pip install torch transformers`
3. Activate the `resume-ner-training` environment

### PyTorch Not Available

If tests fail with PyTorch import errors:
1. Ensure PyTorch is installed: `pip install torch`
2. Verify environment is activated: `conda activate resume-ner-training`
3. Tests are marked with `@pytest.mark.torch` and will be skipped if PyTorch is not available

### Checkpoint Not Found

If checkpoint tests fail:
1. Verify checkpoint directory structure
2. Check that required files exist (config.json, pytorch_model.bin)
3. Verify checkpoint path resolution logic

## Related Test Modules

- **Upstream dependencies** (test modules this depends on):
  - [`../fixtures/README.md`](../fixtures/README.md) - Shared fixtures used by these tests

- **Related test modules** (similar functionality):
  - [`../hpo/README.md`](../hpo/README.md) - HPO tests (use training components)
  - [`../final_training/README.md`](../final_training/README.md) - Final training tests (use training components)
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests use training components

- **Downstream consumers** (test modules that use this):
  - [`../hpo/README.md`](../hpo/README.md) - HPO tests use training components
  - [`../final_training/README.md`](../final_training/README.md) - Final training tests use training components
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests use training components


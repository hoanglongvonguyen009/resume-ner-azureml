# Tracking Tests

MLflow tracking tests covering naming policies, tags registry, MLflow configuration, and Azure ML artifact upload.

## TL;DR / Quick Start

Tracking tests validate MLflow tracking functionality including naming policies, tags registry, MLflow configuration, and Azure ML artifact upload fixes. Tests cover both unit-level validation and integration-level behavior.

```bash
# Run all tracking tests
uvx pytest tests/tracking/ -v

# Run specific category
uvx pytest tests/tracking/unit/ -v
uvx pytest tests/tracking/integration/ -v

# Run Azure ML artifact upload tests
uvx pytest tests/tracking/unit/test_azureml_artifact_upload.py -v
```

## Overview

The `tracking/` module provides tests for MLflow tracking functionality:

- **Unit tests**: Naming policy, tags registry, MLflow config, Azure ML artifact upload
- **Integration tests**: Tracking config enabled, naming integration, Azure ML artifact upload integration
- **Test scripts**: Manual verification tools for artifact upload fixes

These tests validate MLflow naming policies, tags registry functionality, MLflow configuration inference, and Azure ML artifact upload fixes (monkey-patch, child run uploads, refit run completion).

## Test Structure

This test module is organized into the following categories:

- `unit/`: Unit tests for MLflow tracking components
- `integration/`: Integration tests for tracking behavior
- `scripts/`: Manual test scripts and verification tools

## Test Categories

- **Unit Tests** (`unit/`): Fast, isolated tests for tracking components
  - Naming policy and centralized naming
  - Naming placeholder truncation
  - Tags registry and comprehensive tag tests
  - MLflow config comprehensive tests
  - MLflow utilities and config inference
  - Sweep tracker config inference
  - Azure ML artifact upload (monkey-patch, child run uploads)

- **Integration Tests** (`integration/`): Tests with real components
  - Tracking config enabled
  - Naming integration
  - Azure ML artifact upload integration (requires Azure ML workspace)

- **Test Scripts** (`scripts/`): Manual verification tools
  - `test_artifact_upload_manual.py`: Manual test script for real Azure ML environments
  - `verify_artifact_upload_fix.py`: Quick verification that fixes are in place

## Running Tests

### Basic Execution

```bash
# Run all tracking tests
uvx pytest tests/tracking/ -v

# Run with coverage
uvx pytest tests/tracking/ --cov=src.infrastructure.tracking --cov-report=html

# Run specific category
uvx pytest tests/tracking/unit/ -v
uvx pytest tests/tracking/integration/ -v

# Run specific test file
uvx pytest tests/tracking/unit/test_naming_policy.py -v
uvx pytest tests/tracking/unit/test_azureml_artifact_upload.py -v
```

### Advanced Execution

```bash
# Run Azure ML artifact upload unit tests (no Azure ML required)
uvx pytest tests/tracking/unit/test_azureml_artifact_upload.py -v

# Run Azure ML artifact upload integration tests (requires Azure ML)
uvx pytest tests/tracking/integration/test_azureml_artifact_upload_integration.py -v --run-azureml-tests

# Run specific test
uvx pytest tests/tracking/unit/test_azureml_artifact_upload.py::TestAzureMLArtifactBuilderPatch -v

# Verify artifact upload fixes are in place (quick check)
python tests/tracking/scripts/verify_artifact_upload_fix.py

# Manual artifact upload test (requires active MLflow run in Azure ML)
python tests/tracking/scripts/test_artifact_upload_manual.py
```

## Test Fixtures and Helpers

### Available Fixtures

- `mock_mlflow_tracking`: Sets up local file-based MLflow tracking (from `fixtures.mlflow`)

See [`../fixtures/README.md`](../fixtures/README.md) for shared fixtures.

## What Is Tested

### Unit Tests

- ✅ MLflow naming policy and centralized naming
- ✅ Naming placeholder truncation
- ✅ Tags registry functionality
- ✅ Comprehensive tag tests
- ✅ MLflow config comprehensive tests
- ✅ MLflow utilities and config inference
- ✅ Sweep tracker config inference
- ✅ Azure ML artifact upload monkey-patch registration
- ✅ Artifact upload to refit runs (child runs)
- ✅ Artifact upload to parent runs (fallback)
- ✅ Refit run FINISHED status marking

### Integration Tests

- ✅ Tracking config enabled
- ✅ Naming integration
- ✅ Azure ML artifact upload integration (full workflow)
- ✅ Refit run completion logic

### Test Scripts

- ✅ Manual verification of artifact upload fixes
- ✅ Real Azure ML environment testing

## What Is Not Tested

- ❌ Real Azure ML workspace operations (mocked in unit tests, requires Azure ML for integration tests)
- ❌ Large-scale MLflow tracking (only small-scale tests for CI speed)
- ❌ Distributed MLflow tracking (not supported in current implementation)

## Configuration

### Azure ML Artifact Upload Tests

The Azure ML artifact upload tests validate fixes for:

1. **Monkey-patch for `azureml_artifacts_builder`**: Fixes compatibility issue between MLflow 3.5.0 and azureml-mlflow 1.61.0.post1
2. **Artifact upload to child runs**: Verifies artifacts can be uploaded to refit runs (child runs) instead of parent runs
3. **Refit run completion**: Ensures refit runs are marked as FINISHED after artifact upload

See [`README_artifact_upload_tests.md`](README_artifact_upload_tests.md) for detailed documentation.

## Dependencies

- **MLflow**: Required for tracking tests
- **Azure ML SDK**: Required for Azure ML artifact upload integration tests (optional)
- **Test fixtures**: Uses fixtures from `tests/fixtures/` (MLflow mocking)

## Troubleshooting

### Azure ML Builder Not Registered

If you see "Azure ML builder not registered":
- This is expected if not using Azure ML workspace
- Azure ML-specific tests will be skipped
- Unit tests work without Azure ML SDK

### Integration Test Failures

If Azure ML integration tests fail:
- Ensure Azure ML workspace is configured
- Verify `--run-azureml-tests` flag is used
- Check that active MLflow run exists in Azure ML environment

## Related Test Modules

- **Upstream dependencies** (test modules this depends on):
  - [`../fixtures/README.md`](../fixtures/README.md) - Shared fixtures used by these tests

- **Related test modules** (similar functionality):
  - [`../hpo/README.md`](../hpo/README.md) - HPO tests use MLflow tracking
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests use MLflow tracking
  - [`../config/README.md`](../config/README.md) - Config tests (MLflow YAML config)

- **Downstream consumers** (test modules that use this):
  - [`../hpo/README.md`](../hpo/README.md) - HPO tests use MLflow tracking
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests use MLflow tracking

## References

- [`README_artifact_upload_tests.md`](README_artifact_upload_tests.md) - Detailed Azure ML artifact upload test documentation
- [`TEST_SUMMARY.md`](TEST_SUMMARY.md) - Quick reference for artifact upload tests


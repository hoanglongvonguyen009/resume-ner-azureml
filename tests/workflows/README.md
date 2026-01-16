# Workflows Tests

End-to-end workflow tests that validate complete notebook workflows from start to finish.

## TL;DR / Quick Start

These tests validate complete notebook workflows end-to-end, from HPO training through best model selection, final training, and conversion. Tests support both mocked training (CI-compatible) and real training execution modes.

```bash
# Run all workflow tests (default: mocked training, CI-compatible)
uvx pytest tests/workflows/ -v

# Run specific workflow test
uvx pytest tests/workflows/test_notebook_01_e2e.py -v

# Run with real training (slower)
E2E_USE_REAL_TRAINING=true uvx pytest tests/workflows/ -v
```

## Overview

The `workflows/` module provides end-to-end tests that validate complete notebook workflows:

- **Notebook 01 E2E**: Tests the complete workflow from `01_orchestrate_training_colab.ipynb` (HPO + Benchmarking)
- **Notebook 02 E2E**: Tests the complete workflow from `02_best_config_selection.ipynb` (Selection → Final Training → Conversion)
- **Full Workflow E2E**: Tests the complete pipeline from notebook 01 through notebook 02 (HPO → Benchmarking → Selection → Final Training → Conversion)

These tests exercise the real orchestration modules, config usage, naming, paths, and tags without requiring Azure ML, GPUs, or long training/benchmark jobs. They validate:

- Path structure against `paths.yaml` v2 patterns
- Run names against `naming.yaml` patterns
- Tags against `tags.yaml` definitions
- Metadata.json structure throughout the pipeline
- Lineage tracking (HPO → final training → conversion)

## Test Structure

- `test_notebook_01_e2e.py`: E2E test for notebook 01 (HPO + Benchmarking workflow)
- `test_notebook_02_e2e.py`: E2E test for notebook 02 (Best config selection → final training → conversion)
- `test_full_workflow_e2e.py`: E2E test for complete workflow (01 → 02 end-to-end)
- `conftest.py`: Module-specific fixtures (mock_mlflow, mock_subprocess)

## Running Tests

### Basic Execution

```bash
# Run all workflow tests (default: mocked training, CI-compatible)
uvx pytest tests/workflows/ -v

# Run specific workflow test
uvx pytest tests/workflows/test_notebook_01_e2e.py -v
uvx pytest tests/workflows/test_notebook_02_e2e.py -v
uvx pytest tests/workflows/test_full_workflow_e2e.py -v

# Run specific test class
uvx pytest tests/workflows/test_notebook_01_e2e.py::TestNotebookE2E_Core -v
```

### Advanced Execution

#### Test Scope Modes

```bash
# Core workflow (default): Skips repo setup and dependency install
uvx pytest tests/workflows/test_notebook_01_e2e.py -v

# Full workflow: Includes repo setup and dependency install
E2E_TEST_SCOPE=full uvx pytest tests/workflows/test_notebook_01_e2e.py -v
```

#### Training Execution Modes

```bash
# Mocked training (default, CI-compatible): Simulates training without actual execution
uvx pytest tests/workflows/ -v

# Real training: Executes actual training with minimal config
E2E_USE_REAL_TRAINING=true uvx pytest tests/workflows/ -v

# Real training with custom HPO trials
E2E_USE_REAL_TRAINING=true E2E_HPO_TRIALS=2 uvx pytest tests/workflows/test_notebook_01_e2e.py -v
```

#### CI Mode

```bash
# Explicit CI mode (skips GPU checks)
E2E_SKIP_GPU_CHECKS=true E2E_TEST_SCOPE=core uvx pytest tests/workflows/ -v
```

## Test Fixtures and Helpers

### Available Fixtures

- `tiny_dataset`: Creates minimal test dataset (from `fixtures.datasets`)
- `mock_mlflow_tracking`: Sets up local file-based MLflow tracking (from `fixtures.mlflow`)
- `mock_mlflow`: Mock MLflow module for tests (module-specific)
- `mock_subprocess`: Mock subprocess execution for tests (module-specific)

### Validation Helpers

- `validate_path_structure(path, pattern_type, config_dir)`: Validates paths against `paths.yaml` v2 patterns
- `validate_run_name(run_name, process_type, config_dir)`: Validates run names against `naming.yaml` patterns
- `validate_tags(tags, process_type, config_dir)`: Validates tags against `tags.yaml` definitions

See [`../fixtures/README.md`](../fixtures/README.md) for shared fixtures.

## What Is Tested

### Notebook 01 E2E Test

Tests the complete workflow from `01_orchestrate_training_colab.ipynb`:

- ✅ Environment detection
- ✅ Repository setup (optional, full scope)
- ✅ Dependency installation (optional, full scope)
- ✅ Path setup
- ✅ Config loading
- ✅ Dataset verification
- ✅ MLflow setup (with Azure ML mocking)
- ✅ HPO sweep execution (mockable training)
- ✅ Benchmarking execution (mockable)
- ✅ Output validation (path structure, run names, tags)

### Notebook 02 E2E Test

Tests the complete workflow from `02_best_config_selection.ipynb`:

- ✅ Best model selection
- ✅ Artifact acquisition
- ✅ Final training (mocked)
- ✅ Model conversion (mocked)
- ✅ Path structure validation (final_training_v2, conversion_v2, best_config_v2)
- ✅ Run name validation (final_training, conversion)
- ✅ Tag validation (when MLflow runs are available)
- ✅ Metadata.json structure validation (spec_fp, exec_fp, mlflow.run_id)
- ✅ Lineage extraction validation (hpo_study_key_hash, hpo_trial_key_hash)

### Full Workflow E2E Test

Tests the complete workflow from notebook 01 through notebook 02:

- ✅ Complete pipeline: HPO → Benchmarking → Selection → Final Training → Conversion
- ✅ Path structure validation throughout (hpo_v2, benchmarking_v2, final_training_v2, conversion_v2, best_config_v2)
- ✅ Run name validation throughout (hpo, benchmarking, final_training, conversion)
- ✅ Tag validation throughout (when MLflow runs are available)
- ✅ Metadata.json structure validation throughout
- ✅ Lineage tracking validation (HPO → final training → conversion)

## What Is Not Tested

- ❌ Actual GPU training (mocked in CI mode)
- ❌ Azure ML compute target provisioning (requires Azure ML workspace)
- ❌ Long-running training jobs (uses minimal config for real execution)
- ❌ Large-scale HPO sweeps (only small sweeps tested for CI speed)
- ❌ Real benchmark execution (mocked for CI speed)

## Configuration

### Environment Variables

- `E2E_TEST_SCOPE`: Test scope mode (`core` or `full`, default: `core`)
  - `core`: Skips repo setup and dependency install (CI-compatible)
  - `full`: Includes all steps including repo setup and dependency install

- `E2E_USE_REAL_TRAINING`: Enable real training execution (`true` or `false`, default: `false`)
  - `false`: Uses mocked training (CI-compatible, faster)
  - `true`: Executes actual training with minimal config (slower)

- `E2E_SKIP_GPU_CHECKS`: Skip GPU detection checks (`true` or `false`, default: `true`)
  - `true`: Skips GPU checks (CI-compatible)
  - `false`: Performs GPU detection

- `E2E_HPO_TRIALS`: Number of HPO trials for real training (default: `1`)
  - Only used when `E2E_USE_REAL_TRAINING=true`

### Test Configuration

Tests use minimal configs for CI compatibility:
- Minimal HPO trials (1-2 trials)
- Minimal dataset sizes
- Local file-based MLflow tracking
- Mocked Azure ML client creation

## Dependencies

- **Test fixtures**: Uses fixtures from `tests/fixtures/` (datasets, MLflow mocking, validators)
- **Config files**: Requires `config/` directory with YAML configs (paths.yaml, naming.yaml, tags.yaml)
- **Dataset**: Requires tiny dataset (created by `notebooks/00_make_tiny_dataset.ipynb`)

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:
1. Ensure `src/` is in Python path (usually handled automatically by test scripts)
2. Verify test fixtures are available: `from fixtures import ...`

### Dataset Not Found

If tests fail with "Dataset directory not found":
```bash
# Create tiny datasets first
jupyter nbconvert --execute notebooks/00_make_tiny_dataset.ipynb
```

### MLflow Errors

If MLflow tracking fails:
- Tests use local file-based tracking by default
- Check that `mlruns/` directory is writable
- Azure ML-specific tests will be skipped if Azure ML SDK is not installed

### Real Training Failures

If real training fails:
- Ensure GPU is available (if not using `E2E_SKIP_GPU_CHECKS=true`)
- Check that dataset exists and is valid
- Verify HPO config is valid (`config/hpo/smoke.yaml`)

## Related Test Modules

- **Upstream dependencies** (test modules this depends on):
  - [`../fixtures/README.md`](../fixtures/README.md) - Shared fixtures used by these tests

- **Related test modules** (similar functionality):
  - [`../hpo/README.md`](../hpo/README.md) - HPO component tests (unit, integration)
  - [`../benchmarking/README.md`](../benchmarking/README.md) - Benchmarking component tests
  - [`../selection/README.md`](../selection/README.md) - Model selection component tests
  - [`../final_training/README.md`](../final_training/README.md) - Final training component tests
  - [`../conversion/README.md`](../conversion/README.md) - Model conversion component tests


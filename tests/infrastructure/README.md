# Infrastructure Tests

Infrastructure component tests covering config run decisions, naming, paths, and tracking functionality.

## TL;DR / Quick Start

Infrastructure tests validate infrastructure components including config run decisions, naming (HPO keys, semantic suffix), paths (repository root detection, config inference), and tracking (MLflow queries, sweep tracker). Tests are organized by submodule (config, naming, paths, tracking).

```bash
# Run all infrastructure tests
uvx pytest tests/infrastructure/ -v

# Run specific submodule
uvx pytest tests/infrastructure/config/ -v
uvx pytest tests/infrastructure/naming/ -v
uvx pytest tests/infrastructure/paths/ -v
uvx pytest tests/infrastructure/tracking/ -v
```

## Overview

The `infrastructure/` module provides tests for infrastructure components:

- **Config tests**: Run decision logic, selection
- **Naming tests**: HPO keys v2, semantic suffix
- **Paths tests**: Repository root detection, config directory inference, project path resolution
- **Tracking tests**: MLflow queries, sweep tracker hash and search

These tests validate infrastructure component functionality including run decision logic, naming key generation, path resolution, and MLflow tracking utilities.

## Test Structure

This test module is organized by infrastructure submodules:

- `config/`: Config infrastructure tests (run decision, selection)
- `naming/`: Naming infrastructure tests (HPO keys v2, semantic suffix)
- `paths/`: Path infrastructure tests (repository root detection, config inference)
- `tracking/`: Tracking infrastructure tests (MLflow queries, sweep tracker)

## Test Categories

- **Config Tests** (`config/`): Infrastructure config component tests
  - Run decision logic (should_reuse_existing, get_load_if_exists_flag)
  - Selection

- **Naming Tests** (`naming/`): Infrastructure naming component tests
  - HPO keys v2
  - Semantic suffix

- **Paths Tests** (`paths/`): Infrastructure path component tests
  - Repository root detection (`detect_repo_root`)
  - Repository root validation (`validate_repo_root`)
  - Config directory inference (`infer_config_dir`)
  - Project path resolution (`resolve_project_paths`)
  - Deprecated function wrappers (backward compatibility)

- **Tracking Tests** (`tracking/`): Infrastructure tracking component tests
  - MLflow queries
  - Sweep tracker hash and search

## Running Tests

### Basic Execution

```bash
# Run all infrastructure tests
uvx pytest tests/infrastructure/ -v

# Run with coverage
uvx pytest tests/infrastructure/ --cov=src.infrastructure --cov-report=html

# Run specific submodule
uvx pytest tests/infrastructure/config/ -v
uvx pytest tests/infrastructure/naming/ -v
uvx pytest tests/infrastructure/tracking/ -v

# Run specific test file
uvx pytest tests/infrastructure/config/unit/test_run_decision.py -v
uvx pytest tests/infrastructure/naming/test_hpo_keys_v2.py -v
uvx pytest tests/infrastructure/paths/test_repo_root_detection.py -v
```

### Advanced Execution

```bash
# Run specific test
uvx pytest tests/infrastructure/config/unit/test_run_decision.py::TestShouldReuseExisting -v

# Run with markers (if defined)
uvx pytest tests/infrastructure/ -m "slow" -v
```

## Test Fixtures and Helpers

### Available Fixtures

- `tmp_path`: Pytest temporary directory fixture (used for creating test configs)

See [`../fixtures/README.md`](../fixtures/README.md) for complete fixture documentation and usage examples.

## What Is Tested

### Config Tests

- ✅ Run decision logic (should_reuse_existing, get_load_if_exists_flag)
- ✅ Selection

### Naming Tests

- ✅ HPO keys v2 generation
- ✅ Semantic suffix

### Paths Tests

- ✅ Repository root detection from various starting points (config_dir, output_dir, start_path, cwd)
- ✅ Repository root validation (required/optional markers)
- ✅ Config directory inference from paths
- ✅ Project path resolution
- ✅ Deprecated function wrappers (backward compatibility)
- ✅ Configuration loading for repository root detection

### Tracking Tests

- ✅ MLflow queries
- ✅ Sweep tracker hash and search

## What Is Not Tested

- ❌ Large-scale infrastructure operations (only small-scale tests for CI speed)
- ❌ Distributed infrastructure (not supported in current implementation)

## Related Test Modules

- **Upstream dependencies** (test modules this depends on):
  - [`../fixtures/README.md`](../fixtures/README.md) - Shared fixtures used by these tests

- **Related test modules** (similar functionality):
  - [`../config/README.md`](../config/README.md) - Config tests (config loading, project path resolution)
  - [`../tracking/README.md`](../tracking/README.md) - Tracking tests (MLflow tracking)
  - [`../hpo/README.md`](../hpo/README.md) - HPO tests use infrastructure components

- **Downstream consumers** (test modules that use this):
  - [`../hpo/README.md`](../hpo/README.md) - HPO tests use infrastructure components
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests use infrastructure components


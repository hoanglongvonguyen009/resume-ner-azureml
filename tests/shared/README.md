# Shared Tests

Shared test utilities and validation helpers used across test modules.

## TL;DR / Quick Start

This module provides shared utility functions and unit tests for common functionality. Use validation helpers to check HPO studies and notebook indentation.

```bash
# Run all shared tests
uvx pytest tests/shared/ -v

# Run specific test file
uvx pytest tests/shared/unit/test_drive_backup.py -v
uvx pytest tests/shared/unit/test_platform_detection.py -v
```

## Overview

The `shared/` module provides:

- **Validation utilities**: Functions to validate HPO studies dictionary structure and notebook indentation
- **Unit tests**: Tests for shared infrastructure components (e.g., Google Drive backup)

These utilities help prevent common bugs (like the HPO studies indentation bug) and provide reusable validation logic across test modules.

## Test Structure

- `validate_hpo_studies.py`: Validation utilities for HPO studies dictionary
- `unit/test_drive_backup.py`: Unit tests for Google Drive backup functionality
- `unit/test_platform_detection.py`: Unit tests for platform detection utilities (including `is_drive_path()`)

## Running Tests

### Basic Execution

```bash
# Run all shared tests
uvx pytest tests/shared/ -v

# Run unit tests
uvx pytest tests/shared/unit/ -v

# Run specific test file
uvx pytest tests/shared/unit/test_drive_backup.py -v
uvx pytest tests/shared/unit/test_platform_detection.py -v
```

## Test Fixtures and Helpers

### Available Utilities

#### HPO Studies Validation

- `validate_hpo_studies_dict(hpo_studies, backbone_values, strict=True)`: Validates that hpo_studies dictionary contains all expected backbones. Returns `(is_valid, error_message)` tuple. Helps prevent the indentation bug where only the last backbone's study was stored.
- `check_notebook_indentation(notebook_path)`: Checks notebook for correct indentation of `hpo_studies[backbone] = study` assignment. Returns `(is_correct, error_message)` tuple.

### Usage Examples

```python
# Using HPO studies validation
from tests.shared.validate_hpo_studies import validate_hpo_studies_dict

hpo_studies = {
    "distilbert": study1,
    "distilroberta": study2,
}
backbone_values = ["distilbert", "distilroberta"]

is_valid, error = validate_hpo_studies_dict(hpo_studies, backbone_values)
assert is_valid, error

# Using notebook indentation check
from tests.shared.validate_hpo_studies import check_notebook_indentation

notebook_path = Path("notebooks/01_orchestrate_training_colab.ipynb")
is_correct, error = check_notebook_indentation(notebook_path)
assert is_correct, error
```

## What Is Tested

- ✅ Google Drive backup store functionality (backup, restore, ensure_local)
- ✅ Backup result string representation
- ✅ Path mapping and validation
- ✅ Colab-specific mounting functions
- ✅ Platform detection utilities (`detect_platform()`, `resolve_platform_checkpoint_path()`, `is_drive_path()`)
- ✅ HPO studies dictionary validation (preventing indentation bugs)
- ✅ Notebook indentation validation

## What Is Not Tested

- ❌ Actual Google Drive API calls (mocked in tests)
- ❌ Colab environment detection (requires Colab runtime)

## Related Test Modules

- **Upstream dependencies** (test modules this depends on):
  - [`../fixtures/README.md`](../fixtures/README.md) - Shared fixtures used by these tests

- **Downstream consumers** (test modules that use these utilities):
  - [`../hpo/README.md`](../hpo/README.md) - HPO tests use HPO studies validation
  - [`../scripts/README.md`](../scripts/README.md) - Test scripts use notebook validation


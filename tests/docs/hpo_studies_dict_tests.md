# HPO Studies Dictionary Storage Tests

## Overview

These tests prevent the indentation bug where only the last backbone's study was stored in the `hpo_studies` dictionary. The bug occurred when `hpo_studies[backbone] = study` was placed outside the `for backbone in backbone_values:` loop (0 spaces indentation instead of 4).

## Test Files

### 1. `tests/selection/unit/test_study_summary.py`
Unit tests for `print_study_summaries()` function:
- Tests that multiple backbones are processed correctly
- Tests loading missing backbones from disk
- Tests that already printed backbones are not duplicated
- Tests formatting functions

### 2. `tests/hpo/integration/test_hpo_studies_dict_storage.py`
Integration tests for notebook loop pattern:
- Tests that the correct loop pattern stores all backbone studies
- Tests validation function detects missing backbones

### 3. `tests/shared/validate_hpo_studies.py`
Shared validation utilities:
- `validate_hpo_studies_dict()`: Validates hpo_studies dict contains all expected backbones
- `check_notebook_indentation()`: Checks notebook for correct indentation

### 4. `tests/scripts/validate_notebook_hpo_studies.py`
Standalone script to validate notebook indentation:
```bash
python tests/scripts/validate_notebook_hpo_studies.py
```

## Usage

### Run Tests
```bash
# Run all hpo_studies tests
pytest tests/selection/unit/test_study_summary.py tests/hpo/integration/test_hpo_studies_dict_storage.py -v

# Run validation script
python tests/scripts/validate_notebook_hpo_studies.py
```

### Use Validation in Code
```python
from tests.shared.validate_hpo_studies import validate_hpo_studies_dict

hpo_studies = {...}
backbone_values = ["distilbert", "distilroberta"]

is_valid, error = validate_hpo_studies_dict(hpo_studies, backbone_values)
if not is_valid:
    raise ValueError(f"hpo_studies validation failed: {error}")
```

## Correct Pattern

The correct notebook pattern (assignment inside loop):
```python
hpo_studies = {}
for backbone in backbone_values:
    study = run_local_hpo_sweep(...)
    hpo_studies[backbone] = study  # 4 spaces indentation - INSIDE loop
```

## Bug Pattern (Detected by Tests)

The bug pattern (assignment outside loop):
```python
hpo_studies = {}
for backbone in backbone_values:
    study = run_local_hpo_sweep(...)
hpo_studies[backbone] = study  # 0 spaces indentation - OUTSIDE loop (BUG!)
```

This results in only the last backbone's study being stored.


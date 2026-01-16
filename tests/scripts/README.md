# Test Scripts

Test scripts and manual verification tools for validating notebook correctness and test infrastructure.

## TL;DR / Quick Start

This module contains standalone scripts for manual verification and validation of notebooks and test infrastructure. These scripts can be run independently to verify specific functionality.

```bash
# Validate notebook HPO studies dictionary storage
python tests/scripts/validate_notebook_hpo_studies.py

# With custom notebook path
python tests/scripts/validate_notebook_hpo_studies.py --notebook notebooks/01_orchestrate_training_colab.ipynb
```

## Overview

The `scripts/` module provides standalone scripts for:

- **Notebook validation**: Validate notebook correctness (e.g., HPO studies dictionary storage)
- **Manual verification**: Tools for manual verification of fixes and functionality

These scripts are designed to be run independently of the test suite and can be used for manual verification or CI/CD pipelines.

## Script Structure

- `validate_notebook_hpo_studies.py`: Validates notebook HPO studies dictionary storage to prevent indentation bugs

## Available Scripts

### validate_notebook_hpo_studies.py

Validates that notebooks correctly store all backbone studies in the `hpo_studies` dictionary, preventing the indentation bug where only the last backbone's study was stored.

**Usage**:

```bash
# Validate default notebook
python tests/scripts/validate_notebook_hpo_studies.py

# Validate specific notebook
python tests/scripts/validate_notebook_hpo_studies.py --notebook notebooks/01_orchestrate_training_colab.ipynb
```

**What it checks**:
- Correct indentation of `hpo_studies[backbone] = study` assignment
- Assignment is inside the loop (not outside)
- All backbones are stored in the dictionary

**Dependencies**:
- Uses `tests.shared.validate_hpo_studies.check_notebook_indentation()`

## Other Script Locations

Additional test scripts are located in module-specific directories:

- **`tests/tracking/scripts/`**: Azure ML artifact upload verification scripts
  - `verify_artifact_upload_fix.py`: Quick verification of artifact upload fixes
  - `test_artifact_upload_manual.py`: Manual test script for real Azure ML environments

- **`tests/evaluation/selection/scripts/`**: Selection-specific scripts
  - `test_checkpoint_resolution_manual.py`: Manual checkpoint resolution testing

- **`tests/training/hpo/scripts/`**: HPO-specific scripts
  - `verify_hash_consistency.py`: Hash consistency verification

See respective module READMEs for documentation on these scripts.

## What Is Tested

- ✅ Notebook HPO studies dictionary storage validation
- ✅ Indentation bug prevention

## Related Test Modules

- **Upstream dependencies** (test modules this depends on):
  - [`../shared/README.md`](../shared/README.md) - Validation utilities used by these scripts

- **Related test modules** (similar functionality):
  - [`../hpo/README.md`](../hpo/README.md) - HPO tests (validates HPO studies)
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests (validates notebook workflows)


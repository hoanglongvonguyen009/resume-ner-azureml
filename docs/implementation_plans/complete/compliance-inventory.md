# Code Quality Compliance Inventory

**Generated**: 2025-01-27
**Scope**: All Python files in `src/`

## Summary

- **Total Python files**: 280
- **Entry-point scripts**: 6
- **Workflow files**: 4
- **CLI files**: 5

## File Categories

### Entry-Point Scripts
Files with `if __name__ == "__main__"`:
- `src/benchmarking/cli.py`
- `src/deployment/api/cli/run_api.py`
- `src/deployment/api/tools/model_diagnostics.py`
- `src/deployment/conversion/execution.py`
- `src/evaluation/benchmarking/cli.py`
- `src/training/cli/train.py`

### Workflow Files
Files in `**/workflows/` directories:
- `src/evaluation/selection/workflows/__init__.py`
- `src/evaluation/selection/workflows/benchmarking_workflow.py`
- `src/evaluation/selection/workflows/selection_workflow.py`
- `src/evaluation/selection/workflows/utils.py`

### CLI Files
Files with "cli" in name:
- `src/benchmarking/cli.py`
- `src/common/shared/cli_utils.py`
- `src/deployment/conversion/cli.py`
- `src/evaluation/benchmarking/cli.py`
- `src/training/cli/cli.py`

### Module Structure

#### `src/api/`
**Status**: Module does not exist. API code is in `src/deployment/api/`.

#### `src/benchmarking/`
- Entry-point: `cli.py`
- Total files: 1

#### `src/common/`
- Utilities: `shared/` subdirectory
- Constants: `constants/` subdirectory
- Total files: 15

#### `src/conversion/`
**Status**: Module does not exist. Conversion code is in `src/deployment/conversion/`.

#### `src/core/`
- Core logic modules
- Total files: 4

#### `src/data/`
- Data loaders and processing
- Total files: 5

#### `src/deployment/`
- API: `api/` subdirectory (23 files)
- Conversion: `conversion/` subdirectory (7 files)
- Total files: 30

#### `src/evaluation/`
- Benchmarking: `benchmarking/` subdirectory
- Selection: `selection/` subdirectory with workflows
- Total files: 30

#### `src/infrastructure/`
- Config, paths, tracking, naming, platform adapters
- Total files: 60

#### `src/orchestration/`
- Jobs: HPO, benchmarking, conversion, tracking
- Total files: 50

#### `src/selection/`
- Selection logic
- Total files: 4

#### `src/testing/`
- Test utilities, fixtures, validators
- Total files: 18

#### `src/training/`
- Core training, HPO, execution, CLI
- Total files: 40

## Notes

- `src/api/` does not exist - API code is in `src/deployment/api/`
- `src/conversion/` does not exist - Conversion code is in `src/deployment/conversion/`
- Most entry-points are CLI scripts
- Workflow files are primarily in `src/evaluation/selection/workflows/`


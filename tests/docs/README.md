# Test Documentation

Test coverage analysis and documentation for YAML configs and test limitations.

## TL;DR / Quick Start

This module contains coverage analysis documents that track test coverage for YAML configuration files and document test limitations. These documents help identify gaps in test coverage and guide test development.

```bash
# View coverage analysis
cat tests/docs/coverage_analysis.md

# View coverage status
cat tests/docs/coverage_analysis_status.md
```

## Overview

The `docs/` module provides coverage analysis and documentation for:

- **YAML config coverage**: Analysis of test coverage for various YAML configuration files
- **Test limitations**: Documentation of known test limitations and gaps
- **Coverage status**: Status tracking of coverage improvements

These documents help identify gaps in test coverage, track coverage improvements, and guide test development priorities.

## Documentation Structure

### Coverage Analysis Documents

- `coverage_analysis.md`: Main coverage analysis for final_training.yaml and train.yaml
- `coverage_analysis_status.md`: Status tracking comparing missing coverage with actual coverage
- `hpo_studies_dict_tests.md`: HPO studies dictionary test coverage

### YAML Config Coverage Analysis

- `benchmark_yaml_coverage_analysis.md`: Benchmark YAML config coverage
- `data_yaml_coverage_analysis.md`: Data YAML config coverage
- `experiment_yaml_coverage_analysis.md`: Experiment YAML config coverage
- `model_yaml_coverage_analysis.md`: Model YAML config coverage
- `mlflow_yaml_coverage_analysis.md`: MLflow YAML config coverage
- `naming_coverage_analysis.md`: Naming config coverage
- `naming_yaml_explicit_coverage_summary.md`: Naming YAML explicit coverage summary
- `paths_yaml_coverage_analysis.md`: Paths YAML config coverage
- `smoke_yaml_coverage_analysis.md`: Smoke YAML config coverage

### Limitations Documentation

- `mlflow_yaml_limitations.md`: MLflow YAML config limitations
- `tags_yaml_limitations.md`: Tags YAML config limitations

## Coverage Analysis Format

Coverage analysis documents typically include:

- **Covered Options**: Table of tested options with test file and test name
- **Missing Coverage**: Table of untested options with priority and notes
- **Status Tracking**: Comparison of missing items with actual coverage

## Usage

### Viewing Coverage Analysis

```bash
# View main coverage analysis
cat tests/docs/coverage_analysis.md

# View specific YAML config coverage
cat tests/docs/hpo_yaml_coverage_analysis.md
cat tests/docs/paths_yaml_coverage_analysis.md

# View limitations
cat tests/docs/mlflow_yaml_limitations.md
```

### Updating Coverage Analysis

When adding new tests:

1. Update the relevant coverage analysis document
2. Mark newly covered options as ✅
3. Update `coverage_analysis_status.md` if applicable
4. Remove items from "Missing Coverage" section when covered

## What Is Documented

- ✅ YAML config option coverage (what is tested)
- ✅ Missing test coverage (what is not tested)
- ✅ Test limitations and gaps
- ✅ Coverage improvement status

## Related Test Modules

- **Related test modules** (these documents analyze):
  - [`../hpo/README.md`](../hpo/README.md) - HPO tests coverage
  - [`../final_training/README.md`](../final_training/README.md) - Final training tests coverage
  - [`../config/README.md`](../config/README.md) - Config tests coverage
  - [`../tracking/README.md`](../tracking/README.md) - Tracking tests coverage


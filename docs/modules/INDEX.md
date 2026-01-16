# Module Documentation Index

This index provides an overview of all documented modules in the `resume-ner-azureml` project, organized by domain.

## Core Modules

### [`src/core/`](../../src/core/README.md)
Core utilities for token validation, normalization, and placeholder handling.

### [`src/common/`](../../src/common/README.md)
Shared, domain-agnostic utilities including logging, hashing, dictionary manipulation, platform detection, and constants.

## Data Modules

### [`src/data/`](../../src/data/README.md)
Data loading and processing utilities for datasets and test texts.

## Training Modules

### [`src/training/`](../../src/training/README.md)
Model training, hyperparameter optimization, and execution infrastructure.

- [`training/core/`](../../src/training/core/README.md) - Core training components (trainer, evaluator, metrics, model, CV utilities)
- [`training/hpo/`](../../src/training/hpo/README.md) - Hyperparameter optimization workflows
- [`training/execution/`](../../src/training/execution/README.md) - Training execution infrastructure (MLflow setup, distributed training, command building)

## Infrastructure Modules

### [`src/infrastructure/`](../../src/infrastructure/README.md)
Infrastructure layer for configuration, paths, tracking, naming, and platform abstraction.

- [`infrastructure/config/`](../../src/infrastructure/config/README.md) - Configuration loading, validation, and merging
- [`infrastructure/paths/`](../../src/infrastructure/paths/README.md) - Path resolution and management
- [`infrastructure/tracking/`](../../src/infrastructure/tracking/README.md) - MLflow tracking integration
- [`infrastructure/naming/`](../../src/infrastructure/naming/README.md) - Naming conventions and policies
- [`infrastructure/platform/`](../../src/infrastructure/platform/README.md) - Platform adapters for abstraction (Local, AzureML)

## Evaluation Modules

### [`src/evaluation/`](../../src/evaluation/README.md)
Model evaluation, selection, and benchmarking.

- [`evaluation/selection/`](../../src/evaluation/selection/README.md) - Model selection logic and best configuration extraction
- [`evaluation/benchmarking/`](../../src/evaluation/benchmarking/README.md) - Benchmarking utilities (note: `src/benchmarking/` also exists)

## Orchestration Modules

### [`src/orchestration/`](../../src/orchestration/README.md)
Job orchestration and workflow management (deprecated facade - use `orchestration/jobs`).

- [`orchestration/jobs/`](../../src/orchestration/jobs/README.md) - Job definitions and execution (HPO, training, conversion)

## Deployment Modules

### [`src/deployment/`](../../src/deployment/README.md)
Model deployment, ONNX conversion, and FastAPI API serving.

- [`deployment/api/`](../../src/deployment/api/README.md) - FastAPI service for NER predictions
- [`deployment/conversion/`](../../src/deployment/conversion/README.md) - Model conversion workflows (PyTorch to ONNX)

## Testing Modules

### [`src/testing/`](../../src/testing/README.md)
Testing infrastructure and utilities for HPO pipeline testing, validation, and integration tests.

## Additional Modules

### [`src/benchmarking/`](../../src/benchmarking/README.md)
Benchmarking utilities (separate from `evaluation/benchmarking`).

## Module Dependency Overview

```
core
  └─> common
data
  └─> common
training
  ├─> core
  ├─> data
  ├─> infrastructure
  └─> common
infrastructure
  └─> common
evaluation
  ├─> training
  ├─> infrastructure
  └─> common
orchestration
  ├─> training
  ├─> infrastructure
  └─> common
deployment
  ├─> training
  ├─> infrastructure
  └─> common
testing
  ├─> training
  ├─> data
  ├─> infrastructure
  └─> common
```

## Quick Navigation by Use Case

### Getting Started
- **Core utilities**: [`core/`](../../src/core/README.md), [`common/`](../../src/common/README.md)
- **Data loading**: [`data/`](../../src/data/README.md)
- **Configuration**: [`infrastructure/config/`](../../src/infrastructure/config/README.md)

### Training Workflows
- **Training**: [`training/`](../../src/training/README.md)
- **HPO**: [`training/hpo/`](../../src/training/hpo/README.md)
- **Execution**: [`training/execution/`](../../src/training/execution/README.md)

### Model Evaluation
- **Evaluation**: [`evaluation/`](../../src/evaluation/README.md)
- **Selection**: [`evaluation/selection/`](../../src/evaluation/selection/README.md)
- **Benchmarking**: [`evaluation/benchmarking/`](../../src/evaluation/benchmarking/README.md)

### Deployment
- **Deployment**: [`deployment/`](../../src/deployment/README.md)
- **API**: [`deployment/api/`](../../src/deployment/api/README.md)
- **Conversion**: [`deployment/conversion/`](../../src/deployment/conversion/README.md)

### Infrastructure
- **Paths**: [`infrastructure/paths/`](../../src/infrastructure/paths/README.md)
- **Tracking**: [`infrastructure/tracking/`](../../src/infrastructure/tracking/README.md)
- **Naming**: [`infrastructure/naming/`](../../src/infrastructure/naming/README.md)
- **Platform**: [`infrastructure/platform/`](../../src/infrastructure/platform/README.md)

### Testing
- **Testing**: [`testing/`](../../src/testing/README.md)

## Notes

- All module READMEs follow the documentation standards defined in [`docs/TEMPLATE-documentation_standards.md`](../TEMPLATE-documentation_standards.md)
- Module documentation includes TL;DR sections, usage examples, and API references
- Cross-references between modules are provided in each README's "Related Modules" section
- Some modules are deprecated (e.g., `orchestration` top-level is a facade) - see individual READMEs for details


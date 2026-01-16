# Resume NER with Azure ML

Named Entity Recognition (NER) model training, evaluation, and deployment pipeline using Azure ML.

## Overview

This project provides a complete ML pipeline for training, evaluating, and deploying NER models:

- **Training**: Hyperparameter optimization (HPO) and model training workflows
- **Evaluation**: Model selection, benchmarking, and performance evaluation
- **Deployment**: Model conversion (PyTorch to ONNX) and FastAPI API serving
- **Infrastructure**: Configuration management, MLflow tracking, and platform abstraction

## Quick Start

See individual module documentation for usage examples:

- **Training**: [`src/training/README.md`](src/training/README.md)
- **Evaluation**: [`src/evaluation/README.md`](src/evaluation/README.md)
- **Deployment**: [`src/deployment/README.md`](src/deployment/README.md)
- **Infrastructure**: [`src/infrastructure/README.md`](src/infrastructure/README.md)

## Module Documentation

Comprehensive module documentation is available in the [Module Documentation Index](docs/modules/INDEX.md).

The project is organized into the following domains:

- **Core**: Token validation, normalization, shared utilities
- **Data**: Data loading and processing
- **Training**: Model training, HPO, execution
- **Infrastructure**: Configuration, paths, tracking, naming, platform abstraction
- **Evaluation**: Model evaluation, selection, benchmarking
- **Orchestration**: Job orchestration and workflow management
- **Deployment**: Model deployment and API serving
- **Testing**: Testing infrastructure and utilities

## Project Structure

```
src/
├── core/              # Core utilities (tokens, normalization, placeholders)
├── common/            # Shared utilities (logging, hashing, constants)
├── data/              # Data loading and processing
├── training/          # Training workflows, HPO, execution
├── infrastructure/    # Configuration, paths, tracking, naming, platform
├── evaluation/        # Model evaluation, selection, benchmarking
├── orchestration/     # Job orchestration and workflows
├── deployment/        # Model deployment and API serving
└── testing/           # Testing infrastructure

docs/
├── modules/           # Module documentation index
└── implementation_plans/  # Implementation plans

tests/                 # Test suites
config/                # Configuration files
```

## Documentation Standards

Module documentation follows the standards defined in [`docs/TEMPLATE-documentation_standards.md`](docs/TEMPLATE-documentation_standards.md).

Each module includes:
- TL;DR / Quick Start
- Overview and key concepts
- Usage examples
- API reference
- Integration points
- Related modules

## Getting Help

- **Module documentation**: See [Module Documentation Index](docs/modules/INDEX.md)
- **Implementation plans**: See [`docs/implementation_plans/`](docs/implementation_plans/)
- **Documentation standards**: See [`docs/TEMPLATE-documentation_standards.md`](docs/TEMPLATE-documentation_standards.md)

# Deployment Conversion

Model conversion utilities for converting PyTorch models to ONNX format for production deployment.

## TL;DR / Quick Start

Convert trained PyTorch models to ONNX format for efficient production inference.

```python
from src.deployment.conversion.orchestration import execute_conversion

# Convert model to ONNX
onnx_path = execute_conversion(
    root_dir=Path("."),
    config_dir=Path("config/"),
    parent_training_output_dir=Path("outputs/final_training/model"),
    parent_spec_fp="abc123",
    parent_exec_fp="def456",
    experiment_config=experiment_config,
    conversion_experiment_name="conversion",
    platform="local"
)
```

## Overview

The `conversion` module provides model conversion capabilities:

- **ONNX export**: Convert PyTorch models to ONNX format
- **Conversion orchestration**: High-level workflow for model conversion
- **AzureML integration**: Create AzureML conversion jobs (optional)
- **Smoke testing**: Validate converted ONNX models
- **MLflow tracking**: Track conversion runs in MLflow

Conversion enables efficient production inference by converting PyTorch models to ONNX format, which provides better performance and cross-platform compatibility.

## Module Structure

- `orchestration.py`: High-level conversion orchestration
- `export.py`: ONNX export functionality
- `execution.py`: Conversion execution and subprocess handling
- `testing.py`: Smoke testing for converted models
- `azureml.py`: AzureML conversion job creation (optional)
- `cli.py`: CLI for conversion execution

## Usage

### Basic Example: Convert Model

```python
from pathlib import Path
from src.deployment.conversion.orchestration import execute_conversion

# Convert model to ONNX
onnx_path = execute_conversion(
    root_dir=Path("."),
    config_dir=Path("config/"),
    parent_training_output_dir=Path("outputs/final_training/model"),
    parent_spec_fp="abc123",
    parent_exec_fp="def456",
    experiment_config=experiment_config,
    conversion_experiment_name="conversion",
    platform="local"
)

print(f"ONNX model saved to: {onnx_path}")
```

### Basic Example: CLI Conversion

```bash
# Convert model via CLI
python -m src.deployment.conversion.cli \
  --config-dir config/ \
  --parent-training-dir outputs/final_training/model \
  --parent-spec-fp abc123 \
  --parent-exec-fp def456
```

### Basic Example: AzureML Conversion Job

```python
from src.deployment.conversion.azureml import create_conversion_job

# Create AzureML conversion job
conversion_job = create_conversion_job(
    script_path=Path("src/deployment/conversion/cli.py"),
    training_job=completed_training_job,
    environment=environment,
    compute_cluster="cpu-cluster"
)
```

## API Reference

### Orchestration

- `execute_conversion(...)`: Execute model conversion to ONNX
  - Loads conversion config
  - Builds output directories
  - Creates MLflow runs
  - Executes conversion subprocess
  - Returns ONNX model directory path

### Export

- `export_to_onnx(...)`: Export PyTorch model to ONNX format
- See `export.py` for detailed export functions

### AzureML (Optional)

- `create_conversion_job(...)`: Create AzureML conversion job
- `get_checkpoint_output_from_training_job(...)`: Extract checkpoint from training job
- `validate_conversion_job(...)`: Validate conversion job completion

### Testing

- `smoke_test_onnx_model(...)`: Smoke test converted ONNX model

For detailed signatures, see source code.

## Integration Points

### Used By

- **Orchestration**: Uses conversion for deployment workflows
- **Production**: Converted models used by API for inference

### Depends On

- `training/`: Training checkpoints for conversion
- `infrastructure/`: Configuration, paths, naming, MLflow tracking
- `common/`: Platform detection, logging

## Conversion Workflow

1. **Load conversion config**: Load `conversion.yaml` configuration
2. **Build output directory**: Create output directory for ONNX model
3. **Create MLflow run**: Track conversion in MLflow
4. **Execute conversion**: Run conversion subprocess
5. **Validate output**: Smoke test converted model
6. **Return path**: Return path to ONNX model directory

## Testing

```bash
uvx pytest tests/deployment/conversion/
```

## Related Modules

- [`../README.md`](../README.md) - Main deployment module
- [`../api/README.md`](../api/README.md) - API uses converted ONNX models
- [`../../training/README.md`](../../training/README.md) - Training produces checkpoints
- [`../../infrastructure/README.md`](../../infrastructure/README.md) - Infrastructure layer


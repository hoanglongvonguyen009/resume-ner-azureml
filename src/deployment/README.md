# Deployment

Model deployment module for converting models to ONNX format and serving predictions via FastAPI.

## TL;DR / Quick Start

Convert models to ONNX and serve predictions via FastAPI API.

```python
from src.deployment.conversion.orchestration import run_conversion_workflow
from src.deployment.api import app

# Convert model to ONNX
onnx_path = run_conversion_workflow(
    root_dir=Path("."),
    config_dir=Path("config/"),
    parent_training_output_dir=Path("outputs/final_training/model"),
    parent_spec_fp="abc123",
    parent_exec_fp="def456",
    experiment_config=experiment_config,
    conversion_experiment_name="conversion",
    platform="local"
)

# Serve API
# uvicorn deployment.api:app --host 0.0.0.0 --port 8000
```

## Overview

The `deployment` module provides model deployment capabilities:

- **Model conversion**: Convert PyTorch models to ONNX format for production deployment
- **API serving**: FastAPI service for serving NER predictions
- **Inference engine**: ONNX model loading and inference execution
- **Conversion orchestration**: High-level workflow for model conversion

This module enables production deployment of trained models by converting them to ONNX format and serving them via a REST API.

## Key Concepts

- **ONNX conversion**: Convert PyTorch models to ONNX for efficient inference
- **FastAPI service**: REST API for serving predictions
- **Inference engine**: ONNX Runtime-based inference execution
- **Model loading**: Lazy loading of ONNX models and tokenizers

## Module Structure
<!-- AUTO-GENERATED:START -->
### Auto-generated overview for `deployment`

This section is generated from repository structure. Do not edit manually.

#### Files
- `src/deployment/README.md`
- `src/deployment/__init__.py`
- `src/deployment/api/README.md`
- `src/deployment/api/__init__.py`
- `src/deployment/api/app.py`
- `src/deployment/api/cli/__init__.py`
- `src/deployment/api/cli/run_api.py`
- `src/deployment/api/config.py`
- `src/deployment/api/entities.py`
- `src/deployment/api/exception_handlers.py`
- `src/deployment/api/exceptions.py`
- `src/deployment/api/extractors.py`
- `src/deployment/api/inference.py`
- `src/deployment/api/inference/__init__.py`
- `src/deployment/api/inference/decoder.py`
- `src/deployment/api/inference/engine.py`
- `src/deployment/api/middleware.py`
- `src/deployment/api/model_loader.py`
- `src/deployment/api/models.py`
- `src/deployment/api/response_converters.py`
- `src/deployment/api/routes/__init__.py`
- `src/deployment/api/routes/health.py`
- `src/deployment/api/routes/predictions.py`
- `src/deployment/api/startup.py`
- `src/deployment/api/tools/README.md`
- `src/deployment/api/tools/__init__.py`
- `src/deployment/api/tools/model_diagnostics.py`
- `src/deployment/api/tools/model_finder.py`
- `src/deployment/api/tools/notebook_config.py`
- `src/deployment/api/tools/notebook_helpers.py`
- `src/deployment/api/tools/server_launcher.py`
- `src/deployment/conversion/README.md`
- `src/deployment/conversion/__init__.py`
- `src/deployment/conversion/azureml.py`
- `src/deployment/conversion/azureml/__init__.py`
- `src/deployment/conversion/azureml/jobs.py`
- `src/deployment/conversion/cli.py`
- `src/deployment/conversion/execution.py`
- `src/deployment/conversion/export.py`
- `src/deployment/conversion/orchestration.py`
- `src/deployment/conversion/testing.py`
<!-- AUTO-GENERATED:END -->

This module is organized into the following submodules:

- `conversion/`: Model conversion to ONNX
  - Orchestration, export, execution, AzureML job creation
- `api/`: FastAPI service for predictions
  - Application, routes, inference engine, model loading

See individual submodule READMEs for detailed documentation:
- [`conversion/README.md`](conversion/README.md) - Model conversion
- [`api/README.md`](api/README.md) - FastAPI deployment

## Usage

### Basic Workflow: Convert Model

```python
from pathlib import Path
from src.deployment.conversion.orchestration import run_conversion_workflow

# Convert model to ONNX
onnx_path = run_conversion_workflow(
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

### Basic Workflow: Serve API

```bash
# Start API server
uvicorn src.deployment.api:app --host 0.0.0.0 --port 8000

# Or use Python module
python -m src.deployment.api.cli --host 0.0.0.0 --port 8000
```

### Basic Workflow: Make Predictions

```python
import requests

# Single prediction
response = requests.post(
    "http://localhost:8000/predict",
    json={"text": "John Smith worked at Microsoft."}
)
entities = response.json()["entities"]

# Batch prediction
response = requests.post(
    "http://localhost:8000/predict/batch",
    json={"texts": ["Text 1", "Text 2"]}
)
```

## API Reference

### Conversion

- `run_conversion_workflow(...)`: Execute model conversion to ONNX
- `create_conversion_job(...)`: Create AzureML conversion job (optional)
- `validate_conversion_job(...)`: Validate conversion job completion (optional)

### API

- `app`: FastAPI application instance
- See `api/` submodule for detailed API documentation

For detailed signatures, see source code or submodule documentation.

## Integration Points

### Dependencies

- `training/`: Training checkpoints for conversion
- `infrastructure/`: Configuration, paths, naming, MLflow tracking
- `common/`: Tokenization utilities, platform detection

### Used By

- **Orchestration**: Uses conversion for model deployment workflows
- **Production**: API serves predictions in production

## Examples

### Example 1: Convert and Serve

```python
from pathlib import Path
from src.deployment.conversion.orchestration import run_conversion_workflow

# 1. Convert model
onnx_path = run_conversion_workflow(...)

# 2. Start API (via CLI or uvicorn)
# uvicorn src.deployment.api:app --host 0.0.0.0 --port 8000
```

### Example 2: API Usage

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Model info
response = requests.get("http://localhost:8000/info")
print(response.json())

# Prediction
response = requests.post(
    "http://localhost:8000/predict",
    json={"text": "John Smith worked at Microsoft."}
)
print(response.json()["entities"])
```

## Best Practices

1. **Convert before deployment**: Always convert models to ONNX for production
2. **Validate conversions**: Test converted models before deployment
3. **Monitor API**: Monitor API health and performance in production
4. **Use batch predictions**: Use batch endpoints for multiple texts

## Notes

- Conversion requires parent training checkpoint and fingerprints
- API uses ONNX Runtime for efficient inference
- Models are loaded lazily on first request
- API supports both single and batch predictions

## Testing

```bash
uvx pytest tests/deployment/
```

## Related Modules

- [`conversion/README.md`](conversion/README.md) - Model conversion
- [`api/README.md`](api/README.md) - FastAPI deployment
- [`../training/README.md`](../training/README.md) - Training produces checkpoints for conversion
- [`../infrastructure/README.md`](../infrastructure/README.md) - Infrastructure layer


# Deployment API

FastAPI service for serving NER model predictions via REST API.

## TL;DR / Quick Start

Serve NER predictions via FastAPI with ONNX model inference.

```python
from src.deployment.api import app

# Start API server
# uvicorn src.deployment.api:app --host 0.0.0.0 --port 8000

# Or use CLI
# python -m src.deployment.api.cli --host 0.0.0.0 --port 8000
```

## Overview

The `api` module provides a FastAPI service for serving NER predictions:

- **FastAPI application**: REST API with health checks, model info, and predictions
- **Inference engine**: ONNX model loading and inference execution
- **Model loading**: Lazy loading of ONNX models and tokenizers
- **Request handling**: Single and batch prediction endpoints
- **Error handling**: Comprehensive exception handling and error responses

The API serves ONNX models converted from PyTorch checkpoints, providing efficient inference for production use.

## Module Structure

- `app.py`: FastAPI application and route registration
- `config.py`: API configuration (model paths, CORS, etc.)
- `inference/`: Inference engine
  - `engine.py`: ONNX model loading and inference
  - `decoder.py`: Token-level prediction decoding
- `routes/`: API routes
  - `health.py`: Health check and model info endpoints
  - `predictions.py`: Prediction endpoints
- `models.py`: Pydantic models for requests/responses
- `startup.py`: Startup and shutdown event handlers
- `middleware.py`: API middleware
- `exception_handlers.py`: Exception handling
- `model_loader.py`: Model loading utilities
- `cli/`: CLI for starting the API server

## Usage

### Basic Example: Start API Server

```bash
# Using uvicorn
uvicorn src.deployment.api:app --host 0.0.0.0 --port 8000

# Using CLI
python -m src.deployment.api.cli --host 0.0.0.0 --port 8000

# With model path
python -m src.deployment.api.cli \
  --model-path outputs/conversion/model.onnx \
  --checkpoint-dir outputs/final_training/model
```

### Basic Example: Health Check

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())
# {"status": "healthy", "model_loaded": true}
```

### Basic Example: Model Info

```python
# Model information
response = requests.get("http://localhost:8000/info")
print(response.json())
# {"model_path": "...", "labels": [...], "max_length": 512}
```

### Basic Example: Single Prediction

```python
# Single prediction
response = requests.post(
    "http://localhost:8000/predict",
    json={"text": "John Smith worked at Microsoft."}
)
entities = response.json()["entities"]
# [{"text": "John Smith", "label": "PERSON", "start": 0, "end": 10}, ...]
```

### Basic Example: Batch Prediction

```python
# Batch prediction
response = requests.post(
    "http://localhost:8000/predict/batch",
    json={"texts": ["Text 1", "Text 2", "Text 3"]}
)
results = response.json()["results"]
# [{"entities": [...]}, {"entities": [...]}, {"entities": [...]}]
```

## API Endpoints

### Health and Info

- `GET /health`: Health check endpoint
- `GET /info`: Model information endpoint

### Predictions

- `POST /predict`: Single text prediction
- `POST /predict/batch`: Batch text prediction
- `POST /predict/file`: File-based prediction
- `POST /predict/file/batch`: Batch file-based prediction
- `POST /predict/debug`: Debug prediction with detailed output

## API Reference

### Application

- `app`: FastAPI application instance

### Inference Engine

- `ONNXModelLoader`: ONNX model loader class
  - `load()`: Load ONNX model and tokenizer
  - `predict(texts: List[str]) -> List[Dict]`: Run inference on texts
- `InferenceEngine`: Inference engine wrapper

### Configuration

- `APIConfig`: API configuration class
  - `MODEL_PATH`: Path to ONNX model
  - `CHECKPOINT_DIR`: Path to checkpoint directory
  - `MAX_SEQUENCE_LENGTH`: Maximum sequence length
  - `ONNX_PROVIDERS`: ONNX Runtime providers

For detailed signatures, see source code.

## Integration Points

### Used By

- **Production deployment**: API serves predictions in production
- **Testing**: API endpoints used for integration testing

### Depends On

- `fastapi`: FastAPI framework
- `onnxruntime`: ONNX Runtime for inference
- `transformers`: Tokenizer loading
- `common/`: Tokenization utilities

## Configuration

API configuration can be set via:
- Environment variables
- Configuration files
- Command-line arguments

See `config.py` for configuration options.

## Testing

```bash
uvx pytest tests/deployment/api/
```

## Related Modules

- [`../README.md`](../README.md) - Main deployment module
- [`../conversion/README.md`](../conversion/README.md) - Model conversion produces ONNX models
- [`../../common/README.md`](../../common/README.md) - Tokenization utilities


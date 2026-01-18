# API Tests

API and inference tests covering FastAPI server, inference engine, extractors, and performance validation.

## TL;DR / Quick Start

API tests validate FastAPI server functionality, inference engine, entity extractors, and performance. Tests cover both unit-level component validation and integration-level server testing.

```bash
# Run all API tests
uvx pytest tests/unit/api/ tests/integration/api/ -v

# Run specific category
uvx pytest tests/unit/api/ -v
uvx pytest tests/integration/api/ -v
```

## Overview

The `api/` module provides tests for API and inference functionality:

- **Unit tests** (`tests/unit/api/`): Fast, isolated tests for API components
  - Inference engine (ONNXInferenceEngine)
  - Entity extractors
  - Inference fixes
  - Inference performance

- **Integration tests** (`tests/integration/api/`): Tests with real FastAPI server
  - FastAPI local server deployment
  - API endpoints (health, info, prediction, batch, file upload)
  - Direct inference testing
  - ONNX inference
  - Inference performance
  - Tokenization speed

These tests validate FastAPI server functionality, inference engine correctness, entity extraction, performance, and error handling.

## Test Structure

API tests are organized in two locations:

- `tests/unit/api/`: Unit tests for API components
- `tests/integration/api/`: Integration tests for FastAPI server

## Test Categories

- **Unit Tests** (`tests/unit/api/`): Fast, isolated tests for API components
  - Inference engine (ONNXInferenceEngine) - model loading, tokenization, entity extraction
  - Entity extractors
  - Inference fixes
  - Inference performance and correctness

- **Integration Tests** (`tests/integration/api/`): Tests with real FastAPI server
  - FastAPI local server deployment (server lifecycle, startup, shutdown)
  - Health & info endpoints
  - Single text prediction
  - Batch text prediction
  - File upload prediction
  - Batch file upload
  - Debug endpoint
  - Error handling & edge cases
  - Performance validation
  - Stability & consistency
  - Direct inference testing
  - ONNX inference
  - Tokenization speed

## Running Tests

### Basic Execution

```bash
# Run all API tests
uvx pytest tests/unit/api/ tests/integration/api/ -v

# Run with coverage
uvx pytest tests/unit/api/ tests/integration/api/ --cov=src.deployment.api --cov-report=html

# Run specific category
uvx pytest tests/unit/api/ -v
uvx pytest tests/integration/api/ -v

# Run specific test file
uvx pytest tests/unit/api/test_inference.py -v
uvx pytest tests/integration/api/test_api_local_server.py -v
```

### Advanced Execution

```bash
# Run specific test
uvx pytest tests/unit/api/test_inference.py::TestONNXInferenceEngine -v

# Run performance tests
uvx pytest tests/unit/api/test_inference_performance.py -v
uvx pytest tests/integration/api/test_inference_performance.py -v

# Run with markers (if defined)
uvx pytest tests/unit/api/ tests/integration/api/ -m "slow" -v
```

## Test Fixtures and Helpers

### Available Fixtures

- `test_config`: Loads test configuration (integration tests)
- `mock_onnx_path`: Creates mock ONNX file path (unit tests)
- `mock_checkpoint_dir`: Creates mock checkpoint directory (unit tests)

### Test Helpers

- `ServerManager`: Manages FastAPI server lifecycle (integration tests)
- `APIClient`: Client for API endpoint testing (integration tests)
- `load_test_config()`: Loads test configuration
- `validate_latency()`: Validates response latency

### Test Data

Tests use fixtures from `tests/test_data/`:
- `get_text_fixture()`: Get text test data
- `get_file_fixture()`: Get file test data (PDF, PNG)
- `get_batch_text_fixture()`: Get batch text test data
- `get_batch_file_fixture()`: Get batch file test data

See [`../test_data/README.md`](../test_data/README.md) for test data fixtures.

## What Is Tested

### Unit Tests

- ✅ ONNXInferenceEngine model loading
- ✅ Tokenization functionality
- ✅ Entity extraction with offset mapping
- ✅ Entity extractors
- ✅ Inference fixes
- ✅ Inference performance and correctness
- ✅ Error handling (InferenceError, ModelNotLoadedError)

### Integration Tests

- ✅ FastAPI server lifecycle (startup, shutdown, failure handling)
- ✅ Health & info endpoints
- ✅ Single text prediction endpoint
- ✅ Batch text prediction endpoint
- ✅ File upload prediction endpoint
- ✅ Batch file upload endpoint
- ✅ Debug endpoint
- ✅ Error handling & edge cases
- ✅ Performance validation
- ✅ Stability & consistency
- ✅ Direct inference testing
- ✅ ONNX inference
- ✅ Tokenization speed

## What Is Not Tested

- ❌ Production deployment scenarios (only local server tested)
- ❌ Large-scale load testing (only basic performance tests)
- ❌ Authentication/authorization (not implemented in current API)
- ❌ Rate limiting (not implemented in current API)

## Configuration

### Test Configuration

Integration tests use test configuration for:
- Model paths
- Server ports
- Timeout settings
- Performance thresholds

### Test Data

Tests use deterministic test data from `tests/test_data/`:
- Text fixtures (text_1 through text_10, edge cases)
- File fixtures (PDF and PNG versions)
- Batch fixtures (small, medium, large batches)

## Dependencies

- **FastAPI**: Required for integration tests
- **ONNX Runtime**: Required for inference engine tests
- **Transformers**: Required for tokenization tests
- **Test data**: Uses fixtures from `tests/test_data/`
- **Requests**: Required for integration API client tests

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:
1. Ensure `src/` is in Python path
2. Install required dependencies: `pip install fastapi uvicorn onnxruntime transformers requests`

### Server Startup Failures

If FastAPI server fails to start:
1. Check that model files exist
2. Verify port is not in use
3. Check test configuration

### Performance Test Failures

If performance tests fail:
1. Check performance thresholds in test configuration
2. Verify system resources (CPU, memory)
3. Check for background processes affecting performance

## Related Test Modules

- **Upstream dependencies** (test modules this depends on):
  - [`../test_data/README.md`](../test_data/README.md) - Test data fixtures used by these tests
  - [`../fixtures/README.md`](../fixtures/README.md) - Shared fixtures used by these tests

- **Related test modules** (similar functionality):
  - [`../unit/training/`](../unit/training/) - Training tests (model training, no README)
  - [`../conversion/README.md`](../conversion/README.md) - Conversion tests (ONNX conversion)


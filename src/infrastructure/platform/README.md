# Infrastructure Platform

Platform adapters for abstracting platform-specific operations (AzureML, local, Colab).

## TL;DR / Quick Start

Get platform adapters for platform-specific operations.

```python
from src.infrastructure.platform.adapters.adapters import get_platform_adapter

# Get platform adapter
adapter = get_platform_adapter(config=config)

# Use adapter for platform-specific operations
output_path = adapter.resolve_output_path("checkpoint")
adapter.log_metric("f1", 0.85)
adapter.log_param("learning_rate", 2e-5)
```

## Overview

The `platform` module provides platform abstraction:

- **Platform adapters**: Abstract platform-specific operations
- **Checkpoint resolution**: Resolve checkpoint paths across platforms
- **Logging adapters**: Abstract logging operations (MLflow, AzureML)
- **Output management**: Handle outputs across platforms
- **MLflow context**: Manage MLflow context across platforms

This module allows the codebase to work across different platforms (local, AzureML, Colab) without platform-specific code in business logic.

## Module Structure

- `adapters/`: Platform adapters
  - `adapters.py`: Main adapter interface and factory
  - `checkpoint_resolver.py`: Checkpoint path resolution
  - `logging_adapter.py`: Logging abstraction
  - `mlflow_context.py`: MLflow context management
  - `outputs.py`: Output path management
- `azureml/`: AzureML-specific implementations

## Usage

### Basic Example: Get Platform Adapter

```python
from src.infrastructure.platform.adapters.adapters import get_platform_adapter

# Get platform adapter (automatically detects platform)
adapter = get_platform_adapter(config=config)

# Use adapter for operations
output_path = adapter.resolve_output_path("checkpoint")
adapter.log_metric("f1", 0.85)
adapter.log_param("learning_rate", 2e-5)
```

### Basic Example: Checkpoint Resolution

```python
from src.infrastructure.platform.adapters.checkpoint_resolver import resolve_checkpoint_path

# Resolve checkpoint path (works across platforms)
checkpoint_path = resolve_checkpoint_path(
    local_path="outputs/checkpoint",
    azureml_path="azureml://workspace/checkpoint",
    config=config
)
```

## API Reference

### Platform Adapters

- `get_platform_adapter(config: Dict) -> PlatformAdapter`: Get platform adapter for current platform
- `PlatformAdapter`: Interface for platform-specific operations

### Checkpoint Resolution

**Note**: For checkpoint path resolution, use:
- **Low-level**: `common.shared.platform_detection.resolve_platform_checkpoint_path()` - Platform-specific path resolution
- **HPO-specific**: `training.hpo.checkpoint.storage.resolve_storage_path()` - HPO checkpoint storage paths
- **HPO setup**: `training.hpo.utils.helpers.setup_checkpoint_storage()` - Complete HPO checkpoint setup

This module provides platform adapters for abstracting platform-specific operations, but checkpoint path resolution is handled by the functions above.

For detailed signatures, see source code.

## Integration Points

### Used By

- **Training modules**: Use platform adapters for training execution
- **Orchestration modules**: Use platform adapters for job execution

### Depends On

- `common/`: Platform detection utilities

## Platform Detection

Platform adapters automatically detect the current platform:
- **Local**: Standard filesystem operations
- **AzureML**: AzureML workspace operations
- **Colab**: Google Colab-specific operations

## Testing

```bash
uvx pytest tests/infrastructure/platform/
```

## Related Modules

- [`../README.md`](../README.md) - Main infrastructure module
- [`../../common/README.md`](../../common/README.md) - Platform detection utilities


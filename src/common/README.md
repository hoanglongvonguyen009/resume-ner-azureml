# Common

Shared utilities and constants used across the codebase for logging, file operations, hashing, platform detection, MLflow setup, and orchestration constants.

## TL;DR / Quick Start

Generic, domain-agnostic utilities for common operations. Provides logging, file I/O, hashing, platform detection, MLflow setup, and shared constants.

```python
from src.common.shared.logging_utils import get_logger
from src.common.shared.hash_utils import compute_hash_16
from src.common.shared.dict_utils import deep_merge
from src.common.constants import STAGE_HPO, METRICS_FILENAME

# Get a logger
logger = get_logger(__name__)
logger.info("Processing data")

# Compute hash
hash_value = compute_hash_16("some_data")  # 16-char hex hash

# Merge dictionaries
merged = deep_merge({"a": 1, "b": {"c": 2}}, {"b": {"d": 3}})
# {'a': 1, 'b': {'c': 2, 'd': 3}}
```

## Overview

The `common` module provides generic, domain-agnostic utilities organized into two submodules:

- **`shared/`**: Reusable utility functions for:
  - Logging (standardized logger configuration)
  - File operations (verification, modification time)
  - Dictionary utilities (deep merging)
  - Hashing (SHA256, JSON hashing)
  - Platform detection (AzureML vs local)
  - MLflow setup (cross-platform configuration)
  - Tokenization utilities (ONNX input preparation)
  - YAML/JSON utilities (loading, caching)
  - CLI argument parsing helpers
- **`constants/`**: Stable orchestration identifiers (stage names, file names, default values)

These utilities are used extensively across training, evaluation, infrastructure, and orchestration modules.

## Module Structure

- `shared/`: Shared utility functions
  - `logging_utils.py`: Logger configuration
  - `hash_utils.py`: Hash computation
  - `dict_utils.py`: Dictionary operations
  - `file_utils.py`: File operations
  - `platform_detection.py`: Platform detection
  - `mlflow_setup.py`: MLflow configuration
  - `notebook_setup.py`: Notebook environment detection and path setup
  - `yaml_utils.py`: YAML loading
  - `json_cache.py`: JSON caching
  - `tokenization_utils.py`: Tokenization helpers
  - `argument_parsing.py`: CLI argument helpers
- `constants/`: Shared constants
  - `orchestration.py`: Stage names, file names, defaults

## Usage

**Note**: The examples below import directly from submodules (e.g., `src.common.shared.logging_utils`), which matches how these utilities are used throughout the codebase.

### Basic Example: Logging

```python
from src.common.shared.logging_utils import get_logger, get_script_logger

# Get a module logger
logger = get_logger(__name__)
logger.info("Processing started")
logger.error("Error occurred", exc_info=True)

# Get a script logger (for CLI scripts)
logger = get_script_logger("my_script")
```

### Basic Example: Hashing

```python
from src.common.shared.hash_utils import compute_hash_64, compute_hash_16, compute_json_hash

# Full SHA256 hash (64 chars)
full_hash = compute_hash_64("some_data")

# Truncated hash (16 chars)
short_hash = compute_hash_16("some_data")

# Hash a dictionary
config_hash = compute_json_hash({"model": "bert", "lr": 0.001})
```

### Basic Example: Dictionary Operations

```python
from src.common.shared.dict_utils import deep_merge

# Deep merge dictionaries
defaults = {
    "model": {"name": "bert", "lr": 0.001},
    "data": {"batch_size": 32}
}
overrides = {
    "model": {"lr": 0.0001},  # Override lr, keep name
    "data": {"batch_size": 64}  # Override batch_size
}
merged = deep_merge(defaults, overrides)
# {'model': {'name': 'bert', 'lr': 0.0001}, 'data': {'batch_size': 64}}
```

### Basic Example: Platform Detection

```python
from src.common.shared.platform_detection import detect_platform, resolve_platform_checkpoint_path

# Detect current platform
platform = detect_platform()  # "azureml" or "local"

# Resolve checkpoint path based on platform
checkpoint_path = resolve_platform_checkpoint_path(
    local_path="outputs/checkpoint",
    azureml_path="azureml://workspace/checkpoint"
)
```

### Basic Example: Notebook Setup

```python
from src.common.shared.notebook_setup import (
    detect_notebook_environment,
    find_repository_root,
    setup_notebook_paths,
    get_platform_vars,
    ensure_src_in_path,
    ensure_mlflow_installed,
)

# Detect notebook environment
env = detect_notebook_environment()
print(f"Platform: {env.platform}, Colab: {env.is_colab}, Kaggle: {env.is_kaggle}")

# Find repository root (with platform-specific search)
repo_root = find_repository_root()

# Setup paths and add src to Python path
paths = setup_notebook_paths(add_src_to_path=True)
print(f"Root: {paths.root_dir}, Config: {paths.config_dir}, Src: {paths.src_dir}")

# Get platform variables as dict
platform_vars = get_platform_vars()
# {'platform': 'colab', 'is_colab': True, 'is_kaggle': False, ...}

# Ensure mlflow is installed (Colab/Kaggle only)
ensure_mlflow_installed()

# Ensure src is in path (returns repo root if found)
repo_root = ensure_src_in_path()
```

### Basic Example: Constants

```python
from src.common.constants import STAGE_HPO, METRICS_FILENAME, DEFAULT_RANDOM_SEED

# Use stage constants
if stage == STAGE_HPO:
    run_hpo()

# Use file name constants
metrics_file = f"{output_dir}/{METRICS_FILENAME}"

# Use default values
set_seed(DEFAULT_RANDOM_SEED)
```

## API Reference

### Logging Utilities

- `get_logger(name: str, level: Optional[int] = None) -> logging.Logger`: Get configured logger
- `get_script_logger(script_name: str) -> logging.Logger`: Get logger for CLI scripts

### Hash Utilities

- `compute_hash_64(data: str) -> str`: Compute full SHA256 hash (64 chars)
- `compute_hash_16(data: str) -> str`: Compute truncated SHA256 hash (16 chars)
- `compute_json_hash(data: Dict[str, Any], length: int = 64) -> str`: Hash JSON-serialized dict
- `compute_selection_cache_key(...) -> str`: Compute cache key for selection logic

### Dictionary Utilities

- `deep_merge(defaults: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]`: Deep merge dictionaries

### File Utilities

- `verify_output_file(file_path: Path) -> None`: Verify output file exists and is readable
- `get_file_mtime(file_path: Path) -> float`: Get file modification time

### Platform Detection

- `detect_platform() -> str`: Detect platform ("azureml" or "local")
- `resolve_platform_checkpoint_path(local_path: str, azureml_path: str) -> str`: Resolve checkpoint path by platform

### Notebook Setup

- `detect_notebook_environment() -> NotebookEnvironment`: Detect notebook execution environment (Colab, Kaggle, local)
- `find_repository_root(start_dir: Optional[Path] = None) -> Optional[Path]`: Find repository root directory with platform-specific search (returns None if not found)
- `setup_notebook_paths(root_dir: Optional[Path] = None, add_src_to_path: bool = True) -> NotebookPaths`: Setup notebook paths (root, config, src)
- `get_platform_vars() -> dict[str, str | bool | Optional[Path]]`: Get platform variables as a dict (convenience function)
- `ensure_mlflow_installed() -> None`: Install mlflow if needed (Colab/Kaggle only)
- `ensure_src_in_path() -> Optional[Path]`: Ensure src/ is in Python path

### MLflow Setup

- `setup_mlflow_cross_platform(config: Dict) -> None`: Setup MLflow for current platform
- `setup_mlflow_from_config(config_path: Path) -> None`: Setup MLflow from config file
- `create_ml_client_from_config(config: Dict) -> Optional[MLClient]`: Create AzureML client

### Tokenization Utilities

- `prepare_onnx_inputs(texts: List[str], tokenizer) -> Dict`: Prepare inputs for ONNX model
- `get_offset_mapping(text: str, tokenizer) -> List[Tuple[int, int]]`: Get token offset mappings
- `prepare_onnx_inputs_with_offsets(...) -> Tuple[Dict, List]`: Prepare inputs with offsets

### Constants

- `STAGE_SMOKE`, `STAGE_HPO`, `STAGE_TRAINING`: Stage name constants
- `EXPERIMENT_NAME`, `MODEL_NAME`, `PROD_STAGE`: Naming constants
- `METRICS_FILENAME`, `BENCHMARK_FILENAME`, `CHECKPOINT_DIRNAME`: File/directory name constants
- `DEFAULT_RANDOM_SEED`, `DEFAULT_K_FOLDS`: Default value constants

For detailed signatures, see source code.

## Integration Points

### Used By

- **Training modules**: Uses logging, platform detection, MLflow setup, tokenization utilities
- **Evaluation modules**: Uses logging, platform detection, file utilities
- **Infrastructure modules**: Uses logging, YAML utilities, hash utilities, MLflow setup
- **Orchestration modules**: Uses constants, logging, argument parsing
- **Deployment modules**: Uses tokenization utilities, platform detection

### Depends On

- Standard library only (no dependencies on other `src/` modules)

## Testing

```bash
uvx pytest tests/common/
```

## Related Modules

- [`../core/README.md`](../core/README.md) - Core utilities (no dependencies, used by infrastructure)
- [`../infrastructure/README.md`](../infrastructure/README.md) - Infrastructure layer uses common utilities
- [`../training/README.md`](../training/README.md) - Training workflows use common utilities

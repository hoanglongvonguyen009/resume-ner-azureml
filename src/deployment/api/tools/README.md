# API Tools

Utility helpers for the deployment API, including model discovery, server launch helpers, diagnostics, and notebook utilities for API testing.

## TL;DR / Quick Start

Discover the latest converted model, start a local API server, and call it from notebooks or scripts.

```python
from pathlib import Path
from src.deployment.api.tools import (
    find_model_pair,
    start_api_server,
    check_server_health,
)

outputs_dir = Path("outputs")
onnx_path, checkpoint_dir = find_model_pair(outputs_dir)

process = start_api_server(
    onnx_path=onnx_path,
    checkpoint_dir=checkpoint_dir,
    host="0.0.0.0",
    port=8000,
    background=True,
)

assert check_server_health("http://localhost:8000")
```

## Overview

The `tools` package provides reusable helpers for working with the deployment API:

- **Model discovery**: Find the latest ONNX model and matching training checkpoint
- **Server launch**: Start a local API server from Python and wait for it to become healthy
- **Diagnostics**: Run simple diagnostics over predictions
- **Notebook helpers**: Thin helpers for notebooks to keep them focused on orchestration and visualization

These utilities are used by notebooks under `notebooks/` (for local API and Docker testing) and can also be reused in scripts or tests.

## Module Structure

- `model_finder.py`
  - `extract_spec_hash(...)`
  - `find_latest_onnx_model(...)`
  - `find_matching_checkpoint(...)`
  - `find_model_pair(outputs_dir: Path) -> tuple[Path | None, Path | None]`
  - `list_available_models(outputs_dir: Path) -> dict[str, object]`
- `server_launcher.py`
  - `check_server_health(base_url: str) -> bool`
  - `get_server_info(base_url: str) -> dict[str, object]`
  - `start_api_server(...) -> subprocess.Popen | None`
  - `wait_for_server(timeout: int = 30) -> bool`
- `model_diagnostics.py`
  - `check_predictions(...)` – basic prediction sanity checks
- `notebook_config.py`
  - `NotebookConfig` – TypedDict for notebook-level API configuration
  - `get_default_config()` – default base URL and timeout
  - `get_config_from_env()` – override config from environment variables
- `notebook_helpers.py`
  - `setup_notebook_paths(project_root: Path | None = None) -> Path`
  - `make_request(method: str, endpoint: str, *, base_url: str, timeout: int, **kwargs) -> dict[str, object]`
  - `display_entities(entities: list[dict[str, object]], source_text: str | None = None) -> None`

## Usage

### Model Discovery

```python
from pathlib import Path
from src.deployment.api.tools import find_model_pair, list_available_models

outputs_dir = Path("outputs")

all_models = list_available_models(outputs_dir)
print(f"Found {len(all_models['onnx_models'])} ONNX models")

onnx_path, checkpoint_dir = find_model_pair(outputs_dir)
if onnx_path and checkpoint_dir:
    print("ONNX:", onnx_path)
    print("Checkpoint:", checkpoint_dir)
```

### Server Launch (Local API)

```python
from pathlib import Path
from src.deployment.api.tools import (
    find_model_pair,
    start_api_server,
    wait_for_server,
)

outputs_dir = Path("outputs")
onnx_path, checkpoint_dir = find_model_pair(outputs_dir)

process = start_api_server(
    onnx_path=onnx_path,
    checkpoint_dir=checkpoint_dir,
    host="0.0.0.0",
    port=8000,
    background=True,
)

if process and wait_for_server(timeout=30):
    print("API server is ready")
```

### Notebook Helpers

```python
from src.deployment.api.tools import (
    NotebookConfig,
    get_default_config,
    make_request,
    display_entities,
)

config: NotebookConfig = get_default_config()

result = make_request(
    "POST",
    "/predict",
    base_url=config["api_base_url"],
    timeout=config["api_timeout"],
    json={"text": "John Smith worked at Microsoft."},
)

if result.get("status_code") == 200 and result.get("data"):
    entities = result["data"].get("entities", [])
    display_entities(entities)
```

## Testing

```bash
uvx pytest tests/deployment/api/
```

The same tests that cover the deployment API also exercise most of the tooling in this package.

## Related Modules

- [`../README.md`](../README.md) – FastAPI deployment entrypoint and routes
- [`../../README.md`](../../README.md) – Deployment module overview (conversion + API)
- Notebooks:
  - `notebooks/api_testing.ipynb` – Local API testing and entity visualization
  - `notebooks/docker_testing.ipynb` – Docker-based API testing



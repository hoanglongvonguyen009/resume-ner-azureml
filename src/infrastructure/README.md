# Infrastructure

Infrastructure layer for configuration, paths, tracking, naming, and platform abstraction.

## TL;DR / Quick Start

Manage configuration, resolve paths, set up MLflow tracking, and handle platform-specific adapters.

```python
from src.infrastructure.config.loader import load_experiment_config
from src.infrastructure.paths.resolve import resolve_output_path
from src.infrastructure.tracking.mlflow.setup import setup_mlflow
from src.infrastructure.naming.display_policy import format_run_name

# Load experiment configuration
config = load_experiment_config(config_root=Path("config/"), experiment_name="my_experiment")

# Resolve output path
output_path = resolve_output_path(
    root_dir=Path("."),
    config_dir=Path("config/"),
    category="hpo",
    backbone="distilbert"
)

# Setup MLflow
setup_mlflow(config=mlflow_config)

# Format run name
run_name = format_run_name(context=naming_context, policy=policy)
```

## Overview

The `infrastructure` module provides the infrastructure layer for ML operations:

- **Configuration management**: Load, validate, and merge configuration files
- **Path resolution**: Resolve output paths using patterns and placeholders
- **MLflow tracking**: Setup and manage MLflow tracking for experiments
- **Naming conventions**: Generate consistent names for runs, experiments, and artifacts
- **Platform adapters**: Abstract platform-specific operations (AzureML, local)
- **Storage abstractions**: Handle storage operations across platforms
- **Fingerprinting**: Compute fingerprints for reproducibility
- **Metadata management**: Manage experiment metadata

This module provides abstractions that allow the codebase to work across different platforms (local, AzureML, Colab) without platform-specific code in business logic.

## Key Concepts

- **Configuration hierarchy**: Experiment configs reference domain configs (data, model, training, HPO)
- **Path patterns**: Paths are resolved from patterns with placeholders (e.g., `{backbone}/{run_id}`)
- **Naming policies**: Consistent naming using policy files and token-based patterns
- **Platform abstraction**: Platform adapters abstract platform-specific operations
- **MLflow integration**: Unified MLflow setup and tracking across platforms

## Module Structure

This module is organized into the following submodules:

- `config/`: Configuration loading, validation, and merging
- `paths/`: Path resolution and management
- `tracking/`: MLflow tracking integration
- `naming/`: Naming conventions and policies
- `platform/`: Platform adapters (AzureML, local)
- `storage/`: Storage abstractions
- `fingerprints/`: Fingerprinting utilities
- `metadata/`: Metadata management
- `setup/`: Setup utilities

See individual submodule READMEs for detailed documentation:
- [`config/README.md`](config/README.md) - Configuration management
- [`paths/README.md`](paths/README.md) - Path resolution
- [`tracking/README.md`](tracking/README.md) - MLflow tracking
- [`naming/README.md`](naming/README.md) - Naming conventions
- [`platform/README.md`](platform/README.md) - Platform adapters

## Usage

### Basic Workflow: Configuration and Paths

```python
from pathlib import Path
from src.infrastructure.config.loader import load_experiment_config
from src.infrastructure.paths.resolve import resolve_output_path

# Load experiment configuration
config = load_experiment_config(
    config_root=Path("config/"),
    experiment_name="resume_ner_baseline"
)

# Resolve output path for HPO
hpo_path = resolve_output_path(
    root_dir=Path("."),
    config_dir=Path("config/"),
    category="hpo",
    backbone="distilbert",
    study_hash="abc123"
)
# Returns: Path("outputs/hpo/distilbert/study_abc123")
```

### Basic Workflow: MLflow Setup

```python
from src.infrastructure.tracking.mlflow.setup import setup_mlflow

# Setup MLflow tracking
setup_mlflow(config={
    "tracking_uri": "file:./mlruns",
    "experiment_name": "my_experiment"
})
```

### Basic Workflow: Naming

```python
from src.infrastructure.naming.display_policy import format_run_name, load_naming_policy
from src.infrastructure.naming.context import create_naming_context

# Load naming policy
policy = load_naming_policy(config_dir=Path("config/"))

# Create naming context
context = create_naming_context(
    backbone="distilbert",
    stage="hpo",
    study_hash="abc123"
)

# Format run name
run_name = format_run_name(context=context, policy=policy)
```

## API Reference

### Configuration

- `load_experiment_config(...)`: Load experiment configuration
- `merge_configs_with_precedence(...)`: Merge configurations with precedence
- `apply_argument_overrides(...)`: Apply command-line argument overrides

### Paths

- `resolve_output_path(...)`: Resolve output path from config
- `build_output_path(...)`: Build output path from pattern
- `validate_output_path(...)`: Validate output path before creation

### Tracking

- `setup_mlflow(...)`: **SSOT** for MLflow setup - Use this for all MLflow configuration
  - **Layering**: This is the high-level SSOT that wraps `common.shared.mlflow_setup.setup_mlflow_cross_platform()` (internal)
  - See `tracking/mlflow/` for detailed MLflow utilities

### Naming

- `format_run_name(...)`: Format run name from context and policy
- `load_naming_policy(...)`: Load naming policy from config
- `build_mlflow_run_name(...)`: Build MLflow run name
- `build_mlflow_tags(...)`: Build MLflow tags

### Platform

- `get_platform_adapter(...)`: Get platform adapter for current platform
- See `platform/adapters/` for platform-specific operations

For detailed signatures, see source code or submodule documentation.

## Integration Points

### Dependencies

- `core/`: Core utilities (normalization, tokens, placeholders)
- `common/`: Shared utilities (logging, hashing, YAML)

### Used By

- **Training modules**: Use infrastructure for configuration, paths, MLflow tracking
- **Orchestration modules**: Use infrastructure for job orchestration
- **Evaluation modules**: Use infrastructure for artifact discovery and tracking

## Examples

### Example 1: Complete Setup

```python
from pathlib import Path
from src.infrastructure.config.loader import load_experiment_config
from src.infrastructure.paths.resolve import resolve_output_path
from src.infrastructure.tracking.mlflow.setup import setup_mlflow

# Load configuration
config = load_experiment_config(
    config_root=Path("config/"),
    experiment_name="resume_ner_baseline"
)

# Resolve paths
output_path = resolve_output_path(
    root_dir=Path("."),
    config_dir=Path("config/"),
    category="hpo",
    backbone="distilbert"
)

# Setup tracking
setup_mlflow(config={
    "tracking_uri": "file:./mlruns",
    "experiment_name": config.name
})
```

## Best Practices

1. **Use configuration files**: Always load configs from YAML files, don't hardcode
2. **Repository root detection**: Use `detect_repo_root()` from `infrastructure.paths.repo` (canonical function)
3. **Resolve paths through infrastructure**: Use `resolve_output_path` instead of hardcoding paths
4. **Use naming policies**: Generate names using naming policies for consistency
5. **Platform abstraction**: Use platform adapters instead of platform-specific code
6. **MLflow setup**: Always use `infrastructure.tracking.mlflow.setup.setup_mlflow()` (SSOT) for MLflow configuration

## Notes

- Infrastructure modules are designed to have no circular dependencies
- **Repository root detection**: Use `detect_repo_root()` from `infrastructure.paths.repo` (canonical function, replaces deprecated wrappers)
- Path resolution uses pattern-based approach for flexibility
- Naming policies are cached for performance
- Platform adapters abstract away platform differences
- **MLflow setup**: `infrastructure.tracking.mlflow.setup.setup_mlflow()` is the SSOT (wraps `common.shared.mlflow_setup.setup_mlflow_cross_platform()` internally)

## Testing

```bash
uvx pytest tests/infrastructure/
```

## Related Modules

- [`../core/README.md`](../core/README.md) - Core utilities used by infrastructure
- [`../common/README.md`](../common/README.md) - Shared utilities
- [`../training/README.md`](../training/README.md) - Training uses infrastructure
- [`config/README.md`](config/README.md) - Configuration management
- [`paths/README.md`](paths/README.md) - Path resolution
- [`tracking/README.md`](tracking/README.md) - MLflow tracking
- [`naming/README.md`](naming/README.md) - Naming conventions
- [`platform/README.md`](platform/README.md) - Platform adapters


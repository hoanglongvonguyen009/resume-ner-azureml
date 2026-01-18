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
  - `mlflow/`: MLflow tracking utilities
    - `index/`: MLflow run indexing and version management
- `naming/`: Naming conventions and policies
- `platform/`: Platform adapters (AzureML, local)
- `azureml/`: AzureML runtime utilities
  - `runtime.py`: Job submission and monitoring
- `shared/`: Shared cross-domain utilities
  - `backup.py`: Backup utilities for HPO, training, conversion, and benchmarking
- `storage/`: Storage abstractions
  - `drive.py`: Google Drive backup/restore for Colab environments
    - `DriveBackupStore`: Core backup/restore operations with Drive path rejection
    - Rejects Drive paths early to prevent crashes when attempting to backup paths already in Drive
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

### AzureML Runtime

- `infrastructure.azureml.submit_and_wait_for_job(...)`: Submit AzureML job and wait for completion
  - Handles job submission, streaming logs, and status monitoring
  - Raises `RuntimeError` if job fails

### Shared Utilities

- `infrastructure.shared.backup.immediate_backup_if_needed(...)`: Immediate backup utility for files/directories
  - Used by HPO, training, conversion, and benchmarking workflows
  - Checks: backup_enabled, path exists, path not in Drive
- `infrastructure.shared.backup.create_incremental_backup_callback(...)`: Create Optuna callback for incremental backup
- `infrastructure.shared.backup.create_study_db_backup_callback(...)`: Convenience wrapper for study.db backup callback
- `infrastructure.shared.backup.backup_hpo_study_to_drive(...)`: Backup HPO study.db and study folder to Google Drive

### MLflow Indexing

- `infrastructure.tracking.mlflow.index.update_mlflow_index(...)`: Update index with run_key_hash → run_id mapping
- `infrastructure.tracking.mlflow.index.find_in_mlflow_index(...)`: Find run_id in local index by run_key_hash
- `infrastructure.tracking.mlflow.index.get_mlflow_index_path(...)`: Get path to mlflow_index.json
- `infrastructure.tracking.mlflow.index.reserve_run_name_version(...)`: Reserve version number for run name
- `infrastructure.tracking.mlflow.index.commit_run_name_version(...)`: Commit reserved version after MLflow run creation
- `infrastructure.tracking.mlflow.index.cleanup_stale_reservations(...)`: Clean up stale reservations

### Storage

- `DriveBackupStore`: Google Drive backup/restore store for Colab environments
  - `backup(local_path, expect="any")`: Backup file or directory to Drive
  - `restore(local_path)`: Restore file or directory from Drive
  - `drive_path_for(local_path)`: Compute Drive path for local path
  - **Drive Path Rejection**: Both `backup()` and `drive_path_for()` reject Drive paths early to prevent crashes
  - `as_backup_callback()`: Create callback function for backup operations
  - `as_restore_callback()`: Create callback function for restore operations
- `create_colab_store(...)`: Create Drive backup store for Colab environment
- `mount_colab_drive(...)`: Mount Google Drive in Colab (if available)

For detailed signatures, see source code or submodule documentation.

## Integration Points

### Dependencies

- `core/`: Core utilities (normalization, tokens, placeholders)
- `common/`: Shared utilities (logging, hashing, YAML)

### Used By

- **Training modules**: Use infrastructure for configuration, paths, MLflow tracking, AzureML jobs
- **Deployment modules**: Use infrastructure for AzureML conversion jobs
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
4. **Use consolidated path resolution**: Prefer `resolve_project_paths_with_fallback()` for project path resolution (standardized fallback logic)
5. **Use centralized hash utilities**: Always use `get_or_compute_study_key_hash()` and `get_or_compute_trial_key_hash()` instead of manually retrieving hashes from MLflow runs
6. **Trust provided parameters**: When calling functions that accept `config_dir`, trust the provided value - inference only occurs when explicitly `None` (DRY principle)

## Consolidation Patterns

The infrastructure module follows consolidation patterns to eliminate DRY violations:

### Trust Provided Parameters Pattern

All functions that accept `config_dir: Optional[Path] = None` follow the "trust provided parameter" pattern:

- **If `config_dir` is provided** (not `None`), it's used directly without inference
- **Inference only occurs** when `config_dir` is explicitly `None`
- This avoids redundant inference and follows DRY principles

**Example:**
```python
# ✅ Good: Pass config_dir explicitly when available
root_dir = detect_repo_root()
config_dir = root_dir / "config"
tags_registry = load_tags_registry(config_dir=config_dir)  # Uses provided config_dir directly

# ✅ Also valid: Let function infer when config_dir is None
tags_registry = load_tags_registry(config_dir=None)  # Function will infer
```

### Single Source of Truth (SSOT) Functions

The following functions are SSOT for common operations:

- **Path Resolution**: `infrastructure.paths.resolve.resolve_output_path()` - SSOT for output path resolution
- **Path Building**: `infrastructure.paths.resolve.build_output_path()` - SSOT for building paths from patterns
- **Project Paths**: `infrastructure.paths.utils.resolve_project_paths_with_fallback()` - **SSOT** for resolving root_dir and config_dir with standardized fallback logic
- **MLflow Config Loading**: `infrastructure.naming.mlflow.config.load_mlflow_config()` - SSOT for loading MLflow configuration
- **Naming Config**: `infrastructure.naming.mlflow.config.get_naming_config()` - SSOT for naming configuration access
- **Tracking Config**: `infrastructure.naming.mlflow.config.get_tracking_config()` - SSOT for tracking configuration access
- **Index Config**: `infrastructure.naming.mlflow.config.get_index_config()` - SSOT for index configuration access
- **Auto-Increment Config**: `infrastructure.naming.mlflow.config.get_auto_increment_config()` - SSOT for auto-increment configuration access
- **Run Finder Config**: `infrastructure.naming.mlflow.config.get_run_finder_config()` - SSOT for run finder configuration access
  - **Deprecated**: `orchestration.jobs.tracking.config.loader.*` - Use `infrastructure.naming.mlflow.config.*` instead
- **Hash Computation**: `infrastructure.tracking.mlflow.hash_utils.get_or_compute_study_key_hash()` - SSOT for study key hash retrieval/computation
- **Hash Computation**: `infrastructure.tracking.mlflow.hash_utils.get_or_compute_trial_key_hash()` - SSOT for trial key hash retrieval/computation
- **Tags Registry**: `infrastructure.naming.mlflow.tags_registry.load_tags_registry()` - SSOT for loading tags registry
- **YAML Loading**: `common.shared.yaml_utils.load_yaml()` - SSOT for YAML file loading
- **MLflow Setup**: `infrastructure.tracking.mlflow.setup.setup_mlflow()` - SSOT for MLflow configuration

**Best Practice**: Always use SSOT functions instead of duplicating logic. If you need similar functionality, check if an SSOT function exists first.
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
- **Consolidation**: All modules follow the "trust provided config_dir" pattern and use SSOT functions to eliminate DRY violations

**See Also**: 
- [`docs/architecture/mlflow-utilities.md`](../../docs/architecture/mlflow-utilities.md) - Consolidated patterns, SSOT functions, and usage examples
- [`docs/design/mlflow-layering.md`](../../docs/design/mlflow-layering.md) - Detailed MLflow setup layering documentation

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


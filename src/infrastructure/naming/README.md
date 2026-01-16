# Infrastructure Naming

Display and run naming with policy-based name generation and MLflow integration.

## TL;DR / Quick Start

Generate consistent names for runs, experiments, and artifacts using naming policies.

```python
from src.infrastructure.naming.display_policy import format_run_name, load_naming_policy
from src.infrastructure.naming.context import create_naming_context
from src.infrastructure.naming.mlflow.run_names import build_mlflow_run_name

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

# Build MLflow run name
mlflow_name = build_mlflow_run_name(context=context, config=naming_config)
```

## Overview

The `naming` module provides naming conventions and policies:

- **Naming policies**: Load and validate naming policies from YAML
- **Display names**: Format display names using policy patterns
- **MLflow naming**: Build MLflow run names and experiment names
- **Tag generation**: Build MLflow tags from naming contexts
- **Context management**: Create and manage naming contexts
- **Token management**: Build token values for naming patterns
- **HPO keys**: Build HPO study and trial keys
- **Run keys**: Build MLflow run keys and hashes

## Module Structure

- `display_policy.py`: Naming policy loading and display name formatting
- `context.py`: Naming context creation and management
- `context_tokens.py`: Token value building
- `experiments.py`: Experiment name building
- `mlflow/`: MLflow-specific naming
  - `run_names.py`: MLflow run name building
  - `run_keys.py`: MLflow run key building
  - `tags.py`: MLflow tag building
  - `hpo_keys.py`: HPO key building
  - `refit_keys.py`: Refit key building
  - `tags_registry.py`: Tag registry management
  - `config.py`: MLflow naming configuration

## Usage

### Basic Example: Format Run Name

```python
from pathlib import Path
from src.infrastructure.naming.display_policy import format_run_name, load_naming_policy
from src.infrastructure.naming.context import create_naming_context

# Load naming policy
policy = load_naming_policy(config_dir=Path("config/"))

# Create naming context
context = create_naming_context(
    backbone="distilbert",
    stage="hpo",
    study_hash="abc123",
    trial_number=5
)

# Format run name using policy
run_name = format_run_name(context=context, policy=policy)
# Returns formatted name based on policy pattern
```

### Basic Example: Build MLflow Run Name

```python
from src.infrastructure.naming.mlflow.run_names import build_mlflow_run_name
from src.infrastructure.naming.mlflow.config import get_naming_config

# Get naming config
naming_config = get_naming_config(config_dir=Path("config/"))

# Build MLflow run name
mlflow_name = build_mlflow_run_name(
    context=context,
    config=naming_config
)
```

### Basic Example: Build MLflow Tags

```python
from src.infrastructure.naming.mlflow.tags import build_mlflow_tags

# Build MLflow tags from context
tags = build_mlflow_tags(
    context=context,
    config=naming_config
)
# Returns: {"backbone": "distilbert", "stage": "hpo", "study_hash": "abc123", ...}
```

### Basic Example: HPO Keys

```python
from src.infrastructure.naming.mlflow.hpo_keys import (
    build_hpo_study_key,
    build_hpo_trial_key
)

# Build HPO study key
study_key = build_hpo_study_key(
    backbone="distilbert",
    spec_hash="abc123"
)

# Build HPO trial key
trial_key = build_hpo_trial_key(
    study_key=study_key,
    trial_number=5
)
```

## API Reference

### Display Policy

- `load_naming_policy(config_dir: Optional[Path] = None, validate: bool = True) -> Dict[str, Any]`: Load naming policy
- `format_run_name(context: NamingContext, policy: Dict[str, Any]) -> str`: Format run name
- `validate_run_name(name: str, policy: Dict[str, Any]) -> bool`: Validate run name
- `build_parent_training_id(...)`: Build parent training ID
- `parse_parent_training_id(...)`: Parse parent training ID

### Context

- `create_naming_context(**kwargs) -> NamingContext`: Create naming context
- `NamingContext`: Dataclass representing naming context
- `build_token_values(context: NamingContext) -> Dict[str, str]`: Build token values

### MLflow Naming

- `build_mlflow_run_name(...)`: Build MLflow run name
- `build_mlflow_run_key(...)`: Build MLflow run key
- `build_mlflow_run_key_hash(...)`: Build MLflow run key hash
- `build_mlflow_tags(...)`: Build MLflow tags
- `build_hpo_study_key(...)`: Build HPO study key
- `build_hpo_trial_key(...)`: Build HPO trial key

### Experiments

- `build_mlflow_experiment_name(...)`: Build MLflow experiment name
- `build_aml_experiment_name(...)`: Build AzureML experiment name

For detailed signatures, see source code.

## Integration Points

### Used By

- **Training modules**: Use naming for run names and tags
- **HPO modules**: Use naming for study and trial names
- **Orchestration modules**: Use naming for job names
- **Tracking modules**: Use naming for MLflow run names

### Depends On

- `core/`: Token validation, normalization, placeholder extraction
- `common/`: YAML utilities, file utilities

## Naming Policy Format

Naming policies are defined in `config/naming.yaml`:

```yaml
patterns:
  run_name: "{backbone}_{stage}_{study_hash}"
  experiment_name: "{experiment_name}_{stage}"
tokens:
  backbone:
    scope: ["name", "path"]
  stage:
    scope: ["name"]
```

## Testing

```bash
uvx pytest tests/infrastructure/naming/
```

## Related Modules

- [`../README.md`](../README.md) - Main infrastructure module
- [`../tracking/README.md`](../tracking/README.md) - Tracking uses naming
- [`../../core/README.md`](../../core/README.md) - Core utilities for tokens and normalization


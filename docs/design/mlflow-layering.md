# MLflow Setup Layering

This document describes the layering and responsibilities of MLflow-related modules in the codebase.

## Overview

MLflow functionality is organized into distinct layers with clear separation of concerns:

1. **Infrastructure Layer** (SSOT): MLflow setup and configuration
2. **Domain Layer**: Run creation and naming for specific domains (HPO, Training)
3. **Execution Layer**: Scripts that orchestrate workflows

## Layer 1: Infrastructure (SSOT)

### `infrastructure.tracking.mlflow.setup.setup_mlflow()`

**Purpose**: Single source of truth for MLflow experiment setup and configuration.

**Responsibilities**:
- Configure MLflow tracking URI (Azure ML vs local)
- Set up MLflow experiment
- Handle Azure ML compatibility and fallbacks
- Configure artifact timeout settings

**When to use**: Call this **first** in any orchestrator or workflow entry point before creating MLflow runs.

**Example**:
```python
from infrastructure.tracking.mlflow.setup import setup_mlflow

# In orchestrator/entry point
setup_mlflow(experiment_name="my-experiment", config_dir=config_dir)

# Now you can use domain-specific run creation functions
```

### `infrastructure.tracking.mlflow.hash_utils`

**Purpose**: Single source of truth for hash retrieval and computation.

**Key Functions**:
- `get_or_compute_study_key_hash()`: Consolidated utility with fallback hierarchy
- `get_or_compute_trial_key_hash()`: Consolidated utility for trial hashes
- `get_study_key_hash_from_run()`: Retrieve hash from MLflow run tags (SSOT)
- `compute_study_key_hash_v2()`: Compute hash from configs (fallback)

**Priority Order**:
1. Use provided hash (if available)
2. Retrieve from MLflow run tags (SSOT)
3. Compute from configs (fallback)

**When to use**: Always use these utilities instead of manually retrieving hashes from tags or computing them inline.

### `infrastructure.paths.utils.resolve_project_paths_with_fallback()`

**Purpose**: Single source of truth for path resolution.

**Responsibilities**:
- Resolve `root_dir` and `config_dir` from provided parameters
- Trust provided `config_dir` parameter (DRY principle)
- Only infer when explicitly None

**When to use**: Use this consistently for all path resolution instead of `infer_config_dir()` or manual path inference.

## Layer 2: Domain-Specific Run Creation

### `training.hpo.tracking.setup.setup_hpo_mlflow_run()`

**Purpose**: Create HPO-specific naming context and run names.

**Responsibilities**:
- Create HPO naming context
- Generate MLflow run names for HPO sweeps
- Compute study key hash (with fallback to v1/v2)
- **Does NOT** handle MLflow setup/configuration

**Prerequisites**:
- `infrastructure.tracking.mlflow.setup.setup_mlflow()` must be called first

**Usage**:
```python
# Step 1: Setup MLflow (infrastructure layer)
from infrastructure.tracking.mlflow.setup import setup_mlflow
setup_mlflow(experiment_name="hpo-experiment", config_dir=config_dir)

# Step 2: Create HPO run context (domain layer)
from training.hpo.tracking.setup import setup_hpo_mlflow_run
hpo_context, run_name = setup_hpo_mlflow_run(
    backbone=backbone,
    study_name=study_name,
    output_dir=output_dir,
    run_id=run_id,
    should_resume=should_resume,
    checkpoint_enabled=checkpoint_enabled,
    data_config=data_config,
    hpo_config=hpo_config,
    train_config=train_config,  # Optional, enables v2 hash computation
    study_key_hash=study_key_hash,  # Optional, pre-computed hash
    config_dir=config_dir,  # Trust provided parameter (DRY)
)
```

**Key Principles**:
- Trusts provided `config_dir` parameter (no redundant inference)
- Uses v2 hash computation (required)
- Uses `resolve_project_paths_with_fallback()` for path resolution (SSOT)

### `training.execution.mlflow_setup.create_training_mlflow_run()`

**Purpose**: Create MLflow runs for training execution.

**Responsibilities**:
- Create training MLflow runs
- Set up MLflow tracking for training subprocesses
- Manage run lifecycle (parent/child relationships)
- **Does NOT** handle MLflow setup/configuration

**Prerequisites**:
- `infrastructure.tracking.mlflow.setup.setup_mlflow()` must be called first

## Layer 3: Execution Scripts

Execution scripts (e.g., `sweep.py`, `cv.py`, `refit.py`) orchestrate workflows and should:

1. **Call infrastructure setup first**:
   ```python
   from infrastructure.tracking.mlflow.setup import setup_mlflow
   setup_mlflow(experiment_name=..., config_dir=config_dir)
   ```

2. **Use domain-specific run creation**:
   ```python
   from training.hpo.tracking.setup import setup_hpo_mlflow_run
   hpo_context, run_name = setup_hpo_mlflow_run(...)
   ```

3. **Use centralized utilities**:
   - `resolve_project_paths_with_fallback()` for path resolution
   - `get_or_compute_study_key_hash()` for hash retrieval/computation
   - `get_or_compute_trial_key_hash()` for trial hash retrieval/computation

## Common Patterns

### Pattern 1: Path Resolution

**✅ Correct**:
```python
from infrastructure.paths.utils import resolve_project_paths_with_fallback

# Trust provided config_dir (DRY principle)
root_dir, config_dir = resolve_project_paths_with_fallback(
    output_dir=output_dir,
    config_dir=config_dir,  # Use provided value, don't re-infer
)
```

**❌ Incorrect**:
```python
# Redundant inference
if config_dir is None:
    from infrastructure.paths.utils import infer_config_dir
    config_dir = infer_config_dir()  # Don't do this if config_dir was already provided
```

### Pattern 2: Hash Retrieval

**✅ Correct**:
```python
from infrastructure.tracking.mlflow.hash_utils import get_or_compute_study_key_hash

study_key_hash = get_or_compute_study_key_hash(
    study_key_hash=provided_hash,  # Use if available
    hpo_parent_run_id=parent_run_id,  # Retrieve from tags (SSOT)
    data_config=data_config,  # Compute fallback
    hpo_config=hpo_config,
    train_config=train_config,
    backbone=backbone,
    config_dir=config_dir,
)
```

**❌ Incorrect**:
```python
# Manual hash retrieval
run = client.get_run(run_id)
study_key_hash = run.data.tags.get("code.study_key_hash")  # Don't do this
```

### Pattern 3: MLflow Setup

**✅ Correct**:
```python
# In orchestrator/entry point
from infrastructure.tracking.mlflow.setup import setup_mlflow
setup_mlflow(experiment_name="my-experiment", config_dir=config_dir)

# Then use domain-specific functions
from training.hpo.tracking.setup import setup_hpo_mlflow_run
hpo_context, run_name = setup_hpo_mlflow_run(...)
```

**❌ Incorrect**:
```python
# Don't skip infrastructure setup
from training.hpo.tracking.setup import setup_hpo_mlflow_run
hpo_context, run_name = setup_hpo_mlflow_run(...)  # Will fail if MLflow not configured
```

## Summary

| Layer | Module | Responsibility | Prerequisites |
|-------|--------|----------------|---------------|
| Infrastructure | `infrastructure.tracking.mlflow.setup` | MLflow setup (SSOT) | None |
| Infrastructure | `infrastructure.tracking.mlflow.hash_utils` | Hash utilities (SSOT) | None |
| Infrastructure | `infrastructure.paths.utils` | Path resolution (SSOT) | None |
| Domain | `training.hpo.tracking.setup` | HPO run creation | Infrastructure setup |
| Domain | `training.execution.mlflow_setup` | Training run creation | Infrastructure setup |
| Execution | `training.hpo.execution.local.*` | Workflow orchestration | Infrastructure + Domain |

## References

- `src/infrastructure/tracking/mlflow/setup.py` - MLflow setup SSOT
- `src/infrastructure/tracking/mlflow/hash_utils.py` - Hash utilities SSOT
- `src/infrastructure/paths/utils.py` - Path resolution SSOT
- `src/training/hpo/tracking/setup.py` - HPO run creation
- `src/training/execution/mlflow_setup.py` - Training run creation


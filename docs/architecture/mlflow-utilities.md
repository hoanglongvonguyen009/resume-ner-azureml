# MLflow Utilities - Consolidated Patterns

This document describes the consolidated patterns for MLflow utilities, following DRY principles and establishing single sources of truth (SSOT).

## Overview

This consolidation eliminates duplicate code patterns across MLflow-related modules by:
- Establishing SSOT functions for common operations
- Trusting provided parameters (DRY principle)
- Using centralized utilities instead of inline implementations
- Following consistent patterns across all execution scripts

## SSOT Functions and Responsibilities

### Path Resolution

**SSOT**: `infrastructure.paths.utils.resolve_project_paths_with_fallback()`

**Purpose**: Single source of truth for resolving `root_dir` and `config_dir`.

**Key Principles**:
- **Trust provided `config_dir` parameter** - Do not re-infer when caller provides it
- Only infer `config_dir` when explicitly `None` and cannot be derived
- Returns both `root_dir` and `config_dir` for consistency

**Usage Pattern**:
```python
from infrastructure.paths.utils import resolve_project_paths_with_fallback

# Trust provided config_dir (DRY principle)
root_dir, config_dir = resolve_project_paths_with_fallback(
    output_dir=output_dir,
    config_dir=config_dir,  # Use provided value, don't re-infer
)
```

**❌ Anti-pattern** (redundant inference):
```python
# Don't do this - redundant inference
if config_dir is None:
    from infrastructure.paths.utils import infer_config_dir
    config_dir = infer_config_dir()  # Redundant if caller already provided it
```

### Hash Computation and Retrieval

**SSOT**: `infrastructure.tracking.mlflow.hash_utils`

**Key Functions**:
- `get_or_compute_study_key_hash()`: Consolidated utility with fallback hierarchy
- `get_or_compute_trial_key_hash()`: Consolidated utility for trial hashes
- `get_study_key_hash_from_run()`: Retrieve hash from MLflow run tags (SSOT)
- `compute_study_key_hash_v2()`: Compute hash from configs (v2, preferred)
**Priority Order**:
1. Use provided hash (if available) - highest priority
2. Retrieve from MLflow run tags (SSOT) - tags are source of truth
3. Compute from configs (fallback) - v2 required

**Usage Pattern**:
```python
from infrastructure.tracking.mlflow.hash_utils import get_or_compute_study_key_hash

# Consolidated utility with fallback hierarchy
study_key_hash = get_or_compute_study_key_hash(
    study_key_hash=provided_hash,  # Priority 1: Use if available
    hpo_parent_run_id=parent_run_id,  # Priority 2: Retrieve from tags (SSOT)
    data_config=data_config,  # Priority 3: Compute fallback
    hpo_config=hpo_config,
    train_config=train_config,  # Required for v2 computation
    backbone=backbone,
    config_dir=config_dir,
)
```

**❌ Anti-pattern** (manual hash retrieval):
```python
# Don't do this - use centralized utilities
run = client.get_run(run_id)
study_key_hash = run.data.tags.get("code.study_key_hash")  # Manual extraction
```

**Hash Computation Versions**:
- **v2** (preferred): Uses `train_config` for more accurate fingerprints
  - Requires: `data_config`, `hpo_config`, `train_config`, `model`
  - Function: `compute_study_key_hash_v2()`
- **v2** (required): Uses `train_config` for accurate hash computation
  - Requires: `train_config` (includes data_config, hpo_config, model)
  - Function: `build_hpo_study_key_v2()` + `build_hpo_study_key_hash()`

### MLflow Setup

**SSOT**: `infrastructure.tracking.mlflow.setup.setup_mlflow()`

**Purpose**: Single source of truth for MLflow experiment setup and configuration.

**Responsibilities**:
- Configure MLflow tracking URI (Azure ML vs local)
- Set up MLflow experiment
- Handle Azure ML compatibility and fallbacks
- Configure artifact timeout settings

**Usage Pattern**:
```python
from infrastructure.tracking.mlflow.setup import setup_mlflow

# Call this FIRST in orchestrator/entry point
setup_mlflow(experiment_name="my-experiment", config_dir=config_dir)

# Then use domain-specific run creation functions
from training.hpo.tracking.setup import setup_hpo_mlflow_run
hpo_context, run_name = setup_hpo_mlflow_run(...)
```

See [MLflow Layering Documentation](mlflow-layering.md) for detailed layering information.

## Consolidated Patterns in Practice

### Pattern 1: Path Resolution in Functions

**Before** (redundant inference):
```python
def setup_hpo_mlflow_run(..., config_dir: Optional[Path] = None):
    # Redundant inference even when config_dir provided
    if config_dir is None:
        from infrastructure.paths.utils import infer_config_dir
        config_dir = infer_config_dir()
    
    # Later, another inference
    from infrastructure.paths.utils import resolve_project_paths_with_fallback
    root_dir, config_dir = resolve_project_paths_with_fallback(
        output_dir=output_dir,
        config_dir=config_dir,  # Already inferred above
    )
```

**After** (trust provided parameter):
```python
def setup_hpo_mlflow_run(..., config_dir: Optional[Path] = None):
    # Trust provided config_dir, only resolve once
    from infrastructure.paths.utils import resolve_project_paths_with_fallback
    root_dir, config_dir = resolve_project_paths_with_fallback(
        output_dir=output_dir,
        config_dir=config_dir,  # Trust provided parameter (DRY)
    )
```

### Pattern 2: Hash Computation Fallback

**Before** (legacy v1 only):
```python
def setup_hpo_mlflow_run(..., study_key_hash: Optional[str] = None):
    if study_key_hash is None and data_config and hpo_config:
        # Always uses v1 (legacy)
        from infrastructure.naming.mlflow.hpo_keys import (
            build_hpo_study_key,
            build_hpo_study_key_hash,
        )
        study_key = build_hpo_study_key(...)
        study_key_hash = build_hpo_study_key_hash(study_key)
```

**After** (v2 preferred, v1 fallback):
```python
def setup_hpo_mlflow_run(..., train_config: Optional[Dict] = None, study_key_hash: Optional[str] = None):
    if study_key_hash is None and data_config and hpo_config:
        # Try v2 first if train_config available
        if train_config:
            from infrastructure.tracking.mlflow.hash_utils import compute_study_key_hash_v2
            study_key_hash = compute_study_key_hash_v2(
                data_config, hpo_config, train_config, model, config_dir
            )
        
        # v2 hash computation is required - no fallback to v1
```

### Pattern 3: Hash Retrieval from MLflow Runs

**Before** (manual tag extraction):
```python
# Manual hash retrieval
client = mlflow.tracking.MlflowClient()
parent_run = client.get_run(hpo_parent_run_id)
study_key_hash = parent_run.data.tags.get("code.study_key_hash")
study_family_hash = parent_run.data.tags.get("code.study_family_hash")
```

**After** (centralized utilities):
```python
# Use centralized utilities (SSOT)
from mlflow.tracking import MlflowClient
from infrastructure.tracking.mlflow.hash_utils import (
    get_study_key_hash_from_run,
    get_study_family_hash_from_run,
)
client = MlflowClient()
study_key_hash = get_study_key_hash_from_run(
    hpo_parent_run_id, client, config_dir
)
study_family_hash = get_study_family_hash_from_run(
    hpo_parent_run_id, client, config_dir
)
```

## Execution Script Patterns

### Standard Pattern for Execution Scripts

All execution scripts (`sweep.py`, `cv.py`, `refit.py`) should follow this pattern:

```python
# 1. Path resolution (trust provided config_dir)
from infrastructure.paths.utils import resolve_project_paths_with_fallback
root_dir, config_dir = resolve_project_paths_with_fallback(
    output_dir=output_dir,
    config_dir=config_dir,  # Trust provided parameter
)

# 2. MLflow setup (infrastructure layer)
from infrastructure.tracking.mlflow.setup import setup_mlflow
setup_mlflow(experiment_name=experiment_name, config_dir=config_dir)

# 3. Hash retrieval/computation (use centralized utilities)
from infrastructure.tracking.mlflow.hash_utils import get_or_compute_study_key_hash
study_key_hash = get_or_compute_study_key_hash(
    study_key_hash=provided_hash,
    hpo_parent_run_id=parent_run_id,
    data_config=data_config,
    hpo_config=hpo_config,
    train_config=train_config,
    backbone=backbone,
    config_dir=config_dir,
)

# 4. Domain-specific run creation
from training.hpo.tracking.setup import setup_hpo_mlflow_run
hpo_context, run_name = setup_hpo_mlflow_run(
    ...,
    train_config=train_config,  # Enable v2 hash computation
    study_key_hash=study_key_hash,  # Pre-computed hash
    config_dir=config_dir,  # Trust provided parameter
)
```

## Key Principles

### 1. Trust Provided Parameters (DRY)

**Principle**: When a function receives a parameter (e.g., `config_dir`), trust it and use it directly. Do not re-infer or re-compute unless the parameter is explicitly `None` and cannot be derived.

**Example**:
```python
# ✅ Correct: Trust provided config_dir
def my_function(config_dir: Optional[Path] = None):
    root_dir, config_dir = resolve_project_paths_with_fallback(
        output_dir=output_dir,
        config_dir=config_dir,  # Trust provided value
    )

# ❌ Incorrect: Redundant inference
def my_function(config_dir: Optional[Path] = None):
    if config_dir is None:
        config_dir = infer_config_dir()  # Redundant if caller provided it
    root_dir, config_dir = resolve_project_paths_with_fallback(...)
```

### 2. Use Centralized Utilities (SSOT)

**Principle**: Always use centralized utilities from `infrastructure.tracking.mlflow.hash_utils` instead of implementing hash retrieval/computation inline.

**Example**:
```python
# ✅ Correct: Use centralized utility
from infrastructure.tracking.mlflow.hash_utils import get_or_compute_study_key_hash
study_key_hash = get_or_compute_study_key_hash(...)

# ❌ Incorrect: Manual implementation
run = client.get_run(run_id)
study_key_hash = run.data.tags.get("code.study_key_hash")
```

### 3. Consistent Path Resolution

**Principle**: Always use `resolve_project_paths_with_fallback()` for path resolution. Avoid `infer_config_dir()` or manual path inference.

**Example**:
```python
# ✅ Correct: Use SSOT function
from infrastructure.paths.utils import resolve_project_paths_with_fallback
root_dir, config_dir = resolve_project_paths_with_fallback(
    output_dir=output_dir,
    config_dir=config_dir,
)

# ❌ Incorrect: Manual inference
from infrastructure.paths.utils import infer_config_dir
config_dir = infer_config_dir()
```

### 4. Prefer v2 Hash Computation

**Principle**: Use v2 hash computation (`compute_study_key_hash_v2()`). `train_config` is required for accurate hash computation.

**Example**:
```python
# ✅ Correct: v2 preferred, v1 fallback
if train_config:
    study_key_hash = compute_study_key_hash_v2(...)
if not study_key_hash:
    study_key_hash = build_hpo_study_key_hash(...)  # v1 fallback
```

## Migration Checklist

When updating code to use consolidated patterns:

- [ ] Replace `infer_config_dir()` with `resolve_project_paths_with_fallback()`
- [ ] Remove redundant `config_dir` inference when parameter is provided
- [ ] Replace manual hash retrieval with `get_study_key_hash_from_run()` or `get_or_compute_study_key_hash()`
- [ ] Update hash computation to use v2 when `train_config` available
- [ ] Ensure `setup_mlflow()` is called before domain-specific run creation
- [ ] Verify all path resolution uses `resolve_project_paths_with_fallback()`
- [ ] Check that provided parameters are trusted (no redundant inference)

## References

- [MLflow Layering Documentation](mlflow-layering.md) - Detailed layering information
- `src/infrastructure/tracking/mlflow/hash_utils.py` - Hash utilities SSOT
- `src/infrastructure/paths/utils.py` - Path resolution SSOT
- `src/infrastructure/tracking/mlflow/setup.py` - MLflow setup SSOT
- `src/training/hpo/tracking/setup.py` - HPO run creation (uses consolidated patterns)


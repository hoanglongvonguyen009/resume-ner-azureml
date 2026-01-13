# Merged Plan: HPO Run Mode + Variants → Champion Selection → Idempotent Benchmarking

## Overview

### Purpose

This plan merges two related refactoring efforts into a unified, step-by-step implementation:

1. **Unify Run Mode Logic**: Single source of truth for `run.mode` extraction across all stages ✅ **COMPLETED**
2. **Unify Run Decision Logic**: Single source of truth for reuse vs. create new decisions ✅ **COMPLETED**
3. **Champion Selection**: Deterministic champion selection per backbone + idempotent benchmarking ⏳ **PENDING**

**Key Principle**: Follow DRY by reusing and generalizing existing code rather than duplicating.

### Current Status

**✅ Phase 1: HPO Foundation** - COMPLETED
- Run mode utility created and integrated
- Variant generation implemented
- Unified run decision logic implemented
- All redundant code removed

**⏳ Phase 2: Champion Selection** - PENDING
- study_key_hash v2 with bound fingerprints not yet implemented
- Champion selection with safety requirements not yet implemented

**⏳ Phase 3: Idempotent Benchmarking** - PENDING
- Benchmark idempotency not yet implemented

### Why Merge?

- **HPO variants** are the foundation for everything else
- **Retrieval** needs variant-aware logic from HPO
- **Benchmarking** uses both HPO variants and retrieval results
- **Run mode** controls behavior across all three stages
- **Shared utilities** reduce duplication (DRY)

### Scope

**In scope:**
- Phase 1: HPO run mode + variant generation (foundation) ✅ **COMPLETED**
- Phase 1.5: Unified run decision logic ✅ **COMPLETED**
- Phase 2: Deterministic best trial retrieval (uses HPO variants) ⏳ **PENDING**
- Phase 3: Idempotent benchmarking (uses both HPO + retrieval) ⏳ **PENDING**
- Extract shared utilities following DRY principles ✅ **COMPLETED**
- Reuse existing code where possible ✅ **COMPLETED**

**Out of scope:**
- Changing HPO execution logic
- Changing benchmark metrics/scoring
- Changing MLflow tracking structure (only reading)

## Goals & Success Criteria

### Goals

- **G1**: Single source of truth for run mode extraction (no duplication) ✅ **COMPLETED**
- **G2**: HPO variants (v1, v2, v3) with run.mode control ✅ **COMPLETED**
- **G1.5**: Unified run decision logic (single source of truth for reuse vs. create new) ✅ **COMPLETED**
- **G3**: Deterministic champion selection per backbone (MLflow-first, safe grouping) ⏳ **PENDING**
- **G4**: Idempotent benchmarking with stable keys ⏳ **PENDING**
- **G5**: Reuse existing code (DRY) - no unnecessary duplication ✅ **COMPLETED**

### Success Criteria

- [x] `run_mode.py` utility replaces all 4+ duplicate extractions
- [x] HPO creates variants (v1, v2, v3) based on `run.mode`
- [x] Unified `run_decision.py` module for consistent reuse logic
- [x] All existing tests pass
- [x] No code duplication (shared utilities used)
- [ ] `select_champion_per_backbone()` with MLflow-first priority and all safety requirements
- [ ] Benchmarking skips already-benchmarked trials

## DRY Analysis: Reusable Modules

### Existing Code to Reuse

| Component | Location | How to Reuse |
|-----------|----------|--------------|
| **Variant Computation** | `src/infrastructure/config/training.py::_compute_next_variant()` | Generalize to shared `variants.py` module |
| **Variant Scanning** | `src/infrastructure/config/training.py::_find_existing_variant()` | Generalize for HPO variants |
| **Run Mode Extraction** | Duplicated in 4+ places | Extract to `run_mode.py` utility |
| **MLflow Querying** | `src/evaluation/selection/mlflow_selection.py` | Extract patterns to `mlflow/queries.py` |
| **Best Trial Finding** | `src/evaluation/selection/trial_finder.py` | Enhance existing, don't duplicate |
| **Fingerprint/Hash** | `src/infrastructure/fingerprints/` | Reuse existing utilities |

### Strategy: Enhance, Don't Duplicate

- ✅ **Generalize** existing variant logic for HPO
- ✅ **Extract** run mode to shared utility
- ✅ **Enhance** existing `trial_finder.py` with MLflow-first
- ✅ **Reuse** fingerprint utilities for benchmark keys

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: HPO Foundation (Run Mode + Variants) ✅          │
├─────────────────────────────────────────────────────────────┤
│ 1.1: Extract run_mode.py utility (replaces 4+ duplicates)  │
│ 1.2: Generalize variants.py (reuse from training.py)       │
│ 1.3: Add run.mode to HPO configs                           │
│ 1.4: Implement HPO variant generation (uses variants.py)   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 1.5: Unified Run Decision Logic ✅                   │
├─────────────────────────────────────────────────────────────┤
│ 1.5.1: Create run_decision.py (should_reuse_existing)      │
│ 1.5.2: Implement get_load_if_exists_flag()                 │
│ 1.5.3: Refactor HPO to use unified logic                    │
│ 1.5.4: Refactor final training to use unified logic        │
│ 1.5.5: Remove redundant fallbacks and duplicate code       │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Deterministic Retrieval (Champion Selection) ⏳  │
├─────────────────────────────────────────────────────────────┤
│ 2.0: Update selection config (centralized, goal→direction) │
│ 2.1: Upgrade study_key_hash to v2 (bound fingerprints)     │
│ 2.2: Extract MLflow query patterns (reuse from mlflow_     │
│      selection.py)                                          │
│ 2.3: Implement select_champion_per_backbone() with all     │
│      safety requirements (config-driven, v1/v2 migration,  │
│      winner's curse, artifact filtering, explicit direction)│
│ 2.4: Update HPO tracking to set new tags                    │
│ 2.5: Update notebooks (explicit champion selection)         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 3: Idempotent Benchmarking (Uses Champions) ⏳      │
├─────────────────────────────────────────────────────────────┤
│ 3.1: Build stable benchmark keys (champion run_id + fps)  │
│ 3.2: Add idempotency check (MLflow + disk)                 │
│ 3.3: Add run mode inheritance (uses run_mode.py)           │
│ 3.4: Update benchmarking to use champions (not variants)  │
│ 3.5: Update notebooks (complete 3-step flow)              │
└─────────────────────────────────────────────────────────────┘
```

## Phase 1: HPO Foundation (Run Mode + Variants)

### Step 1.1: Create Unified Run Mode Utility

**File:** `src/infrastructure/config/run_mode.py` (NEW)

**Purpose:** Single source of truth for run mode extraction (replaces 4+ duplicates)

**Implementation:**
```python
from typing import Literal, Any, Dict

RunMode = Literal["reuse_if_exists", "force_new", "resume_if_incomplete"]

def get_run_mode(config: Dict[str, Any], default: RunMode = "reuse_if_exists") -> RunMode:
    """
    Extract run.mode from configuration with consistent defaults.
    
    Used across all stages:
    - HPO: Controls whether to create new study or reuse existing
    - Final Training: Controls variant creation and checkpoint reuse
    - Best Model Selection: Controls cache reuse
    - Benchmarking: Inherits from HPO
    
    Args:
        config: Configuration dictionary (e.g., from YAML)
        default: Default mode if not specified (default: "reuse_if_exists")
    
    Returns:
        Run mode string: "reuse_if_exists", "force_new", or "resume_if_incomplete"
    """
    return config.get("run", {}).get("mode", default)

def is_force_new(config: Dict[str, Any]) -> bool:
    """Check if run.mode is force_new."""
    return get_run_mode(config) == "force_new"

def is_reuse_if_exists(config: Dict[str, Any]) -> bool:
    """Check if run.mode is reuse_if_exists."""
    return get_run_mode(config) == "reuse_if_exists"
```

**Refactor existing code:**
- `src/evaluation/selection/cache.py:97` → Use `get_run_mode()`
- `src/selection/cache.py:97` → Use `get_run_mode()`
- `src/training/execution/executor.py:190` → Use `get_run_mode()`
- `src/infrastructure/config/training.py:142` → Use `get_run_mode()`

**Tests:** Unit tests for all helper functions

---

### Step 1.2: Generalize Variant Logic (DRY)

**File:** `src/infrastructure/config/variants.py` (NEW - extracted from `training.py`)

**Purpose:** Shared variant computation for both `final_training` and `hpo`

**Implementation:**
```python
from pathlib import Path
from typing import Optional, List
from common.shared.platform_detection import detect_platform
from infrastructure.paths import build_output_path

def compute_next_variant(
    root_dir: Path,
    config_dir: Path,
    process_type: str,  # "final_training" or "hpo"
    model: str,
    spec_fp: Optional[str] = None,  # Required for final_training
    exec_fp: Optional[str] = None,  # Required for final_training
    base_name: Optional[str] = None,  # For HPO: "hpo_distilbert"
) -> int:
    """
    Compute next available variant number for any process type.
    
    Generalizes existing _compute_next_variant() from training.py
    to support both final_training and hpo.
    
    Args:
        process_type: "final_training" or "hpo"
        model: Model backbone name
        spec_fp: Specification fingerprint (final_training only)
        exec_fp: Execution fingerprint (final_training only)
        base_name: Base study name (hpo only, e.g., "hpo_distilbert")
    
    Returns:
        Next available variant number (starts at 1 if none exist)
    """
    existing = find_existing_variants(
        root_dir, config_dir, process_type, model, spec_fp, exec_fp, base_name
    )
    if not existing:
        return 1
    return max(existing) + 1

def find_existing_variants(
    root_dir: Path,
    config_dir: Path,
    process_type: str,
    model: str,
    spec_fp: Optional[str] = None,
    exec_fp: Optional[str] = None,
    base_name: Optional[str] = None,
) -> List[int]:
    """
    Find all existing variant numbers for a process type.
    
    Generalizes existing _find_existing_variant() from training.py.
    """
    if process_type == "final_training":
        # Reuse existing logic from training.py
        from infrastructure.metadata.training import find_by_spec_and_env
        environment = detect_platform()
        entries = find_by_spec_and_env(root_dir, spec_fp, environment, "final_training")
        if entries:
            variants = [e.get("variant", 1) for e in entries if e.get("exec_fp") == exec_fp]
            return variants if variants else []
        # Fallback: scan filesystem
        return _scan_final_training_variants(root_dir, config_dir, spec_fp, exec_fp, model)
    
    elif process_type == "hpo":
        # New logic: scan HPO output directories
        return _scan_hpo_variants(root_dir, config_dir, model, base_name)
    
    return []

def _scan_hpo_variants(
    root_dir: Path,
    config_dir: Path,
    model: str,
    base_name: str,
) -> List[int]:
    """
    Scan HPO output directories for existing variants.
    
    Looks for study folders matching:
    - {base_name} (variant 1, implicit)
    - {base_name}_v1, {base_name}_v2, etc.
    """
    environment = detect_platform()
    model_name = model.split("-")[0] if "-" in model else model
    
    # Build HPO output path
    hpo_output_dir = build_output_path(
        root_dir=root_dir,
        config_dir=config_dir,
        process_type="hpo",
        model=model_name,
        environment=environment,
    )
    
    if not hpo_output_dir.exists():
        return []
    
    variants = []
    for item in hpo_output_dir.iterdir():
        if not item.is_dir():
            continue
        
        folder_name = item.name
        
        # Check for base name (variant 1, implicit)
        if folder_name == base_name:
            variants.append(1)
        # Check for explicit variant suffix (_v1, _v2, etc.)
        elif folder_name.startswith(f"{base_name}_v"):
            try:
                variant_num = int(folder_name.split("_v")[-1])
                variants.append(variant_num)
            except ValueError:
                pass
    
    return sorted(set(variants))

def _scan_final_training_variants(
    root_dir: Path,
    config_dir: Path,
    spec_fp: str,
    exec_fp: str,
    model: str,
) -> List[int]:
    """Reuse existing filesystem scanning logic from training.py."""
    # Copy logic from _find_existing_variant() fallback
    # ... (existing implementation)
```

**Update existing code:**
- `src/infrastructure/config/training.py` → Import from `variants.py`
- Keep backward compatibility (re-export functions)

**Tests:** Unit tests for both process types

---

### Step 1.3: Add Run Mode to HPO Configs

**Files:**
- `config/hpo/smoke.yaml`
- `config/hpo/prod.yaml`

**Changes:**
```yaml
# Run mode configuration (unified behavior control)
run:
  # Run mode determines overall behavior:
  # - reuse_if_exists: Reuse existing study if found (default, respects auto_resume)
  # - force_new: Always create a new study with next variant (v1, v2, v3...)
  mode: force_new  # or reuse_if_exists

checkpoint:
  enabled: true
  # study_name: null  # null = auto-generate base as "hpo_{backbone}" (default)
  #                    # When run.mode=force_new, code will compute next variant (v1, v2, v3...)
  storage_path: "{study_name}/study.db"
  auto_resume: true
  save_only_best: true
```

**Documentation:** Add comments explaining variant behavior

---

### Step 1.4: Implement HPO Variant Generation

**File:** `src/training/hpo/utils/helpers.py`

**Changes:**
```python
from infrastructure.config.run_mode import get_run_mode
from infrastructure.config.variants import compute_next_variant, find_existing_variants

def create_study_name(
    backbone: str,
    run_id: str,
    should_resume: bool,
    checkpoint_config: Optional[Dict[str, Any]] = None,
    hpo_config: Optional[Dict[str, Any]] = None,
    run_mode: Optional[str] = None,
    root_dir: Optional[Path] = None,
    config_dir: Optional[Path] = None,
) -> str:
    """
    Create Optuna study name with variant support (like final training).
    
    When run_mode == "force_new", computes next variant number (v1, v2, v3...).
    When run_mode == "reuse_if_exists", uses base name for resumability.
    
    Uses shared variants.py module (DRY).
    """
    checkpoint_config = checkpoint_config or {}
    hpo_config = hpo_config or {}
    checkpoint_enabled = checkpoint_config.get("enabled", False)
    
    # Get run_mode from config if not provided
    if run_mode is None:
        combined_config = {**hpo_config, **checkpoint_config}
        run_mode = get_run_mode(combined_config)
    
    # Check for custom study_name in checkpoint config first, then HPO config
    study_name_template = checkpoint_config.get("study_name") or hpo_config.get("study_name")
    
    if study_name_template:
        study_name = study_name_template.replace("{backbone}", backbone)
        # If force_new and we have root_dir/config_dir, compute variant
        if run_mode == "force_new" and root_dir and config_dir:
            variant = compute_next_variant(
                root_dir=root_dir,
                config_dir=config_dir,
                process_type="hpo",
                model=backbone,
                base_name=study_name,
            )
            return f"{study_name}_v{variant}" if variant > 1 else study_name
        # If reuse_if_exists, use base name
        return study_name
    
    # Default behavior when no custom study_name is provided
    base_name = f"hpo_{backbone}"
    
    if run_mode == "force_new":
        # Compute next variant when force_new
        if root_dir and config_dir:
            variant = compute_next_variant(
                root_dir=root_dir,
                config_dir=config_dir,
                process_type="hpo",
                model=backbone,
                base_name=base_name,
            )
            return f"{base_name}_v{variant}" if variant > 1 else base_name
        else:
            # Fallback: use run_id if root_dir/config_dir not available
            return f"{base_name}_{run_id}"
    elif checkpoint_enabled or should_resume:
        # Use consistent name for resumability (no variant suffix)
        return base_name
    else:
        # Use unique name for fresh start (only when checkpointing is disabled)
        return f"{base_name}_{run_id}"

def find_study_variants(
    output_dir: Path,
    backbone: str,
) -> List[str]:
    """
    Find all study variants for a given backbone.
    
    Uses shared variants.py module (DRY).
    
    Scans output directory for study folders matching pattern:
    - hpo_{backbone} (variant 1, implicit)
    - hpo_{backbone}_v1, hpo_{backbone}_v2, etc.
    
    Returns:
        List of variant names (study folder names)
    """
    base_name = f"hpo_{backbone}"
    variants = []
    
    if not output_dir.exists():
        return variants
    
    for item in output_dir.iterdir():
        if not item.is_dir():
            continue
        
        folder_name = item.name
        if folder_name == base_name:
            variants.append(base_name)
        elif folder_name.startswith(f"{base_name}_v"):
            variants.append(folder_name)
    
    return sorted(variants)
```

**Update HPO study creation:**
- `src/training/hpo/core/study.py` → Extract `run_mode` using `get_run_mode()`
- Pass `root_dir`, `config_dir`, `run_mode` to `create_study_name()`

**Tests:** Test variant generation (v1, v2, v3) with `force_new`

---

## Phase 2: Deterministic Retrieval (Champion Selection)

### Overview

**Goal**: Select **champion (best configuration group winner) per backbone** with deterministic, safe selection logic.

**Key Concept**: Replace "best variant" terminology with **"champion per backbone"**. Groups runs by `study_key_hash` v2 (comparable configuration groups), then selects the best group and best trial within that group.

**Critical Requirements**:
1. **Bound fingerprints**: `study_key_hash` v2 includes actual `eval_fingerprint` and `data_fingerprint` values (not markers)
2. **No benchmark in HPO grouping**: Benchmark config is separate phase, not in HPO grouping key
3. **Explicit objective direction**: Never assume maximize; include `direction` in key and use in selection
4. **Strict v1/v2 migration**: Prefer v2 when present, fallback to v1, **never mix** versions in same selection
5. **Missing metrics handling**: Exclude NaN/Inf metrics deterministically; log counts
6. **Winner's curse guardrail**: Require `min_trials_per_group` (default 3, configurable)
7. **Artifact availability**: Filter runs without checkpoints before champion selection

### Step 2.0: Update Selection Configuration

**File:** `config/best_model_selection.yaml`

**Purpose:** Centralize Phase 2 champion selection settings in existing config file

**Changes:**
```yaml
# Best Model Selection Configuration
# Controls how the best model is selected from MLflow

# Run mode configuration
run:
  mode: force_new

# Objective metric configuration
objective:
  metric: "macro-f1"
  # MIGRATION: Renamed from "goal" to "direction" for consistency
  # Code will accept both during migration period (warns if "goal" is used)
  direction: "maximize"  # "maximize" or "minimize"

# Champion Selection Configuration (Phase 2)
champion_selection:
  # Winner's curse guardrail: minimum trials per group
  min_trials_per_group: 3
  
  # Stable score computation: median of top-K trials
  # CONSTRAINT: Must be <= min_trials_per_group (enforced in code)
  top_k_for_stable_score: 3
  
  # Artifact availability: require checkpoints before selection
  require_artifact_available: true
  
  # Artifact availability source (authoritative check)
  artifact_check_source: "tag"  # "tag" (uses artifact.available tag) or "disk" (checks filesystem)
  
  # Schema version handling
  prefer_schema_version: "2.0"  # "2.0" or "1.0" or "auto" (auto = prefer v2, fallback to v1)
  
  # CRITICAL: Prevent mixing v1 and v2 runs in same selection
  # If false, v1 and v2 runs are partitioned separately (never compared)
  allow_mixed_schema_groups: false  # Default: false (strict separation)

# Composite scoring configuration (for cross-model ranking AFTER benchmarking)
# NOTE: This is NOT used in Phase 2 champion selection (kept separate)
scoring:
  f1_weight: 0.7
  latency_weight: 0.3
  normalize_weights: true

# Benchmark requirements
benchmark:
  required_metrics:
    - "latency_batch_1_ms"
```

**Migration Helper:**
```python
def get_objective_direction(selection_config: Dict[str, Any]) -> str:
    """
    Get objective direction with migration support for goal→direction.
    
    Accepts both "goal" and "direction" keys during migration period.
    """
    objective = selection_config.get("objective", {})
    
    # Prefer new "direction" key
    if "direction" in objective:
        return objective["direction"]
    
    # Fallback to legacy "goal" key (with warning)
    if "goal" in objective:
        import warnings
        warnings.warn(
            "Using deprecated 'objective.goal' key. "
            "Please update config to use 'objective.direction' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        goal = objective["goal"]
        # Map goal values to direction
        if goal.lower() in ["maximize", "max"]:
            return "maximize"
        elif goal.lower() in ["minimize", "min"]:
            return "minimize"
        else:
            return goal  # Pass through if already correct format
    
    # Default
    return "maximize"
```

**File:** `src/infrastructure/config/selection.py` (NEW)

**Purpose:** Centralized selection config utilities

**Implementation:**
```python
from typing import Dict, Any
import warnings

def get_objective_direction(selection_config: Dict[str, Any]) -> str:
    """
    Get objective direction with migration support for goal→direction.
    
    Accepts both "goal" and "direction" keys during migration period.
    """
    objective = selection_config.get("objective", {})
    
    # Prefer new "direction" key
    if "direction" in objective:
        return objective["direction"]
    
    # Fallback to legacy "goal" key (with warning)
    if "goal" in objective:
        warnings.warn(
            "Using deprecated 'objective.goal' key. "
            "Please update config to use 'objective.direction' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        goal = objective["goal"]
        # Map goal values to direction
        if goal.lower() in ["maximize", "max"]:
            return "maximize"
        elif goal.lower() in ["minimize", "min"]:
            return "minimize"
        else:
            return goal  # Pass through if already correct format
    
    # Default
    return "maximize"

def get_champion_selection_config(selection_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract champion selection config with defaults and constraint validation.
    
    Returns validated config with constraints enforced (e.g., top_k <= min_trials).
    """
    champion_config = selection_config.get("champion_selection", {})
    
    min_trials = champion_config.get("min_trials_per_group", 3)
    top_k = champion_config.get("top_k_for_stable_score", 3)
    
    # ENFORCE CONSTRAINT: top_k <= min_trials
    if top_k > min_trials:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"top_k_for_stable_score ({top_k}) > min_trials_per_group ({min_trials}). "
            f"Clamping top_k to {min_trials}."
        )
        top_k = min_trials
    
    return {
        "min_trials_per_group": min_trials,
        "top_k_for_stable_score": top_k,
        "require_artifact_available": champion_config.get("require_artifact_available", True),
        "artifact_check_source": champion_config.get("artifact_check_source", "tag"),
        "prefer_schema_version": champion_config.get("prefer_schema_version", "auto"),
        "allow_mixed_schema_groups": champion_config.get("allow_mixed_schema_groups", False),
    }
```

**Tests:** Test migration path (goal→direction), config validation, constraint enforcement

---

### Step 2.1: Upgrade study_key_hash to v2 (Bound Fingerprints)

**File:** `src/infrastructure/naming/mlflow/hpo_keys.py`

**Purpose:** Extend `study_key_hash` to v2 schema with bound fingerprints and explicit direction

**Implementation:**
```python
def build_hpo_study_key_v2(
    data_config: Dict[str, Any],
    hpo_config: Dict[str, Any],
    train_config: Dict[str, Any],
    model: str,
    *,
    data_fingerprint: str,  # REQUIRED - actual value, not marker
    eval_fingerprint: str,  # REQUIRED - actual value, not marker
    include_code_version: bool = False,
) -> str:
    """
    Build study_key_hash v2 with bound fingerprints.
    
    CRITICAL: Fingerprints are actual values in the key, not markers.
    This prevents grouping runs with different eval/data configs.
    
    Changes from v1:
    - Removed local_path (too fragile, use data_fingerprint tag instead)
    - Added train_budget (max_steps/epochs) to prevent winner's curse
    - Added seed_policy
    - Bound eval_fingerprint and data_fingerprint (actual values)
    - Explicit objective direction (never assume maximize)
    - NO benchmark config (that's separate phase)
    """
    # Data identity (no local_path, fingerprints bound)
    data_key = {
        "name": data_config.get("name", ""),
        "version": data_config.get("version", ""),
        "schema": data_config.get("schema", {}),
        "split_seed": data_config.get("split_seed", "default"),
        "label_mapping": data_config.get("label_mapping", {}),
        "data_fingerprint": data_fingerprint,  # BOUND - actual value
    }
    
    # HPO config (explicit direction, NO benchmark)
    objective = hpo_config.get("objective", {})
    hpo_key = {
        "search_space": hpo_config.get("search_space", {}),
        "objective": {
            "metric": objective.get("metric", "macro-f1"),
            "direction": objective.get("direction", "maximize"),  # EXPLICIT
        },
        "k_fold": hpo_config.get("k_fold", {}),
        "sampling": {
            "algorithm": hpo_config.get("sampling", {}).get("algorithm", "random"),
        },
        "early_termination": hpo_config.get("early_termination", {}),
    }
    
    # Training budget (prevents winner's curse)
    train_key = {
        "max_steps": train_config.get("max_steps"),
        "num_epochs": train_config.get("num_epochs"),
        "seed_policy": train_config.get("seed_policy", "default"),
    }
    
    payload = {
        "schema_version": "2.0",
        "data": data_key,
        "hpo": hpo_key,
        "training": train_key,
        "evaluation": {
            "eval_fingerprint": eval_fingerprint,  # BOUND - actual value
        },
        "model": model.lower().strip(),
        # NO benchmark config - that's separate phase
    }
    
    if include_code_version:
        payload["code_version"] = get_git_commit_hash()
    
    return json.dumps(payload, sort_keys=True, separators=(',', ':'))
```

**Add fingerprint computation:**
```python
def compute_data_fingerprint(data_config: Dict[str, Any]) -> str:
    """
    Compute data fingerprint (content-based if available, semantic fallback).
    
    Priority:
    1. content_hash or manifest_hash (if available) - pure content identity
    2. Semantic fields (name/version/split_seed/etc) - fallback
    
    Note: If using semantic fallback, there's overlap with study_key_hash v2
    data_key fields. This is acceptable - fingerprint is for filtering/tagging,
    study_key_hash is for grouping. Both serve different purposes.
    """
    # Prefer content-based identity
    content_hash = data_config.get("content_hash") or data_config.get("manifest_hash")
    if content_hash:
        return _compute_hash_64(str(content_hash))
    
    # Fallback: semantic identity
    fallback_payload = {
        "name": data_config.get("name"),
        "version": data_config.get("version"),
        "split_seed": data_config.get("split_seed"),
        "label_mapping": data_config.get("label_mapping", {}),
        "schema": data_config.get("schema", {}),
    }
    return _compute_hash_64(json.dumps(fallback_payload, sort_keys=True))

def compute_eval_fingerprint(eval_config: Dict[str, Any]) -> str:
    """
    Compute evaluation fingerprint (content-based, not script name).
    
    Hashes: evaluator_version + metric_spec + thresholding + full_eval_config
    NOT: script filename (too fragile)
    """
    fingerprint_payload = {
        "evaluator_version": eval_config.get("evaluator_version", "default"),
        "metric_spec": eval_config.get("metric", {}),
        "thresholding": eval_config.get("thresholding", {}),
        "full_eval_config": eval_config,  # if stable serialization exists
    }
    return _compute_hash_64(json.dumps(fingerprint_payload, sort_keys=True))
```

**Update TagsRegistry:**
- Add `fingerprint.data` and `fingerprint.eval` tags
- Add `study.key_schema_version` tag
- Add `artifact.available` tag
- Add `objective.direction` tag

**Tests:** Test v2 key generation, fingerprint computation, backward compatibility

---

### Step 2.2: Extract MLflow Query Patterns (DRY)

**File:** `src/infrastructure/tracking/mlflow/queries.py` (NEW)

**Purpose:** Extract common MLflow query patterns from `mlflow_selection.py`

**Implementation:**
```python
from mlflow.tracking import MlflowClient
from typing import List, Optional, Dict, Any, Tuple

def query_runs_by_tags(
    client: MlflowClient,
    experiment_ids: List[str],
    required_tags: Dict[str, str],
    filter_string: str = "",
    max_results: int = 1000,
) -> List[Any]:
    """
    Query MLflow runs filtered by required tags.
    
    Reuses pattern from mlflow_selection.py.
    
    Args:
        client: MLflow client
        experiment_ids: List of experiment IDs to query
        required_tags: Dict of tag_key -> tag_value to filter by
        filter_string: Additional MLflow filter string
        max_results: Maximum number of results
    
    Returns:
        List of runs matching criteria
    """
    all_runs = client.search_runs(
        experiment_ids=experiment_ids,
        filter_string=filter_string,
        max_results=max_results,
    )
    
    # Filter for finished runs
    finished_runs = [r for r in all_runs if r.info.status == "FINISHED"]
    
    # Filter by required tags
    valid_runs = []
    for run in finished_runs:
        has_all_tags = all(
            run.data.tags.get(tag_key) == tag_value
            for tag_key, tag_value in required_tags.items()
        )
        if has_all_tags:
            valid_runs.append(run)
    
    return valid_runs

def find_best_run_by_metric(
    runs: List[Any],
    metric_name: str,
    maximize: bool = True,
) -> Optional[Any]:
    """
    Select best run by metric value.
    
    Args:
        runs: List of MLflow runs
        metric_name: Name of metric to optimize
        maximize: True to maximize, False to minimize
    
    Returns:
        Best run or None if no runs have metric
    """
    runs_with_metric = [
        r for r in runs
        if metric_name in r.data.metrics
    ]
    
    if not runs_with_metric:
        return None
    
    if maximize:
        return max(runs_with_metric, key=lambda r: r.data.metrics[metric_name])
    else:
        return min(runs_with_metric, key=lambda r: r.data.metrics[metric_name])

def group_runs_by_variant(
    runs: List[Any],
    variant_tag: str = "code.variant",
) -> Dict[str, List[Any]]:
    """
    Group runs by variant tag.
    
    Args:
        runs: List of MLflow runs
        variant_tag: Tag key for variant (default: "code.variant")
    
    Returns:
        Dict mapping variant -> list of runs
    """
    grouped = {}
    for run in runs:
        variant = run.data.tags.get(variant_tag, "default")
        if variant not in grouped:
            grouped[variant] = []
        grouped[variant].append(run)
    return grouped
```

**Update existing code:**
- `src/evaluation/selection/mlflow_selection.py` → Use `queries.py` utilities
- Keep backward compatibility

**Tests:** Unit tests for query utilities

---

### Step 2.3: Implement Champion Selection (MLflow-First)

**File:** `src/evaluation/selection/trial_finder.py`

**Changes:** Implement `select_champion_per_backbone()` with all safety requirements and config-driven parameters

**Implementation:**
```python
from infrastructure.tracking.mlflow.queries import (
    query_runs_by_tags,
    find_best_run_by_metric,
)
from infrastructure.naming.mlflow.tags_registry import TagsRegistry
from infrastructure.config.selection import (
    get_objective_direction,
    get_champion_selection_config,
)
from common.shared.logging_utils import get_logger
import math
import numpy as np

def select_champion_per_backbone(
    backbone: str,
    hpo_experiment: Dict[str, str],
    selection_config: Dict[str, Any],
    mlflow_client: MlflowClient,
) -> Optional[Dict[str, Any]]:
    """
    Select champion (best configuration group winner) per backbone.
    
    Groups runs by study_key_hash v2 (comparable configuration groups),
    then selects best group and best trial within that group.
    
    All parameters come from selection_config (centralized config).
    
    Requirements enforced:
    1. Bound fingerprints in study_key_hash v2
    2. Never mix v1 and v2 runs in same selection (config-driven)
    3. Explicit objective direction (never assume max, with migration support)
    4. Handle missing/NaN metrics deterministically
    5. Minimum trial count guardrail (config-driven)
    6. Artifact availability constraint (config-driven source)
    7. Deterministic constraints (top_k <= min_trials)
    
    Returns:
        {
            "backbone": "distilbert",
            "champion": {
                "run_id": "...",  # PRIMARY: MLflow handle
                "trial_key_hash": "...",  # Optional: for display
                "metric": 0.87,
                "stable_score": 0.86,
                "study_key_hash": "abc123...",
                "schema_version": "2.0",
                "checkpoint_path": Path(...),
            },
            "all_groups": {...},
            "selection_metadata": {...},
        }
    """
    logger = get_logger(__name__)
    
    # Extract config values with defaults and constraint validation
    champion_config = get_champion_selection_config(selection_config)
    min_trials_per_group = champion_config["min_trials_per_group"]
    top_k_for_stable_score = champion_config["top_k_for_stable_score"]
    require_artifact_available = champion_config["require_artifact_available"]
    artifact_check_source = champion_config["artifact_check_source"]
    allow_mixed_schema_groups = champion_config["allow_mixed_schema_groups"]
    prefer_schema_version = champion_config["prefer_schema_version"]
    
    # Get objective direction (with migration support)
    objective_metric = selection_config.get("objective", {}).get("metric", "macro-f1")
    objective_direction = get_objective_direction(selection_config)  # Uses migration helper
    maximize = objective_direction.lower() == "maximize"
    
    tags_registry = TagsRegistry.load_default()
    backbone_tag = tags_registry.key("process", "backbone")
    stage_tag = tags_registry.key("process", "stage")
    study_key_tag = tags_registry.key("grouping", "study_key_hash")
    trial_key_tag = tags_registry.key("grouping", "trial_key_hash")
    schema_version_tag = tags_registry.key("study", "key_schema_version")
    artifact_tag = tags_registry.key("artifact", "available")
    
    backbone_name = backbone.split("-")[0] if "-" in backbone else backbone
    
    # Step 1: Filter runs
    required_tags = {
        backbone_tag: backbone_name,
        stage_tag: "hpo_trial",
    }
    
    runs = query_runs_by_tags(
        client=mlflow_client,
        experiment_ids=[hpo_experiment["id"]],
        required_tags=required_tags,
        max_results=1000,
    )
    
    # Step 2: Artifact availability filter (config-driven source)
    if require_artifact_available:
        runs = _filter_by_artifact_availability(
            runs, artifact_check_source, artifact_tag, logger
        )
    
    # Step 3: Partition by study_key_hash AND schema version
    # CRITICAL: Never mix v1 and v2 runs if allow_mixed_schema_groups is False
    groups_v1 = {}  # v1 runs
    groups_v2 = {}  # v2 runs
    
    for run in runs:
        study_key_hash = run.data.tags.get(study_key_tag)
        if not study_key_hash:
            continue  # Skip runs without grouping tag
        
        # Check schema version (default to "1.0" if missing for backward compat)
        schema_version = run.data.tags.get(schema_version_tag, "1.0")
        
        # Partition by version (NEVER MIX if allow_mixed_schema_groups is False)
        if schema_version == "2.0":
            if study_key_hash not in groups_v2:
                groups_v2[study_key_hash] = []
            groups_v2[study_key_hash].append(run)
        else:
            # v1 or missing version
            if study_key_hash not in groups_v1:
                groups_v1[study_key_hash] = []
            groups_v1[study_key_hash].append(run)
    
    # Step 4: Select groups based on prefer_schema_version and allow_mixed_schema_groups
    if allow_mixed_schema_groups:
        # WARNING: This is dangerous - only allow if explicitly enabled
        logger.warning(
            f"allow_mixed_schema_groups=True is enabled for {backbone}. "
            f"This may compare non-comparable runs. Use with caution."
        )
        # Merge groups (dangerous but allowed)
        groups_to_use = {**groups_v1, **groups_v2}
        schema_version_used = "mixed"
    else:
        # Safe: Prefer v2, fallback to v1 (never mix)
        if prefer_schema_version == "2.0" or (prefer_schema_version == "auto" and groups_v2):
            groups_to_use = groups_v2
            schema_version_used = "2.0"
        elif prefer_schema_version == "1.0" or (prefer_schema_version == "auto" and not groups_v2):
            groups_to_use = groups_v1
            schema_version_used = "1.0"
        else:
            groups_to_use = groups_v2 if groups_v2 else groups_v1
            schema_version_used = "2.0" if groups_v2 else "1.0"
    
    if not groups_to_use:
        logger.warning(f"No valid groups found for {backbone}")
        return None
    
    # Log version usage
    if groups_v1 and groups_v2 and not allow_mixed_schema_groups:
        logger.info(
            f"Found both v1 and v2 runs for {backbone}. "
            f"Using {schema_version_used} groups only (never mixing versions)."
        )
    
    # Step 5: Compute stable score per group (with all guards)
    group_scores = {}
    
    for study_key_hash, group_runs in groups_to_use.items():
        # Extract metrics (handle missing/NaN deterministically)
        run_metrics = []
        valid_count = 0
        invalid_count = 0
        
        for run in group_runs:
            if objective_metric not in run.data.metrics:
                invalid_count += 1
                continue
            
            metric_value = run.data.metrics[objective_metric]
            
            # Handle NaN/Inf deterministically
            if not isinstance(metric_value, (int, float)) or not math.isfinite(metric_value):
                invalid_count += 1
                continue
            
            valid_count += 1
            run_metrics.append((run.info.run_id, metric_value))
        
        # Log metric validity
        if invalid_count > 0:
            logger.debug(
                f"Group {study_key_hash[:16]}...: "
                f"{valid_count} valid metrics, {invalid_count} missing/invalid"
            )
        
        # Winner's curse guardrail: require minimum trials
        if len(run_metrics) < min_trials_per_group:
            logger.warning(
                f"Skipping group {study_key_hash[:16]}... - "
                f"only {len(run_metrics)} valid trials (minimum: {min_trials_per_group})"
            )
            continue
        
        # Extract metrics for scoring
        metrics = [m for _, m in run_metrics]
        
        # Best metric (for champion selection within group)
        best_metric = max(metrics) if maximize else min(metrics)
        
        # Stable score: median of top-K (reduces flukes)
        # CONSTRAINT: top_k is already clamped to <= min_trials_per_group in config helper
        top_k = min(top_k_for_stable_score, len(metrics))
        sorted_metrics = sorted(metrics, reverse=maximize)
        stable_score = np.median(sorted_metrics[:top_k]) if top_k > 0 else 0
        
        group_scores[study_key_hash] = {
            "stable_score": stable_score,
            "best_metric": best_metric,
            "n_trials": len(run_metrics),
            "n_valid": valid_count,
            "n_invalid": invalid_count,
            "run_metrics": run_metrics,  # Lightweight: (run_id, metric) tuples
        }
    
    if not group_scores:
        logger.warning(f"No eligible groups for {backbone} (all below min_trials threshold)")
        return None
    
    # Step 6: Select winning group (by stable_score, respecting direction)
    if maximize:
        winning_key = max(group_scores.items(), key=lambda x: x[1]["stable_score"])[0]
    else:
        winning_key = min(group_scores.items(), key=lambda x: x[1]["stable_score"])[0]
    
    winning_group = group_scores[winning_key]
    
    # Step 7: Select champion within winning group (by best_metric, respecting direction)
    if maximize:
        champion_run_id, champion_metric = max(
            winning_group["run_metrics"],
            key=lambda x: x[1]
        )
    else:
        champion_run_id, champion_metric = min(
            winning_group["run_metrics"],
            key=lambda x: x[1]
        )
    
    # Fetch full run only when needed
    champion_run = mlflow_client.get_run(champion_run_id)
    champion_trial_key = champion_run.data.tags.get(trial_key_tag)
    
    return {
        "backbone": backbone,
        "champion": {
            "run_id": champion_run_id,  # PRIMARY: MLflow handle
            "trial_key_hash": champion_trial_key,  # Optional: for display
            "metric": champion_metric,
            "stable_score": winning_group["stable_score"],
            "study_key_hash": winning_key,
            "schema_version": schema_version_used,  # Track which version was used
            "checkpoint_path": _get_checkpoint_path_from_run(champion_run),
        },
        "all_groups": {
            k: {
                "best_metric": v["best_metric"],
                "stable_score": v["stable_score"],
                "n_trials": v["n_trials"],
                "n_valid": v["n_valid"],
                "n_invalid": v["n_invalid"],
            }
            for k, v in group_scores.items()
        },
        "selection_metadata": {
            "objective_direction": objective_direction,
            "min_trials_required": min_trials_per_group,
            "top_k_for_stable": top_k_for_stable_score,
            "artifact_required": require_artifact_available,
            "artifact_check_source": artifact_check_source,
            "allow_mixed_schema_groups": allow_mixed_schema_groups,
            "schema_version_used": schema_version_used,
        },
    }

def _filter_by_artifact_availability(
    runs: List[Any],
    check_source: str,
    artifact_tag: str,
    logger,
) -> List[Any]:
    """
    Filter runs by artifact availability using config-specified source.
    
    Args:
        check_source: "tag" (uses MLflow tag) or "disk" (checks filesystem)
        artifact_tag: Tag key for artifact availability
        logger: Logger instance
    """
    if check_source == "tag":
        # Use MLflow tag as authoritative source
        return [
            r for r in runs
            if r.data.tags.get(artifact_tag, "false").lower() == "true"
        ]
    elif check_source == "disk":
        # Fallback: check filesystem (requires run_id -> path mapping)
        # This is a fallback - tag should be primary
        logger.warning(
            "Using disk-based artifact check (fallback). "
            "Consider using 'tag' source for better performance."
        )
        # Implementation would check checkpoint files exist
        # For now, return all runs (disk check would need run_id -> path logic)
        return runs
    else:
        logger.error(f"Unknown artifact_check_source: {check_source}. Using tag-based check.")
        return [
            r for r in runs
            if r.data.tags.get(artifact_tag, "false").lower() == "true"
        ]

def select_champions_for_backbones(
    backbone_values: List[str],
    hpo_experiments: Dict[str, Dict[str, str]],  # backbone -> {name, id}
    selection_config: Dict[str, Any],
    mlflow_client: MlflowClient,
    **kwargs,  # Pass through to select_champion_per_backbone
) -> Dict[str, Dict[str, Any]]:
    """
    Select champions for multiple backbones.
    
    Wrapper around select_champion_per_backbone() for multiple backbones.
    """
    champions = {}
    for backbone in backbone_values:
        if backbone not in hpo_experiments:
            logger.warning(f"No HPO experiment found for {backbone}, skipping")
            continue
        
        champion = select_champion_per_backbone(
            backbone=backbone,
            hpo_experiment=hpo_experiments[backbone],
            selection_config=selection_config,
            mlflow_client=mlflow_client,
            **kwargs,
        )
        if champion:
            champions[backbone] = champion
    
    return champions

# Keep existing function for backward compatibility
def find_best_trials_for_backbones(
    backbone_values: list[str],
    hpo_studies: Optional[Dict[str, Any]],
    hpo_config: Dict[str, Any],
    data_config: Dict[str, Any],
    root_dir: Path,
    environment: str,
) -> Dict[str, Dict[str, Any]]:
    """
    Find best trials for multiple backbones (backward compatibility).
    
    DEPRECATED: Use select_champions_for_backbones() instead.
    This function now calls select_champions_for_backbones() internally.
    """
    import warnings
    warnings.warn(
        "find_best_trials_for_backbones() is deprecated. Use select_champions_for_backbones() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Convert to new format and call
    from mlflow.tracking import MlflowClient
    mlflow_client = MlflowClient()
    
    # Build hpo_experiments dict (empty for now - will need to be passed)
    hpo_experiments = {}
    
    selection_config = {
        "objective": {
            "metric": hpo_config.get("objective", {}).get("metric", "macro-f1"),
            "direction": hpo_config.get("objective", {}).get("direction", "maximize"),
        }
    }
    
    champions = select_champions_for_backbones(
        backbone_values=backbone_values,
        hpo_experiments=hpo_experiments,
        selection_config=selection_config,
        mlflow_client=mlflow_client,
    )
    
    # Convert back to old format for backward compatibility
    result = {}
    for backbone, champion_data in champions.items():
        champion = champion_data["champion"]
        result[backbone] = {
            "trial_id": champion.get("trial_key_hash", "unknown"),
            "run_id": champion["run_id"],
            "accuracy": champion["metric"],
            "source": "mlflow",
        }
    
    return result
```

**Tests:** 
- Test config-driven parameters
- Test goal→direction migration
- Test allow_mixed_schema_groups=False (strict separation)
- Test top_k clamping when > min_trials
- Test artifact_check_source (tag vs disk)
- Test prefer_schema_version logic
- Test champion selection with v2 groups
- Test v1/v2 migration (never mix)
- Test missing/NaN metrics handling
- Test minimum trial count guardrail
- Test artifact availability filtering
- Test explicit direction (maximize/minimize)
- Test stable score computation

---

### Step 2.4: Update HPO Tracking to Set New Tags

**File:** `src/training/hpo/tracking/setup.py`

**Changes:** Set new tags when creating HPO runs:
- `code.study.key_schema_version = "2.0"` (or "1.0" for backward compat)
- `code.fingerprint.data = data_fingerprint`
- `code.fingerprint.eval = eval_fingerprint`
- `code.artifact.available = "true"` (after checkpoint is saved)
- `code.objective.direction = "maximize"` or `"minimize"`

**Implementation:**
```python
# In setup_hpo_mlflow_run() or similar
from infrastructure.naming.mlflow.hpo_keys import (
    build_hpo_study_key_v2,
    compute_data_fingerprint,
    compute_eval_fingerprint,
)

# Compute fingerprints
data_fp = compute_data_fingerprint(data_config)
eval_fp = compute_eval_fingerprint(eval_config)

# Build v2 study key
study_key_v2 = build_hpo_study_key_v2(
    data_config=data_config,
    hpo_config=hpo_config,
    train_config=train_config,
    model=backbone,
    data_fingerprint=data_fp,
    eval_fingerprint=eval_fp,
)
study_key_hash_v2 = build_hpo_study_key_hash(study_key_v2)

# Set tags
tags = {
    tags_registry.key("grouping", "study_key_hash"): study_key_hash_v2,
    tags_registry.key("study", "key_schema_version"): "2.0",
    tags_registry.key("fingerprint", "data"): data_fp,
    tags_registry.key("fingerprint", "eval"): eval_fp,
    tags_registry.key("objective", "direction"): hpo_config.get("objective", {}).get("direction", "maximize"),
    tags_registry.key("artifact", "available"): "false",  # Will be updated after checkpoint save
}
```

---

### Step 2.5: Update Notebooks (Explicit Champion Selection)

**File:** `notebooks/01_orchestrate_training_colab.ipynb`

**Changes:** Add explicit champion selection step before benchmarking

```python
# Step 1: Explicit Champion Selection (NEW)
# Load selection config (includes champion_selection settings)
selection_config = load_yaml(CONFIG_DIR / "best_model_selection.yaml")

print("🏆 Selecting champions per backbone...")
champions = select_champions_for_backbones(
    backbone_values=backbone_values,
    hpo_experiments=hpo_experiments,
    selection_config=selection_config,  # All settings come from config
    mlflow_client=mlflow_client,
    # No manual overrides - all from config.champion_selection
)

# Print champion selection results table
print("\n✓ Champions Selected:")
print(f"{'Backbone':<15} {'Run ID':<40} {'Metric':<10} {'Stable Score':<12} {'Schema':<8} {'Groups':<8}")
print("-" * 105)
for backbone, champion_data in champions.items():
    champ = champion_data["champion"]
    groups = champion_data["all_groups"]
    print(f"{backbone:<15} {champ['run_id']:<40} "
          f"{champ['metric']:<10.4f} {champ['stable_score']:<12.4f} "
          f"{champ['schema_version']:<8} {len(groups):<8}")

# Extract champions for benchmarking
champion_runs = {
    backbone: champ_data["champion"]
    for backbone, champ_data in champions.items()
}
```

---

## Phase 3: Idempotent Benchmarking (Uses Champions)

### Overview

**Goal**: Benchmark only the **champions** (best configuration group winners) selected in Phase 2, with idempotency to skip already-benchmarked runs.

**Key Concept**: Use champions from Phase 2 (not all variants). Each champion represents the best trial from the best configuration group for that backbone.

### Step 3.1: Build Stable Benchmark Keys (Reuse Fingerprints)

**File:** `src/evaluation/benchmarking/orchestrator.py`

**Implementation:**
```python
from infrastructure.fingerprints import compute_config_hash
import hashlib
import json

def build_benchmark_key(
    champion_run_id: str,  # MLflow run_id of champion
    data_fingerprint: str,  # From Phase 2
    eval_fingerprint: str,  # From Phase 2
    benchmark_config: Dict[str, Any],
) -> str:
    """
    Build stable benchmark identity key.
    
    Reuses fingerprints from Phase 2 (DRY).
    
    Key format: {champion_run_id}:{data_fp}:{eval_fp}:{bench_fp}
    
    Note: Uses champion_run_id (MLflow handle) as primary identifier.
    This ensures idempotency even if trial_key_hash changes.
    """
    # Benchmark config hash (reuse existing utility)
    bench_fp = compute_config_hash(benchmark_config)
    
    # Build key using champion run_id and fingerprints from Phase 2
    key = f"{champion_run_id}:{data_fingerprint}:{eval_fingerprint}:{bench_fp}"
    
    return key

def _compute_data_fingerprint(data_config: Dict[str, Any]) -> str:
    """Compute data fingerprint (version + config hash, excludes local_path)."""
    # Exclude local_path (environment-specific)
    config_copy = {k: v for k, v in data_config.items() if k != "local_path"}
    
    # Normalize and hash
    normalized = json.dumps(config_copy, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]
```

---

### Step 3.2: Add Idempotency Check

**File:** `src/evaluation/benchmarking/orchestrator.py`

**Implementation:**
```python
def filter_missing_benchmarks(
    champions: Dict[str, Dict[str, Any]],  # From Phase 2 champion selection
    benchmark_experiment: Dict[str, str],
    benchmark_config: Dict[str, Any],
    data_fingerprint: str,  # From Phase 2
    eval_fingerprint: str,  # From Phase 2
    root_dir: Path,
    environment: str,
    mlflow_client: Optional[MlflowClient] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Filter out champions that already have benchmarks.
    
    Uses stable benchmark_key to check:
    - MLflow: existing benchmark run with matching key tag
    - Disk: cached benchmark_{key}.json
    """
    if mlflow_client is None:
        from mlflow.tracking import MlflowClient
        mlflow_client = MlflowClient()
    
    champions_to_benchmark = {}
    
    for backbone, champion_data in champions.items():
        champion = champion_data["champion"]
        champion_run_id = champion["run_id"]
        
        # Build stable key using champion run_id and fingerprints
        benchmark_key = build_benchmark_key(
            champion_run_id=champion_run_id,
            data_fingerprint=data_fingerprint,
            eval_fingerprint=eval_fingerprint,
            benchmark_config=benchmark_config,
        )
        
        # Check if benchmark exists
        if benchmark_already_exists(
            benchmark_key, benchmark_experiment, root_dir, environment, mlflow_client
        ):
            logger.info(f"Skipping {backbone} - benchmark already exists (key: {benchmark_key[:32]}...)")
            continue
        
        champions_to_benchmark[backbone] = champion_data
    
    return champions_to_benchmark

def benchmark_already_exists(
    benchmark_key: str,
    benchmark_experiment: Dict[str, str],
    root_dir: Path,
    environment: str,
    mlflow_client: Optional[MlflowClient] = None,
) -> bool:
    """Check if benchmark exists (MLflow or disk)."""
    # Check MLflow first (authoritative)
    if mlflow_client:
        if _benchmark_exists_in_mlflow(benchmark_key, benchmark_experiment, mlflow_client):
            return True
    
    # Fallback to disk
    if _benchmark_exists_on_disk(benchmark_key, root_dir, environment):
        return True
    
    return False

def _benchmark_exists_in_mlflow(
    benchmark_key: str,
    benchmark_experiment: Dict[str, str],
    mlflow_client: MlflowClient,
) -> bool:
    """Check if benchmark run exists in MLflow with matching key."""
    runs = mlflow_client.search_runs(
        experiment_ids=[benchmark_experiment["id"]],
        filter_string=f"tags.benchmark_key = '{benchmark_key}'",
        max_results=1,
    )
    
    return len(runs) > 0 and runs[0].info.status == "FINISHED"

def _benchmark_exists_on_disk(
    benchmark_key: str,
    root_dir: Path,
    environment: str,
) -> Optional[Path]:
    """Check if benchmark file exists on disk."""
    cache_dir = root_dir / "outputs" / "benchmarking" / environment / "cache"
    benchmark_file = cache_dir / f"benchmark_{benchmark_key}.json"
    
    return benchmark_file if benchmark_file.exists() else None
```

---

### Step 3.3: Add Run Mode Inheritance

**File:** `src/evaluation/benchmarking/orchestrator.py`

**Implementation:**
```python
from infrastructure.config.run_mode import get_run_mode

def get_benchmark_run_mode(
    benchmark_config: Dict[str, Any],
    hpo_config: Dict[str, Any],
) -> str:
    """
    Get benchmark run mode (inherits from HPO if null).
    
    Uses shared run_mode.py utility (DRY).
    """
    # Get run mode from benchmark config (null = inherit from HPO)
    benchmark_run_mode = benchmark_config.get("run", {}).get("mode")
    
    if benchmark_run_mode is None:
        # Inherit from HPO config
        hpo_run_mode = get_run_mode(hpo_config, default="reuse_if_exists")
        return hpo_run_mode
    
    return get_run_mode(benchmark_config)
```

**Update config:** `config/benchmark.yaml`
```yaml
# Run mode configuration (inherits from HPO if null)
run:
  # Run mode determines overall behavior:
  # - null: Inherit from HPO config (default behavior)
  # - reuse_if_exists: Reuse existing benchmark results if found
  # - force_new: Always create new benchmark run (ignores existing)
  mode: null  # null = inherit from HPO config
```

---

### Step 3.4: Update Benchmarking to Use Champions

**File:** `src/evaluation/benchmarking/orchestrator.py`

**Changes:** Update `benchmark_best_trials()` to accept champions from Phase 2

**Note:** The variant completeness check from original plan is replaced by champion selection in Phase 2. We benchmark champions, not all variants.

**Implementation:**
```python
def benchmark_champions(
    champions: Dict[str, Dict[str, Any]],  # From Phase 2
    test_data_path: Path,
    root_dir: Path,
    environment: str,
    data_config: dict,
    hpo_config: dict,
    benchmark_config: Optional[dict] = None,
    mlflow_client: Optional[MlflowClient] = None,
) -> Dict[str, Path]:
    """
    Benchmark champions selected in Phase 2.
    
    Each champion represents the best trial from the best configuration group
    for that backbone. We only benchmark champions, not all variants.
    """
    from common.shared.platform_detection import detect_platform
    from infrastructure.paths import build_output_path
    
    # Get benchmark strategy
    benchmark_all = benchmark_config.get("benchmark_all_variants", True)
    strategy = benchmark_config.get("benchmark_strategy", "best_per_variant")
    
    if not benchmark_all or strategy == "latest_only":
        return []
    
    # Find all study variants for this backbone
    environment = detect_platform()
    hpo_output_dir = build_output_path(
        root_dir=root_dir,
        config_dir=config_dir,
        process_type="hpo",
        model=backbone,
        environment=environment,
    )
    
    # Scan for all variants (uses shared find_study_variants)
    variants = find_study_variants(hpo_output_dir, backbone)
    
    if not variants:
        return []
    
    # Get run mode (inherited from HPO)
    hpo_run_mode = get_run_mode(hpo_config, default="reuse_if_exists")
    benchmark_run_mode = get_benchmark_run_mode(benchmark_config, hpo_config)
    
    benchmarked_variants = []
    
    for variant_name in variants:
        # Find best trial in this variant
        best_trial = _find_best_trial_in_variant(
            root_dir, config_dir, backbone, variant_name, hpo_config, data_config
        )
        
        if not best_trial:
            continue
        
        # Check if this best trial has been benchmarked
        benchmark_exists = benchmark_already_exists(
            build_benchmark_key(...),  # Build key for this trial
            benchmark_experiment,
            root_dir,
            environment,
            mlflow_client,
        )
        
        if not benchmark_exists:
            # Benchmark missing variant's best trial
            if benchmark_run_mode == "force_new" or not benchmark_exists:
                logger.info(f"Benchmarking best trial from variant: {variant_name}")
                # Call benchmark_best_trials() for this variant
                benchmarked_variants.append(variant_name)
        else:
            benchmarked_variants.append(variant_name)
    
    return benchmarked_variants
```

---

### Step 3.5: Update Notebooks (Complete Flow)

**File:** `notebooks/01_orchestrate_training_colab.ipynb`

**Changes:** Complete 3-step flow using champions

---

```python
# Step 1: Explicit Champion Selection (Phase 2)
print("🏆 Selecting champions per backbone...")
champions = select_champions_for_backbones(
    backbone_values=backbone_values,
    hpo_experiments=hpo_experiments,
    selection_config=selection_config,
    mlflow_client=mlflow_client,
    min_trials_per_group=3,
    require_artifact_available=True,
)

# Extract fingerprints for benchmark key building
data_fp = compute_data_fingerprint(data_config)
eval_fp = compute_eval_fingerprint(eval_config)

# Step 2: Filter Missing Benchmarks
champions_to_benchmark = filter_missing_benchmarks(
    champions=champions,
    benchmark_experiment=benchmark_experiment,
    benchmark_config=benchmark_config,
    data_fingerprint=data_fp,
    eval_fingerprint=eval_fp,
    root_dir=ROOT_DIR,
    environment=environment,
    mlflow_client=mlflow_client,
)

skipped_count = len(champions) - len(champions_to_benchmark)
if skipped_count > 0:
    print(f"⏭️  Skipping {skipped_count} already-benchmarked champion(s)")

# Step 3: Benchmark Only Missing Champions
if champions_to_benchmark:
    benchmark_results = benchmark_champions(
        champions=champions_to_benchmark,  # Only missing ones
        test_data_path=test_data_path,
        root_dir=ROOT_DIR,
        environment=environment,
        data_config=data_config,
        hpo_config=hpo_config,
        benchmark_config=benchmark_config,
        mlflow_client=mlflow_client,
    )
else:
    print("✓ All champions already benchmarked - nothing to do!")
```

---

## Implementation Plan Summary

### Phase 1: HPO Foundation (Week 1)
- ✅ Step 1.1: Create `run_mode.py` utility
- ✅ Step 1.2: Generalize `variants.py` module
- ✅ Step 1.3: Add run.mode to HPO configs
- ✅ Step 1.4: Implement HPO variant generation

### Phase 1.5: Unified Run Decision Logic (Completed)
- ✅ Step 1.5.1: Create `run_decision.py` module with `should_reuse_existing()`
- ✅ Step 1.5.2: Implement `get_load_if_exists_flag()` for Optuna
- ✅ Step 1.5.3: Refactor HPO to use unified decision logic
- ✅ Step 1.5.4: Refactor final training to use unified decision logic
- ✅ Step 1.5.5: Remove redundant fallbacks and duplicate logic
- ✅ Step 1.5.6: All tests pass

### Phase 2: Deterministic Retrieval (Champion Selection)
- [ ] Step 2.0: Update selection configuration (centralized config with all requirements)
- [ ] Step 2.1: Upgrade study_key_hash to v2 (bound fingerprints)
- [ ] Step 2.2: Extract MLflow query patterns (DRY)
- [ ] Step 2.3: Implement champion selection with all safety requirements (config-driven)
- [ ] Step 2.4: Update HPO tracking to set new tags (schema_version, fingerprints, artifact.available)
- [ ] Step 2.5: Update notebooks (explicit champion selection)

### Phase 3: Idempotent Benchmarking (Uses Champions)
- [ ] Step 3.1: Build stable benchmark keys (using champion run_id + fingerprints)
- [ ] Step 3.2: Add idempotency check (MLflow + disk)
- [ ] Step 3.3: Add run mode inheritance (uses run_mode.py)
- [ ] Step 3.4: Update benchmarking to use champions (not all variants)
- [ ] Step 3.5: Update notebooks (complete 3-step flow)

## Testing Strategy

### Unit Tests
- `run_mode.py`: Test extraction, helpers
- `variants.py`: Test computation for both process types
- `mlflow/queries.py`: Test query patterns
- `trial_finder.py`: Test MLflow-first priority, fallbacks
- `benchmarking/orchestrator.py`: Test idempotency, keys

### Integration Tests
- HPO variant creation (v1, v2, v3)
- Retrieval with MLflow-first priority
- Benchmarking idempotency
- Variant completeness check
- End-to-end notebook flow

## Migration & Backward Compatibility

### Backward Compatibility
- Keep `find_best_trials_for_backbones()` with deprecation warning
- Old notebooks continue to work
- Existing configs work (defaults unchanged)

### Gradual Migration
1. Phase 1: Add new utilities (no breaking changes)
2. Phase 2: Enhance existing functions (backward compatible)
3. Phase 3: Add new features (optional)
4. Deprecate old functions gradually

## Success Metrics

- **DRY Compliance**: No code duplication (shared utilities used)
- **Determinism**: Same inputs → same best trial selection
- **Efficiency**: Skipped benchmarks reduce compute time
- **Debuggability**: Explicit retrieval step shows reasoning
- **Flexibility**: Both overall and per-variant modes work

## References

- Existing variant logic: `src/infrastructure/config/training.py`
- Run mode utility: `src/infrastructure/config/run_mode.py` ✅ **CREATED**
- Run decision utility: `src/infrastructure/config/run_decision.py` ✅ **CREATED**
- Variants utility: `src/infrastructure/config/variants.py` ✅ **CREATED**
- Existing MLflow querying: `src/evaluation/selection/mlflow_selection.py`
- Existing trial finding: `src/evaluation/selection/trial_finder.py`
- Existing fingerprints: `src/infrastructure/fingerprints/`

## Related Implementation Plans

- `unify-run-decision-logic.plan.md` - ✅ **COMPLETED** (Phase 1.5)
- `unify-run-mode-logic.plan.md` - ✅ **COMPLETED** (Phase 1)


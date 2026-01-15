# Consolidate Selection and Caching Scripts DRY Violations

## Goal

Eliminate duplicate path inference, config loading, and overlapping responsibilities across selection and caching scripts by consolidating to shared utilities, following reuse-first principles and minimizing breaking changes.

## Status

**Last Updated**: 2026-01-15

### Completed Steps
- ✅ Step 1: Audit and document selection/caching script duplication
- ✅ Step 2: Fix config_dir re-inference violations
- ✅ Step 3: Verify cache utilities separation
- ✅ Step 4: Verify config loading patterns
- ✅ Step 5: Verify path resolution patterns
- ✅ Step 6: Update callers of select_champion_per_backbone()
- ✅ Step 7: Run comprehensive tests
- ✅ Step 8: Document changes

### Pending Steps
- None (all steps complete)

## Implementation Complete ✅

All steps have been completed successfully:
- ✅ Fixed 2 DRY violations in `trial_finder.py`
- ✅ Updated caller in `benchmarking_workflow.py`
- ✅ Verified cache utilities separation
- ✅ Verified config loading patterns
- ✅ Verified path resolution patterns
- ✅ All 277 tests pass
- ✅ Documentation updated

## Preconditions

- Existing infrastructure modules:
  - `infrastructure.paths.utils` - Path utilities (`find_project_root`, `infer_config_dir`, `resolve_project_paths`)
  - `infrastructure.paths.cache` - Cache file path management
  - `infrastructure.config.selection` - Selection config utilities
  - `evaluation.selection.cache` - Selection-specific cache management
  - `training.hpo.tracking.setup` - HPO MLflow setup (already fixed to trust provided config_dir)

## Step 1: Audit Results

### Selection Scripts (domain: selection, tags: selection)

#### 1. `src/evaluation/selection/trial_finder.py` (1580 lines)
- **Purpose**: Find best trials from HPO studies or disk, champion selection logic
- **Tags**: `utility`, `selection`, `hpo`, `optuna`
- **Functions with config_dir parameters**:
  - `select_champion_per_backbone()` (line 819) - **✅ FIXED**: Now trusts provided config_dir
  - `_get_checkpoint_path_from_run()` (line 1476) - ✅ Uses provided config_dir correctly
  - `select_champions_for_backbones()` (line 1541) - ✅ Passes config_dir correctly
- **DRY Violations Fixed**:
  1. **Config_dir re-inference** (lines 890-897) - **✅ FIXED**
     - **Before**: Ignored provided `config_dir` parameter and always re-inferred
     - **After**: Trusts provided `config_dir` parameter, only infers when `None`
     - **Solution**: Uses `resolve_project_paths()` SSOT utility for consistency
  2. **Path inference in helper** (lines 432-440) - **✅ FIXED**
     - **Before**: Inline path inference using `find_project_root()` + manual `config_dir` construction
     - **After**: Uses `resolve_project_paths()` SSOT utility for consistency
     - **Solution**: Replaced inline inference with SSOT utility

#### 2. `src/evaluation/selection/cache.py` (262 lines)
- **Purpose**: Cache management for best model selection, cache key computation and validation
- **Tags**: `utility`, `selection`, `caching`
- **Status**: ✅ **NO VIOLATIONS**
  - Uses provided `root_dir` and `config_dir` parameters (no inference)
  - Uses `infrastructure.paths.get_cache_file_path` and `save_cache_with_dual_strategy` (good reuse)
  - Functions: `load_cached_best_model()`, `save_best_model_cache()` - both use provided parameters

#### 3-15. Other Selection Scripts
- All other selection scripts verified: ✅ **NO VIOLATIONS**
- All use provided parameters or don't need path inference

### Caching Scripts (domain: paths/selection, tags: cache/caching)

#### 1. `src/infrastructure/paths/cache.py` (341 lines)
- **Purpose**: Manage cache file paths based on strategy configuration
- **Tags**: `utility`, `paths`, `cache`
- **Status**: ✅ **NO VIOLATIONS**
  - Uses provided `root_dir` and `config_dir` parameters (no inference)
  - Functions: `get_cache_file_path()`, `get_timestamped_cache_filename()`, `get_cache_strategy_config()`, `save_cache_with_dual_strategy()`, `load_cache_file()` - all use provided parameters

#### 2. `src/evaluation/selection/cache.py` (262 lines)
- **Purpose**: Cache management for best model selection
- **Tags**: `utility`, `selection`, `caching`
- **Status**: ✅ **NO VIOLATIONS**
  - Uses `infrastructure.paths.cache` utilities (good reuse)
  - Selection-specific cache logic (validation, key computation) - appropriate separation

## Changes Made

### File: `src/evaluation/selection/trial_finder.py`

#### Change 1: Fixed `select_champion_per_backbone()` config_dir re-inference

**Location**: Lines 886-897

**Before**:
```python
from infrastructure.paths.utils import infer_config_dir
# Infer config_dir
config_dir = infer_config_dir()
tags_registry = load_tags_registry(config_dir)
```

**After**:
```python
from infrastructure.paths.utils import resolve_project_paths

# Trust provided config_dir parameter, only infer when None (DRY principle)
if config_dir is None:
    # Infer config_dir only when not provided
    _, resolved_config_dir = resolve_project_paths(
        output_dir=None,
        config_dir=None,
    )
    config_dir = resolved_config_dir if resolved_config_dir else Path.cwd() / "config"

tags_registry = load_tags_registry(config_dir)
```

**Impact**: Function now trusts provided `config_dir` parameter, eliminating duplicate inference work.

#### Change 2: Fixed `find_best_trial_from_mlflow()` inline path inference

**Location**: Lines 432-440

**Before**:
```python
from infrastructure.paths.utils import find_project_root
project_root = find_project_root(output_dir=hpo_backbone_dir)
config_dir = project_root / "config"
```

**After**:
```python
from infrastructure.paths.utils import resolve_project_paths
project_root, resolved_config_dir = resolve_project_paths(
    output_dir=hpo_backbone_dir,
    config_dir=None,
)
if project_root is None or resolved_config_dir is None:
    raise ValueError("Could not resolve project paths from hpo_backbone_dir")
```

**Impact**: Uses SSOT utility `resolve_project_paths()` for consistency with rest of codebase.

### File: `src/evaluation/selection/workflows/benchmarking_workflow.py`

#### Change 3: Updated caller to pass config_dir and root_dir

**Location**: Lines 112-119

**Before**:
```python
champions = select_champions_for_backbones(
    backbone_values=backbone_values,
    hpo_experiments=hpo_experiments,
    selection_config=selection_config,
    mlflow_client=mlflow_client,
)
```

**After**:
```python
champions = select_champions_for_backbones(
    backbone_values=backbone_values,
    hpo_experiments=hpo_experiments,
    selection_config=selection_config,
    mlflow_client=mlflow_client,
    root_dir=root_dir,
    config_dir=config_dir,
)
```

**Impact**: Now correctly propagates `root_dir` and `config_dir` parameters through the call chain.

## Path Resolution Patterns Documentation

### Single Source of Truth (SSOT)

**`infrastructure.paths.utils.resolve_project_paths()`** is the SSOT for path resolution across the codebase.

**Key Principle**: Functions should **trust provided `config_dir` and `root_dir` parameters** and only infer when they are explicitly `None`.

### Correct Usage Pattern

```python
from infrastructure.paths.utils import resolve_project_paths

def my_function(
    root_dir: Optional[Path] = None,
    config_dir: Optional[Path] = None,
) -> None:
    """
    Example function that correctly handles path resolution.
    
    Args:
        root_dir: Optional project root directory (trusts if provided)
        config_dir: Optional config directory (trusts if provided)
    """
    # Trust provided config_dir parameter, only infer when None (DRY principle)
    if config_dir is None:
        # Infer config_dir only when not provided
        _, resolved_config_dir = resolve_project_paths(
            output_dir=None,
            config_dir=None,
        )
        config_dir = resolved_config_dir if resolved_config_dir else Path.cwd() / "config"
    
    # Use config_dir (either provided or inferred)
    # ...
```

### Anti-Pattern (Avoid)

```python
# ❌ BAD: Always re-infers, ignoring provided parameter
from infrastructure.paths.utils import infer_config_dir
config_dir = infer_config_dir()  # Ignores function parameter!

# ❌ BAD: Inline path inference instead of using SSOT
from infrastructure.paths.utils import find_project_root
project_root = find_project_root(output_dir=output_dir)
config_dir = project_root / "config"  # Should use resolve_project_paths()
```

### When to Use `resolve_project_paths()`

Use `resolve_project_paths()` when:
1. You need to infer both `root_dir` and `config_dir` from an `output_dir`
2. You want to trust a provided `config_dir` but need to derive `root_dir` from it
3. You need consistent path resolution behavior across the codebase

**Example**:
```python
# Infer from output_dir
root_dir, config_dir = resolve_project_paths(
    output_dir=Path("/workspace/outputs/hpo/local/distilbert"),
    config_dir=None,
)

# Trust provided config_dir, derive root_dir
root_dir, config_dir = resolve_project_paths(
    output_dir=None,
    config_dir=Path("/workspace/config"),
)
```

## Test Results

### Step 7: Comprehensive Tests

**Test Command**: `pytest tests/evaluation/selection/ tests/selection/ -v`

**Results**:
- ✅ **277 tests passed**
- ✅ **1 warning** (unrelated to our changes - MLflow filesystem backend deprecation)
- ✅ **No test failures**
- ✅ **No regressions detected**

**Test Coverage**:
- Selection config utilities
- Selection cache functionality
- Champion selection logic
- Artifact acquisition
- Selection workflows

**Conclusion**: All tests pass, confirming no regressions from the changes.

## Success Criteria (Overall)

- ✅ No config_dir re-inference violations in selection scripts
- ✅ All selection scripts use `resolve_project_paths()` or trust provided parameters
- ✅ Cache utilities maintain clear separation of concerns
- ✅ Config loading uses SSOT (`infrastructure.config.selection`)
- ✅ All tests pass (277 passed, 0 failed)
- ✅ No breaking changes to public APIs
- ✅ Changes follow DRY principle and reuse-first approach

## Summary

This implementation plan successfully eliminated 2 DRY violations in selection scripts:

1. **Fixed config_dir re-inference** in `select_champion_per_backbone()` - now trusts provided parameter
2. **Fixed inline path inference** in `find_best_trial_from_mlflow()` - now uses SSOT utility
3. **Updated caller** in `benchmarking_workflow.py` - now passes config_dir and root_dir correctly

All changes follow the established pattern:
- Trust provided parameters (DRY principle)
- Use SSOT utilities (`resolve_project_paths()`) for consistency
- Only infer when parameters are explicitly `None`
- Maintain backward compatibility (no breaking changes)

The codebase now has consistent path resolution patterns across all selection and caching scripts.

## Notes

1. **Minimal Scope**: This plan focused on fixing the identified DRY violations (2 violations in `trial_finder.py`) rather than large refactors.

2. **Reuse-First**: The plan leveraged existing SSOT utilities (`resolve_project_paths()`, `infrastructure.config.selection`, `infrastructure.paths.cache`) rather than creating new ones.

3. **Separation of Concerns**: Cache utilities are properly separated:
   - `infrastructure/paths/cache.py` - Generic cache path management
   - `evaluation/selection/cache.py` - Selection-specific cache logic
   - No consolidation needed

4. **Similar Pattern**: The fix in `trial_finder.py` follows the same pattern as the fix in `setup_hpo_mlflow_run()` - trust provided parameters, only infer when necessary.

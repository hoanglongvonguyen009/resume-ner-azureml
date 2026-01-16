# Deprecation Warnings Audit Report

**Date**: 2025-01-27  
**Phase**: Phase 1 - Comprehensive Audit  
**Status**: ✅ Complete

## Executive Summary

This audit identified **13 DeprecationWarning instances** across **9 source files**, categorized into 4 main types:
1. **Deprecated Facade Modules** (2 files, 3 warnings)
2. **Deprecated Config Keys** (5 files, 6 warnings)
3. **Deprecated Functions** (1 file, 2 warnings)
4. **Deprecated Fallback Behaviors** (1 file, 1 warning)
5. **Suppressed Warnings** (1 file, 1 warning - not our deprecation)

## Category 1: Deprecated Facade Modules

### 1.1 `src/orchestration/__init__.py`

**Status**: `lifecycle: status: deprecated` (line 24)  
**Warnings**: 2 DeprecationWarning instances (lines 125, 231)

**Current Behavior**:
- Emits deprecation warning on direct import (not for `orchestration.jobs.*` submodules)
- Re-exports functions from new modular structure
- Provides backward compatibility shim

**Replacement Modules**:
- `infrastructure.config` - Configuration management
- `infrastructure.fingerprints` - Fingerprint computation
- `infrastructure.metadata` - Metadata and index management
- `common.constants` - Shared constants
- `infrastructure.platform.azureml` - Azure ML utilities
- `infrastructure.storage` - Storage and backup utilities
- `evaluation.selection` - Configuration selection
- `evaluation.benchmarking` - Benchmarking orchestration
- `deployment.conversion` - Conversion execution
- `training.execution` - Final training execution

**Usage Audit**:
```bash
# Check for remaining imports from orchestration (excluding orchestration.jobs.*)
grep -rn "from orchestration import\|^import orchestration" src/ tests/ notebooks/ --include="*.py" | grep -v "orchestration\.jobs\|orchestration/__init__"
```
**Result**: No remaining imports found (✅ All migrated)

**Migration Path**:
1. ✅ All imports already migrated (verified)
2. Remove deprecation warnings
3. Remove facade logic (re-exports)
4. Keep minimal `__init__.py` if `orchestration/` directory has active submodules

**Breaking Changes**: None (all imports already migrated)

---

### 1.2 `src/selection/__init__.py`

**Status**: `lifecycle: status: deprecated` (line 25)  
**Warnings**: 1 DeprecationWarning instance (line 165)

**Current Behavior**:
- Emits deprecation warning on import
- Compatibility shim that proxies to `evaluation.selection.*`
- Custom import finder handles submodule imports

**Replacement Module**: `evaluation.selection.*`

**Usage Audit**:
```bash
# Check for remaining imports from selection
grep -rn "from selection import\|^import selection" src/ tests/ notebooks/ --include="*.py" | grep -v "selection/__init__\|selection\.selection\|selection\.selection_logic\|selection\.types"
```
**Result**: No remaining imports found (✅ All migrated)

**Migration Path**:
1. ✅ All imports already migrated (verified)
2. Remove deprecation warnings
3. Remove facade logic (proxy mechanism)
4. Keep minimal `__init__.py` if `selection/` directory has active submodules

**Breaking Changes**: None (all imports already migrated)

---

## Category 2: Deprecated Config Keys

### 2.1 `objective.goal` → `objective.direction`

**Files Affected**: 5 source files, 6 occurrences

#### File: `src/training/hpo/checkpoint/cleanup.py`
- **Line 189-194**: First occurrence in `initialize_best_trial_from_study()`
- **Line 287-292**: Second occurrence in `handle_trial_completion()`

#### File: `src/training/hpo/execution/azureml/sweeps.py`
- **Line 132-137**: First occurrence in `create_dry_run_sweep_job()`
- **Line 240-245**: Second occurrence in `create_hpo_sweep_job_for_backbone()`

#### File: `src/training/hpo/core/study.py`
- **Line 172-177**: Single occurrence in `__init__()`

#### File: `src/infrastructure/config/selection.py`
- **Line 73-78**: Single occurrence in `get_objective_direction()`

**Current Behavior**:
- Code supports both `objective.direction` (new) and `objective.goal` (deprecated)
- Emits DeprecationWarning when `objective.goal` is used
- Maps `goal` values: `maximize`/`max` → `maximize`, `minimize`/`min` → `minimize`

**Config Files Audit**:
```bash
# Find all YAML files with objective.goal
find config/ -name "*.yaml" -exec grep -l "objective\.goal" {} \;
```
**Result**: No config files found using `objective.goal` (✅ All configs already migrated)

**Migration Path**:
1. ✅ All config files already use `objective.direction` (verified)
2. Remove backward compatibility code (6 locations)
3. Remove deprecation warnings
4. Keep only `objective.direction` support

**Breaking Changes**: None (all configs already migrated, code still supports both keys)

---

## Category 3: Deprecated Functions

### 3.1 `find_checkpoint_in_trial_dir()` in `evaluation/benchmarking/orchestrator.py`

**Location**: `src/evaluation/benchmarking/orchestrator.py:361`  
**Deprecation Warning**: Line 381  
**Message**: "Use champions from Phase 2 which already have checkpoint_path set"

**Current Usage**: 1 internal use (line 759)

**Context**:
```python
# Line 759: Used in benchmark_best_trials() function
checkpoint_dir = find_checkpoint_in_trial_dir(trial_dir)
```

**Replacement**: Champions from Phase 2 already have `checkpoint_path` set in the data structure

**Migration Path**:
1. Update caller at line 759 to use `checkpoint_path` from champion data structure
2. Remove function definition (lines 361-464)
3. Verify no other callers exist

**Breaking Changes**: None (only internal use)

---

### 3.2 `compute_grouping_tags()` in `evaluation/benchmarking/orchestrator.py`

**Location**: `src/evaluation/benchmarking/orchestrator.py:467`  
**Deprecation Warning**: Line 492  
**Message**: "Use champions from Phase 2 which already have study_key_hash and trial_key_hash set"

**Current Usage**: 
- 1 internal use (line 794)
- 4 exports:
  - `src/evaluation/benchmarking/__init__.py:9,16`
  - `src/evaluation/__init__.py:12,46`
  - `src/orchestration/jobs/benchmarking/__init__.py:3,5`

**Context**:
```python
# Line 794: Used in benchmark_best_trials() function (legacy mode only)
if not is_champion and (not study_key_hash or not trial_key_hash):
    study_key_hash, trial_key_hash, study_family_hash = compute_grouping_tags(
        trial_info, data_config, hpo_config, benchmark_config
    )
```

**Replacement**: Champions from Phase 2 already have `study_key_hash` and `trial_key_hash` set in the data structure

**Migration Path**:
1. Update caller at line 794 (already handles champion mode, only used for legacy)
2. Remove function definition (lines 467-565)
3. Remove from exports:
   - `src/evaluation/benchmarking/__init__.py`
   - `src/evaluation/__init__.py`
   - `src/orchestration/jobs/benchmarking/__init__.py` (if exists)
4. Verify no external callers exist

**Breaking Changes**: 
- ⚠️ **Potential**: If external code imports `compute_grouping_tags` from exports, it will break
- **Mitigation**: Check for external usage before removal

---

## Category 4: Deprecated Fallback Behaviors

### 4.1 Inline Config Building Fallback in `infrastructure/config/training.py`

**Location**: `src/infrastructure/config/training.py:90-98`  
**Deprecation Warning**: Line 93  
**Message**: "config/final_training.yaml not found. Falling back to inline config building"

**Current Behavior**:
- If `config/final_training.yaml` not found, falls back to `_build_final_training_config_inline()`
- Emits DeprecationWarning when fallback is used

**Fallback Function**: `_build_final_training_config_inline()` (line 888)

**Migration Path**:
1. Verify `config/final_training.yaml` exists in all expected locations
2. Remove fallback logic (lines 89-98)
3. Remove `_build_final_training_config_inline()` function (if no longer used)
4. Raise `FileNotFoundError` with clear message if config file missing
5. Remove deprecation warning

**Breaking Changes**: 
- ⚠️ **Potential**: If any workflow relies on fallback, it will break
- **Mitigation**: Ensure all workflows have `final_training.yaml` before removing fallback

---

## Category 5: Suppressed Warnings (Not Our Deprecation)

### 5.1 MLflow Deprecation Warning Suppression in `common/shared/mlflow_setup.py`

**Location**: `src/common/shared/mlflow_setup.py:247`  
**Category**: DeprecationWarning (suppressed, not emitted)

**Current Behavior**:
- Suppresses MLflow's own deprecation warnings about "uploading mode"
- This is intentional - we're using `mlflow.log_artifact()` instead of Azure ML SDK

**Action**: **No action needed** - This is suppressing external library warnings, not our code deprecation

---

## Summary Statistics

| Category | Files | Warnings | Status |
|----------|-------|----------|--------|
| Deprecated Facades | 2 | 3 | ✅ All imports migrated |
| Deprecated Config Keys | 5 | 6 | ✅ All configs migrated |
| Deprecated Functions | 1 | 2 | ⏳ Needs migration |
| Deprecated Fallbacks | 1 | 1 | ⏳ Needs verification |
| Suppressed Warnings | 1 | 1 | ✅ No action needed |
| **Total** | **9** | **13** | |

## Migration Priority

### High Priority (Low Risk)
1. ✅ **Deprecated Facades** - All imports already migrated, safe to remove warnings
2. ✅ **Deprecated Config Keys** - All configs already migrated, safe to remove backward compatibility

### Medium Priority (Medium Risk)
3. ⏳ **Deprecated Functions** - Need to verify external usage before removal
4. ⏳ **Deprecated Fallbacks** - Need to verify all workflows have required files

## Next Steps

1. ✅ **Phase 1 Complete**: Audit finished
2. ⏳ **Phase 2**: Migrate deprecated config keys (remove backward compatibility)
3. ⏳ **Phase 3**: Replace deprecated functions (after external usage check)
4. ⏳ **Phase 4**: Remove deprecated facade modules (after verification)
5. ⏳ **Phase 5**: Remove deprecated fallback behaviors (after file verification)

## Verification Commands

```bash
# Verify no objective.goal in config files
find config/ -name "*.yaml" -exec grep -H "objective\.goal" {} \; && echo "⚠️ Found!" || echo "✅ None found"

# Verify no imports from deprecated facades
grep -rn "from orchestration import\|^import orchestration" src/ tests/ notebooks/ --include="*.py" | grep -v "orchestration\.jobs\|orchestration/__init__" && echo "⚠️ Found!" || echo "✅ None found"

grep -rn "from selection import\|^import selection" src/ tests/ notebooks/ --include="*.py" | grep -v "selection/__init__\|selection\.selection\|selection\.selection_logic\|selection\.types" && echo "⚠️ Found!" || echo "✅ None found"

# Count deprecation warnings
grep -rn "DeprecationWarning" src/ --include="*.py" | grep -v "test\|#.*DeprecationWarning" | wc -l
```


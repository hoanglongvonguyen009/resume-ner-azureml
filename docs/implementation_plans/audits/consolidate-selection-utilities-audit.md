# Selection Utilities Duplication Audit

**Date**: 2025-01-27  
**Purpose**: Detailed comparison of duplicate modules between `src/selection/` and `src/evaluation/selection/`  
**Related Plan**: `FINISHED-consolidate-selection-utilities-dry-violations.plan.md`  
**Status**: ✅ Plan completed (2026-01-15)

## Executive Summary

- **Total duplicate modules**: 7 pairs
- **Total duplicate code**: ~2000+ lines
- **Direct imports found**: 5 test files import `selection.selection_logic.SelectionLogic`
- **Backward compatibility**: Already handled via `selection/__init__.py` (custom import finder)
- **SSOT**: `evaluation.selection` is the more feature-rich implementation

## Module-by-Module Comparison

### 1. `mlflow_selection.py`

#### Public Functions
- **selection**: `find_best_model_from_mlflow`
- **evaluation**: `find_best_model_from_mlflow`, `add_to_lookup` (internal helper)

#### Key Differences

| Aspect | `selection.mlflow_selection` | `evaluation.selection.mlflow_selection` |
|--------|------------------------------|------------------------------------------|
| **Function signature** | `find_best_model_from_mlflow(benchmark_experiment: Dict[str, str], ..., use_python_filtering: bool = True)` | `find_best_model_from_mlflow(benchmark_experiment: Optional[Dict[str, str]], ...)` |
| **MLflow queries** | Direct `client.search_runs()` calls | Uses `infrastructure.tracking.mlflow.queries.query_runs_by_tags()` (SSOT) |
| **Latency aggregation** | Not supported | Supports `latest`, `median`, `mean` strategies |
| **Benchmark grouping** | Simple deduplication | Groups by `(study_key_hash, trial_key_hash, benchmark_key)` |
| **Error handling** | Basic | More robust with detailed logging |
| **Return type** | `Optional[BestModelInfo]` (TypedDict) | `Optional[Dict[str, Any]]` |
| **Print statements** | Uses `print()` for user feedback | Uses `logger.info()` primarily |

#### API Compatibility Issues
- ⚠️ **Breaking**: `use_python_filtering` parameter exists only in `selection` version
- ⚠️ **Breaking**: `benchmark_experiment` is non-optional in `selection`, optional in `evaluation`
- ⚠️ **Type difference**: Return type is `BestModelInfo` (TypedDict) vs `Dict[str, Any]`

#### Consolidation Notes
- `evaluation.selection.mlflow_selection` is more feature-rich and uses SSOT for queries
- Need to handle `use_python_filtering` parameter (can be ignored, evaluation version always uses Python filtering)
- Need to ensure `BestModelInfo` type compatibility

---

### 2. `trial_finder.py`

#### Public Functions
- **selection**: `find_best_trial_in_study_folder`, `format_trial_identifier`, `find_study_folder_in_backbone_dir`, `find_best_trial_from_study`, `find_best_trials_for_backbones`
- **evaluation**: All of the above PLUS `select_champion_per_backbone`, `select_champions_for_backbones`

#### Key Differences

| Aspect | `selection.trial_finder` | `evaluation.selection.trial_finder` |
|--------|--------------------------|--------------------------------------|
| **Size** | 745 lines | 1580 lines |
| **Champion selection** | Not available | `select_champion_per_backbone()` - groups runs by study_key_hash, selects best group |
| **Artifact filtering** | Not available | `_filter_by_artifact_availability()` - filters runs by artifact availability tag |
| **Schema version handling** | Basic | Supports v1/v2 schema version separation |
| **Hash extraction** | Basic | More comprehensive, includes hashes in return values |
| **Trial metadata** | Basic | Enhanced with `study_key_hash`, `trial_key_hash` in results |

#### API Compatibility Issues
- ✅ **Compatible**: All functions from `selection` exist in `evaluation` version
- ℹ️ **Additional features**: `evaluation` version has extra functions (champion selection)

#### Consolidation Notes
- `evaluation.selection.trial_finder` is a superset of `selection.trial_finder`
- All functions from `selection` version exist in `evaluation` version
- Safe to consolidate - no breaking changes

---

### 3. `disk_loader.py`

#### Public Functions
- **selection**: `load_benchmark_speed_score`, `load_best_trial_from_disk`
- **evaluation**: `load_benchmark_speed_score`, `load_best_trial_from_disk`

#### Key Differences

| Aspect | `selection.disk_loader` | `evaluation.selection.disk_loader` |
|--------|-------------------------|-------------------------------------|
| **Size** | 239 lines | 236 lines |
| **Function signatures** | Identical | Identical |
| **Implementation** | Nearly identical | Nearly identical |
| **Return types** | `Optional[TrialInfo]` (TypedDict) | `Optional[Dict[str, Any]]` |
| **Type imports** | Imports `TrialInfo` from `.types` | No type imports |

#### API Compatibility Issues
- ⚠️ **Type difference**: Return type is `TrialInfo` (TypedDict) vs `Dict[str, Any]`
- ✅ **Functionally identical**: Same logic, same behavior

#### Consolidation Notes
- Nearly identical implementations
- Only difference is return type annotation (both return dicts at runtime)
- Safe to consolidate - runtime behavior is identical

---

### 4. `local_selection_v2.py`

#### Public Functions
- **selection**: `parse_version_from_name`, `fold_index`, `find_study_folder_by_config`, `load_best_trial_from_study_folder`, `write_active_study_marker`, `find_trial_checkpoint_by_hash`
- **evaluation**: All of the above (identical list)

#### Key Differences

| Aspect | `selection.local_selection_v2` | `evaluation.selection.local_selection_v2` |
|--------|-------------------------------|-------------------------------------------|
| **Size** | 524 lines | 528 lines |
| **Trial naming support** | v2 format only (`trial-{hash}`) | Both v2 (`trial-{hash}`) and legacy (`trial_{n}_{run_id}`) |
| **Constants** | `FOLD_INDEX_NOT_FOUND = 10**9` | `_INVALID_FOLD_INDEX = 10**9` (private) |
| **Implementation** | Nearly identical | Nearly identical |

#### API Compatibility Issues
- ✅ **Compatible**: All functions exist in both versions
- ℹ️ **Enhanced**: `evaluation` version supports legacy trial naming

#### Consolidation Notes
- Nearly identical implementations
- `evaluation` version has better backward compatibility (supports legacy trial names)
- Safe to consolidate - `evaluation` version is a superset

---

### 5. `cache.py`

#### Public Functions
- **selection**: `load_cached_best_model`, `save_best_model_cache`
- **evaluation**: `load_cached_best_model`, `save_best_model_cache`

#### Key Differences

| Aspect | `selection.cache` | `evaluation.selection.cache` |
|--------|-------------------|------------------------------|
| **Size** | 270 lines | 261 lines |
| **Function signatures** | Identical | Identical |
| **Constants** | `RUN_ID_DISPLAY_LENGTH = 12`, `HASH_LENGTH = 16` | No constants (hardcoded values) |
| **Type hints** | Uses `BestModelInfo`, `CacheData` TypedDicts | Uses `Dict[str, Any]` |
| **Return types** | `Optional[CacheData]` (TypedDict) | `Optional[Dict[str, Any]]` |

#### API Compatibility Issues
- ⚠️ **Type difference**: Uses TypedDict types vs `Dict[str, Any]`
- ✅ **Functionally identical**: Same logic, same behavior

#### Consolidation Notes
- Nearly identical implementations
- Only difference is type annotations (both return dicts at runtime)
- Constants in `selection` version are minor improvements (can be added to `evaluation` version)

---

### 6. `study_summary.py`

#### Public Functions
- **selection**: `extract_cv_statistics`, `get_trial_hash_info`, `load_study_from_disk`, `find_trial_hash_info_for_study`, `format_study_summary_line`, `print_study_summaries`, `normalize_backbone` (nested)
- **evaluation**: `extract_cv_statistics`, `get_trial_hash_info`, `load_study_from_disk`, `find_trial_hash_info_for_study`, `format_study_summary_line`, `print_study_summaries`

#### Key Differences

| Aspect | `selection.study_summary` | `evaluation.selection.study_summary` |
|--------|---------------------------|-------------------------------------|
| **Size** | 329 lines | 317 lines |
| **normalize_backbone** | Nested function in `print_study_summaries()` | Not present (logic inline) |
| **format_study_summary_line** | No `from_disk` parameter | Has `from_disk: bool = False` parameter |
| **Backbone normalization** | Uses `normalize_backbone()` helper | Inline logic: `backbone.split("-")[0]` |
| **Type hints** | Uses `TYPE_CHECKING` for Optuna types | Uses `Any` type |

#### API Compatibility Issues
- ⚠️ **Missing function**: `normalize_backbone` is nested in `selection` version, not exported
- ⚠️ **Parameter difference**: `format_study_summary_line` has `from_disk` parameter in `evaluation` version
- ✅ **Compatible**: All exported functions exist in both versions

#### Consolidation Notes
- `normalize_backbone` is not exported, so no API breakage
- `from_disk` parameter in `evaluation` version is optional, so backward compatible
- Safe to consolidate

---

### 7. `artifact_acquisition.py`

#### Public Functions
- **selection**: `acquire_best_model_checkpoint` (plus internal helpers)
- **evaluation**: `acquire_best_model_checkpoint` (plus internal helpers)

#### Key Differences

| Aspect | `selection.artifact_acquisition` | `evaluation.selection.artifact_acquisition` |
|--------|----------------------------------|-----------------------------------------------|
| **Size** | 396 lines | 187 lines |
| **Implementation** | Full implementation + wrapper | Thin wrapper only |
| **Unified system** | Uses `evaluation.selection.artifact_unified.compat` | Uses `evaluation.selection.artifact_unified.compat` |
| **Legacy code** | Contains legacy implementation code | Pure wrapper |

#### API Compatibility Issues
- ✅ **Compatible**: Both use unified system under the hood
- ✅ **Functionally identical**: Same API, same behavior

#### Consolidation Notes
- `evaluation.selection.artifact_acquisition` is already a thin wrapper (better)
- `selection.artifact_acquisition` still contains legacy code that can be removed
- Safe to consolidate - `evaluation` version is cleaner

---

## Direct Import Analysis

### Files Importing from `selection.*` Directly

1. **`tests/hpo/integration/test_hpo_full_workflow.py`**
   ```python
   from selection.selection_logic import SelectionLogic
   ```

2. **`tests/hpo/unit/test_trial_selection.py`**
   ```python
   from selection.selection_logic import SelectionLogic
   ```

3. **`tests/hpo/integration/test_best_trial_selection_component.py`**
   ```python
   from selection.selection_logic import SelectionLogic
   ```

4. **`tests/hpo/integration/test_error_handling.py`**
   ```python
   from selection.selection_logic import SelectionLogic
   # Also has inline import: from selection.selection_logic import SelectionLogic
   ```

5. **`tests/conftest.py`**
   - Has comment about ensuring `selection.selection_logic` imports work
   - No direct import found in grep results

### Notes on Direct Imports

- **All direct imports are for `SelectionLogic`**: Only `selection.selection_logic.SelectionLogic` is imported directly
- **`SelectionLogic` exists in both**: Both `selection.selection_logic` and `evaluation.selection.selection_logic` have `SelectionLogic` class
- **Backward compatibility**: `selection/__init__.py` already handles submodule imports via custom finder
- **Action needed**: Update test imports to use `evaluation.selection.selection_logic.SelectionLogic` OR ensure `selection.selection_logic` re-exports correctly

---

## API Differences Summary

### Breaking Changes (Require Handling)

1. **`mlflow_selection.find_best_model_from_mlflow`**:
   - `use_python_filtering` parameter missing in `evaluation` version (can be ignored - always uses Python filtering)
   - `benchmark_experiment` type: `Dict[str, str]` vs `Optional[Dict[str, str]]`
   - Return type: `BestModelInfo` (TypedDict) vs `Dict[str, Any]`

2. **Type annotations**:
   - `selection` modules use TypedDict types (`BestModelInfo`, `TrialInfo`, `CacheData`)
   - `evaluation` modules use `Dict[str, Any]`
   - **Runtime compatible**: Both return dicts, only type annotations differ

### Non-Breaking Differences (Enhancements)

1. **Additional functions in `evaluation.selection.trial_finder`**:
   - `select_champion_per_backbone()`
   - `select_champions_for_backbones()`

2. **Enhanced features in `evaluation.selection.mlflow_selection`**:
   - Latency aggregation strategies
   - Benchmark grouping by `benchmark_key`
   - Uses SSOT for MLflow queries

3. **Better backward compatibility**:
   - `evaluation.selection.local_selection_v2` supports legacy trial naming
   - `evaluation.selection.mlflow_selection` handles optional `benchmark_experiment`

---

## Consolidation Strategy

### Recommended Approach

1. **Keep `evaluation.selection` as SSOT** (already more feature-rich)
2. **Update `selection/*.py` modules to re-export from `evaluation.selection`**
3. **Handle API differences**:
   - Add wrapper functions for `use_python_filtering` parameter (if needed)
   - Ensure type compatibility (TypedDict vs Dict - runtime compatible)
4. **Update test imports** to use `evaluation.selection.selection_logic.SelectionLogic` OR ensure re-exports work
5. **Remove duplicate code** from `selection/*.py` modules

### Risk Assessment

- **Low risk**: Most modules are functionally identical
- **Medium risk**: `mlflow_selection` has parameter differences (can be handled with wrapper)
- **Low risk**: Type annotation differences don't affect runtime behavior
- **Low risk**: Backward compatibility already handled via `__init__.py`

---

## Next Steps

1. ✅ **Step 1 Complete**: Audit and document current duplication
2. ⏳ **Step 2**: Consolidate `mlflow_selection.py` (handle `use_python_filtering` parameter)
3. ⏳ **Step 3**: Consolidate `trial_finder.py` (straightforward - superset)
4. ⏳ **Step 4**: Consolidate `disk_loader.py` (straightforward - identical)
5. ⏳ **Step 5**: Consolidate `local_selection_v2.py` (straightforward - superset)
6. ⏳ **Step 6**: Consolidate `cache.py` (straightforward - identical)
7. ⏳ **Step 7**: Consolidate `study_summary.py` (straightforward - compatible)
8. ⏳ **Step 8**: Verify `artifact_acquisition.py` (already consolidated)
9. ⏳ **Step 9**: Update all imports (5 test files need updates)
10. ⏳ **Step 10**: Remove duplicate implementations
11. ⏳ **Step 11**: Run tests and verify backward compatibility

---

## Verification Commands

```bash
# Find all direct imports from selection.*
grep -r "from selection\." src/ tests/ --exclude-dir=__pycache__ | grep -v "__init__.py"

# Compare function signatures
python3 -c "import sys; sys.path.insert(0, 'src'); from selection.mlflow_selection import find_best_model_from_mlflow; import inspect; print(inspect.signature(find_best_model_from_mlflow))"

# Count lines of duplicate code
wc -l src/selection/mlflow_selection.py src/evaluation/selection/mlflow_selection.py
wc -l src/selection/trial_finder.py src/evaluation/selection/trial_finder.py
wc -l src/selection/disk_loader.py src/evaluation/selection/disk_loader.py
wc -l src/selection/local_selection_v2.py src/evaluation/selection/local_selection_v2.py
wc -l src/selection/cache.py src/evaluation/selection/cache.py
wc -l src/selection/study_summary.py src/evaluation/selection/study_summary.py
```


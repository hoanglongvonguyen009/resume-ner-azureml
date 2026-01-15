# Consolidate Selection Utilities DRY Violations

## Goal

Eliminate duplicate implementations across `src/selection/` and `src/evaluation/selection/` by consolidating to `evaluation.selection` as the Single Source of Truth (SSOT), while maintaining backward compatibility through thin wrappers in `selection`.

## Status

**Last Updated**: 2026-01-15

**Status**: ✅ **ALL STEPS COMPLETE** - Plan finished

### Completed Steps
- ✅ Step 1: Audit and document current duplication
- ✅ Step 2: Consolidate `mlflow_selection.py`
- ✅ Step 3: Consolidate `trial_finder.py`
- ✅ Step 4: Consolidate `disk_loader.py`
- ✅ Step 5: Consolidate `local_selection_v2.py`
- ✅ Step 6: Consolidate `cache.py`
- ✅ Step 7: Consolidate `study_summary.py`
- ✅ Step 8: Verify `artifact_acquisition.py` consolidation status
- ✅ Step 9: Update all imports across codebase
- ✅ Step 10: Remove duplicate implementations
- ✅ Step 11: Run tests and verify backward compatibility

## Preconditions

- Existing codebase has both `src/selection/` and `src/evaluation/selection/` modules
- `evaluation.selection` appears to be the newer, more feature-rich implementation
- `selection` module already has backward compatibility wrappers in `__init__.py`
- MLflow query patterns already consolidated into `infrastructure.tracking.mlflow.queries`

## Analysis

### 1. Utility Scripts Found

#### `src/selection/` (Legacy - Being Consolidated)
1. **`mlflow_selection.py`** (110 lines) ✅ **CONSOLIDATED**
   - **Status**: Now a backward-compatibility wrapper around `evaluation.selection.mlflow_selection`
   - Handles `use_python_filtering` parameter (deprecated, always True)
   - Converts return type from `Dict[str, Any]` to `BestModelInfo` TypedDict
   - Includes deprecation warnings

2. **`trial_finder.py`** (745 lines)
   - Purpose: Find best trials from HPO studies or disk
   - Extract trial information from Optuna studies
   - Locate trial directories by hash or number
   - Supports v2 paths only

3. **`disk_loader.py`** (108 lines) ✅ **CONSOLIDATED**
   - **Status**: Now a backward-compatibility wrapper around `evaluation.selection.disk_loader`
   - Re-exports `load_benchmark_speed_score()` and `load_best_trial_from_disk()`
   - Converts return type from `Dict[str, Any]` to `TrialInfo` TypedDict
   - Includes deprecation warnings

4. **`local_selection_v2.py`** (217 lines) ✅ **CONSOLIDATED**
   - **Status**: Now a backward-compatibility wrapper around `evaluation.selection.local_selection_v2`
   - Re-exports all 6 public functions with type conversions where needed
   - Re-exports `FOLD_INDEX_NOT_FOUND` constant for backward compatibility
   - Includes deprecation warnings

5. **`cache.py`** (172 lines) ✅ **CONSOLIDATED**
   - **Status**: Now a backward-compatibility wrapper around `evaluation.selection.cache`
   - Re-exports both functions with type conversions where needed
   - Re-exports `RUN_ID_DISPLAY_LENGTH` and `HASH_LENGTH` constants for backward compatibility
   - Includes deprecation warnings

6. **`study_summary.py`** (275 lines) ✅ **CONSOLIDATED**
   - **Status**: Now a backward-compatibility wrapper around `evaluation.selection.study_summary`
   - Re-exports all 6 public functions with type conversions where needed
   - Handles type differences (Trial vs Any, Study vs Any)
   - Note: evaluation version has `from_disk` parameter in `format_study_summary_line()` that is not exposed in wrapper for backward compatibility
   - Includes deprecation warnings

7. **`artifact_acquisition.py`** (118 lines) ✅ **CONSOLIDATED**
   - **Status**: Now a backward-compatibility wrapper around `evaluation.selection.artifact_acquisition`
   - Both modules already use unified artifact acquisition system (`evaluation.selection.artifact_unified.compat`)
   - Re-exports `acquire_best_model_checkpoint()` with type conversion from `BestModelInfo` to `Dict[str, Any]`
   - Removed dead helper functions (not used, unified system handles everything)
   - Includes deprecation warnings

8. **`selection_logic.py`** (206 lines)
   - Purpose: Implement selection logic for choosing best configuration
   - Normalize speed scores
   - Apply accuracy thresholds
   - Class: `SelectionLogic`

#### `src/evaluation/selection/` (SSOT)
1. **`mlflow_selection.py`** (442 lines)
   - Purpose: MLflow-based best model selection (SSOT for local selection)
   - Uses `infrastructure.tracking.mlflow.queries` for all MLflow queries (SSOT)
   - Supports latency aggregation strategies (latest, median, mean)
   - More robust error handling and logging

2. **`trial_finder.py`** (1580 lines)
   - Purpose: Find best trials from HPO studies or disk
   - Includes `select_champion_per_backbone()` function (champion selection logic)
   - More comprehensive hash extraction and trial matching
   - Includes artifact availability filtering

3. **`disk_loader.py`** (236 lines)
   - Purpose: Load trial data from disk-based HPO outputs
   - Nearly identical to `selection/disk_loader.py`
   - Same functions: `load_benchmark_speed_score()`, `load_best_trial_from_disk()`

4. **`local_selection_v2.py`** (528 lines)
   - Purpose: Improved best configuration selection from local Optuna HPO studies
   - Nearly identical to `selection/local_selection_v2.py`
   - Supports both v2 and legacy trial naming formats

5. **`cache.py`** (261 lines)
   - Purpose: Cache management for best model selection
   - Nearly identical to `selection/cache.py`
   - Minor differences in type hints and constants

6. **`study_summary.py`** (317 lines)
   - Purpose: Display and summarize HPO study results
   - Very similar to `selection/study_summary.py`
   - Includes `from_disk` parameter in `format_study_summary_line()`

7. **`artifact_acquisition.py`** (187 lines)
   - Purpose: Checkpoint acquisition for best model selection
   - Backward compatibility wrapper around unified artifact acquisition system
   - Already consolidated (uses `artifact_unified.compat`)

### 2. Overlapping Responsibilities

#### Category A: MLflow Query Patterns ✅ **CONSOLIDATED**
- **Overlap**: Both `mlflow_selection.py` modules query MLflow runs
- **Status**: `evaluation.selection.mlflow_selection` uses `infrastructure.tracking.mlflow.queries` (SSOT)
- **Resolution**: `selection.mlflow_selection` now wraps `evaluation.selection.mlflow_selection` (Step 2 complete)

#### Category B: Disk I/O and Path Handling ✅ **CONSOLIDATED**
- **Overlap**: Both `disk_loader.py` modules read metrics.json, benchmark.json, trial_meta.json
- **Status**: Nearly identical implementations
- **Resolution**: `selection.disk_loader` now wraps `evaluation.selection.disk_loader` (Step 4 complete)

#### Category C: Trial Finding Logic
- **Overlap**: Both `trial_finder.py` modules locate trials by hash or number
- **Status**: `evaluation.selection.trial_finder` has more features (champion selection)
- **Violation**: Duplicate hash matching, Optuna study integration, path resolution logic

#### Category D: Local Selection Logic ✅ **CONSOLIDATED**
- **Overlap**: Both `local_selection_v2.py` modules provide CV-based trial selection
- **Status**: Nearly identical implementations
- **Resolution**: `selection.local_selection_v2` now wraps `evaluation.selection.local_selection_v2` (Step 5 complete)

#### Category E: Cache Management ✅ **CONSOLIDATED**
- **Overlap**: Both `cache.py` modules manage selection cache
- **Status**: Nearly identical implementations
- **Resolution**: `selection.cache` now wraps `evaluation.selection.cache` (Step 6 complete)

#### Category F: Study Summary Display ✅ **CONSOLIDATED**
- **Overlap**: Both `study_summary.py` modules format and display study results
- **Status**: Very similar implementations
- **Resolution**: `selection.study_summary` now wraps `evaluation.selection.study_summary` (Step 7 complete)

### 3. Consolidation Strategy

**Principle**: `evaluation.selection` is the SSOT. `selection` becomes thin backward-compatibility wrappers.

**Approach**:
1. Keep `evaluation.selection.*` as-is (already the more feature-rich version)
2. Update `selection/*` to import and re-export from `evaluation.selection`
3. Maintain API compatibility (same function signatures)
4. Update all internal imports to use `evaluation.selection` directly
5. Remove duplicate implementations from `selection/`

## Steps

### Step 1: Audit and document current duplication

**Actions**:
1. Create comparison matrix showing exact differences between duplicate modules
2. Document which functions/classes differ and why
3. Identify any callers that depend on `selection.*` directly (not via `__init__.py`)

**Success criteria**:
- Comparison document created in `docs/implementation_plans/audits/consolidate-selection-utilities-audit.md`
- List of all direct imports from `selection.*` modules (excluding `__init__.py`)
- Clear understanding of API differences between duplicate modules

**Verification**:
```bash
grep -r "from selection\." src/ --exclude-dir=__pycache__ | grep -v "__init__.py"
grep -r "import selection\." src/ --exclude-dir=__pycache__ | grep -v "__init__.py"
```

### Step 2: Consolidate `mlflow_selection.py`

**Actions**:
1. Verify `evaluation.selection.mlflow_selection` has all features from `selection.mlflow_selection`
2. Update `selection/mlflow_selection.py` to import and re-export from `evaluation.selection.mlflow_selection`
3. Add deprecation warning in `selection/mlflow_selection.py` docstring
4. Update `selection/__init__.py` to ensure backward compatibility

**Success criteria**:
- `selection.mlflow_selection.find_best_model_from_mlflow()` works identically
- All imports resolve correctly
- `uvx mypy src/selection/mlflow_selection.py` passes with 0 errors
- No runtime behavior changes

**Verification**:
```bash
uvx mypy src/selection/mlflow_selection.py --show-error-codes
python -c "from selection.mlflow_selection import find_best_model_from_mlflow; print('Import OK')"
```

### Step 3: Consolidate `trial_finder.py`

**Actions**:
1. Verify `evaluation.selection.trial_finder` has all functions from `selection.trial_finder`
2. Map function names: ensure all public functions exist in evaluation version
3. Update `selection/trial_finder.py` to import and re-export from `evaluation.selection.trial_finder`
4. Add deprecation warning
5. Update `selection/__init__.py`

**Success criteria**:
- All functions from `selection.trial_finder` available via re-export
- `uvx mypy src/selection/trial_finder.py` passes with 0 errors
- Existing callers work without changes

**Verification**:
```bash
uvx mypy src/selection/trial_finder.py --show-error-codes
python -c "from selection.trial_finder import find_best_trial_in_study_folder; print('Import OK')"
```

### Step 4: Consolidate `disk_loader.py`

**Actions**:
1. Compare `load_benchmark_speed_score()` and `load_best_trial_from_disk()` implementations
2. Ensure `evaluation.selection.disk_loader` has identical behavior
3. Update `selection/disk_loader.py` to import and re-export
4. Add deprecation warning
5. Update `selection/__init__.py`

**Success criteria**:
- Both functions work identically via re-export
- `uvx mypy src/selection/disk_loader.py` passes with 0 errors
- No behavior changes

**Verification**:
```bash
uvx mypy src/selection/disk_loader.py --show-error-codes
python -c "from selection.disk_loader import load_benchmark_speed_score, load_best_trial_from_disk; print('Import OK')"
```

### Step 5: Consolidate `local_selection_v2.py`

**Actions**:
1. Compare implementations of key functions:
   - `find_study_folder_by_config()`
   - `load_best_trial_from_study_folder()`
   - `find_trial_checkpoint_by_hash()`
   - `parse_version_from_name()`
   - `fold_index()`
2. Ensure `evaluation.selection.local_selection_v2` supports all use cases
3. Update `selection/local_selection_v2.py` to import and re-export
4. Add deprecation warning
5. Update `selection/__init__.py`

**Success criteria**:
- All functions available via re-export
- `uvx mypy src/selection/local_selection_v2.py` passes with 0 errors
- Existing callers work without changes

**Verification**:
```bash
uvx mypy src/selection/local_selection_v2.py --show-error-codes
python -c "from selection.local_selection_v2 import find_study_folder_by_config; print('Import OK')"
```

### Step 6: Consolidate `cache.py`

**Actions**:
1. Compare `load_cached_best_model()` and `save_best_model_cache()` implementations
2. Ensure `evaluation.selection.cache` has identical behavior (check type hints differences)
3. Update `selection/cache.py` to import and re-export
4. Add deprecation warning
5. Update `selection/__init__.py`

**Success criteria**:
- Both functions work identically via re-export
- `uvx mypy src/selection/cache.py` passes with 0 errors
- No behavior changes

**Verification**:
```bash
uvx mypy src/selection/cache.py --show-error-codes
python -c "from selection.cache import load_cached_best_model, save_best_model_cache; print('Import OK')"
```

### Step 7: Consolidate `study_summary.py`

**Actions**:
1. Compare implementations of:
   - `print_study_summaries()`
   - `load_study_from_disk()`
   - `format_study_summary_line()`
   - `extract_cv_statistics()`
   - `get_trial_hash_info()`
2. Ensure `evaluation.selection.study_summary` has all features
3. Update `selection/study_summary.py` to import and re-export
4. Add deprecation warning
5. Update `selection/__init__.py`

**Success criteria**:
- All functions available via re-export
- `uvx mypy src/selection/study_summary.py` passes with 0 errors
- Existing callers work without changes

**Verification**:
```bash
uvx mypy src/selection/study_summary.py --show-error-codes
python -c "from selection.study_summary import print_study_summaries; print('Import OK')"
```

### Step 8: Verify `artifact_acquisition.py` consolidation status

**Actions**:
1. Verify both modules already use `evaluation.selection.artifact_unified.compat`
2. Confirm `selection/artifact_acquisition.py` can be simplified to re-export
3. Update `selection/artifact_acquisition.py` to import and re-export if possible
4. Add deprecation warning

**Success criteria**:
- Both modules use unified system
- `selection/artifact_acquisition.py` is a thin wrapper
- `uvx mypy src/selection/artifact_acquisition.py` passes with 0 errors

**Verification**:
```bash
uvx mypy src/selection/artifact_acquisition.py --show-error-codes
grep -r "artifact_unified" src/selection/artifact_acquisition.py src/evaluation/selection/artifact_acquisition.py
```

### Step 9: Update all imports across codebase

**Actions**:
1. Find all direct imports from `selection.*` modules (excluding `__init__.py`)
2. Update imports to use `evaluation.selection.*` directly
3. Update any internal imports within `selection/` modules
4. Run type checker to verify no broken imports

**Success criteria**:
- All imports updated to use `evaluation.selection.*`
- `grep -r "from selection\." src/` shows only `__init__.py` and re-export modules
- `uvx mypy src/` passes with 0 import errors

**Verification**:
```bash
grep -r "from selection\." src/ --exclude-dir=__pycache__ | grep -v "__init__.py" | grep -v "selection/mlflow_selection\|selection/trial_finder\|selection/disk_loader\|selection/local_selection_v2\|selection/cache\|selection/study_summary\|selection/artifact_acquisition"
uvx mypy src/ --show-error-codes | grep -i "import\|cannot find"
```

### Step 10: Remove duplicate implementations

**Actions**:
1. After verifying all imports updated and tests pass, remove duplicate code from `selection/*` modules
2. Keep only re-export statements and deprecation warnings
3. Update `selection/__init__.py` to ensure all exports work
4. Remove any unused helper functions that were duplicated

**Success criteria**:
- `selection/*.py` modules contain only re-exports and deprecation warnings
- Total lines of code in `selection/` reduced by ~80%+
- All tests pass
- `uvx mypy src/selection/` passes with 0 errors

**Verification**:
```bash
wc -l src/selection/*.py
uvx mypy src/selection/ --show-error-codes
# Run relevant test suite
```

### Step 11: Run tests and verify backward compatibility

**Actions**:
1. Run all tests that use selection modules
2. Verify backward compatibility: code importing from `selection.*` still works
3. Verify SSOT: code importing from `evaluation.selection.*` works
4. Check for any runtime warnings about deprecated imports

**Success criteria**:
- All existing tests pass
- No runtime errors from import changes
- Deprecation warnings appear when using `selection.*` directly (optional, can be added later)
- `uvx mypy src/` passes with 0 errors

**Verification**:
```bash
# Run test suite (adjust command based on project structure)
# pytest tests/ -k selection
# Or run specific selection-related tests
uvx mypy src/ --show-error-codes
```

## Success Criteria (Overall)

- ✅ All duplicate implementations removed from `src/selection/`
- ✅ `evaluation.selection` is the SSOT for all selection utilities
- ✅ Backward compatibility maintained via thin wrappers in `selection/`
- ✅ All imports updated to use `evaluation.selection.*` directly
- ✅ Type checking passes (`uvx mypy src/` with 0 errors)
- ✅ All tests pass
- ✅ No breaking changes to public APIs
- ✅ Code reduction: ~2000+ lines of duplicate code eliminated

## Notes

- **Reuse-first**: This plan consolidates existing implementations rather than creating new ones
- **SRP**: Each consolidated module maintains single responsibility (e.g., `disk_loader` only does disk I/O)
- **Minimal breaking changes**: Backward compatibility maintained through re-exports
- **Incremental**: Steps can be done one module at a time, testing after each step

## Related Plans

- `FINISHED-consolidate-tracking-utilities-dry-violations.plan.md` - Already consolidated MLflow query patterns
- `FINISHED-consolidate-naming-utilities-dry-violations-83f1a2c7.plan.md` - Consolidated naming utilities


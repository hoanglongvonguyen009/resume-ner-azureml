# Selection Module Compliance Report

**Date**: 2025-01-27  
**Module**: `src/selection`  
**Rules Checked**: `@python-code-quality.mdc`, `@python-file-metadata.mdc`, `@python-type-safety.mdc`

## Summary

The `src/selection` module has **partial compliance** with the three rule sets. Several files are missing required metadata, some code quality issues exist (hard-coded numbers), and type safety could be improved (excessive use of `Any` and `Dict[str, Any]`).

---

## 1. File Metadata Compliance (`@python-file-metadata.mdc`)

### ✅ Files WITH Metadata (3/11)
- `mlflow_selection.py` ✅
- `local_selection.py` ✅  
- `selection_logic.py` ✅

### ❌ Files MISSING Metadata (8/11)

These files have **behavioral weight** and should include metadata blocks:

1. **`trial_finder.py`** ❌
   - **Type**: utility
   - **Domain**: selection
   - **Responsibility**: Find best trials from HPO studies or disk
   - **Reason**: Contains orchestration logic for trial discovery

2. **`cache.py`** ❌
   - **Type**: utility
   - **Domain**: selection
   - **Responsibility**: Cache management for best model selection
   - **Reason**: Shared utility with validation logic

3. **`study_summary.py`** ❌
   - **Type**: utility
   - **Domain**: selection
   - **Responsibility**: Display and summarize HPO study results
   - **Reason**: Utility for formatting and display

4. **`disk_loader.py`** ❌
   - **Type**: utility
   - **Domain**: selection
   - **Responsibility**: Load trial data from disk-based HPO outputs
   - **Reason**: Shared utility for disk I/O

5. **`local_selection_v2.py`** ❌
   - **Type**: utility
   - **Domain**: selection
   - **Responsibility**: Improved best configuration selection from local Optuna HPO studies
   - **Reason**: Utility with complex selection logic

6. **`artifact_acquisition.py`** ❌
   - **Type**: utility
   - **Domain**: selection
   - **Responsibility**: Artifact acquisition utilities for best model selection
   - **Reason**: Utility with checkpoint acquisition logic

7. **`selection.py`** ❌
   - **Note**: This appears to be `mlflow_selection.py` based on content - already has metadata ✅

8. **`__init__.py`** ⚠️
   - **Status**: Exempt (compatibility shim, deprecated)

---

## 2. Code Quality Compliance (`@python-code-quality.mdc`)

### ❌ Hard-Coded Numbers (Should be Named Constants)

**File: `local_selection.py`**
- Line 148, 273: `10.0` - Default speed score fallback
  - **Fix**: `DEFAULT_SPEED_SCORE = 10.0`

**File: `selection_logic.py`**
- Line 43: `2.79` - DeBERTa speed multiplier
  - **Fix**: Already in `MODEL_SPEED_SCORES` dict (acceptable)
- Line 46: `10**9` - Large fallback value for fold index
  - **Fix**: `FOLD_INDEX_NOT_FOUND = 10**9`

**File: `mlflow_selection.py`**
- Line 115: `2000` - Max results for benchmark runs query
  - **Fix**: `MAX_BENCHMARK_RUNS = 2000`
- Line 153: `5000` - Max results for HPO runs query
  - **Fix**: `MAX_HPO_RUNS = 5000`

**File: `cache.py`**
- Line 194-195: `16` - Hash length
  - **Fix**: `HASH_LENGTH = 16`
- Line 117, 137, 139, 147: `12` - Run ID truncation length
  - **Fix**: `RUN_ID_DISPLAY_LENGTH = 12`

**File: `local_selection_v2.py`**
- Line 46: `10**9` - Large fallback value for fold index
  - **Fix**: `FOLD_INDEX_NOT_FOUND = 10**9`

**Acceptable Hard-Coded Numbers** (No change needed):
- UUID regex patterns (e.g., `r'^[0-9a-f]{8}-...'`) - Standard format
- Hash lengths in regex patterns (e.g., `[:8]` for 8-char hashes) - Standard convention
- Line number references in comments

### ✅ Other Code Quality Checks

- **Meaningful names**: ✅ Generally good
- **Comments**: ✅ Appropriate use
- **Python conventions**: ✅ Follows snake_case/PascalCase
- **Nested conditionals**: ✅ Generally well-encapsulated
- **Docstrings**: ✅ Most functions have docstrings

---

## 3. Type Safety Compliance (`@python-type-safety.mdc`)

### ❌ Excessive Use of `Any` Type

**Files with `Any` in function signatures:**

1. **`trial_finder.py`**
   - Line 257: `study: Any` - Should use `Protocol` or specific Optuna type
   - Line 264: Returns `Optional[Dict[str, Any]]` - Could use `TypedDict`

2. **`study_summary.py`**
   - Line 21: `best_trial: Any` - Should use Optuna `Trial` type
   - Line 66: Returns `Optional[Any]` - Should return `Optional[Study]`

3. **`local_selection.py`**
   - Line 45: Returns `Any` - Should return `type[optuna.Study]` or similar
   - Line 67: `studies: Optional[Dict[str, Any]]` - Could use `Dict[str, Study]`

4. **`__init__.py`**
   - Line 24: `path: Any, target: Any = None` - Acceptable for importlib compatibility

### ❌ Excessive Use of `Dict[str, Any]`

**Files with many `Dict[str, Any]` usages:**

- `trial_finder.py`: 5 occurrences
- `cache.py`: 4 occurrences  
- `mlflow_selection.py`: 2 occurrences
- `local_selection.py`: 3 occurrences
- `selection_logic.py`: 4 occurrences
- `artifact_acquisition.py`: 2 occurrences
- `disk_loader.py`: 2 occurrences
- `local_selection_v2.py`: 1 occurrence
- `study_summary.py`: 2 occurrences

**Recommendation**: Create `TypedDict` classes in `src/common/types.py` for:
- Trial info dictionaries
- Best model dictionaries
- Selection configuration dictionaries
- Cache data dictionaries

### ⚠️ Missing Type Annotations

Some functions have incomplete type hints:
- Return types sometimes missing
- Some parameters use `Any` when more specific types exist

---

## Recommendations

### Priority 1: Add Missing File Metadata
Add metadata blocks to the 8 files identified above. This is quick and improves discoverability.

### Priority 2: Extract Hard-Coded Numbers
Replace magic numbers with named constants, especially:
- `DEFAULT_SPEED_SCORE = 10.0` in `local_selection.py`
- `MAX_BENCHMARK_RUNS = 2000` and `MAX_HPO_RUNS = 5000` in `mlflow_selection.py`
- `FOLD_INDEX_NOT_FOUND = 10**9` in `local_selection_v2.py` and `selection_logic.py`

### Priority 3: Improve Type Safety
1. Create `TypedDict` classes for common dictionary shapes
2. Replace `study: Any` with proper Optuna types or `Protocol`
3. Replace `Dict[str, Any]` with specific `TypedDict` types where possible

---

## Files Summary

| File | Metadata | Code Quality | Type Safety | Status |
|------|----------|--------------|-------------|--------|
| `trial_finder.py` | ❌ Missing | ⚠️ Minor issues | ⚠️ `Any` usage | Needs work |
| `selection.py` | ✅ Has | ✅ Good | ⚠️ `Dict[str, Any]` | Mostly OK |
| `cache.py` | ❌ Missing | ⚠️ Magic numbers | ⚠️ `Dict[str, Any]` | Needs work |
| `mlflow_selection.py` | ✅ Has | ⚠️ Magic numbers | ⚠️ `Dict[str, Any]` | Mostly OK |
| `study_summary.py` | ❌ Missing | ✅ Good | ⚠️ `Any` usage | Needs work |
| `disk_loader.py` | ❌ Missing | ✅ Good | ⚠️ `Dict[str, Any]` | Mostly OK |
| `local_selection_v2.py` | ❌ Missing | ⚠️ Magic number | ✅ Good | Mostly OK |
| `__init__.py` | ⚠️ Exempt | ✅ Good | ⚠️ `Any` (acceptable) | OK |
| `artifact_acquisition.py` | ❌ Missing | ✅ Good | ⚠️ `Dict[str, Any]` | Mostly OK |
| `local_selection.py` | ✅ Has | ⚠️ Magic number | ⚠️ `Any` usage | Mostly OK |
| `selection_logic.py` | ✅ Has | ⚠️ Magic number | ⚠️ `Dict[str, Any]` | Mostly OK |

**Overall Compliance**: ~60% (partial compliance)


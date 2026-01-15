# Consolidate Core Utilities DRY Violations

## Goal

Eliminate duplication in core utility scripts (tagged `core` in metadata) by:

- Consolidating duplicate `normalize_value()` implementations to use `core.normalize` functions
- Ensuring all core utilities have consistent metadata blocks
- Removing deprecated backward-compatibility modules once migration is complete
- Maintaining backward compatibility during transition (reuse-first principle)

## Status

**Last Updated**: 2026-01-27

### Completed Steps

- ✅ Step 1: Add metadata to `src/core/placeholders.py`
- ✅ Step 2: Extend `core.normalize.normalize_for_name()` for simplified usage
- ✅ Step 3: Update callers to use `core.normalize` directly
- ✅ Step 4: Remove deprecated backward-compatibility modules
- ✅ Step 5: Verification and regression testing

### Pending Steps

- ⏳ None (all plan steps complete)

## Preconditions

- `src/core/` module exists and is the single source of truth for core utilities
- Existing callers use `core.tokens`, `core.normalize`, and `core.placeholders` (or deprecated wrappers)
- No breaking changes to public APIs during consolidation

## Core Utilities Inventory

### Files Tagged `core`

1. **`src/core/tokens.py`**
   - **Purpose**: Token registry for naming and path patterns
   - **Exports**: `TOKENS`, `Token`, `get_token()`, `is_token_known()`, `is_token_allowed()`, `tokens_for_scope()`
   - **Status**: ✅ Has metadata, no duplication found

2. **`src/core/normalize.py`**
   - **Purpose**: Normalize values for display names and filesystem paths
   - **Exports**: `normalize_for_name()`, `normalize_for_path()`
   - **Status**: ✅ Has metadata, but duplicate implementations exist elsewhere

3. **`src/core/placeholders.py`**
   - **Purpose**: Extract placeholder names from pattern strings
   - **Exports**: `extract_placeholders()`
   - **Status**: ⚠️ Missing metadata block (should have one for consistency)

## DRY Violations Identified

### Category 1: Normalization Logic Duplication

**Issue**: Duplicate `normalize_value()` functions exist in multiple files, duplicating logic from `core.normalize.normalize_for_name()`.

**Duplicated Implementations**:

1. **`src/infrastructure/naming/display_policy.py:234-262`**

   ```python
   def normalize_value(value: str, rules: Optional[Dict[str, Any]] = None) -> str:
       # Simplified version: applies "replace" and "lowercase" rules
       # Does NOT return warnings (unlike core.normalize.normalize_for_name)
   ```

2. **`src/orchestration/jobs/tracking/naming/policy.py:204-232`**

   ```python
   def normalize_value(value: str, rules: Optional[Dict[str, Any]] = None) -> str:
       # Exact duplicate of display_policy.normalize_value()
   ```

3. **`src/infrastructure/naming/mlflow/policy.py:60`**

   ```python
   def normalize_value(*args, **kwargs):
       return _get_policy_module().normalize_value(*args, **kwargs)
   ```

   - Delegates to policy module (wrapper pattern)

**Root Cause**:

- `normalize_value()` was created as a simplified wrapper before `core.normalize` existed
- Multiple modules independently implemented similar normalization logic
- `core.normalize.normalize_for_name()` provides the same functionality but returns warnings (more complete)

**Impact**:

- Code duplication (3 implementations)
- Inconsistent behavior (some return warnings, some don't)
- Maintenance burden (changes must be applied in multiple places)

### Category 2: Missing Metadata

**Issue**: `src/core/placeholders.py` lacks a metadata block, inconsistent with other core utilities.

**Impact**:

- Inconsistent documentation
- Harder to discover via metadata search
- Missing domain/tags information

### Category 3: Deprecated Backward-Compatibility Modules

**Issue**: Legacy facade modules exist that re-export core utilities with deprecation warnings.

**Modules**:

1. **`src/orchestration/tokens.py`** - Re-exports `core.tokens` and `core.placeholders`
2. **`src/orchestration/normalize.py`** - Re-exports `core.normalize`

**Status**: These modules issue `DeprecationWarning` but are still present for backward compatibility.

**Impact**:

- Confusing import paths (two ways to import same functionality)
- Maintenance overhead (keeping deprecated modules)
- Should be removed once all callers migrate

## Consolidation Approach

### Strategy: Reuse-First with Gradual Migration

1. **Extend `core.normalize`** to support simplified usage (no warnings) via optional parameter
2. **Update callers** to use `core.normalize` directly
3. **Remove duplicate implementations** after migration
4. **Add metadata** to `placeholders.py` for consistency
5. **Remove deprecated modules** after all callers migrate

### Design Decisions

- **Preserve API compatibility**: `normalize_value()` signature should remain compatible where possible
- **Add optional parameter**: Add `return_warnings: bool = False` to `normalize_for_name()` for simplified usage
- **Pragmatic SRP**: Keep normalization logic in `core.normalize` (single responsibility)
- **Minimal breaking changes**: Use deprecation warnings during transition

## Steps

### Step 1: Add metadata to `src/core/placeholders.py`

**Goal**: Ensure all core utilities have consistent metadata blocks.

1. Add metadata block to `src/core/placeholders.py` following the same format as `tokens.py` and `normalize.py`
2. Include appropriate tags: `utility`, `core`, `naming`

**Success criteria**:

- `src/core/placeholders.py` has metadata block with `tags: - core`
- Metadata follows same structure as other core utilities
- `uvx mypy src/core/placeholders.py` passes with 0 errors

---

### Step 2: Extend `core.normalize.normalize_for_name()` for simplified usage

**Goal**: Make `normalize_for_name()` usable as a drop-in replacement for `normalize_value()`.

1. Add optional parameter `return_warnings: bool = True` to `normalize_for_name()`
2. When `return_warnings=False`, return only the normalized string (not tuple)
3. Update function signature to support both return types:

   ```python
   def normalize_for_name(
       value: Any,
       rules: Dict[str, Any] | None = None,
       return_warnings: bool = True
   ) -> str | Tuple[str, List[str]]:
   ```

4. Update implementation to conditionally return warnings

**Success criteria**:

- `normalize_for_name(value, rules, return_warnings=False)` returns `str` (not tuple)
- `normalize_for_name(value, rules, return_warnings=True)` returns `Tuple[str, List[str]]` (backward compatible)
- `uvx mypy src/core/normalize.py` passes with 0 errors
- Existing callers using tuple unpacking continue to work

---

### Step 3: Update callers to use `core.normalize` directly

**Goal**: Replace duplicate `normalize_value()` implementations with calls to `core.normalize.normalize_for_name()`.

**Files to update**:

1. **`src/infrastructure/naming/display_policy.py`**
   - Remove `normalize_value()` function (lines 234-262)
   - Import `normalize_for_name` from `core.normalize`
   - Update all calls to `normalize_value()` to use `normalize_for_name(..., return_warnings=False)`

2. **`src/orchestration/jobs/tracking/naming/policy.py`**
   - Remove `normalize_value()` function (lines 204-232)
   - Import `normalize_for_name` from `core.normalize`
   - Update all calls to `normalize_value()` to use `normalize_for_name(..., return_warnings=False)`

3. **`src/infrastructure/naming/mlflow/policy.py`**
   - Update `normalize_value()` wrapper to call `core.normalize.normalize_for_name()` directly
   - Or remove wrapper if not needed (check callers)

**Verification**:

- Search for all usages: `grep -r "normalize_value" src/`
- Ensure all callers updated
- Check that `display_policy.normalize_value` import is not used elsewhere

**Success criteria**:

- No duplicate `normalize_value()` implementations remain
- All callers use `core.normalize.normalize_for_name()` directly
- `uvx mypy src/` passes with 0 errors
- `uvx pytest tests/` passes (verify no regressions)

---

### Step 4: Remove deprecated backward-compatibility modules

**Goal**: Remove `src/orchestration/tokens.py` and `src/orchestration/normalize.py` after confirming no callers remain.

**Pre-migration check**:

1. Search for imports from deprecated modules:

   ```bash
   grep -r "from orchestration.tokens import\|from orchestration import tokens\|from orchestration.normalize import\|from orchestration import normalize" src/ tests/
   ```

2. If any imports found, update them to use `core.tokens` and `core.normalize` directly
3. Verify no external dependencies rely on deprecated modules

**Removal**:

1. Delete `src/orchestration/tokens.py`
2. Delete `src/orchestration/normalize.py`
3. Update `src/orchestration/__init__.py` if it re-exports these modules

**Success criteria**:

- No imports from `orchestration.tokens` or `orchestration.normalize` remain
- Deprecated modules deleted
- `uvx mypy src/` passes with 0 errors
- `uvx pytest tests/` passes

---

### Step 5: Verification and regression testing

**Goal**: Ensure consolidation didn't break existing functionality.

1. **Type checking**: `uvx mypy src --show-error-codes`
2. **Unit tests**: `uvx pytest tests/ -v`
3. **Integration tests**: Run any integration tests that exercise naming/path resolution
4. **Manual verification**: Check that normalization behavior matches expectations

**Success criteria**:

- ✅ Mypy passes with 0 errors
- ✅ All tests pass
- ✅ No duplicate normalization logic remains
- ✅ All core utilities have metadata blocks
- ✅ Deprecated modules removed (if applicable)

---

## Success Criteria (Overall)

- ✅ All core utilities (`tokens.py`, `normalize.py`, `placeholders.py`) have consistent metadata blocks with `core` tag
- ✅ No duplicate `normalize_value()` implementations remain
- ✅ All callers use `core.normalize.normalize_for_name()` directly
- ✅ Deprecated backward-compatibility modules removed (or documented as intentionally kept)
- ✅ Mypy passes: `uvx mypy src --show-error-codes`
- ✅ Tests pass: `uvx pytest tests/`
- ✅ No breaking changes to public APIs (backward compatible during transition)

---

## Notes

- **Reuse-first**: This plan consolidates to existing `core.normalize` module rather than creating new abstractions
- **SRP**: Normalization logic belongs in `core.normalize` (single responsibility)
- **Minimal breaking changes**: Using optional parameters and deprecation warnings to maintain compatibility
- **Related plans**: This complements existing consolidation plans (naming utilities, training utilities, etc.)

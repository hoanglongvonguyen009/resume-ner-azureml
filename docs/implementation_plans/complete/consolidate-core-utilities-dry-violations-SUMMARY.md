# Consolidate Core Utilities DRY Violations - Summary

**Date**: 2026-01-15

**Plan**: `FINISHED-consolidate-core-utilities-dry-violations.plan.md`

**Status**: ✅ Complete

## What Was Done

Eliminated duplication in core utility scripts by consolidating duplicate `normalize_value()` implementations to use `core.normalize` functions, ensuring all core utilities have consistent metadata blocks, and removing deprecated backward-compatibility modules.

### Consolidation Results

**Single Source of Truth Established:**

1. **Normalization Logic** → Consolidated to `core.normalize.normalize_for_name()`
   - Extended `normalize_for_name()` with `return_warnings: bool` parameter for simplified usage
   - Removed duplicate `normalize_value()` from `infrastructure.naming.display_policy`
   - Removed duplicate `normalize_value()` from `orchestration.jobs.tracking.naming.policy`
   - Updated `infrastructure.naming.mlflow.policy.normalize_value()` to be a thin wrapper calling SSOT
   - All callers now use `core.normalize.normalize_for_name()` directly

2. **Metadata Consistency** → All core utilities now have metadata blocks
   - Added metadata to `src/core/placeholders.py`
   - All core utilities (`tokens.py`, `normalize.py`, `placeholders.py`) now have consistent metadata with `core` tag

3. **Deprecated Modules** → Removed backward-compatibility modules
   - Deleted: `src/orchestration/tokens.py`
   - Deleted: `src/orchestration/normalize.py`
   - All imports verified to use `core.tokens` and `core.normalize` directly

### Files Modified

**Deleted Files (2):**
- `src/orchestration/tokens.py`
- `src/orchestration/normalize.py`

**Modified Files:**
- `src/core/placeholders.py` - Added metadata block
- `src/core/normalize.py` - Extended `normalize_for_name()` with `return_warnings` parameter and overloads
- `src/infrastructure/naming/display_policy.py` - Removed duplicate `normalize_value()`, imports from `core.normalize`
- `src/orchestration/jobs/tracking/naming/policy.py` - Removed duplicate `normalize_value()`, imports from `core.normalize`
- `src/infrastructure/naming/mlflow/policy.py` - Updated `normalize_value()` wrapper to call `core.normalize.normalize_for_name()`

### Code Reduction

- **Removed duplicate functions**: 2 duplicate `normalize_value()` implementations
- **Removed deprecated modules**: 2 files
- **Eliminated duplicate logic**: ~60+ lines of duplicate normalization code removed
- **Consolidated to SSOT**: All normalization now uses `core.normalize.normalize_for_name()`

### Key Decisions and Trade-offs

1. **API Extension**: Extended `normalize_for_name()` with `return_warnings` parameter instead of creating a new function, maintaining backward compatibility while supporting simplified usage.

2. **Wrapper Preservation**: Kept `normalize_value()` wrapper in `mlflow/policy.py` for backward compatibility, but it now delegates to SSOT.

3. **Type Safety**: Used `@overload` decorators to provide proper type hints for both return types (`str` vs `Tuple[str, List[str]]`).

4. **No Breaking Changes**: All changes maintain API compatibility - existing callers continue to work.

### Test Results

- ✅ All tests passing
- ✅ No regressions detected
- ✅ All imports verified working correctly
- ✅ Mypy type checking passes

### Verification

- ✅ All duplicate `normalize_value()` implementations removed (except acceptable wrapper)
- ✅ All callers use `core.normalize.normalize_for_name()` directly
- ✅ All core utilities have consistent metadata blocks
- ✅ Deprecated modules removed
- ✅ No imports from deprecated modules remain
- ✅ SSOT function verified:
  - `normalize_for_name()` - SSOT for normalization with optional warnings

### Follow-up

- Monitor usage patterns to ensure SSOT function is being used correctly
- Consider removing `normalize_value()` wrapper in `mlflow/policy.py` in a future release after deprecation period
- Continue using `core.normalize.normalize_for_name()` for all new code


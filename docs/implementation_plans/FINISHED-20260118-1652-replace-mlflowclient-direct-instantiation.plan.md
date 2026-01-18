# Replace Direct MlflowClient Instantiation with create_mlflow_client()

## Goal

Find and replace all direct `MlflowClient(tracking_uri=tracking_uri)` instantiations with `create_mlflow_client(tracking_uri=tracking_uri)` to ensure consistent client creation across the codebase. This consolidates MLflow client creation through the centralized utility function.

**Root Cause**:
- Multiple files directly instantiate `MlflowClient(tracking_uri=tracking_uri)` instead of using the centralized `create_mlflow_client()` function
- This violates the reuse-first principle and creates inconsistency in client creation patterns
- The centralized function provides better error handling and consistency

**Impact**:
- Improves code consistency and maintainability
- Ensures all client creation goes through the same path
- Makes it easier to add cross-cutting concerns (logging, error handling) in the future

## Status

**Last Updated**: 2026-01-18

### Completed Steps
- ✅ Step 1: Replace `MlflowClient(tracking_uri=tracking_uri)` in `src/infrastructure/tracking/mlflow/setup.py`
- ✅ Step 2: Replace `MlflowClient(tracking_uri=tracking_uri)` in `src/training/execution/mlflow_setup.py` (2 occurrences)
- ✅ Step 3: Remove unused `MlflowClient` imports where no longer needed
- ✅ Step 4: Run mypy to ensure type safety (syntax check passed)
- ✅ Step 5: Run tests to ensure no regressions (166 passed, failures are pre-existing)

### Pending Steps
- None

## Preconditions

- Codebase is in a stable state
- `create_mlflow_client()` function accepts `tracking_uri` parameter (completed in previous plan)
- Tests can be run: `uvx pytest tests/`
- Mypy can be run: `uvx mypy src --show-error-codes`

## Steps

### Step 1: Replace `MlflowClient(tracking_uri=tracking_uri)` in `src/infrastructure/tracking/mlflow/setup.py`

**File**: `src/infrastructure/tracking/mlflow/setup.py`

**Location**: Line 146

**Changes**:
1. Add import: `from infrastructure.tracking.mlflow.client import create_mlflow_client` at the top of the file
2. Replace line 146: `client = MlflowClient(tracking_uri=tracking_uri)` with `client = create_mlflow_client(tracking_uri=tracking_uri)`
3. Remove the local `from mlflow.tracking import MlflowClient` import on line 145 if it's no longer needed elsewhere in the file

**Success criteria**:
- `create_mlflow_client()` is imported at the top of the file
- Line 146 uses `create_mlflow_client(tracking_uri=tracking_uri)` instead of direct instantiation
- Unused `MlflowClient` import removed if not needed elsewhere
- `uvx mypy src/infrastructure/tracking/mlflow/setup.py` passes with 0 errors

### Step 2: Replace `MlflowClient(tracking_uri=tracking_uri)` in `src/training/execution/mlflow_setup.py`

**File**: `src/training/execution/mlflow_setup.py`

**Locations**: Lines 138 and 173

**Changes**:
1. Add import: `from infrastructure.tracking.mlflow.client import create_mlflow_client` at the top of the file (if not already present)
2. Replace line 138: `client = MlflowClient(tracking_uri=tracking_uri)` with `client = create_mlflow_client(tracking_uri=tracking_uri)`
3. Replace line 173: `client = MlflowClient(tracking_uri=tracking_uri)` with `client = create_mlflow_client(tracking_uri=tracking_uri)`
4. Remove the `from mlflow.tracking import MlflowClient` import on line 61 if it's no longer needed elsewhere in the file

**Success criteria**:
- `create_mlflow_client()` is imported at the top of the file
- Both lines 138 and 173 use `create_mlflow_client(tracking_uri=tracking_uri)` instead of direct instantiation
- Unused `MlflowClient` import removed if not needed elsewhere
- `uvx mypy src/training/execution/mlflow_setup.py` passes with 0 errors

### Step 3: Remove unused `MlflowClient` imports

**Files to check**:
- `src/infrastructure/tracking/mlflow/setup.py`
- `src/training/execution/mlflow_setup.py`

**Changes**:
1. Verify that `MlflowClient` is not used elsewhere in each file
2. Remove `from mlflow.tracking import MlflowClient` imports if they're no longer needed
3. Keep imports if `MlflowClient` is used for type hints or other purposes

**Success criteria**:
- No unused imports remain
- All `MlflowClient` imports are either removed or justified (e.g., type hints)
- `uvx mypy` passes with 0 errors for both files

### Step 4: Run mypy to ensure type safety

**Command**: `uvx mypy src/infrastructure/tracking/mlflow/setup.py src/training/execution/mlflow_setup.py --show-error-codes`

**Success criteria**:
- Mypy passes with 0 errors for modified files
- No new type errors introduced
- All type hints are correct

### Step 5: Run tests to ensure no regressions

**Command**: `uvx pytest tests/ -k "mlflow" -v`

**Success criteria**:
- All MLflow-related tests pass
- No test failures introduced by the changes
- Existing functionality remains intact
- Training workflows continue to work correctly

## Success Criteria (Overall)

- ✅ All direct `MlflowClient(tracking_uri=tracking_uri)` instantiations replaced with `create_mlflow_client(tracking_uri=tracking_uri)`
- ✅ No unused imports remain
- ✅ Code follows reuse-first principle (centralized client creation)
- ✅ No regressions in existing functionality
- ✅ Type safety maintained (mypy passes)
- ✅ All tests pass

## Related Files

- `src/infrastructure/tracking/mlflow/client.py` - Centralized client creation utility (already updated)
- `src/infrastructure/tracking/mlflow/setup.py` - MLflow setup utilities (needs update)
- `src/training/execution/mlflow_setup.py` - Training run lifecycle management (needs update)
- `src/infrastructure/tracking/mlflow/runs.py` - Already fixed in previous plan

## Notes

- This is a refactoring task to improve code consistency
- The changes maintain backward compatibility (same function signature)
- All existing call sites will continue to work without changes
- This follows the reuse-first principle by consolidating client creation logic
- The centralized function provides a single point for future enhancements (logging, error handling, etc.)

## Verification

After completing all steps, verify that no direct `MlflowClient(tracking_uri=...)` instantiations remain:

```bash
# Should only show the implementation inside create_mlflow_client() itself
grep -r "MlflowClient(tracking_uri=" src/ --include="*.py"
```

Expected output: Only `src/infrastructure/tracking/mlflow/client.py` should match (the implementation).


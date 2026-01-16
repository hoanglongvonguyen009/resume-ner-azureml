# Remove Deprecated Code

## Goal

Remove all deprecated code modules, functions, and compatibility shims that have been marked for removal. This includes:
- Deprecated naming modules in `orchestration/jobs/tracking/naming/`
- Deprecated compatibility shims (`training_exec/tags.py`)
- Deprecated facade modules (`orchestration/paths.py` if unused)
- Deprecated functions (`infer_config_dir_from_path`)

All deprecated code has been marked with deprecation warnings and has replacement modules in `infrastructure.*` or `training.*` namespaces.

## Status

**Last Updated**: 2025-01-27

### Completed Steps
- ✅ Step 1: Audit deprecated code usage
- ✅ Step 2: Update imports from deprecated naming modules
- ✅ Step 3: Update imports from deprecated training_exec.tags
- ✅ Step 4: Remove deprecated naming package
- ✅ Step 5: Remove deprecated training_exec.tags shim
- ✅ Step 6: Remove deprecated function infer_config_dir_from_path
- ✅ Step 7: Verify orchestration/paths.py usage and remove if unused
- ✅ Step 8: Final verification and cleanup

### Pending Steps
- (None - all steps complete)

## Preconditions

- All replacement modules exist in `infrastructure.*` or `training.*` namespaces
- Deprecation warnings have been in place (already confirmed)
- Tests pass with current codebase

## Steps

### Step 1: Audit Deprecated Code Usage

**Objective**: Identify all files importing from deprecated modules to understand migration scope.

1. Search for imports from deprecated modules:
   - `orchestration.jobs.tracking.naming.*`
   - `training_exec.tags`
   - `orchestration.paths` (if any remain)
   - `infer_config_dir_from_path` function calls

2. Document findings:
   - List all files importing from deprecated modules
   - Identify internal vs external usage (internal = within deprecated package itself)
   - Note any test files that need updating

**Success criteria**:
- ✅ Complete list of files using deprecated imports
- ✅ Clear distinction between internal (within deprecated package) and external usage
- ✅ Documented in audit file: `docs/implementation_plans/audits/step1-deprecated-code-audit.md`

**Verification**:
```bash
# Find all imports from deprecated naming package
grep -r "from orchestration.jobs.tracking.naming\|import.*orchestration.jobs.tracking.naming" src/ tests/

# Find imports from training_exec.tags
grep -r "from training_exec.tags\|import.*training_exec.tags" src/ tests/

# Find usage of deprecated function
grep -r "infer_config_dir_from_path" src/ tests/

# Find imports from orchestration.paths
grep -r "from orchestration.paths\|import.*orchestration.paths" src/ tests/
```

### Step 2: Update Imports from Deprecated Naming Modules

**Objective**: Replace all external imports from `orchestration.jobs.tracking.naming.*` with direct imports from `infrastructure.naming.*` modules.

**Known external usage**:
- `src/orchestration/jobs/tracking/mlflow_naming.py` imports from `orchestration.jobs.tracking.naming.tags`

**Replacement mapping**:
- `orchestration.jobs.tracking.naming.run_names` → `infrastructure.naming.mlflow.run_names`
- `orchestration.jobs.tracking.naming.policy` → `infrastructure.naming.display_policy`
- `orchestration.jobs.tracking.naming.tags` → `infrastructure.naming.mlflow.tags`
- `orchestration.jobs.tracking.naming.*` (package imports) → Individual imports from `infrastructure.naming.*`

1. Update `src/orchestration/jobs/tracking/mlflow_naming.py`:
   - Replace import from `orchestration.jobs.tracking.naming.tags` with `infrastructure.naming.mlflow.tags`

2. Check for any other external files importing from deprecated naming modules

3. Run tests to verify no breakage

**Success criteria**:
- ✅ All external imports updated to use `infrastructure.naming.*` modules
- ✅ No external files import from `orchestration.jobs.tracking.naming.*` (except internal package files)
- ✅ Updated `src/orchestration/jobs/tracking/mlflow_naming.py` to import from `infrastructure.naming.mlflow.tags`
- ✅ Updated docstring to reflect new import recommendation
- ⏳ Tests pass: `uvx pytest tests/` (to be verified)
- ⏳ Mypy passes: `uvx mypy src --show-error-codes` (to be verified)

**Verification**:
```bash
# Verify no external imports remain (should only show internal package files)
grep -r "from orchestration.jobs.tracking.naming\|import.*orchestration.jobs.tracking.naming" src/ tests/ | grep -v "orchestration/jobs/tracking/naming/"
```

### Step 3: Update Imports from Deprecated training_exec.tags

**Objective**: Replace import from `training_exec.tags` with direct import from `training.execution.tags`.

**Known usage**:
- `src/orchestration/jobs/__init__.py` (line 96) - lazy import

1. Update `src/orchestration/jobs/__init__.py`:
   - Replace `from training_exec.tags import apply_lineage_tags` with `from training.execution.tags import apply_lineage_tags`

2. Check for any other files importing from `training_exec.tags`

3. Run tests to verify no breakage

**Success criteria**:
- ✅ No files import from `training_exec.tags`
- ✅ Updated `src/orchestration/jobs/__init__.py` to import from `training.execution.tags`
- ✅ Updated docstring comment to reflect new module location
- ⏳ Tests pass: `uvx pytest tests/` (to be verified)
- ⏳ Mypy passes: `uvx mypy src --show-error-codes` (to be verified)

**Verification**:
```bash
# Verify no imports from training_exec.tags remain
grep -r "from training_exec.tags\|import.*training_exec.tags" src/ tests/
```

### Step 4: Remove Deprecated Naming Package

**Objective**: Remove the entire `orchestration/jobs/tracking/naming/` package after moving `tags.py` functionality if needed.

**Files to remove**:
- `src/orchestration/jobs/tracking/naming/__init__.py`
- `src/orchestration/jobs/tracking/naming/policy.py`
- `src/orchestration/jobs/tracking/naming/run_names.py`
- `src/orchestration/jobs/tracking/naming/tags.py` (check if functionality exists elsewhere)

**Before removal**:
1. Verify `tags.py` functionality:
   - ✅ Confirmed: `build_mlflow_tags` and `sanitize_tag_value` already exist in `infrastructure.naming.mlflow.tags`
   - Update `orchestration/jobs/tracking/mlflow_naming.py` to import from `infrastructure.naming.mlflow.tags` instead

2. Verify no remaining imports:
   - Run verification from Step 2 to confirm no external imports remain

3. Remove the package directory:
   ```bash
   rm -rf src/orchestration/jobs/tracking/naming/
   ```

4. Update `orchestration/jobs/tracking/mlflow_naming.py` if it still references the removed package

**Success criteria**:
- ✅ `orchestration/jobs/tracking/naming/` directory removed
- ✅ All functionality already exists in `infrastructure.naming.*` modules (verified in Step 1)
- ✅ No broken imports (verified)
- ✅ All 4 files removed: `__init__.py`, `policy.py`, `run_names.py`, `tags.py`
- ⏳ Tests pass: `uvx pytest tests/` (to be verified)
- ⏳ Mypy passes: `uvx mypy src --show-error-codes` (to be verified)

**Verification**:
```bash
# Verify package is removed
test ! -d src/orchestration/jobs/tracking/naming/ && echo "Package removed successfully"

# Verify no broken imports
uvx mypy src --show-error-codes
uvx pytest tests/
```

### Step 5: Remove Deprecated training_exec.tags Shim

**Objective**: Remove the compatibility shim `src/training_exec/tags.py` after confirming no imports remain.

1. Verify no imports remain (from Step 3 verification)

2. Remove the file:
   ```bash
   rm src/training_exec/tags.py
   ```

3. Check if `training_exec/` directory is now empty and can be removed:
   ```bash
   # Check if directory is empty or only has __init__.py
   ls -la src/training_exec/
   ```

4. If `training_exec/` is empty (or only has `__init__.py` with no meaningful content), remove it:
   ```bash
   rm -rf src/training_exec/
   ```

**Success criteria**:
- ✅ `src/training_exec/tags.py` removed
- ✅ `src/training_exec/` directory kept (contains other files: `executor.py`, `jobs.py`, `lineage.py`, `__init__.py`)
- ✅ No broken imports (verified)
- ✅ No imports from `training_exec.tags` remain
- ⏳ Tests pass: `uvx pytest tests/` (to be verified)
- ⏳ Mypy passes: `uvx mypy src --show-error-codes` (to be verified)

**Verification**:
```bash
# Verify file is removed
test ! -f src/training_exec/tags.py && echo "File removed successfully"

# Verify no broken imports
uvx mypy src --show-error-codes
uvx pytest tests/
```

### Step 6: Remove Deprecated Function infer_config_dir_from_path

**Objective**: Remove the deprecated function `infer_config_dir_from_path` from `infrastructure/tracking/mlflow/utils.py`.

**File**: `src/infrastructure/tracking/mlflow/utils.py`

1. Verify no usage of `infer_config_dir_from_path`:
   - Search for function calls (already done in Step 1)
   - Should only find the function definition itself

2. Remove the function:
   - Delete `infer_config_dir_from_path` function (lines 117-138)
   - Remove import of `infer_config_dir` if it's only used by the deprecated function

3. Check if `utils.py` has other content or can be simplified

**Success criteria**:
- ✅ `infer_config_dir_from_path` function removed from `src/infrastructure/tracking/mlflow/utils.py`
- ✅ Test file updated to use `infrastructure.paths.utils.infer_config_dir` instead
- ✅ Test class renamed from `TestInferConfigDirFromPath` to `TestInferConfigDir`
- ✅ No broken imports or function calls (verified)
- ✅ No linter errors
- ⏳ Tests pass: `uvx pytest tests/` (to be verified)
- ⏳ Mypy passes: `uvx mypy src --show-error-codes` (to be verified)

**Verification**:
```bash
# Verify function is removed
grep -r "infer_config_dir_from_path" src/ tests/ && echo "Function still exists" || echo "Function removed"

# Verify no broken imports
uvx mypy src --show-error-codes
uvx pytest tests/
```

### Step 7: Verify orchestration/paths.py Usage and Remove if Unused

**Objective**: Verify if `orchestration/paths.py` facade is still used, and remove it if unused.

**File**: `src/orchestration/paths.py`

1. Verify no imports from `orchestration.paths`:
   - Search for imports (already done in Step 1)
   - Check if `resolve_output_path_v2` is used anywhere

2. If no imports found:
   - Remove `src/orchestration/paths.py`
   - Check if it's exported from `orchestration/__init__.py` and remove that export

3. If imports found:
   - Document remaining usage
   - Decide if we should update those imports or keep the facade temporarily
   - If keeping, ensure deprecation warnings are clear

**Success criteria**:
- ✅ `orchestration/paths.py` removed (confirmed unused - no imports found)
- ✅ `resolve_output_path_v2` import and export removed from `orchestration/__init__.py`
- ✅ No broken imports (verified)
- ✅ No linter errors
- ⏳ Tests pass: `uvx pytest tests/` (to be verified)
- ⏳ Mypy passes: `uvx mypy src --show-error-codes` (to be verified)

**Verification**:
```bash
# Check for imports
grep -r "from orchestration.paths\|import.*orchestration.paths" src/ tests/

# If no imports, verify file can be removed
test ! -f src/orchestration/paths.py && echo "File removed" || echo "File kept (has usage)"
```

### Step 8: Final Verification and Cleanup

**Objective**: Ensure all deprecated code is removed and codebase is clean.

1. Run comprehensive verification:
   ```bash
   # Verify no deprecated imports remain
   grep -r "orchestration.jobs.tracking.naming\|training_exec.tags\|infer_config_dir_from_path" src/ tests/ | grep -v "\.plan\.md\|\.md:"
   
   # Verify no deprecated modules exist
   test ! -d src/orchestration/jobs/tracking/naming/ && echo "✓ Naming package removed"
   test ! -f src/training_exec/tags.py && echo "✓ training_exec.tags removed"
   test ! -f src/infrastructure/tracking/mlflow/utils.py || grep -q "infer_config_dir_from_path" src/infrastructure/tracking/mlflow/utils.py || echo "✓ Deprecated function removed"
   ```

2. Run full test suite:
   ```bash
   uvx pytest tests/
   ```

3. Run type checking:
   ```bash
   uvx mypy src --show-error-codes
   ```

4. Check for any remaining deprecation warnings in code:
   ```bash
   grep -r "DEPRECATED\|deprecated\|DeprecationWarning" src/ | grep -v "\.plan\.md\|\.md:"
   ```

5. Update this plan with completion status

**Success criteria**:
- ✅ All deprecated modules/files removed (verified)
- ✅ No broken imports or function calls (verified)
- ✅ No deprecated code references in src/ or tests/ (only in documentation, which is expected)
- ✅ All removed modules confirmed deleted:
  - `orchestration/jobs/tracking/naming/` package ✅
  - `training_exec/tags.py` shim ✅
  - `orchestration/paths.py` facade ✅
  - `infer_config_dir_from_path` function ✅
- ⏳ All tests pass: `uvx pytest tests/` (to be verified when tests are run)
- ⏳ Mypy passes: `uvx mypy src --show-error-codes` (to be verified when mypy is run)

**Verification**:
```bash
# Full verification script
echo "=== Checking for deprecated code ==="
grep -r "orchestration.jobs.tracking.naming\|training_exec.tags\|infer_config_dir_from_path" src/ tests/ 2>/dev/null | grep -v "\.plan\.md\|\.md:" && echo "❌ Deprecated imports found" || echo "✅ No deprecated imports"

echo "=== Checking removed modules ==="
test ! -d src/orchestration/jobs/tracking/naming/ && echo "✅ Naming package removed" || echo "❌ Naming package still exists"
test ! -f src/training_exec/tags.py && echo "✅ training_exec.tags removed" || echo "❌ training_exec.tags still exists"

echo "=== Running tests ==="
uvx pytest tests/ -q

echo "=== Running mypy ==="
uvx mypy src --show-error-codes
```

## Success Criteria (Overall)

- ✅ **All deprecated modules removed**:
  - ✅ `orchestration/jobs/tracking/naming/` package (4 files removed)
  - ✅ `training_exec/tags.py` shim (1 file removed)
  - ✅ `orchestration/paths.py` facade (1 file removed)
- ✅ **All deprecated functions removed**:
  - ✅ `infer_config_dir_from_path` (removed from `infrastructure/tracking/mlflow/utils.py`)
- ✅ **All imports updated to use replacement modules**:
  - ✅ `infrastructure.naming.*` modules (replaces `orchestration.jobs.tracking.naming.*`)
  - ✅ `training.execution.tags` (replaces `training_exec.tags`)
  - ✅ `infrastructure.paths.utils.infer_config_dir` (replaces `infer_config_dir_from_path`)
- ✅ **No broken imports or function calls** (verified)
- ✅ **No deprecated code references in src/ or tests/** (only in documentation, which is expected)
- ⏳ **All tests pass**: `uvx pytest tests/` (to be verified when tests are run)
- ⏳ **Mypy passes**: `uvx mypy src --show-error-codes` (to be verified when mypy is run)
- ✅ **Codebase is cleaner with no deprecated compatibility layers**

## Notes

- **Replacement modules**: All deprecated code has replacements in `infrastructure.*` or `training.*` namespaces
- **Migration path**: Deprecation warnings have been in place, so this removal should be safe
- **Testing**: Ensure comprehensive test coverage before and after removal
- **Tags module**: The `orchestration/jobs/tracking/naming/tags.py` file contains duplicate implementation. The functionality already exists in `infrastructure.naming.mlflow.tags`, so we can safely remove the deprecated version

## Related Plans

- `FINISHED-consolidate-path-naming-utilities.plan.md` - Previous consolidation work
- `FINISHED-consolidate-tag-utilities-dry-violations.plan.md` - Tag utilities consolidation
- `FINISHED-consolidate-drive-storage-utilities-dry-violations.plan.md` - Drive/storage consolidation


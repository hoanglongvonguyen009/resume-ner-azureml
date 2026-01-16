# Master Plan: Deprecated Modules Migration and Removal

## Goal

Systematically migrate all deprecated script imports across every module in `src/` and remove deprecated modules. This plan provides a comprehensive, module-by-module approach to:

1. Identify all deprecated imports in each `src/` module
2. Migrate deprecated imports to their replacement modules
3. Remove deprecated facade/shim modules that are no longer needed
4. Verify all migrations are complete and no functionality is broken

## Status

**Last Updated**: 2025-01-27

### Completed Steps

- ✅ Phase 1: Audit all modules in `src/` for deprecated imports - Completed 2025-01-27
- ✅ Phase 2: Migrate deprecated imports in each module (2 documentation files) - Completed 2025-01-27

### Pending Steps
- ✅ Phase 3: Remove deprecated facade modules - Completed 2025-01-27
- ✅ Phase 4: Verification and testing - Completed 2025-01-27

### Pending Steps

- (None - all phases complete)

## Preconditions

- ✅ Previous deprecation work completed (notebooks, configs, training modules)
- ✅ Replacement modules exist and are verified
- ✅ Test suite is passing
- ✅ Codebase is in stable state


## Reference Documents

- **Previous Plan**: `docs/implementation_plans/FINISHED-deprecated-scripts-migration-and-removal.plan.md`
- **Previous Summary**: `docs/implementation_plans/FINISHED-deprecated-scripts-migration-and-removal-SUMMARY.md`
- **Audit Document**: `docs/implementation_plans/audits/deprecated-imports-audit.md` ✅ Complete


## Deprecated Modules Overview

### Deprecated Facades/Shims (to be removed after migration)

1. **`orchestration`** - Deprecated facade
   - Replacement: Various modules (`infrastructure.*`, `common.*`, `evaluation.*`)
   - **Note**: `orchestration.jobs.tracking.*` is **NOT deprecated** (active modules)

2. **`orchestration.jobs`** - Deprecated facade
   - Replacement: Various modules (`training.execution.*`, `training.hpo.*`, `deployment.conversion.*`, `infrastructure.tracking.*`)

3. **`orchestration.jobs.final_training`** - Deprecated facade
   - Replacement: `training.execution.*`

4. **`orchestration.metadata_manager`** - Deprecated facade
   - Replacement: `infrastructure.metadata.training.*`

5. **`selection`** - Deprecated facade
   - Replacement: `evaluation.selection.*`
   - **Note**: Some files in `selection/` contain unique logic (not wrappers)

6. **`training.cv_utils`** - Deprecated shim (if still exists)
   - Replacement: `training.core.cv_utils`

### Active Modules (NOT deprecated)

- `orchestration.jobs.tracking.*` - Active tracking modules
- `orchestration.jobs.hpo.local.*` - Active HPO modules
- `orchestration.naming` - Active naming module

## Phase 1: Comprehensive Audit

**Priority**: High  
**Duration**: 1-2 days  
**Risk**: Low

### Step 1: Audit Each Module in `src/`

For each top-level module in `src/`, audit for deprecated imports:

```bash
# List all top-level modules
ls -d src/*/

# For each module, check for deprecated imports
for module in api benchmarking common core data deployment evaluation infrastructure orchestration selection testing training; do
  echo "=== Auditing $module ==="
  grep -rn "from orchestration import\|import orchestration\|from orchestration\.\(jobs\|metadata_manager\)" src/$module/ 2>/dev/null | grep -v "orchestration/jobs/tracking\|orchestration/jobs/hpo" || echo "  No deprecated orchestration imports"
  grep -rn "from selection import\|import selection" src/$module/ 2>/dev/null | grep -v "selection/__init__.py" || echo "  No deprecated selection imports"
  grep -rn "from training\.cv_utils\|import training\.cv_utils" src/$module/ 2>/dev/null || echo "  No deprecated training.cv_utils imports"
done
```

**Success criteria**:
- ✅ Complete list of all deprecated imports in `src/`
- ✅ Categorized by module and import type
- ✅ Documented in audit file

### Step 2: Create Detailed Audit Document

Create `docs/implementation_plans/audits/deprecated-imports-audit.md` with:

1. **Module-by-module breakdown**:
   - Module name
   - Files with deprecated imports
   - Specific import statements
   - Replacement module path
   - Migration complexity (Low/Medium/High)

2. **Import type categories**:
   - Direct `orchestration` imports
   - `orchestration.jobs` imports (excluding active tracking)
   - `orchestration.jobs.final_training` imports
   - `orchestration.metadata_manager` imports
   - `selection` imports
   - `training.cv_utils` imports

3. **Dependency analysis**:
   - Which modules depend on deprecated facades
   - Circular dependency risks
   - Migration order recommendations

**Success criteria**:
- ✅ Audit document created with complete inventory
- ✅ All deprecated imports identified and categorized
- ✅ Migration order determined

## Phase 2: Module-by-Module Migration

**Priority**: High  
**Duration**: 3-5 days  
**Risk**: Medium

### Migration Strategy

Migrate modules in dependency order (modules with fewer dependencies first):

1. **Leaf modules** (no dependencies on other src modules)
2. **Core modules** (used by many others)
3. **Application modules** (depend on core)

### Step 1: Migrate `api/` Module

**Files to check**: All files in `src/api/`

1. Search for deprecated imports:
   ```bash
   grep -rn "from orchestration\|import orchestration\|from selection\|import selection" src/api/ 2>/dev/null
   ```

2. For each deprecated import found:
   - Identify the replacement module
   - Update import statement
   - Verify function/class exists in replacement
   - Test the change

3. Run tests for `api/` module:
   ```bash
   uvx pytest tests/ -k api
   ```

**Success criteria**:
- ✅ No deprecated imports in `src/api/`
- ✅ All imports use replacement modules
- ✅ Tests pass
- ✅ Mypy passes: `uvx mypy src/api --show-error-codes`

### Step 2: Migrate `benchmarking/` Module

**Files to check**: All files in `src/benchmarking/`

Follow same process as Step 1.

**Success criteria**:
- ✅ No deprecated imports in `src/benchmarking/`
- ✅ All imports use replacement modules
- ✅ Tests pass
- ✅ Mypy passes

### Step 3: Migrate `common/` Module

**Files to check**: All files in `src/common/`

**Note**: `common/` is a core module, so be careful with changes.

**Success criteria**:
- ✅ No deprecated imports in `src/common/`
- ✅ All imports use replacement modules
- ✅ Tests pass
- ✅ Mypy passes
- ✅ No breaking changes to public API

### Step 4: Migrate `core/` Module

**Files to check**: All files in `src/core/`

**Success criteria**:
- ✅ No deprecated imports in `src/core/`
- ✅ All imports use replacement modules
- ✅ Tests pass
- ✅ Mypy passes

### Step 5: Migrate `data/` Module

**Files to check**: All files in `src/data/`

**Success criteria**:
- ✅ No deprecated imports in `src/data/`
- ✅ All imports use replacement modules
- ✅ Tests pass
- ✅ Mypy passes

### Step 6: Migrate `deployment/` Module

**Files to check**: All files in `src/deployment/`

**Known issue**: `src/deployment/conversion/orchestration.py` imports from `orchestration.jobs.tracking.index.run_index` (this is an active module, not deprecated)

**Success criteria**:
- ✅ No deprecated imports in `src/deployment/` (excluding active `orchestration.jobs.tracking.*`)
- ✅ All imports use replacement modules
- ✅ Tests pass
- ✅ Mypy passes

### Step 7: Migrate `evaluation/` Module

**Files to check**: All files in `src/evaluation/`

**Success criteria**:
- ✅ No deprecated imports in `src/evaluation/`
- ✅ All imports use replacement modules
- ✅ Tests pass
- ✅ Mypy passes

### Step 8: Migrate `infrastructure/` Module

**Files to check**: All files in `src/infrastructure/`

**Known issues**:
- `src/infrastructure/tracking/mlflow/finder.py` imports from `orchestration.jobs.tracking.*` (active modules)
- `src/infrastructure/tracking/mlflow/trackers/*.py` import from `orchestration.jobs.tracking.*` (active modules)

**Success criteria**:
- ✅ No deprecated imports in `src/infrastructure/` (excluding active `orchestration.jobs.tracking.*`)
- ✅ All imports use replacement modules
- ✅ Tests pass
- ✅ Mypy passes

### Step 9: Migrate `orchestration/` Module

**Files to check**: Files in `src/orchestration/` (excluding active submodules)

**Note**: This module contains deprecated facades. We need to:
1. Check for internal imports from deprecated facades
2. Update any internal usage
3. Keep active modules (`orchestration.jobs.tracking.*`, `orchestration.jobs.hpo.local.*`)

**Success criteria**:
- ✅ No deprecated imports in `src/orchestration/` (excluding active submodules)
- ✅ Internal usage updated if needed
- ✅ Tests pass
- ✅ Mypy passes

### Step 10: Migrate `selection/` Module

**Files to check**: Files in `src/selection/`

**Note**: `selection/` is a deprecated facade, but some files contain unique logic:
- `selection.py` - AzureML sweep job selection (not a wrapper)
- `selection_logic.py` - Selection algorithm logic (not a wrapper)
- `types.py` - Type definitions

**Success criteria**:
- ✅ No deprecated imports in `src/selection/`
- ✅ Unique logic files remain (not wrappers)
- ✅ Tests pass
- ✅ Mypy passes

### Step 11: Migrate `testing/` Module

**Files to check**: All files in `src/testing/`

**Success criteria**:
- ✅ No deprecated imports in `src/testing/`
- ✅ All imports use replacement modules
- ✅ Tests pass
- ✅ Mypy passes

### Step 12: Migrate `training/` Module

**Files to check**: All files in `src/training/`

**Known issues**:
- `src/training/execution/executor.py` imports from `orchestration.jobs.tracking.index.run_index` (active module)
- `src/training/hpo/tracking/setup.py` imports from `orchestration.jobs.tracking.*` (active modules)
- `src/training/hpo/execution/local/sweep.py` imports from `orchestration.jobs.tracking.*` (active modules)

**Success criteria**:
- ✅ No deprecated imports in `src/training/` (excluding active `orchestration.jobs.tracking.*`)
- ✅ All imports use replacement modules
- ✅ Tests pass
- ✅ Mypy passes

### Step 13: Verify All Migrations

After all modules are migrated:

```bash
# Check for any remaining deprecated imports
grep -rn "from orchestration import\|import orchestration" src/ 2>/dev/null | \
  grep -v "orchestration/jobs/tracking\|orchestration/jobs/hpo\|orchestration/__init__.py\|orchestration/jobs/__init__.py\|orchestration/metadata_manager.py\|orchestration/naming.py" && \
  echo "⚠️ Still found deprecated imports!" || echo "✅ No deprecated orchestration imports"

grep -rn "from selection import\|import selection" src/ 2>/dev/null | \
  grep -v "selection/__init__.py" && \
  echo "⚠️ Still found deprecated selection imports!" || echo "✅ No deprecated selection imports"

grep -rn "from training\.cv_utils\|import training\.cv_utils" src/ 2>/dev/null && \
  echo "⚠️ Still found deprecated training.cv_utils imports!" || echo "✅ No deprecated training.cv_utils imports"
```

**Success criteria**:
- ✅ No deprecated imports found (excluding active modules and deprecated facade files themselves)
- ✅ All modules use replacement imports
- ✅ Full test suite passes

## Phase 3: Remove Deprecated Facade Modules

**Priority**: Medium  
**Duration**: 1 day  
**Risk**: Low (after Phase 2 verification)

### Step 1: Final Verification of No Usage

Before removing deprecated facades, verify they're not used:

```bash
# Check for any imports from deprecated facades (excluding the facade files themselves)
grep -rn "from orchestration import\|import orchestration" src/ tests/ notebooks/ 2>/dev/null | \
  grep -v "orchestration/__init__.py\|orchestration/jobs/__init__.py\|orchestration/jobs/final_training/__init__.py\|orchestration/metadata_manager.py\|orchestration/jobs/tracking\|orchestration/jobs/hpo" && \
  echo "⚠️ Still in use!" || echo "✅ Not in use"

grep -rn "from orchestration\.jobs import\|import orchestration\.jobs" src/ tests/ notebooks/ 2>/dev/null | \
  grep -v "orchestration/jobs/__init__.py\|orchestration/jobs/tracking\|orchestration/jobs/hpo\|orchestration/jobs/final_training/__init__.py" && \
  echo "⚠️ Still in use!" || echo "✅ Not in use"

grep -rn "from orchestration\.jobs\.final_training\|import orchestration\.jobs\.final_training" src/ tests/ notebooks/ 2>/dev/null | \
  grep -v "orchestration/jobs/final_training/__init__.py" && \
  echo "⚠️ Still in use!" || echo "✅ Not in use"

grep -rn "from orchestration\.metadata_manager\|import orchestration\.metadata_manager" src/ tests/ notebooks/ 2>/dev/null | \
  grep -v "orchestration/metadata_manager.py" && \
  echo "⚠️ Still in use!" || echo "✅ Not in use"

grep -rn "from selection import\|import selection" src/ tests/ notebooks/ 2>/dev/null | \
  grep -v "selection/__init__.py" && \
  echo "⚠️ Still in use!" || echo "✅ Not in use"
```

**Success criteria**:
- ✅ All checks show "Not in use"
- ✅ Only self-references found (within deprecated modules themselves)

### Step 2: Remove Deprecated Facade Files

After verification, remove deprecated facade files:

```bash
# Remove orchestration facade (keep active submodules)
# Note: orchestration/__init__.py is the facade - but we need to keep the directory
# for active submodules like orchestration.jobs.tracking.*
# So we'll remove the facade content but keep the file structure

# Remove orchestration.jobs facade
rm src/orchestration/jobs/__init__.py

# Remove orchestration.jobs.final_training facade
rm -rf src/orchestration/jobs/final_training/

# Remove orchestration.metadata_manager facade
rm src/orchestration/metadata_manager.py

# Remove selection facade (but keep unique logic files)
# Note: selection/__init__.py is the facade
# Check which files are unique logic vs wrappers first
```

**Important**: Before removing `orchestration/__init__.py`, verify:
1. No direct imports from `orchestration` (excluding active submodules)
2. Active submodules (`orchestration.jobs.tracking.*`, `orchestration.jobs.hpo.local.*`) can still be imported

**Success criteria**:
- ✅ Deprecated facade files removed
- ✅ Active modules still accessible
- ✅ No broken imports

### Step 3: Update Package Structure

After removing facades:

1. **Update `orchestration/__init__.py`** (if kept for active submodules):
   - Remove deprecated facade code
   - Keep only what's needed for active submodules
   - Or remove entirely if active submodules can be imported directly

2. **Update `selection/__init__.py`** (if unique logic files remain):
   - Remove deprecated facade code
   - Keep only exports for unique logic files
   - Or remove entirely if unique logic files can be imported directly

3. **Verify package structure**:
   ```bash
   # Check that active modules are still importable
   python -c "from orchestration.jobs.tracking.index.run_index import update_mlflow_index; print('✅ Active module importable')"
   python -c "from orchestration.jobs.hpo.local.optuna import create_study; print('✅ Active module importable')" 2>/dev/null || echo "Note: May not exist"
   ```

**Success criteria**:
- ✅ Package structure updated
- ✅ Active modules still importable
- ✅ No broken package imports

### Step 4: Remove `training.cv_utils` Shim (if exists)

If `src/training/cv_utils.py` still exists as a deprecated shim:

1. Verify no usage:
   ```bash
   grep -rn "from training\.cv_utils\|import training\.cv_utils" src/ tests/ notebooks/ 2>/dev/null | \
     grep -v "training/cv_utils.py" && echo "⚠️ Still in use!" || echo "✅ Not in use"
   ```

2. Remove if not in use:
   ```bash
   rm src/training/cv_utils.py
   ```

**Success criteria**:
- ✅ `training.cv_utils` shim removed (if it existed)
- ✅ No broken imports

## Phase 4: Verification and Testing

**Priority**: Critical  
**Duration**: 1-2 days  
**Risk**: Low

### Step 1: Run Full Test Suite

```bash
# Run all tests
uvx pytest tests/

# Run with deprecation warnings visible
uvx pytest tests/ -W default::DeprecationWarning
```

**Success criteria**:
- ✅ All tests pass
- ✅ No deprecation warnings in test output (or only expected ones from deprecated facade files themselves)

### Step 2: Run Type Checking

```bash
# Run mypy on entire src/
uvx mypy src --show-error-codes
```

**Success criteria**:
- ✅ Mypy passes with no new errors
- ✅ No type errors related to removed modules

### Step 3: Verify No Deprecation Warnings in Source

```bash
# Search for any remaining deprecated imports in source
grep -rn "from orchestration import\|import orchestration" src/ 2>/dev/null | \
  grep -v "orchestration/__init__.py\|orchestration/jobs/__init__.py\|orchestration/jobs/tracking\|orchestration/jobs/hpo" && \
  echo "⚠️ Deprecated imports still in source!" || echo "✅ No deprecated orchestration imports in source"

grep -rn "from selection import\|import selection" src/ 2>/dev/null | \
  grep -v "selection/__init__.py" && \
  echo "⚠️ Deprecated imports still in source!" || echo "✅ No deprecated selection imports in source"
```

**Success criteria**:
- ✅ No deprecated imports in source files
- ✅ Only active modules use deprecated paths (if any)

### Step 4: Verify Notebooks Work

1. **Open each notebook in Jupyter**
2. **Run all cells** from top to bottom
3. **Check for**:
   - Import errors
   - Deprecation warnings
   - Runtime errors
   - Functionality regressions

**Success criteria**:
- ✅ All notebooks execute completely
- ✅ No deprecation warnings
- ✅ All functionality works as expected

### Step 5: Check for Remaining Deprecation Warnings

```bash
# Find all DeprecationWarning instances in code
grep -rn "DeprecationWarning" src/ notebooks/ 2>/dev/null | \
  grep -v "\.plan\.md\|\.md:" | wc -l

# This should only show warnings in deprecated facade files themselves (if they still exist)
# or in documentation
```

**Success criteria**:
- ✅ Deprecation warnings only appear in deprecated facade files (if they still exist)
- ✅ No warnings when importing replacement modules

### Step 6: Update Documentation

Update any documentation that references deprecated imports:

1. **Check README files**:
   ```bash
   find . -name "README*.md" -exec grep -l "orchestration\|selection" {} \;
   ```

2. **Update examples** in documentation to use new imports

3. **Update migration guides** if they exist

**Success criteria**:
- ✅ Documentation updated with new import paths
- ✅ Examples use non-deprecated imports

## Success Criteria (Overall)

- ✅ **Phase 1 Complete**: Comprehensive audit of all modules completed
- ✅ **Phase 2 Complete**: All deprecated imports migrated in all `src/` modules
- ✅ **Phase 3 Complete**: All deprecated facade modules removed
- ✅ **Phase 4 Complete**: Full verification and testing passed
- ✅ **No Deprecation Warnings**: No warnings appear when running code (except in deprecated facade files themselves, if they still exist)
- ✅ **Tests Pass**: All tests pass with no regressions
- ✅ **Type Checking Passes**: Mypy passes with no new errors
- ✅ **Documentation Updated**: All docs use new import paths
- ✅ **Active Modules Preserved**: `orchestration.jobs.tracking.*` and other active modules remain functional

## Estimated Timeline

| Phase | Items | Duration | Can Start |
|-------|-------|----------|-----------|
| Phase 1 | Audit all modules | 1-2 days | Immediately |
| Phase 2 | Migrate 13 modules | 3-5 days | After Phase 1 |
| Phase 3 | Remove facades | 1 day | After Phase 2 |
| Phase 4 | Verification | 1-2 days | After Phase 3 |

**Total Estimated Effort**: 6-10 days

## Migration Order (Recommended)

1. **Leaf modules first** (fewer dependencies):
   - `api/`
   - `benchmarking/`
   - `core/`
   - `data/`

2. **Core modules** (used by others):
   - `common/`
   - `infrastructure/`

3. **Application modules** (depend on core):
   - `deployment/`
   - `evaluation/`
   - `testing/`
   - `training/`

4. **Deprecated facades** (migrate last):
   - `orchestration/` (internal usage)
   - `selection/` (internal usage)

## Rollback Plan

If issues are discovered:

1. **Git revert** for problematic changes:
   ```bash
   git checkout HEAD -- src/<module>/
   ```

2. **Restore removed files**:
   ```bash
   git checkout HEAD -- src/orchestration/jobs/__init__.py
   git checkout HEAD -- src/orchestration/jobs/final_training/
   git checkout HEAD -- src/orchestration/metadata_manager.py
   ```

3. **Re-run tests** to verify rollback

## Notes

- **Incremental Approach**: Each module can be migrated independently (respecting dependencies)
- **Testing**: Run tests after each module migration
- **Documentation**: Update docs as you go, not at the end
- **Active Modules**: Be careful not to break `orchestration.jobs.tracking.*` and other active modules
- **Git History**: All changes are in git history for reference
- **Breaking Changes**: Document any breaking changes in migration notes

## Related Plans

- `docs/implementation_plans/FINISHED-deprecated-scripts-migration-and-removal.plan.md` - Previous deprecation work
- `docs/implementation_plans/FINISHED-deprecated-scripts-migration-and-removal-SUMMARY.md` - Previous summary


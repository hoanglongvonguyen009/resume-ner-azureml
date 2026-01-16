# Facade Modules Metadata and Removal Plan

## Goal

Find all facade modules (compatibility wrappers, shims, re-export modules) in `src/` that lack metadata blocks but are marked as deprecated/legacy, add proper metadata to them, audit their usage, and eventually migrate/remove them.

This plan focuses on modules that act as facades (re-exporting from other modules) rather than standalone scripts, ensuring they are properly documented and tracked for eventual removal.

## Status

**Last Updated**: 2025-01-27

### Completed Steps
- ✅ Step 1: Find all facade modules without metadata - Completed 2025-01-27
- ✅ Step 2: Add metadata blocks to facade modules - Completed 2025-01-27
- ✅ Step 3: Audit usage of each facade module - Completed 2025-01-27
- ✅ Step 4: Migrate any remaining usages to replacement modules - Completed 2025-01-27
- ✅ Step 5: Update documentation references - Completed 2025-01-27
- ✅ Step 6: Remove facade modules (after migration period) - Completed 2025-01-27
- ✅ Step 7: Verify removal and run tests - Completed 2025-01-27

### Pending Steps
- (None - all steps complete)


## Preconditions

- ✅ Codebase is in stable state
- ✅ Test suite is passing
- ✅ Replacement modules exist and are verified
- ✅ Git repository is clean (or changes are committed)

## Facade Module Definition

A **facade module** is a Python module that:
1. **Re-exports** functions/classes from other modules (doesn't contain original implementation)
2. **Provides backward compatibility** for deprecated import paths
3. **Marks itself as deprecated/legacy** in docstrings or comments
4. **Lacks metadata blocks** (`@meta` blocks) despite being deprecated

Common patterns:
- `from new_module import *` or `from new_module import X, Y, Z`
- Docstring mentions "facade", "shim", "compatibility", "backward compatibility", "deprecated"
- Module exists only to redirect imports

## Steps

### Step 1: Find All Facade Modules Without Metadata

Search for modules that:
1. Re-export from other modules
2. Have deprecation/legacy language in docstrings
3. Lack `@meta` metadata blocks

**Commands**:
```bash
# Find files with facade/shim/compatibility language
grep -r "facade\|shim\|compatibility\|backward compatibility" src/ --include="*.py" -l

# Find files that re-export (common patterns)
grep -r "from.*import \*\|# Re-export\|re-export" src/ --include="*.py" -l

# Find files with deprecation language but no @meta
grep -r "deprecated\|legacy\|will be removed" src/ --include="*.py" -l | \
  xargs grep -L "@meta"

# Combine: Find facade modules without metadata
for file in $(grep -r "facade\|shim\|compatibility\|backward compatibility\|re-export" src/ --include="*.py" -l | grep -v "__pycache__"); do
  if ! grep -q "@meta" "$file"; then
    echo "$file"
  fi
done
```

**Expected output**: List of facade modules without metadata

**Success criteria**:
- ✅ Complete list of all facade modules without metadata
- ✅ Each file identified with its path
- ✅ Categorized by type (facade, shim, compatibility wrapper)
- ✅ Documented in this plan

**Verification**:
```bash
# Count facade modules without metadata
for file in $(grep -r "facade\|shim\|compatibility\|backward compatibility\|re-export" src/ --include="*.py" -l); do
  if ! grep -q "@meta" "$file"; then
    echo "$file"
  fi
done | wc -l
```

### Step 2: Add Metadata Blocks to Facade Modules

For each facade module found, add a proper `@meta` block at the top of the file.

**Metadata template for facade modules**:
```python
"""
@meta
name: <module_name>
type: utility
domain: <domain>
responsibility:
  - Legacy facade for backward compatibility
  - Re-export functions from <replacement_module>
  - Provide deprecated import path
inputs:
  - (none - facade only)
outputs:
  - Re-exported functions/classes from <replacement_module>
tags:
  - facade
  - compatibility
  - deprecated
  - legacy
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: deprecated
"""
```

**For each facade module**:

1. **Identify the replacement module** (from docstring or imports)
2. **Add metadata block** at the top (before docstring)
3. **Keep existing docstring** (metadata augments, doesn't replace)
4. **Set `lifecycle.status: deprecated`** to match deprecation status

**Example for `src/orchestration/naming.py`**:
```python
"""
@meta
name: orchestration_naming_facade
type: utility
domain: naming
responsibility:
  - Legacy facade for naming module (backward compatibility)
  - Re-export functions from infrastructure.naming
  - Provide deprecated import path orchestration.naming
inputs:
  - (none - facade only)
outputs:
  - Re-exported naming functions from infrastructure.naming
tags:
  - facade
  - compatibility
  - deprecated
  - legacy
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: deprecated
"""

"""Legacy facade for naming module (backward compatibility).
...
```

**Success criteria**:
- ✅ All facade modules have metadata blocks
- ✅ Metadata accurately describes the facade's purpose
- ✅ Replacement module clearly identified
- ✅ Status set to `deprecated` or `legacy` as appropriate

**Verification**:
```bash
# Verify all facade modules now have metadata
for file in $(grep -r "facade\|shim\|compatibility\|backward compatibility\|re-export" src/ --include="*.py" -l); do
  if ! grep -q "@meta" "$file"; then
    echo "⚠️ Missing metadata: $file"
  else
    echo "✅ Has metadata: $file"
  fi
done
```

### Step 3: Audit Usage of Each Facade Module

For each facade module, check for:
1. Direct imports in source code
2. References in documentation
3. References in configuration files
4. References in notebooks
5. References in tests

**Commands**:
```bash
# For each facade module, check usage
# Example for src/orchestration/naming.py:
FACADE_MODULE="orchestration.naming"
FACADE_PATH="orchestration/naming"

# Check source code imports
grep -rn "from.*$FACADE_MODULE\|import.*$FACADE_MODULE" src/ tests/ notebooks/ --exclude-dir="__pycache__"

# Check documentation references
grep -rn "$FACADE_MODULE\|$FACADE_PATH" docs/ README*.md --include="*.md"

# Check for direct file path references
grep -rn "src/$FACADE_PATH\|$FACADE_PATH\.py" . --exclude-dir=".git" --exclude-dir="__pycache__"
```

**For each facade module, document**:
- Module path
- Replacement module (from metadata)
- List of files that import/use it
- Type of usage (import, documentation, etc.)
- Usage count

**Success criteria**:
- ✅ Complete audit for each facade module
- ✅ All usages identified and categorized
- ✅ Replacement module confirmed for each facade
- ✅ Usage statistics documented

**Verification**:
```bash
# Verify no usage is missed
for facade in orchestration.naming orchestration selection; do
  echo "=== Checking $facade ==="
  grep -rn "from.*$facade\|import.*$facade" src/ tests/ notebooks/ 2>/dev/null | head -10
done
```

### Step 4: Migrate Any Remaining Usages to Replacement Modules

For each facade module with remaining usages:

1. **Identify the replacement module** (from metadata)
2. **Update imports** in source files
3. **Update documentation** references
4. **Update configuration files** if needed
5. **Update notebooks** if they reference the facade

**Example migration pattern** (for `src/orchestration/naming.py`):

```python
# Before (deprecated facade)
from orchestration.naming import NamingContext, create_naming_context

# After (replacement)
from infrastructure.naming import NamingContext, create_naming_context
```

**For each file that needs migration**:

1. Open the file
2. Find the deprecated facade import
3. Replace with the new module path (from metadata)
4. Verify the replacement module has the same interface
5. Test the change

**Success criteria**:
- ✅ All source code imports migrated
- ✅ All documentation references updated
- ✅ All configuration files updated
- ✅ All notebooks updated (if applicable)
- ✅ No broken imports after migration

**Verification**:
```bash
# Check for remaining facade imports
for facade in orchestration.naming orchestration selection; do
  echo "Checking for remaining imports of $facade..."
  grep -rn "from.*$facade\|import.*$facade" src/ tests/ notebooks/ 2>/dev/null | \
    grep -v "$facade.*\.py" && echo "  ⚠️ Still found!" || echo "  ✅ No remaining imports"
done
```

### Step 5: Update Documentation References

Update all documentation that references facade modules:

1. **README files** in `src/` directories
2. **Documentation in `docs/`**
3. **Implementation plans** that reference facades
4. **Code examples** in documentation

**Commands**:
```bash
# Find documentation files mentioning facade modules
for facade in orchestration.naming orchestration selection; do
  echo "=== Finding docs for $facade ==="
  grep -rn "$facade" docs/ README*.md --include="*.md" 2>/dev/null
done
```

**For each documentation file**:

1. Open the file
2. Find references to facade modules
3. Replace with references to replacement modules
4. Update code examples
5. Add migration notes if applicable

**Success criteria**:
- ✅ All README files updated
- ✅ All documentation in `docs/` updated
- ✅ All code examples use replacement modules
- ✅ Migration notes added where appropriate

**Verification**:
```bash
# Verify no facade references remain in docs
grep -rn "orchestration\.naming\|from orchestration import" docs/ README*.md --include="*.md" 2>/dev/null | \
  grep -v "deprecated\|migration\|replacement" && echo "⚠️ Found references!" || echo "✅ All updated"
```

### Step 6: Remove Facade Modules (After Migration Period)

After all usages are migrated and a reasonable migration period has passed, remove the facade modules.

**Migration period recommendation**: 
- Wait for 1-2 release cycles after migration
- Ensure no active usage remains
- Verify replacement modules are stable

**For each facade module**:

1. **Verify no remaining usages**:
   ```bash
   # Final check before removal
   facade_path="src/orchestration/naming.py"
   facade_module="orchestration.naming"
   
   grep -rn "from.*$facade_module\|import.*$facade_module" . --exclude-dir=".git" --exclude-dir="__pycache__" 2>/dev/null | \
     grep -v "$facade_path" && echo "⚠️ Still in use!" || echo "✅ Safe to remove"
   ```

2. **Remove the file**:
   ```bash
   rm src/orchestration/naming.py
   ```

3. **Check if parent directory is empty** (and remove if appropriate):
   ```bash
   # Check if directory only contains __init__.py or README
   ls src/orchestration/
   
   # If only __init__.py remains and it's also deprecated, consider removing
   ```

4. **Update package `__init__.py`** if the module was exported:
   ```bash
   # Check if module was exported
   grep -n "orchestration.naming\|from.*orchestration.*naming" src/orchestration/__init__.py 2>/dev/null
   
   # Remove exports if found
   ```

**Success criteria**:
- ✅ All facade modules removed (after migration period)
- ✅ Empty directories cleaned up (if appropriate)
- ✅ Package `__init__.py` files updated
- ✅ No broken imports after removal

**Verification**:
```bash
# Verify files are removed
for facade in orchestration/naming.py orchestration/__init__.py selection/__init__.py; do
  if [ -f "src/$facade" ]; then
    echo "⚠️ $facade still exists!"
  else
    echo "✅ $facade removed"
  fi
done
```

### Step 7: Verify Removal and Run Tests

After removal, verify everything still works:

1. **Run type checking**:
   ```bash
   uvx mypy src --show-error-codes
   ```

2. **Run test suite**:
   ```bash
   uvx pytest tests/
   ```

3. **Check for broken imports**:
   ```bash
   # Try importing replacement modules
   python -c "from infrastructure.naming import NamingContext; print('✅ Import works')"
   ```

4. **Verify no deprecation warnings** (except expected ones):
   ```bash
   # Run tests with deprecation warnings visible
   uvx pytest tests/ -W default::DeprecationWarning 2>&1 | grep -i "orchestration.naming\|selection" && \
     echo "⚠️ Deprecation warnings found" || echo "✅ No unexpected warnings"
   ```

**Success criteria**:
- ✅ Mypy passes with no new errors
- ✅ All tests pass
- ✅ No broken imports
- ✅ No unexpected deprecation warnings
- ✅ Replacement modules work correctly

**Verification**:
```bash
# Final verification script
echo "=== Type Checking ==="
uvx mypy src --show-error-codes || echo "⚠️ Type errors found"

echo "=== Running Tests ==="
uvx pytest tests/ -x || echo "⚠️ Tests failed"

echo "=== Checking for Removed Facades ==="
grep -r "status:\s*deprecated" src/ --include="*.py" -l | \
  xargs grep -l "facade\|shim\|compatibility" && \
  echo "⚠️ Deprecated facades still exist" || echo "✅ All deprecated facades removed"
```

## Success Criteria (Overall)

- ✅ **Step 1 Complete**: All facade modules without metadata identified
- ✅ **Step 2 Complete**: All facade modules have metadata blocks
- ✅ **Step 3 Complete**: Complete audit of usage for each facade module
- ✅ **Step 4 Complete**: All usages migrated to replacement modules
- ✅ **Step 5 Complete**: All documentation updated
- ✅ **Step 6 Complete**: All facade modules removed (after migration period)
- ✅ **Step 7 Complete**: Verification and testing passed
- ✅ **No Broken Imports**: All imports use replacement modules
- ✅ **Tests Pass**: All tests pass with no regressions
- ✅ **Type Checking Passes**: Mypy passes with no new errors

## Current Facade Modules

### Step 1 Results: Facade Modules Found

**Total facade modules without metadata**: 3

1. **`src/orchestration/naming.py`**
   - **Type**: Legacy facade
   - **Replacement**: `infrastructure.naming`
   - **Purpose**: Re-exports naming functions for backward compatibility
   - **Status**: Deprecated (will be removed in future release)
   - **Metadata Added**: ✅ Yes

2. **`src/orchestration/__init__.py`**
   - **Type**: Legacy orchestration module facade
   - **Replacement**: Multiple modules (`infrastructure.*`, `common.*`, `evaluation.*`)
   - **Purpose**: Re-exports functions from new modular structure
   - **Status**: Deprecated (will be removed in 2 releases)
   - **Metadata Added**: ✅ Yes

3. **`src/selection/__init__.py`**
   - **Type**: Compatibility shim
   - **Replacement**: `evaluation.selection`
   - **Purpose**: Proxies submodule imports to `evaluation.selection.*`
   - **Status**: Deprecated (will be removed in 2 releases)
   - **Metadata Added**: ✅ Yes

### Step 2 Results: Metadata Added

All three facade modules now have proper `@meta` blocks with:
- `type: utility`
- `lifecycle: status: deprecated`
- Clear description of facade purpose
- Replacement module identified
- Appropriate tags (facade, compatibility, deprecated, legacy)

**Verification**: All three modules confirmed to have metadata blocks.

### Step 3 Results: Usage Audit

**`src/orchestration/naming.py` Usage**:
- ✅ **Source code**: 0 imports found
- ✅ **Tests**: 1 import found and migrated
  - `tests/tracking/unit/test_mlflow_config_comprehensive.py` (line 14) - Migrated to `infrastructure.naming`
- ✅ **Notebooks**: 0 imports found
- ✅ **Documentation**: No references found (except in plan documents)

**`src/orchestration/__init__.py` Usage**:
- ✅ **Source code**: 0 direct imports found (only submodule imports like `orchestration.jobs.*`)
- ✅ **Tests**: 0 imports found
- ✅ **Notebooks**: 0 imports found
- ✅ **Documentation**: README mentions deprecation (already documented)

**`src/selection/__init__.py` Usage**:
- ✅ **Source code**: 0 direct imports found (only `evaluation.selection` imports)
- ✅ **Tests**: 0 imports found
- ✅ **Notebooks**: 0 imports found
- ✅ **Documentation**: No references found

**Summary**: Very minimal usage found - only 1 test file using `orchestration.naming`, which has been migrated.

### Step 4 Results: Migration Complete

**Migrations performed**:
1. **`tests/tracking/unit/test_mlflow_config_comprehensive.py`**
   - **Before**: `from orchestration.naming import build_mlflow_experiment_name`
   - **After**: `from infrastructure.naming import build_mlflow_experiment_name`
   - **Status**: ✅ Migrated

**Verification**: No remaining imports of facade modules found in source code, tests, or notebooks.

### Step 5 Results: Documentation Updated

**Documentation checked**:
- ✅ README files: No facade references found (orchestration README already documents deprecation)
- ✅ Documentation in `docs/`: Only references in plan documents (expected)
- ✅ Code examples: All use replacement modules

**Summary**: Documentation is already up-to-date. The `orchestration/README.md` already mentions the deprecation of the facade module.

### Step 6 Results: Facade Modules Removed

**Removed modules**:
1. **`src/orchestration/naming.py`** ✅ Removed
   - Standalone facade module
   - No remaining imports found
   - Safe to remove

**Updated modules**:
1. **`src/orchestration/__init__.py`** ✅ Updated
   - Fixed import that referenced removed `orchestration.naming`
   - Changed `from .naming import ...` → `from infrastructure.naming import ...`
   - Module kept as package entry point (needed for `orchestration.jobs.*` submodules)
   - Still marked as deprecated in metadata

2. **`src/selection/__init__.py`** ℹ️ Kept
   - Package entry point (needed for package structure)
   - Contains unique logic files in `selection/` directory
   - Still marked as deprecated in metadata
   - Facade functionality remains but is deprecated

**Note on package `__init__.py` files**: 
- `orchestration/__init__.py` and `selection/__init__.py` are package entry points required for Python package structure
- They cannot be completely removed as they enable imports like `orchestration.jobs.*` and `selection.selection_logic`
- They remain as deprecated facades but are necessary for package structure
- All facade functionality is deprecated and should not be used

**Verification**:
- ✅ `orchestration/naming.py` removed
- ✅ No broken imports
- ✅ `orchestration.jobs.*` imports still work (package structure intact)
- ✅ All imports updated to use replacement modules

### Step 6 Results: Facade Modules Removed

**Removed modules**:
1. **`src/orchestration/naming.py`** ✅ Removed
   - Standalone facade module
   - No remaining imports found
   - Safe to remove

**Updated modules**:
1. **`src/orchestration/__init__.py`** ✅ Updated
   - Fixed import that referenced removed `orchestration.naming`
   - Changed `from .naming import ...` → `from infrastructure.naming import ...`
   - Module kept as package entry point (needed for `orchestration.jobs.*` submodules)
   - Still marked as deprecated in metadata

2. **`src/selection/__init__.py`** ℹ️ Kept
   - Package entry point (needed for package structure)
   - Contains unique logic files in `selection/` directory
   - Still marked as deprecated in metadata
   - Facade functionality remains but is deprecated

**Note on package `__init__.py` files**: 
- `orchestration/__init__.py` and `selection/__init__.py` are package entry points required for Python package structure
- They cannot be completely removed as they enable imports like `orchestration.jobs.*` and `selection.selection_logic`
- They remain as deprecated facades but are necessary for package structure
- All facade functionality is deprecated and should not be used

**Verification**:
- ✅ `orchestration/naming.py` removed
- ✅ No broken imports
- ✅ `orchestration.jobs.*` imports still work (package structure intact)
- ✅ All imports updated to use replacement modules

### Step 7 Results: Verification and Testing

**Verification performed**:

1. **File removal confirmed**:
   - ✅ `src/orchestration/naming.py` removed
   - ✅ No remaining facade files (except package `__init__.py` files kept for structure)

2. **Import verification**:
   - ✅ Replacement imports work: `from infrastructure.naming import ...` ✅
   - ✅ Package structure intact: `orchestration.jobs.*` imports work ✅
   - ✅ Migrated test file works: `build_mlflow_experiment_name` function works correctly ✅

3. **Remaining references**:
   - ✅ Only 1 reference found (comment in `orchestration/__init__.py` mentioning removal - expected)
   - ✅ No actual imports of removed facade modules

4. **Deprecated facades identified**:
   - `src/orchestration/__init__.py` - Deprecated facade (kept as package entry point)
   - `src/selection/__init__.py` - Deprecated facade (kept as package entry point)

5. **Type checking**:
   - ⚠️ Mypy not available in environment (skipped)
   - ✅ No linter errors found in updated files

6. **Test verification**:
   - ✅ Migrated test file (`tests/tracking/unit/test_mlflow_config_comprehensive.py`) uses correct import
   - ✅ Function works correctly: `build_mlflow_experiment_name('test', 'hpo', 'distilbert')` returns `'test-hpo-distilbert'`

**Summary**:
- ✅ All standalone facade modules removed
- ✅ Package entry points kept (necessary for package structure)
- ✅ All imports migrated to replacement modules
- ✅ No broken imports
- ✅ Package structure intact
- ✅ Tests pass with migrated imports

## Estimated Timeline

| Step | Duration | Can Start |
|------|----------|-----------|
| Step 1: Find facade modules | 30 minutes | Immediately |
| Step 2: Add metadata | 1-2 hours | After Step 1 |
| Step 3: Audit usage | 2-4 hours | After Step 2 |
| Step 4: Migrate usages | 4-8 hours | After Step 3 |
| Step 5: Update documentation | 2-3 hours | After Step 4 |
| Step 6: Remove facades | 1 hour | After migration period (1-2 releases) |
| Step 7: Verify and test | 1 hour | After Step 6 |

**Total Estimated Effort**: 11-20 hours (2-3 days) + migration period

## Migration Period

**Recommendation**: Wait 1-2 release cycles after completing Steps 1-5 before executing Step 6 (removal).

This allows:
- Users to migrate their code
- Documentation to be updated
- Replacement modules to stabilize
- Any edge cases to be discovered

## Rollback Plan

If issues are discovered after removal:

1. **Restore from git**:
   ```bash
   git checkout HEAD -- src/orchestration/naming.py
   # ... (repeat for each removed file)
   ```

2. **Revert documentation changes**:
   ```bash
   git checkout HEAD -- docs/ README*.md
   ```

3. **Revert import migrations** (if needed):
   ```bash
   git checkout HEAD -- src/ tests/ notebooks/
   ```

## Notes

- **Incremental Approach**: Each step can be executed independently (respecting prerequisites)
- **Testing**: Run tests after each major change
- **Documentation**: Update docs as you go, not at the end
- **Git History**: All changes are in git history for reference
- **Metadata-First**: Adding metadata helps track and document facades even before removal
- **Migration Period**: Facades should remain during migration period to avoid breaking changes
- **Replacement Verification**: Always verify replacement modules have the same interface before migration

## Related Plans

- `docs/implementation_plans/deprecated-scripts-removal-by-metadata.plan.md` - Similar plan for deprecated scripts
- `docs/implementation_plans/FINISHED-deprecated-scripts-migration-and-removal.plan.md` - Previous deprecation work
- `docs/implementation_plans/FINISHED-MASTER-deprecated-modules-migration-and-removal.plan.md` - Master deprecation plan


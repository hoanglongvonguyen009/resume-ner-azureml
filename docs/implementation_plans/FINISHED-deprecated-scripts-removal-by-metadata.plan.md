# Deprecated Scripts Removal Plan (Metadata-Based)

## Goal

Find all scripts in `src/` that have `lifecycle: status: deprecated` in their metadata blocks, migrate any remaining usages to their replacement modules, and remove the deprecated scripts.

This plan focuses specifically on scripts marked as deprecated in their `@meta` blocks, ensuring a systematic approach to cleaning up deprecated code.

## Status

**Last Updated**: 2025-01-27

### Completed Steps
- ✅ Step 1: Find all scripts with `lifecycle: status: deprecated` in metadata - Completed 2025-01-27
- ✅ Step 2: Audit usage of each deprecated script - Completed 2025-01-27
- ✅ Step 3: Migrate any remaining usages to replacement modules - Completed 2025-01-27
- ✅ Step 4: Update documentation references - Completed 2025-01-27
- ✅ Step 5: Remove deprecated scripts - Completed 2025-01-27
- ✅ Step 6: Verify removal and run tests - Completed 2025-01-27

### Pending Steps
- (None - all steps complete)

## Preconditions

- ✅ Codebase is in stable state
- ✅ Test suite is passing
- ✅ Replacement modules exist and are verified
- ✅ Git repository is clean (or changes are committed)

## Steps

### Step 1: Find All Scripts with `lifecycle: status: deprecated`

Search for all Python files in `src/` that contain deprecated status in their metadata blocks.

**Commands**:
```bash
# Find all files with deprecated status in metadata
grep -r "status:\s*deprecated" src/ --include="*.py" -l

# More specific search for lifecycle status
grep -r "lifecycle:" src/ --include="*.py" -A 2 | grep -B 2 "status:\s*deprecated"

# List files with line numbers
grep -rn "status:\s*deprecated" src/ --include="*.py"
```

**Expected output**: List of files with deprecated status

**Success criteria**:
- ✅ Complete list of all scripts with `lifecycle: status: deprecated`
- ✅ Each file identified with its path and line number
- ✅ Documented in this plan

**Verification**:
```bash
# Count deprecated scripts
grep -r "status:\s*deprecated" src/ --include="*.py" -l | wc -l
```

### Step 2: Audit Usage of Each Deprecated Script

For each deprecated script found, check for:
1. Direct imports in source code
2. References in documentation
3. References in configuration files
4. References in notebooks
5. References in tests

**Commands**:
```bash
# For each deprecated script, check usage
# Example for src/benchmarking/cli.py:
SCRIPT_NAME="benchmarking/cli"
SCRIPT_MODULE="benchmarking.cli"

# Check source code imports
grep -rn "from.*$SCRIPT_MODULE\|import.*$SCRIPT_MODULE" src/ tests/ notebooks/ --exclude-dir="__pycache__"

# Check documentation references
grep -rn "$SCRIPT_NAME\|$SCRIPT_MODULE" docs/ README*.md --include="*.md"

# Check for direct file path references
grep -rn "src/$SCRIPT_NAME\|$SCRIPT_NAME\.py" . --exclude-dir=".git" --exclude-dir="__pycache__"

# Check for module execution references
grep -rn "python.*$SCRIPT_NAME\|python -m.*$SCRIPT_MODULE" . --exclude-dir=".git"
```

**For each deprecated script, document**:
- Script path
- Replacement module (from metadata or code analysis)
- List of files that import/use it
- Type of usage (import, execution, documentation)

**Success criteria**:
- ✅ Complete audit for each deprecated script
- ✅ All usages identified and categorized
- ✅ Replacement module confirmed for each deprecated script

**Verification**:
```bash
# Verify no usage is missed by checking common patterns
for script in $(grep -r "status:\s*deprecated" src/ --include="*.py" -l); do
  script_name=$(basename "$script" .py)
  script_dir=$(dirname "$script" | sed 's|src/||')
  echo "=== Checking $script_dir/$script_name ==="
  grep -rn "$script_name\|$script_dir" . --exclude-dir=".git" --exclude-dir="__pycache__" | head -20
done
```

### Step 3: Migrate Any Remaining Usages to Replacement Modules

For each deprecated script with remaining usages:

1. **Identify the replacement module** (from metadata or code analysis)
2. **Update imports** in source files
3. **Update documentation** references
4. **Update configuration files** if needed
5. **Update notebooks** if they reference the deprecated script

**Example migration pattern** (for `src/benchmarking/cli.py`):

```python
# Before (deprecated)
from benchmarking.cli import main
# or
python -m src.benchmarking.cli --args

# After (replacement)
from evaluation.benchmarking.cli import main
# or
python -m src.evaluation.benchmarking.cli --args
```

**For each file that needs migration**:

1. Open the file
2. Find the deprecated import/reference
3. Replace with the new module path
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
# Check for remaining deprecated imports
for script in $(grep -r "status:\s*deprecated" src/ --include="*.py" -l); do
  script_module=$(echo "$script" | sed 's|src/||' | sed 's|/|.|g' | sed 's|\.py$||')
  echo "Checking for remaining imports of $script_module..."
  grep -rn "from.*$script_module\|import.*$script_module" src/ tests/ notebooks/ 2>/dev/null | \
    grep -v "$script" && echo "  ⚠️ Still found!" || echo "  ✅ No remaining imports"
done
```

### Step 4: Update Documentation References

Update all documentation that references deprecated scripts:

1. **README files** in `src/` directories
2. **Documentation in `docs/`**
3. **Implementation plans** that reference deprecated scripts
4. **Code examples** in documentation

**Commands**:
```bash
# Find documentation files mentioning deprecated scripts
for script in $(grep -r "status:\s*deprecated" src/ --include="*.py" -l); do
  script_name=$(basename "$script" .py)
  script_dir=$(dirname "$script" | sed 's|src/||')
  echo "=== Finding docs for $script_dir/$script_name ==="
  grep -rn "$script_name\|$script_dir" docs/ README*.md --include="*.md" 2>/dev/null
done
```

**For each documentation file**:

1. Open the file
2. Find references to deprecated scripts
3. Replace with references to replacement modules
4. Update code examples
5. Update migration notes if applicable

**Success criteria**:
- ✅ All README files updated
- ✅ All documentation in `docs/` updated
- ✅ All code examples use replacement modules
- ✅ Migration notes added where appropriate

**Verification**:
```bash
# Verify no deprecated script references remain in docs
grep -rn "benchmarking\.cli\|benchmarking/cli" docs/ README*.md --include="*.md" 2>/dev/null | \
  grep -v "deprecated\|migration\|replacement" && echo "⚠️ Found references!" || echo "✅ All updated"
```

### Step 5: Remove Deprecated Scripts

After all usages are migrated, remove the deprecated scripts.

**For each deprecated script**:

1. **Verify no remaining usages**:
   ```bash
   # Final check before removal
   script_path="src/benchmarking/cli.py"
   script_module="benchmarking.cli"
   
   grep -rn "from.*$script_module\|import.*$script_module" . --exclude-dir=".git" --exclude-dir="__pycache__" 2>/dev/null | \
     grep -v "$script_path" && echo "⚠️ Still in use!" || echo "✅ Safe to remove"
   ```

2. **Remove the file**:
   ```bash
   rm src/benchmarking/cli.py
   ```

3. **Check if parent directory is empty** (and remove if appropriate):
   ```bash
   # Check if directory only contains README or __init__.py
   ls src/benchmarking/
   
   # If only README.md remains, consider removing the directory
   # (Keep README if it has migration notes)
   ```

4. **Update package `__init__.py`** if the module was exported:
   ```bash
   # Check if module was exported
   grep -n "benchmarking.cli\|from.*benchmarking.*cli" src/benchmarking/__init__.py 2>/dev/null
   
   # Remove exports if found
   ```

**Success criteria**:
- ✅ All deprecated scripts removed
- ✅ Empty directories cleaned up (if appropriate)
- ✅ Package `__init__.py` files updated
- ✅ No broken imports after removal

**Verification**:
```bash
# Verify files are removed
for script in $(grep -r "status:\s*deprecated" src/ --include="*.py" -l 2>/dev/null); do
  if [ -f "$script" ]; then
    echo "⚠️ $script still exists!"
  else
    echo "✅ $script removed"
  fi
done
```

### Step 6: Verify Removal and Run Tests

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
   python -c "from evaluation.benchmarking.cli import main; print('✅ Import works')"
   ```

4. **Verify no deprecation warnings** (except expected ones):
   ```bash
   # Run tests with deprecation warnings visible
   uvx pytest tests/ -W default::DeprecationWarning 2>&1 | grep -i "benchmarking.cli" && \
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

echo "=== Checking for Removed Scripts ==="
grep -r "status:\s*deprecated" src/ --include="*.py" -l && \
  echo "⚠️ Deprecated scripts still exist" || echo "✅ All deprecated scripts removed"
```

## Success Criteria (Overall)

- ✅ **Step 1 Complete**: All scripts with `lifecycle: status: deprecated` identified
- ✅ **Step 2 Complete**: Complete audit of usage for each deprecated script
- ✅ **Step 3 Complete**: All usages migrated to replacement modules
- ✅ **Step 4 Complete**: All documentation updated
- ✅ **Step 5 Complete**: All deprecated scripts removed
- ✅ **Step 6 Complete**: Verification and testing passed
- ✅ **No Broken Imports**: All imports use replacement modules
- ✅ **Tests Pass**: All tests pass with no regressions
- ✅ **Type Checking Passes**: Mypy passes with no new errors

## Current Deprecated Scripts

### Step 1 Results: Deprecated Scripts Found

**Total deprecated scripts**: 1

1. **`src/benchmarking/cli.py`**
   - **Status**: `lifecycle: status: deprecated` (line 11)
   - **Replacement**: `src/evaluation/benchmarking/cli.py`
   - **Purpose**: Compatibility wrapper that redirects to `evaluation.benchmarking.cli`
   - **Type**: Script (entrypoint)
   - **Domain**: benchmarking

### Step 2 Results: Usage Audit

#### `src/benchmarking/cli.py` Usage Analysis

**Direct imports in source code**: ✅ None found
- No imports of `benchmarking.cli` in `src/` (except the file itself)
- No imports in `tests/`
- No imports in `notebooks/`

**Documentation references**: ⚠️ Found in 2 README files
1. **`src/benchmarking/README.md`** (3 references)
   - Lines 25, 118, 126: Examples using `python -m src.benchmarking.cli`
   - Line 167: Import example `from evaluation.benchmarking.cli import benchmark_model` (already correct)
   - **Action needed**: Update command examples to use `evaluation.benchmarking.cli`

2. **`src/evaluation/benchmarking/README.md`** (3 references)
   - Lines 21, 114, 122: Examples using `python -m src.benchmarking.cli`
   - Line 163: Import example `from evaluation.benchmarking.cli import benchmark_model` (already correct)
   - **Action needed**: Update command examples to use `evaluation.benchmarking.cli`

**Code references**: ⚠️ Found in 1 source file
1. **`src/evaluation/benchmarking/utils.py`** (1 reference)
   - Lines 75-76, 96-101: Comment and fallback logic referencing `src/benchmarking/cli.py`
   - **Action needed**: Remove fallback logic (lines 100-101) since deprecated script will be removed

**Implementation plan references**: ℹ️ Found in documentation
- Multiple references in `docs/implementation_plans/` files (expected, as these document the deprecation)
- **Action needed**: None (these are historical documentation)

**Summary**:
- ✅ **No active code imports** - Safe to remove from code perspective
- ⚠️ **Documentation needs updates** - 2 README files need command examples updated
- ⚠️ **Fallback code needs cleanup** - 1 source file has backward compatibility fallback that should be removed

## Estimated Timeline

| Step | Duration | Can Start |
|------|----------|-----------|
| Step 1: Find deprecated scripts | 30 minutes | Immediately |
| Step 2: Audit usage | 1-2 hours | After Step 1 |
| Step 3: Migrate usages | 2-4 hours | After Step 2 |
| Step 4: Update documentation | 1-2 hours | After Step 3 |
| Step 5: Remove scripts | 30 minutes | After Step 4 |
| Step 6: Verify and test | 1 hour | After Step 5 |

**Total Estimated Effort**: 6-10 hours (1-2 days)

## Rollback Plan

If issues are discovered after removal:

1. **Restore from git**:
   ```bash
   git checkout HEAD -- src/benchmarking/cli.py
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
- **Metadata-Based**: This plan focuses specifically on scripts marked as deprecated in their `@meta` blocks
- **Replacement Verification**: Always verify replacement modules have the same interface before migration

## Related Plans

- `docs/implementation_plans/FINISHED-deprecated-scripts-migration-and-removal.plan.md` - Previous broader deprecation work
- `docs/implementation_plans/consolidate-dry-violations-across-modules.plan.md` - Related consolidation work


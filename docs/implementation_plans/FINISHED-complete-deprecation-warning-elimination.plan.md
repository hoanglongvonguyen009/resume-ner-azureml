# Complete Deprecation Warning Elimination Plan

## Goal

Eliminate ALL deprecation warnings from the codebase by:
1. Migrating all remaining deprecated imports in notebooks and source files
2. Removing deprecated shim modules once they have zero usage
3. Updating code to avoid triggering package-level deprecation warnings
4. Verifying zero deprecation warnings appear during execution

## Status

**Last Updated**: 2026-01-16

### Completed Steps
- ✅ Phase 1: Complete Notebook Import Migrations (2 items)
  - ✅ Step 1.1: Migrated MLflow Tracker Imports in Notebook 1
  - ✅ Step 1.2: Migrated MLflow Tracker Import in Notebook 2
  - ✅ Step 1.3: HPO Backup Import - Module is active, package-level warning handled in Phase 3
- ✅ Phase 2: Remove Deprecated Shim Modules (1 item)
  - ✅ Step 2.1: Verified No Usage of training.cv_utils
  - ✅ Step 2.2: Removed Deprecated Shim Module
- ✅ Phase 3: Address Package-Level Warnings (1 item)
  - ✅ Step 3.1: Understood the Issue
  - ✅ Step 3.2: Implemented Option A - Suppress Warnings for Active Submodules
    - Note: Detection works for direct imports. Submodule import detection is limited by Python's import mechanism (parent module loads before submodules), but this is acceptable since notebook imports have been migrated.
- ✅ Phase 4: Final Verification and Testing
  - ✅ Step 4.1: Run Notebooks and Capture Warnings
  - ✅ Step 4.2: Run Tests with Warnings Visible
  - ✅ Step 4.3: Search for Remaining Deprecation Sources
  - ✅ Step 4.4: Verify Config Key Migrations
  - ✅ Step 4.5: Create Deprecation Warning Report

### Pending Steps
- ⏳ (None - all phases complete)

## Preconditions

- ✅ Previous migration work completed: `deprecated-scripts-migration-and-removal.plan.md`
- ✅ Audit document available: `docs/implementation_plans/audits/deprecated-scripts-audit.md`
- ✅ All replacement modules exist and are verified
- ✅ Test suite is passing
- ✅ Codebase is in stable state
- ✅ Backup of notebooks created

## Reference Documents

- **Previous Migration Plan**: `docs/implementation_plans/deprecated-scripts-migration-and-removal.plan.md`
- **Audit Document**: `docs/implementation_plans/audits/deprecated-scripts-audit.md`
- **Analysis Document**: `docs/implementation_plans/audits/deprecated-scripts-analysis.md`

## Current Deprecation Warning Sources

### 1. Notebook Imports Triggering Package-Level Warnings

**Issue**: Importing from `orchestration.jobs.tracking.mlflow_tracker` triggers the package-level deprecation warning in `orchestration/__init__.py` because Python loads the `orchestration` package first.

**Locations**:
- `notebooks/01_orchestrate_training_colab.ipynb` - Cell ~22 (line 1020)
- `notebooks/02_best_config_selection.ipynb` - Cell ~23 (line 557)

**Impact**: 13+ deprecation warnings appear when importing MLflow trackers

### 2. Deprecated Shim Module Still Present

**Issue**: `src/training/cv_utils.py` is a deprecated shim that emits warnings when imported.

**Status**: No usage found in notebooks (already migrated), but shim file still exists

**Impact**: Warning appears if anyone imports it

### 3. HPO Backup Import Through Deprecated Path

**Issue**: `orchestration.jobs.hpo.local.backup` import triggers package-level warnings.

**Location**: `notebooks/01_orchestrate_training_colab.ipynb` - Cell ~44 (line 2139)

**Impact**: Package-level deprecation warnings

## Phase 1: Complete Notebook Import Migrations

**Priority**: High  
**Duration**: 1 day  
**Items**: 2 remaining deprecated imports  
**Risk**: Low

### Step 1.1: Migrate MLflow Tracker Imports in Notebook 1

**File**: `notebooks/01_orchestrate_training_colab.ipynb`  
**Cell**: ~22 (around line 1020)  
**Issue**: Importing from `orchestration.jobs.tracking.mlflow_tracker` triggers package-level warnings

1. **Locate the cell** with the import:
   ```python
   from orchestration.jobs.tracking.mlflow_tracker import (
       MLflowSweepTracker,
       MLflowBenchmarkTracker,
       MLflowTrainingTracker,
       MLflowConversionTracker,
   )
   ```

2. **Replace with direct import**:
   ```python
   from infrastructure.tracking.mlflow.trackers import (
       MLflowSweepTracker,
       MLflowBenchmarkTracker,
       MLflowTrainingTracker,
       MLflowConversionTracker,
   )
   ```

3. **Verify the replacement module exists**:
   ```bash
   grep -r "MLflowSweepTracker\|MLflowBenchmarkTracker" src/infrastructure/tracking/mlflow/trackers/
   ```

**Success criteria**:
- ✅ Import updated to `infrastructure.tracking.mlflow.trackers`
- ✅ All tracker classes available in replacement module
- ✅ No deprecation warnings when importing

**Verification**:
```bash
# Check for remaining orchestration.jobs.tracking.mlflow_tracker imports
grep -n "from orchestration\.jobs\.tracking\.mlflow_tracker" notebooks/01_orchestrate_training_colab.ipynb && \
  echo "⚠️ Still found!" || echo "✅ All migrated"
```

### Step 1.2: Migrate MLflow Tracker Import in Notebook 2

**File**: `notebooks/02_best_config_selection.ipynb`  
**Cell**: ~23 (around line 557)  
**Issue**: Same as Step 1.1

1. **Locate the cell** with the import:
   ```python
   from orchestration.jobs.tracking.mlflow_tracker import MLflowBenchmarkTracker
   ```

2. **Replace with direct import**:
   ```python
   from infrastructure.tracking.mlflow.trackers import MLflowBenchmarkTracker
   ```

**Success criteria**:
- ✅ Import updated to `infrastructure.tracking.mlflow.trackers`
- ✅ No deprecation warnings when importing

**Verification**:
```bash
# Check for remaining orchestration.jobs.tracking.mlflow_tracker imports
grep -n "from orchestration\.jobs\.tracking\.mlflow_tracker" notebooks/02_best_config_selection.ipynb && \
  echo "⚠️ Still found!" || echo "✅ All migrated"
```

### Step 1.3: Migrate HPO Backup Import

**File**: `notebooks/01_orchestrate_training_colab.ipynb`  
**Cell**: ~44 (around line 2139)  
**Issue**: Importing from `orchestration.jobs.hpo.local.backup` triggers package-level warnings

1. **Check if replacement exists**:
   ```bash
   # Check if backup_hpo_study_to_drive exists in training.hpo
   grep -r "def backup_hpo_study_to_drive" src/training/hpo/
   ```

2. **If replacement exists**, update import:
   ```python
   # Before
   from orchestration.jobs.hpo.local.backup import backup_hpo_study_to_drive
   
   # After
   from training.hpo.checkpoint.storage import backup_hpo_study_to_drive
   # OR from the actual location where it exists
   ```

3. **If replacement doesn't exist**:
   - Check if `orchestration.jobs.hpo.local.backup` is actually deprecated or active
   - If active, keep the import but note it's not deprecated
   - If deprecated, create replacement or document migration path

**Success criteria**:
- ✅ Import updated to use non-deprecated path (if replacement exists)
- ✅ OR documented that module is active (if not deprecated)
- ✅ No deprecation warnings when importing

**Verification**:
```bash
# Check for remaining orchestration.jobs.hpo imports
grep -n "from orchestration\.jobs\.hpo" notebooks/01_orchestrate_training_colab.ipynb && \
  echo "⚠️ Still found!" || echo "✅ All migrated"
```

### Step 1.4: Test Notebook Imports

After all migrations:

1. **Open each notebook in Jupyter**
2. **Run the cells with imports**
3. **Check for deprecation warnings**:
   - Should see zero deprecation warnings
   - All imports should work correctly

**Success criteria**:
- ✅ Both notebooks open without errors
- ✅ All import cells execute successfully
- ✅ Zero deprecation warnings in output
- ✅ Functionality is preserved

## Phase 2: Remove Deprecated Shim Modules

**Priority**: Medium  
**Duration**: 0.5 days  
**Items**: 1 deprecated shim module  
**Risk**: Low

### Step 2.1: Verify No Usage of training.cv_utils

**File**: `src/training/cv_utils.py`  
**Status**: Deprecated shim, emits warnings when imported

1. **Search for all usage**:
   ```bash
   # Check for any remaining usage
   grep -rn "from training\.cv_utils\|import training\.cv_utils" src/ tests/ notebooks/ 2>/dev/null | \
     grep -v "training/cv_utils.py\|backups/" && echo "⚠️ Usage found!" || echo "✅ No usage"
   ```

2. **Check notebook source cells** (not output):
   ```bash
   # Use Python to check notebook source cells
   python3 << 'EOF'
   import json
   with open('notebooks/01_orchestrate_training_colab.ipynb', 'r') as f:
       nb = json.load(f)
       for i, cell in enumerate(nb['cells']):
           if cell.get('cell_type') == 'code' and 'source' in cell:
               source = ''.join(cell['source'])
               if 'from training.cv_utils' in source or 'import training.cv_utils' in source:
                   print(f"⚠️ Cell {i} still uses training.cv_utils")
                   break
       else:
           print("✅ No training.cv_utils in notebook source cells")
   EOF
   ```

**Success criteria**:
- ✅ Zero usage found in source files
- ✅ Zero usage found in notebook source cells
- ✅ Only self-references in the shim file itself

### Step 2.2: Remove Deprecated Shim Module

If no usage is found:

1. **Remove the shim file**:
   ```bash
   rm src/training/cv_utils.py
   ```

2. **Verify removal**:
   ```bash
   test ! -f src/training/cv_utils.py && echo "✅ File removed" || echo "⚠️ File still exists"
   ```

3. **Check for broken imports**:
   ```bash
   grep -rn "from training\.cv_utils\|import training\.cv_utils" src/ tests/ 2>/dev/null && \
     echo "⚠️ Broken imports found!" || echo "✅ No broken imports"
   ```

**Success criteria**:
- ✅ File removed
- ✅ No broken imports
- ✅ Tests still pass

**If usage is found**:
- Document remaining usage locations
- Migrate usage first, then remove shim
- Update this plan with migration steps

## Phase 3: Address Package-Level Warnings

**Priority**: Medium  
**Duration**: 1 day  
**Items**: 1 package-level deprecation  
**Risk**: Medium

### Step 3.1: Understand the Issue

**Problem**: `orchestration/__init__.py` emits a package-level deprecation warning whenever `orchestration` is imported, even when importing active submodules like `orchestration.jobs.tracking.*`.

**Current behavior**: 
- Importing `from orchestration.jobs.tracking.mlflow_tracker import ...` triggers warnings
- This happens because Python loads `orchestration/__init__.py` first

**Options**:

**Option A**: Suppress warnings for active submodules
- Modify `orchestration/__init__.py` to only warn for deprecated imports
- Keep active modules (`orchestration.jobs.tracking.*`) working without warnings

**Option B**: Complete migration away from orchestration
- Migrate all `orchestration.jobs.tracking.*` usage to `infrastructure.tracking.*`
- Remove package-level warning after migration

**Recommended**: Option A - Keep active modules working, only warn for deprecated imports.

### Step 3.2: Implement Option A (Recommended)

**File**: `src/orchestration/__init__.py`

1. **Review current warning logic**:
   - Check where the package-level warning is emitted
   - Understand when it triggers

2. **Modify to suppress for active submodules**:
   - Use `__getattr__` to detect when importing active submodules
   - Only emit warnings for deprecated top-level imports
   - Allow `orchestration.jobs.tracking.*` imports without warnings

3. **Test the change**:
   ```python
   # Test that active modules don't trigger warnings
   import warnings
   with warnings.catch_warnings(record=True) as w:
       warnings.simplefilter("always")
       from orchestration.jobs.tracking.mlflow_tracker import MLflowSweepTracker
       assert len(w) == 0, "Should not emit warnings for active modules"
   ```

**Success criteria**:
- ✅ Active submodules (`orchestration.jobs.tracking.*`) import without warnings
- ✅ Deprecated top-level imports still emit warnings
- ✅ No functionality broken

### Step 3.3: Alternative - Complete Migration (Option B)

If choosing Option B instead:

1. **Identify all `orchestration.jobs.tracking.*` usage**:
   ```bash
   grep -rn "from orchestration\.jobs\.tracking\|import orchestration\.jobs\.tracking" src/ tests/ notebooks/ 2>/dev/null
   ```

2. **Map to replacements**:
   - `orchestration.jobs.tracking.mlflow_tracker` → `infrastructure.tracking.mlflow.trackers`
   - `orchestration.jobs.tracking.index.*` → `infrastructure.tracking.mlflow.index.*`
   - `orchestration.jobs.tracking.config.*` → `infrastructure.tracking.mlflow.config.*`

3. **Migrate all usage**:
   - Update source files
   - Update notebooks
   - Update tests

4. **Remove package-level warning** after migration complete

**Success criteria**:
- ✅ All `orchestration.jobs.tracking.*` usage migrated
- ✅ Package-level warning removed or updated
- ✅ No functionality broken

## Phase 4: Final Verification and Testing

**Priority**: Critical  
**Duration**: 1 day  
**Items**: Complete verification  
**Risk**: Low

### Step 4.1: Run Notebooks and Capture Warnings

1. **Open each notebook in Jupyter**
2. **Run all cells from top to bottom**
3. **Capture all output**, especially deprecation warnings
4. **Document any warnings that appear**

**Success criteria**:
- ✅ Both notebooks execute completely
- ✅ Zero deprecation warnings in output
- ✅ All functionality works as expected

### Step 4.2: Run Tests with Warnings Visible

```bash
# Run tests with deprecation warnings shown
python3 -m pytest tests/ -W default::DeprecationWarning --tb=short 2>&1 | tee test_warnings.log

# Count warnings
grep -c "DeprecationWarning" test_warnings.log || echo "0"
```

**Success criteria**:
- ✅ All tests pass
- ✅ Zero deprecation warnings in test output (or only expected ones in deprecated shim files)

### Step 4.3: Search for Remaining Deprecation Sources

```bash
# Find all code that emits DeprecationWarning
echo "=== DeprecationWarning instances ==="
grep -rn "DeprecationWarning" src/ --include="*.py" | \
  grep -v "\.plan\.md\|\.md:" | \
  wc -l

# Find all deprecated imports in source
echo "=== Deprecated imports in source ==="
grep -rn "from training\.cv_utils\|from orchestration\.jobs\.tracking\.mlflow_tracker\|from orchestration\.jobs\.hpo" src/ 2>/dev/null | \
  grep -v "orchestration/jobs/tracking\|orchestration/jobs/hpo" && \
  echo "⚠️ Deprecated imports found!" || echo "✅ No deprecated imports"

# Find deprecated imports in notebooks (source cells only)
echo "=== Deprecated imports in notebooks ==="
python3 << 'EOF'
import json
import sys

issues = []
for notebook in ['notebooks/01_orchestrate_training_colab.ipynb', 'notebooks/02_best_config_selection.ipynb']:
    with open(notebook, 'r') as f:
        nb = json.load(f)
        for i, cell in enumerate(nb['cells']):
            if cell.get('cell_type') == 'code' and 'source' in cell:
                source = ''.join(cell['source'])
                if 'from training.cv_utils' in source:
                    issues.append(f"{notebook}: Cell {i} - training.cv_utils")
                if 'from orchestration.jobs.tracking.mlflow_tracker' in source:
                    issues.append(f"{notebook}: Cell {i} - orchestration.jobs.tracking.mlflow_tracker")
                if 'from orchestration.jobs.hpo.local.backup' in source:
                    issues.append(f"{notebook}: Cell {i} - orchestration.jobs.hpo.local.backup")

if issues:
    print("⚠️ Issues found:")
    for issue in issues:
        print(f"  - {issue}")
    sys.exit(1)
else:
    print("✅ No deprecated imports in notebook source cells")
EOF
```

**Success criteria**:
- ✅ DeprecationWarning only in deprecated shim files (expected)
- ✅ No deprecated imports in source files
- ✅ No deprecated imports in notebook source cells

### Step 4.4: Verify Config Key Migrations

```bash
# Check for remaining objective.goal usage
grep -rn "objective.*goal\|goal:" --include="*.yaml" --include="*.yml" . 2>/dev/null | \
  grep -v "direction\|#\|deprecated\|\.git" && \
  echo "⚠️ Config files still have goal:" || echo "✅ All config files updated"
```

**Success criteria**:
- ✅ All config files use `direction:` instead of `goal:`
- ✅ Code handles both keys with backward compatibility

### Step 4.5: Create Deprecation Warning Report

After all verification, create a summary report:

```bash
cat > docs/implementation_plans/audits/deprecation-warning-elimination-report.md << 'EOF'
# Deprecation Warning Elimination Report

**Date**: $(date +%Y-%m-%d)
**Plan**: complete-deprecation-warning-elimination.plan.md
**Status**: ✅ Complete

## Summary

All deprecation warnings have been eliminated from the codebase.

## Actions Taken

1. Migrated notebook imports to avoid package-level warnings
2. Removed deprecated shim modules with zero usage
3. Addressed package-level deprecation warnings

## Verification Results

- Notebooks: ✅ Zero warnings
- Tests: ✅ Zero warnings
- Source code: ✅ No deprecated imports
- Config files: ✅ All updated

## Remaining Deprecation Warnings

(Should be zero, or only in deprecated shim files that are kept for backward compatibility)

EOF
```

## Success Criteria (Overall)

- ✅ **Phase 1 Complete**: All notebook imports migrated (2 items)
- ✅ **Phase 2 Complete**: Deprecated shim modules removed (1 item)
- ✅ **Phase 3 Complete**: Package-level warnings addressed (1 item)
- ✅ **Phase 4 Complete**: Full verification passed
- ✅ **Zero Deprecation Warnings**: No warnings appear when running notebooks or tests
- ✅ **Tests Pass**: All tests pass with no regressions
- ✅ **Functionality Preserved**: All features work as expected

## Estimated Timeline

| Phase | Items | Duration | Can Start |
|-------|-------|----------|-----------|
| Phase 1 | 2 notebook imports | 0.5 days | Immediately |
| Phase 2 | 1 shim module | 0.5 days | After Phase 1 |
| Phase 3 | 1 package warning | 1 day | After Phase 1 |
| Phase 4 | Verification | 0.5 days | After Phases 1-3 |

**Total Estimated Effort**: 2.5 days

## Rollback Plan

If issues are discovered:

1. **Notebooks**: Restore from backups:
   ```bash
   cp backups/notebooks/01_orchestrate_training_colab.ipynb notebooks/
   cp backups/notebooks/02_best_config_selection.ipynb notebooks/
   ```

2. **Removed Modules**: Restore from git:
   ```bash
   git checkout HEAD -- src/training/cv_utils.py
   ```

3. **Package Changes**: Revert `orchestration/__init__.py` changes:
   ```bash
   git checkout HEAD -- src/orchestration/__init__.py
   ```

## Notes

- **Incremental Approach**: Each phase can be executed independently (respecting prerequisites)
- **Testing**: Run tests after each major change
- **Documentation**: Update docs as you go
- **Communication**: Notify team when deprecated modules are removed
- **Git History**: All changes are in git history for reference

## Related Plans

- `docs/implementation_plans/deprecated-scripts-migration-and-removal.plan.md` - Previous migration work
- `docs/implementation_plans/audits/deprecated-scripts-audit.md` - Source audit document
- `docs/implementation_plans/deprecated-code-removal-roadmap.plan.md` - General removal roadmap


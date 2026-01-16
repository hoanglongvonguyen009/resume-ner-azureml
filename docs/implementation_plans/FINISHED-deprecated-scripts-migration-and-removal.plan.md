# Deprecated Scripts Migration and Removal Plan

## Goal

Migrate all deprecated script imports and remove deprecated modules based on the comprehensive audit in `docs/implementation_plans/audits/deprecated-scripts-audit.md`. This plan provides step-by-step instructions for:
1. Migrating deprecated imports in notebooks and source files
2. Updating configuration files with deprecated keys
3. Removing deprecated modules that are no longer used
4. Verifying all migrations are complete

## Status

**Last Updated**: 2025-01-27

### Completed Steps
- ✅ Phase 1: Migrate Notebook Imports (16 items) - Completed 2025-01-27
- ✅ Phase 2: Update Configuration Files (1 item, 3 files) - Completed 2025-01-27
- ✅ Phase 3: Remove Unused Deprecated Modules (10 items) - Completed 2025-01-27
- ✅ Phase 4: Verification and Testing - Completed 2025-01-27

### Pending Steps
- (None - all phases complete)

## Preconditions

- ✅ Audit document complete: `docs/implementation_plans/audits/deprecated-scripts-audit.md`
- ✅ All replacement modules exist and are verified
- ✅ Test suite is passing
- ✅ Codebase is in stable state
- ✅ Backup of notebooks created

## Reference Documents

- **Audit Document**: `docs/implementation_plans/audits/deprecated-scripts-audit.md`
- **Analysis Document**: `docs/implementation_plans/audits/deprecated-scripts-analysis.md`
- **Removal Roadmap**: `docs/implementation_plans/deprecated-code-removal-roadmap.plan.md`

## Phase 1: Migrate Notebook Imports

**Priority**: High  
**Duration**: 2-3 days  
**Items**: 16 deprecated imports in 2 notebooks  
**Risk**: Low-Medium

### Items to Migrate

#### Notebook 1: `notebooks/01_orchestrate_training_colab.ipynb`

1. `training.cv_utils` → `training.core.cv_utils` (lines 1606, 1611)
2. `orchestration` (package-level) → Various replacements (multiple locations)
3. `orchestration.constants` → `common.constants` (line 1514, 2102)
4. `orchestration.jobs.hpo.local.backup` → `training.hpo.checkpoint.storage` (line 2171)
5. `orchestration.jobs.tracking.mlflow_tracker` → `infrastructure.tracking.mlflow.trackers` (line 1020)

#### Notebook 2: `notebooks/02_best_config_selection.ipynb`

1. `conversion` → `deployment.conversion` (line 933)
2. `orchestration.jobs.tracking.mlflow_tracker` → `infrastructure.tracking.mlflow.trackers` (line 563)

### Step 1: Backup Notebooks

Before making changes, create backups:

```bash
# Create backup directory
mkdir -p backups/notebooks

# Backup notebooks
cp notebooks/01_orchestrate_training_colab.ipynb backups/notebooks/
cp notebooks/02_best_config_selection.ipynb backups/notebooks/

# Verify backups
ls -lh backups/notebooks/
```

**Success criteria**:
- ✅ Both notebooks backed up
- ✅ Backup files are readable

### Step 2: Migrate `training.cv_utils` in Notebook 1

**File**: `notebooks/01_orchestrate_training_colab.ipynb`  
**Lines**: 1606, 1611

1. Open the notebook in editor
2. Find all occurrences of `from training.cv_utils import`
3. Replace with `from training.core.cv_utils import`
4. Verify the import statement matches:
   ```python
   # Before
   from training.cv_utils import (
       create_kfold_splits,
       load_fold_splits,
       save_fold_splits,
   )
   
   # After
   from training.core.cv_utils import (
       create_kfold_splits,
       load_fold_splits,
       save_fold_splits,
   )
   ```

**Success criteria**:
- ✅ All `training.cv_utils` imports replaced with `training.core.cv_utils`
- ✅ No remaining references to `training.cv_utils` in notebook
- ✅ Notebook syntax is valid (can be opened in Jupyter)

**Verification**:
```bash
# Check for remaining deprecated imports
grep -n "training\.cv_utils" notebooks/01_orchestrate_training_colab.ipynb && echo "Still found!" || echo "All migrated"
```

### Step 3: Migrate `orchestration` Package Imports in Notebook 1

**File**: `notebooks/01_orchestrate_training_colab.ipynb`  
**Locations**: Multiple (lines 978, 981, 983, 985, 987, 989, 991, 993, 995, 997, 999, 1001, 1003, 1009, 1045, 1514, 2102)

This is a complex migration because `orchestration` is a package-level import that needs to be split into multiple specific imports.

1. **Identify all imports from `orchestration`**:
   - Search for `from orchestration import` in the notebook
   - List all imported items

2. **Map each import to its replacement**:
   - Constants → `common.constants`
   - Paths → `infrastructure.paths`
   - Fingerprints → `infrastructure.fingerprints`
   - Metadata → `infrastructure.metadata`
   - Storage → `infrastructure.storage`
   - Config → `infrastructure.config.*`
   - Benchmarking → `evaluation.benchmarking.*`

3. **Update imports systematically**:

   **Example migration pattern**:
   ```python
   # Before (deprecated)
   from orchestration import (
       STAGE_HPO,
       EXPERIMENT_NAME,
       resolve_output_path,
       compute_spec_fp,
       update_index,
   )
   
   # After (replacement)
   from common.constants import STAGE_HPO, EXPERIMENT_NAME
   from infrastructure.paths import resolve_output_path
   from infrastructure.fingerprints import compute_spec_fp
   from infrastructure.metadata.index import update_index
   ```

4. **For each cell with `orchestration` imports**:
   - Identify what's being imported
   - Replace with appropriate new imports
   - Test the cell to ensure it still works

**Success criteria**:
- ✅ All `from orchestration import` statements replaced
- ✅ All imports use new module paths
- ✅ No remaining references to `orchestration` package (except `orchestration.jobs.tracking.*` which is not deprecated)
- ✅ Notebook cells can execute without deprecation warnings

**Verification**:
```bash
# Check for remaining orchestration imports (excluding non-deprecated jobs.tracking)
grep -n "from orchestration import\|import orchestration" notebooks/01_orchestrate_training_colab.ipynb | \
  grep -v "orchestration.jobs.tracking" && echo "Still found!" || echo "All migrated"
```

### Step 4: Migrate `orchestration.jobs.hpo.local.backup` in Notebook 1

**File**: `notebooks/01_orchestrate_training_colab.ipynb`  
**Line**: 2171

1. Find the import statement:
   ```python
   from orchestration.jobs.hpo.local.backup import backup_hpo_study_to_drive
   ```

2. Replace with:
   ```python
   from training.hpo.checkpoint.storage import backup_hpo_study_to_drive
   # Note: Verify the actual function name in the replacement module
   ```

3. Verify the function exists in the replacement module:
   ```bash
   grep -r "def backup_hpo_study_to_drive\|backup_hpo_study_to_drive" src/training/hpo/
   ```

**Success criteria**:
- ✅ Import updated to use new module path
- ✅ Function exists in replacement module
- ✅ No deprecation warning when importing

### Step 5: Migrate `orchestration.jobs.tracking.mlflow_tracker` in Notebook 1

**File**: `notebooks/01_orchestrate_training_colab.ipynb`  
**Line**: 1020

**Note**: `orchestration.jobs.tracking.*` modules are **NOT deprecated** - they are active modules. However, if there's a better location, we should migrate.

1. Check if this is actually deprecated or if it's an active module:
   ```bash
   grep -r "orchestration.jobs.tracking" src/orchestration/jobs/tracking/
   ```

2. If it's an active module, keep the import as-is
3. If it's deprecated, find the replacement:
   ```bash
   # Check for replacement in infrastructure.tracking
   find src/infrastructure/tracking -name "*mlflow*" -type f
   ```

**Success criteria**:
- ✅ Import verified (either kept if active, or migrated if deprecated)
- ✅ No broken imports

### Step 6: Migrate `conversion` in Notebook 2

**File**: `notebooks/02_best_config_selection.ipynb`  
**Line**: 933

1. Find the import statement:
   ```python
   from conversion import execute_conversion
   ```

2. Replace with:
   ```python
   from deployment.conversion import execute_conversion
   ```

3. Verify the function exists:
   ```bash
   grep -r "def execute_conversion" src/deployment/conversion/
   ```

**Success criteria**:
- ✅ Import updated to `deployment.conversion`
- ✅ Function exists in replacement module
- ✅ No deprecation warning

### Step 7: Migrate `orchestration.jobs.tracking.mlflow_tracker` in Notebook 2

**File**: `notebooks/02_best_config_selection.ipynb`  
**Line**: 563

Follow the same process as Step 5 - verify if this is deprecated or active.

### Step 8: Test Notebooks

After all migrations:

1. **Open each notebook in Jupyter**:
   ```bash
   # Start Jupyter (if not already running)
   jupyter notebook
   ```

2. **Run each cell sequentially**:
   - Check for import errors
   - Check for deprecation warnings
   - Verify functionality is preserved

3. **Look for deprecation warnings in output**:
   - Should see no `DeprecationWarning` messages
   - All imports should work correctly

**Success criteria**:
- ✅ Both notebooks open without errors
- ✅ All cells execute successfully
- ✅ No deprecation warnings in output
- ✅ Functionality is preserved

**Verification**:
```bash
# Run a quick syntax check (if you have nbconvert)
jupyter nbconvert --to python notebooks/01_orchestrate_training_colab.ipynb --stdout > /dev/null && echo "Notebook 1: Valid" || echo "Notebook 1: Invalid"
jupyter nbconvert --to python notebooks/02_best_config_selection.ipynb --stdout > /dev/null && echo "Notebook 2: Valid" || echo "Notebook 2: Invalid"
```

## Phase 2: Update Configuration Files

**Priority**: Low  
**Duration**: 1 day  
**Items**: 1 deprecated config key  
**Risk**: Low

### Items to Update

1. `objective.goal` → `objective.direction` in YAML config files (7 files)

### Step 1: Find All Config Files Using `objective.goal`

```bash
# Find all YAML files with objective.goal
find . -name "*.yaml" -o -name "*.yml" | xargs grep -l "objective.*goal\|goal:" 2>/dev/null

# Or more specific
grep -rn "objective.*goal\|goal:" --include="*.yaml" --include="*.yml" . 2>/dev/null | grep -v "direction"
```

**Success criteria**:
- ✅ Complete list of config files using `objective.goal`
- ✅ Count matches expected (7 files)

### Step 2: Update Each Config File

For each config file found:

1. **Open the file**
2. **Find the `objective.goal` key**:
   ```yaml
   objective:
     goal: maximize  # deprecated
   ```

3. **Replace with `objective.direction`**:
   ```yaml
   objective:
     direction: maximize  # new key
   ```

4. **Remove any deprecation comments** if present

5. **Verify YAML syntax is valid**:
   ```bash
   # If you have yamllint or similar
   yamllint <config_file>
   ```

**Success criteria**:
- ✅ All `objective.goal` keys replaced with `objective.direction`
- ✅ YAML syntax is valid
- ✅ No broken config files

**Verification**:
```bash
# Check for remaining objective.goal
grep -rn "objective.*goal\|goal:" --include="*.yaml" --include="*.yml" . 2>/dev/null | \
  grep -v "direction\|#\|deprecated" && echo "Still found!" || echo "All migrated"
```

### Step 3: Test Config Loading

After updating config files:

1. **Test config loading in code**:
   ```python
   from infrastructure.config.selection import load_selection_config
   
   # Try loading a config file
   config = load_selection_config("path/to/config.yaml")
   assert "direction" in config.get("objective", {})
   assert "goal" not in config.get("objective", {})
   ```

2. **Run any tests that use config files**:
   ```bash
   uvx pytest tests/ -k config
   ```

**Success criteria**:
- ✅ Config files load successfully
- ✅ Tests pass
- ✅ No errors related to missing `goal` key (automatic mapping should handle it)

## Phase 3: Remove Unused Deprecated Modules

**Priority**: Low  
**Duration**: 1 day  
**Items**: 10 deprecated modules with no usage  
**Risk**: Very Low

### Items to Remove

All these modules have **no external usage** and can be safely removed:

1. `src/training/checkpoint_loader.py`
2. `src/training/data.py`
3. `src/training/distributed.py`
4. `src/training/distributed_launcher.py`
5. `src/training/evaluator.py`
6. `src/training/metrics.py`
7. `src/training/model.py`
8. `src/training/train.py`
9. `src/training/trainer.py`
10. `src/training/utils.py`

### Step 1: Final Verification of No Usage

Before removing, do a final check:

```bash
# Check each module for any usage
for module in checkpoint_loader data distributed distributed_launcher evaluator metrics model train trainer utils; do
  echo "Checking training.$module..."
  grep -rn "from training\.$module\|import training\.$module" src/ tests/ notebooks/ 2>/dev/null | \
    grep -v "training/$module.py" && echo "  ⚠️ Usage found!" || echo "  ✅ No usage"
done
```

**Success criteria**:
- ✅ All modules show "No usage"
- ✅ Only self-references found (within the deprecated module itself)

### Step 2: Remove Deprecated Modules

After verification, remove the files:

```bash
# Remove deprecated training modules
rm src/training/checkpoint_loader.py
rm src/training/data.py
rm src/training/distributed.py
rm src/training/distributed_launcher.py
rm src/training/evaluator.py
rm src/training/metrics.py
rm src/training/model.py
rm src/training/train.py
rm src/training/trainer.py
rm src/training/utils.py

# Verify removal
ls src/training/*.py 2>/dev/null | grep -E "(checkpoint_loader|data|distributed|evaluator|metrics|model|train|trainer|utils)" && \
  echo "⚠️ Some files still exist" || echo "✅ All files removed"
```

**Success criteria**:
- ✅ All 10 files removed
- ✅ No broken imports in codebase

### Step 3: Update Training Package `__init__.py` (if needed)

Check if `src/training/__init__.py` exports any of the removed modules:

```bash
# Check for exports
grep -n "from.*checkpoint_loader\|from.*data\|from.*distributed\|from.*evaluator\|from.*metrics\|from.*model\|from.*train\|from.*trainer\|from.*utils" src/training/__init__.py
```

If exports are found, remove them:

1. Open `src/training/__init__.py`
2. Remove any imports/exports of removed modules
3. Verify the file is still valid

**Success criteria**:
- ✅ No exports of removed modules in `__init__.py`
- ✅ File syntax is valid

### Step 4: Verify No Broken Imports

After removal, verify nothing is broken:

```bash
# Check for broken imports
grep -rn "from training\.\(checkpoint_loader\|data\|distributed\|distributed_launcher\|evaluator\|metrics\|model\|train\|trainer\|utils\)\|import training\.\(checkpoint_loader\|data\|distributed\|distributed_launcher\|evaluator\|metrics\|model\|train\|trainer\|utils\)" src/ tests/ 2>/dev/null && \
  echo "⚠️ Broken imports found!" || echo "✅ No broken imports"
```

**Success criteria**:
- ✅ No broken imports found
- ✅ All imports use replacement modules

## Phase 4: Verification and Testing

**Priority**: Critical  
**Duration**: 1 day  
**Items**: Full verification  
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
- ✅ No deprecation warnings in test output (or only expected ones)

### Step 2: Run Type Checking

```bash
# Run mypy
uvx mypy src --show-error-codes

# Check notebooks (if mypy supports it)
# Note: Notebooks may not be type-checkable
```

**Success criteria**:
- ✅ Mypy passes with no new errors
- ✅ No type errors related to removed modules

### Step 3: Verify No Deprecation Warnings in Source

```bash
# Search for any remaining deprecated imports in source
grep -rn "from training\.\(cv_utils\|checkpoint_loader\|data\|distributed\|distributed_launcher\|evaluator\|metrics\|model\|train\|trainer\|utils\)" src/ 2>/dev/null | \
  grep -v "training/\(cv_utils\|checkpoint_loader\|data\|distributed\|distributed_launcher\|evaluator\|metrics\|model\|train\|trainer\|utils\)\.py" && \
  echo "⚠️ Deprecated imports still in source!" || echo "✅ No deprecated imports in source"

# Check for orchestration imports (excluding active jobs.tracking)
grep -rn "from orchestration import\|import orchestration" src/ 2>/dev/null | \
  grep -v "orchestration/__init__.py\|orchestration/jobs/tracking" && \
  echo "⚠️ Orchestration imports still in source!" || echo "✅ No orchestration imports in source (except active modules)"

# Check for conversion imports
grep -rn "from conversion import\|import conversion" src/ 2>/dev/null | \
  grep -v "conversion/__init__.py" && \
  echo "⚠️ Conversion imports still in source!" || echo "✅ No conversion imports in source"
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
- ✅ Both notebooks execute completely
- ✅ No deprecation warnings
- ✅ All functionality works as expected

### Step 5: Check for Remaining Deprecation Warnings

Run a comprehensive search:

```bash
# Find all DeprecationWarning instances in code
grep -rn "DeprecationWarning" src/ notebooks/ 2>/dev/null | \
  grep -v "\.plan\.md\|\.md:" | wc -l

# This should only show warnings in deprecated modules themselves (which is expected)
```

**Success criteria**:
- ✅ Deprecation warnings only appear in deprecated module files (expected)
- ✅ No warnings when importing replacement modules

### Step 6: Update Documentation

Update any documentation that references deprecated imports:

1. **Check README files**:
   ```bash
   find . -name "README*.md" -exec grep -l "training\.\(cv_utils\|checkpoint_loader\|data\|distributed\|distributed_launcher\|evaluator\|metrics\|model\|train\|trainer\|utils\)\|orchestration\|conversion" {} \;
   ```

2. **Update examples** in documentation to use new imports

3. **Update migration guides** if they exist

**Success criteria**:
- ✅ Documentation updated with new import paths
- ✅ Examples use non-deprecated imports

## Success Criteria (Overall)

- ✅ **Phase 1 Complete**: All notebook imports migrated (16 items)
- ✅ **Phase 2 Complete**: All config files updated (1 item, 7 files)
- ✅ **Phase 3 Complete**: All unused deprecated modules removed (10 items)
- ✅ **Phase 4 Complete**: Full verification and testing passed
- ✅ **No Deprecation Warnings**: No warnings appear when running code (except in deprecated modules themselves)
- ✅ **Tests Pass**: All tests pass with no regressions
- ✅ **Type Checking Passes**: Mypy passes with no new errors
- ✅ **Documentation Updated**: All docs use new import paths

## Estimated Timeline

| Phase | Items | Duration | Can Start |
|-------|-------|----------|-----------|
| Phase 1 | 16 notebook imports | 2-3 days | Immediately |
| Phase 2 | 1 config key (7 files) | 1 day | After Phase 1 |
| Phase 3 | 10 modules | 1 day | After Phase 1 |
| Phase 4 | Verification | 1 day | After Phases 1-3 |

**Total Estimated Effort**: 5-6 days

## Rollback Plan

If issues are discovered:

1. **Notebooks**: Restore from backups:
   ```bash
   cp backups/notebooks/01_orchestrate_training_colab.ipynb notebooks/
   cp backups/notebooks/02_best_config_selection.ipynb notebooks/
   ```

2. **Config Files**: Use git to revert:
   ```bash
   git checkout -- config/*.yaml
   ```

3. **Removed Modules**: Restore from git:
   ```bash
   git checkout HEAD -- src/training/checkpoint_loader.py
   # ... (repeat for each removed file)
   ```

## Notes

- **Incremental Approach**: Each phase can be executed independently (respecting prerequisites)
- **Testing**: Run tests after each major change
- **Documentation**: Update docs as you go, not at the end
- **Communication**: Notify team when deprecated modules are removed
- **Git History**: All changes are in git history for reference

## Related Plans

- `docs/implementation_plans/audits/deprecated-scripts-audit.md` - Source audit document
- `docs/implementation_plans/deprecated-code-removal-roadmap.plan.md` - General removal roadmap
- `docs/implementation_plans/audits/deprecated-scripts-analysis.md` - Detailed analysis


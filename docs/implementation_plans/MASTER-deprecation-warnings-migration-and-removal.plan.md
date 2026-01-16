# Master Plan: Deprecation Warnings Migration and Removal

## Goal

Find all scripts with `DeprecationWarning`/deprecation warnings and build a comprehensive plan to replace/remove/migrate the code/logic so that we totally change to the latest version. This plan covers:

1. **Deprecated facade modules** - Remove compatibility shims after migration
2. **Deprecated config keys** - Migrate to new key names
3. **Deprecated functions** - Replace with modern alternatives or remove
4. **Deprecated fallback behaviors** - Remove fallback code paths

## Status

**Last Updated**: 2025-01-27

### Completed Steps
- (None yet - plan creation)

### Pending Steps
- ⏳ Phase 1: Audit all deprecation warnings and categorize
- ⏳ Phase 2: Migrate deprecated config keys
- ⏳ Phase 3: Replace deprecated functions
- ⏳ Phase 4: Remove deprecated facade modules
- ⏳ Phase 5: Remove deprecated fallback behaviors
- ⏳ Phase 6: Verification and testing

## Preconditions

- ✅ Test suite is passing
- ✅ Codebase is in stable state
- ✅ Replacement modules/functions exist and are verified
- ✅ Previous deprecation work documented (see Reference Documents)

## Reference Documents

- `docs/implementation_plans/FINISHED-MASTER-deprecated-modules-migration-and-removal.plan.md` - Previous facade module work
- `docs/implementation_plans/FINISHED-deprecated-scripts-migration-and-removal.plan.md` - Previous script migration work
- `docs/implementation_plans/FINISHED-complete-deprecation-warning-elimination.plan.md` - Previous warning elimination work
- `docs/implementation_plans/FINISHED-deprecated-code-removal-roadmap.plan.md` - Previous deprecation roadmap

## Deprecation Inventory

### Category 1: Deprecated Facade Modules (2 modules)

#### 1.1 `src/orchestration/__init__.py`
- **Status**: `lifecycle: status: deprecated`
- **Replacement**: Various modules (`infrastructure.*`, `common.*`, `evaluation.*`)
- **Deprecation Warning**: Emitted on direct import (not for `orchestration.jobs.*` submodules)
- **Usage**: Re-exports functions from new modular structure
- **Action**: Remove after all imports migrated

#### 1.2 `src/selection/__init__.py`
- **Status**: `lifecycle: status: deprecated`
- **Replacement**: `evaluation.selection.*`
- **Deprecation Warning**: Emitted on import
- **Usage**: Compatibility shim that proxies to `evaluation.selection.*`
- **Action**: Remove after all imports migrated

### Category 2: Deprecated Config Keys (1 key)

#### 2.1 `objective.goal` → `objective.direction`
- **Files affected**: 5 source files
  - `src/training/hpo/checkpoint/cleanup.py` (2 occurrences)
  - `src/training/hpo/execution/azureml/sweeps.py` (2 occurrences)
  - `src/training/hpo/core/study.py` (1 occurrence)
  - `src/infrastructure/config/selection.py` (1 occurrence)
- **Replacement**: Use `objective.direction` instead
- **Current behavior**: Code supports both keys with deprecation warning for `goal`
- **Action**: Remove support for `goal` key, update all config files

### Category 3: Deprecated Functions (2 functions)

#### 3.1 `find_checkpoint_in_trial_dir()` in `evaluation/benchmarking/orchestrator.py`
- **Location**: `src/evaluation/benchmarking/orchestrator.py:361`
- **Deprecation**: "Use champions from Phase 2 which already have checkpoint_path set"
- **Usage**: 3 internal uses in same file
- **Replacement**: Champions from Phase 2 already have `checkpoint_path` set
- **Action**: Remove function and update callers to use `checkpoint_path` from champions

#### 3.2 `compute_grouping_tags()` in `evaluation/benchmarking/orchestrator.py`
- **Location**: `src/evaluation/benchmarking/orchestrator.py:467`
- **Deprecation**: "Use champions from Phase 2 which already have study_key_hash and trial_key_hash set"
- **Usage**: 9 uses (3 internal, 6 exported)
- **Replacement**: Champions from Phase 2 already have `study_key_hash` and `trial_key_hash` set
- **Action**: Remove function and update callers to use hashes from champions

### Category 4: Deprecated Fallback Behaviors (1 fallback)

#### 4.1 Inline config building fallback in `infrastructure/config/training.py`
- **Location**: `src/infrastructure/config/training.py:90`
- **Deprecation**: "config/final_training.yaml not found. Falling back to inline config building"
- **Current behavior**: Falls back to `_build_final_training_config_inline()` if `final_training.yaml` not found
- **Action**: Remove fallback, require `final_training.yaml` to exist

### Category 5: UserWarning/DeprecationWarning (Not actual deprecations - informational)

These are warnings for missing dependencies or fallback behaviors, not code deprecations:
- Missing `onnxruntime` in `deployment/conversion/testing.py` (UserWarning)
- Missing `mlflow` in `common/shared/mlflow_setup.py` (suppressing MLflow's own deprecation warnings)
- Missing fingerprint functions in `infrastructure/config/training.py` (RuntimeWarning)
- Missing `ml_client` in `orchestration/jobs/conversion.py` and `deployment/conversion/azureml.py` (UserWarning)
- Int8 quantization fallback in `deployment/conversion/export.py` (UserWarning)
- Stratification fallback in `data/loaders/dataset_loader.py` (UserWarning)

**Note**: These are not code deprecations - they're runtime warnings for missing dependencies or fallback behaviors. They should remain as-is.

## Phase 1: Comprehensive Audit

**Priority**: High  
**Duration**: 2-3 hours  
**Risk**: Low

### Step 1: Audit All Deprecation Warnings

Find all files that emit `DeprecationWarning`:

```bash
# Find all DeprecationWarning usage
grep -rn "DeprecationWarning" src/ --include="*.py" | grep -v "test\|#.*DeprecationWarning"

# Find all files with deprecated status in metadata
grep -rn "status:\s*deprecated" src/ --include="*.py"

# Find all config files using deprecated keys
find config/ -name "*.yaml" -exec grep -l "objective\.goal" {} \;

# Find all usages of deprecated functions
grep -rn "find_checkpoint_in_trial_dir\|compute_grouping_tags" src/ tests/ --include="*.py"
```

**Success criteria**:
- ✅ Complete inventory of all deprecation warnings
- ✅ Categorized by type (facade, config key, function, fallback)
- ✅ Usage count for each deprecated item
- ✅ Replacement identified for each deprecated item

### Step 2: Document Migration Paths

For each deprecated item, document:
1. Current usage locations
2. Replacement approach
3. Migration steps
4. Breaking changes (if any)

**Success criteria**:
- ✅ Migration path documented for each deprecated item
- ✅ Breaking changes identified and documented
- ✅ Rollback plan documented (if needed)

## Phase 2: Migrate Deprecated Config Keys

**Priority**: High  
**Duration**: 1-2 hours  
**Risk**: Medium (config changes affect all workflows)

### Step 1: Find All Config Files Using `objective.goal`

```bash
# Find all YAML files with objective.goal
find config/ -name "*.yaml" -exec grep -l "objective\.goal" {} \;

# Count occurrences
find config/ -name "*.yaml" -exec grep -H "objective\.goal" {} \; | wc -l
```

**Success criteria**:
- ✅ Complete list of config files using `objective.goal`
- ✅ Count of occurrences

### Step 2: Update Config Files

For each config file:
1. Replace `objective.goal` with `objective.direction`
2. Map values: `maximize`/`max` → `maximize`, `minimize`/`min` → `minimize`
3. Verify config still valid

**Success criteria**:
- ✅ All config files updated
- ✅ No `objective.goal` keys remain in config files
- ✅ Config files still valid (YAML syntax correct)

### Step 3: Remove Backward Compatibility Code

Remove the backward compatibility code that supports `objective.goal`:

**Files to update**:
- `src/training/hpo/checkpoint/cleanup.py` (2 locations)
- `src/training/hpo/execution/azureml/sweeps.py` (2 locations)
- `src/training/hpo/core/study.py` (1 location)
- `src/infrastructure/config/selection.py` (1 location)

**Changes**:
- Remove `elif "goal" in objective:` branches
- Remove deprecation warnings
- Keep only `direction` key support

**Success criteria**:
- ✅ All backward compatibility code removed
- ✅ Only `objective.direction` supported
- ✅ No deprecation warnings for `objective.goal`
- ✅ Tests pass: `uvx pytest tests/`

## Phase 3: Replace Deprecated Functions

**Priority**: Medium  
**Duration**: 2-3 hours  
**Risk**: Medium (function removal affects callers)

### Step 1: Audit Function Usage

```bash
# Find all usages of find_checkpoint_in_trial_dir
grep -rn "find_checkpoint_in_trial_dir" src/ tests/ --include="*.py"

# Find all usages of compute_grouping_tags
grep -rn "compute_grouping_tags" src/ tests/ --include="*.py"

# Check exports
grep -rn "from.*compute_grouping_tags\|import.*compute_grouping_tags" src/ --include="*.py"
```

**Success criteria**:
- ✅ Complete list of all callers
- ✅ Exports identified
- ✅ Internal vs external usage identified

### Step 3.1: Replace `find_checkpoint_in_trial_dir()` Usage

**Location**: `src/evaluation/benchmarking/orchestrator.py:759`

**Current usage**:
```python
checkpoint_dir = find_checkpoint_in_trial_dir(trial_dir)
```

**Replacement**: Use `checkpoint_path` from champions (Phase 2 format)

**Action**:
1. Update caller to use `checkpoint_path` from champion data structure
2. Remove function definition
3. Remove from exports (if exported)

**Success criteria**:
- ✅ Function removed
- ✅ All callers updated to use `checkpoint_path` from champions
- ✅ Tests pass: `uvx pytest tests/`

### Step 3.2: Replace `compute_grouping_tags()` Usage

**Locations**: Multiple (9 uses total)

**Current usage**: Called to compute `study_key_hash`, `trial_key_hash`, `study_family_hash`

**Replacement**: Use `study_key_hash` and `trial_key_hash` from champions (Phase 2 format)

**Action**:
1. Update all callers to use hashes from champion data structure
2. Remove function definition
3. Remove from exports:
   - `src/evaluation/benchmarking/__init__.py`
   - `src/evaluation/__init__.py`
   - `src/orchestration/jobs/benchmarking/__init__.py` (if exists)

**Success criteria**:
- ✅ Function removed
- ✅ All callers updated to use hashes from champions
- ✅ Removed from all exports
- ✅ Tests pass: `uvx pytest tests/`

## Phase 4: Remove Deprecated Facade Modules

**Priority**: Medium  
**Duration**: 2-3 hours  
**Risk**: High (breaking changes for any remaining imports)

### Step 1: Audit Remaining Imports

```bash
# Find all imports from orchestration (excluding orchestration.jobs.*)
grep -rn "from orchestration import\|^import orchestration" src/ tests/ notebooks/ --include="*.py" | grep -v "orchestration\.jobs\|orchestration/__init__"

# Find all imports from selection
grep -rn "from selection import\|^import selection" src/ tests/ notebooks/ --include="*.py" | grep -v "selection/__init__\|selection\.selection\|selection\.selection_logic\|selection\.types"
```

**Success criteria**:
- ✅ Complete list of remaining imports
- ✅ Categorized by module (orchestration vs selection)
- ✅ Replacement module identified for each import

### Step 2: Migrate Remaining Imports

For each import found:
1. Identify replacement module
2. Update import statement
3. Verify functionality unchanged
4. Run tests

**Success criteria**:
- ✅ All imports migrated
- ✅ No imports from deprecated facades remain (except in facade files themselves)
- ✅ Tests pass: `uvx pytest tests/`

### Step 3: Remove Deprecated Facade Modules

**Files to remove**:
- `src/orchestration/__init__.py` (if no longer needed)
- `src/selection/__init__.py` (if no longer needed)

**Note**: Check if these files are needed as package entry points. If `orchestration/` or `selection/` directories contain active submodules, keep the `__init__.py` files but remove deprecation warnings and facade logic.

**Action**:
1. Verify no remaining imports
2. Remove deprecation warnings
3. Remove facade logic (re-exports)
4. If directory has active submodules, keep minimal `__init__.py`
5. If directory is empty, remove entire directory

**Success criteria**:
- ✅ Deprecated facade modules removed or cleaned up
- ✅ No deprecation warnings from facade modules
- ✅ Tests pass: `uvx pytest tests/`
- ✅ No broken imports

## Phase 5: Remove Deprecated Fallback Behaviors

**Priority**: Low  
**Duration**: 1 hour  
**Risk**: Medium (removing fallback may break workflows)

### Step 1: Audit Fallback Usage

```bash
# Find inline config building usage
grep -rn "_build_final_training_config_inline" src/ --include="*.py"

# Check if final_training.yaml exists in all expected locations
find . -name "final_training.yaml" -type f
```

**Success criteria**:
- ✅ Complete list of fallback usage
- ✅ All expected `final_training.yaml` files exist

### Step 2: Ensure Required Files Exist

Before removing fallback:
1. Verify `config/final_training.yaml` exists in all expected locations
2. Create template if missing
3. Update documentation

**Success criteria**:
- ✅ All required config files exist
- ✅ Documentation updated

### Step 3: Remove Fallback Code

**File**: `src/infrastructure/config/training.py`

**Action**:
1. Remove fallback logic (lines 89-98)
2. Remove `_build_final_training_config_inline()` function (if no longer used)
3. Raise `FileNotFoundError` if `final_training.yaml` not found
4. Remove deprecation warning

**Success criteria**:
- ✅ Fallback code removed
- ✅ Clear error message if config file missing
- ✅ Tests pass: `uvx pytest tests/`

## Phase 6: Verification and Testing

**Priority**: High  
**Duration**: 2-3 hours  
**Risk**: Low

### Step 1: Run Full Test Suite

```bash
# Run all tests
uvx pytest tests/ -v

# Run with deprecation warnings as errors
uvx pytest tests/ -W error::DeprecationWarning

# Check for any remaining deprecation warnings
uvx pytest tests/ -W default::DeprecationWarning 2>&1 | grep -i "deprecation" | grep -v "test\|#.*deprecation"
```

**Success criteria**:
- ✅ All tests pass
- ✅ No deprecation warnings in test output (except expected ones in deprecated facade files, if they still exist)
- ✅ No broken imports

### Step 2: Verify Config Files

```bash
# Verify no objective.goal in config files
find config/ -name "*.yaml" -exec grep -H "objective\.goal" {} \; && echo "⚠️ Found objective.goal!" || echo "✅ No objective.goal found"

# Verify all config files are valid YAML
for file in $(find config/ -name "*.yaml"); do
  python -c "import yaml; yaml.safe_load(open('$file'))" || echo "⚠️ Invalid YAML: $file"
done
```

**Success criteria**:
- ✅ No `objective.goal` in config files
- ✅ All config files are valid YAML

### Step 3: Check for Remaining Deprecation Warnings

```bash
# Find all DeprecationWarning in source (should only be in deprecated facade files, if they still exist)
grep -rn "DeprecationWarning" src/ --include="*.py" | grep -v "test\|#.*DeprecationWarning"

# Count deprecation warnings
grep -rn "DeprecationWarning" src/ --include="*.py" | grep -v "test\|#.*DeprecationWarning" | wc -l
```

**Success criteria**:
- ✅ Only expected deprecation warnings remain (in deprecated facade files, if they still exist)
- ✅ All other deprecation warnings removed

### Step 4: Documentation Update

Update documentation to reflect changes:
1. Remove references to deprecated config keys
2. Remove references to deprecated functions
3. Update migration guides
4. Update API documentation

**Success criteria**:
- ✅ Documentation updated
- ✅ No references to deprecated items (except in migration notes)

## Success Criteria (Overall)

- ✅ All deprecated config keys migrated (`objective.goal` → `objective.direction`)
- ✅ All deprecated functions removed or replaced
- ✅ All deprecated facade modules removed or cleaned up
- ✅ All deprecated fallback behaviors removed
- ✅ Zero deprecation warnings in test output (except expected ones in deprecated facade files, if they still exist)
- ✅ All tests pass: `uvx pytest tests/`
- ✅ All config files valid and using new keys
- ✅ Documentation updated

## Risk Assessment

| Phase | Risk Level | Mitigation |
|-------|-----------|------------|
| Phase 2: Config Keys | Medium | Test all workflows after config changes |
| Phase 3: Functions | Medium | Update all callers before removing functions |
| Phase 4: Facades | High | Comprehensive import audit before removal |
| Phase 5: Fallbacks | Medium | Ensure required files exist before removing fallback |

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Audit | 2-3 hours | None |
| Phase 2: Config Keys | 1-2 hours | Phase 1 |
| Phase 3: Functions | 2-3 hours | Phase 1 |
| Phase 4: Facades | 2-3 hours | Phase 1, Phase 2, Phase 3 |
| Phase 5: Fallbacks | 1 hour | Phase 1 |
| Phase 6: Verification | 2-3 hours | All phases |
| **Total** | **10-15 hours** | |

## Notes

- **Facade modules**: May need to keep `__init__.py` files if directories contain active submodules. In that case, remove deprecation warnings and facade logic, but keep minimal package structure.
- **Legacy format support**: `find_checkpoint_in_trial_dir()` and `compute_grouping_tags()` are marked as "legacy format only". If legacy format support is still needed, these functions should remain but be clearly documented as legacy-only.
- **Breaking changes**: Removing facade modules and deprecated functions may break external code. Consider version bump if this is a library.


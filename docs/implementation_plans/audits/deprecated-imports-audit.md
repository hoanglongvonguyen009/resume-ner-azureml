# Deprecated Imports Audit

**Date**: 2025-01-27  
**Scope**: All modules in `src/`  
**Status**: Complete

## Executive Summary

Comprehensive audit of all modules in `src/` for deprecated imports. **Excellent news**: Almost all deprecated imports have already been migrated! Only documentation files contain deprecated import examples.

### Key Findings

- ✅ **No deprecated imports in source code** - All source files use correct import paths
- ✅ **No deprecated facade imports** - No imports from `orchestration`, `orchestration.jobs`, `orchestration.jobs.final_training`, `orchestration.metadata_manager`
- ✅ **No deprecated selection imports** - No imports from deprecated `selection` facade
- ✅ **No deprecated training.cv_utils imports** - All migrated to `training.core.cv_utils`
- ⚠️ **Documentation only** - 2 README files contain example code with deprecated imports

### Active Modules (NOT Deprecated)

All imports from `orchestration.jobs.tracking.*` are **ACTIVE** and should **NOT** be migrated:
- `orchestration.jobs.tracking.index.run_index`
- `orchestration.jobs.tracking.index.version_counter`
- `orchestration.jobs.tracking.config.loader`
- `orchestration.jobs.tracking.*` (all submodules)

## Module-by-Module Breakdown

### api/ Module

**Status**: ✅ Clean  
**Files Checked**: All files in `src/api/`

- No deprecated imports found
- No migration needed

### benchmarking/ Module

**Status**: ⚠️ Documentation Only  
**Files Checked**: All files in `src/benchmarking/`

**Issues Found**:
1. **File**: `src/benchmarking/README.md:132`
   - **Import**: `from orchestration.jobs.local_selection import select_best_configuration_across_studies`
   - **Replacement**: `from evaluation.selection import select_best_configuration_across_studies`
   - **Type**: Documentation example code
   - **Complexity**: Low (documentation update only)

**Migration**:
- Update README example to use `evaluation.selection`

### common/ Module

**Status**: ✅ Clean  
**Files Checked**: All files in `src/common/`

- No deprecated imports found
- No migration needed

### core/ Module

**Status**: ✅ Clean  
**Files Checked**: All files in `src/core/`

- No deprecated imports found
- No migration needed

### data/ Module

**Status**: ✅ Clean  
**Files Checked**: All files in `src/data/`

- No deprecated imports found
- No migration needed

### deployment/ Module

**Status**: ✅ Clean (Active Modules Only)  
**Files Checked**: All files in `src/deployment/`

**Imports Found** (All ACTIVE - No Migration Needed):
- `src/deployment/conversion/orchestration.py:62`: `from orchestration.jobs.tracking.index.run_index import update_mlflow_index`
  - **Status**: ✅ ACTIVE module - No migration needed
  - **Module**: `orchestration.jobs.tracking.index.run_index` is an active module

### evaluation/ Module

**Status**: ⚠️ Documentation Only  
**Files Checked**: All files in `src/evaluation/`

**Issues Found**:
1. **File**: `src/evaluation/benchmarking/README.md:132`
   - **Import**: `from orchestration.jobs.local_selection import select_best_configuration_across_studies`
   - **Replacement**: `from evaluation.selection import select_best_configuration_across_studies`
   - **Type**: Documentation example code
   - **Complexity**: Low (documentation update only)

**Migration**:
- Update README example to use `evaluation.selection`

### infrastructure/ Module

**Status**: ✅ Clean (Active Modules Only)  
**Files Checked**: All files in `src/infrastructure/`

**Imports Found** (All ACTIVE - No Migration Needed):
- `src/infrastructure/naming/mlflow/run_names.py:199`: `from orchestration.jobs.tracking.index.version_counter import reserve_run_name_version`
- `src/infrastructure/tracking/mlflow/trackers/conversion_tracker.py:47`: `from orchestration.jobs.tracking.index.run_index import update_mlflow_index`
- `src/infrastructure/tracking/mlflow/trackers/conversion_tracker.py:90`: `from orchestration.jobs.tracking.config.loader import get_tracking_config`
- `src/infrastructure/tracking/mlflow/trackers/conversion_tracker.py:222`: `from orchestration.jobs.tracking.config.loader get_tracking_config`
- `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py:60`: `from orchestration.jobs.tracking.index.run_index import update_mlflow_index`
- `src/infrastructure/tracking/mlflow/trackers/training_tracker.py:47`: `from orchestration.jobs.tracking.index.run_index import update_mlflow_index`
- `src/infrastructure/tracking/mlflow/trackers/training_tracker.py:102`: `from orchestration.jobs.tracking.config.loader import get_tracking_config`
- `src/infrastructure/tracking/mlflow/trackers/benchmark_tracker.py:47`: `from orchestration.jobs.tracking.index.run_index import update_mlflow_index`
- `src/infrastructure/tracking/mlflow/trackers/benchmark_tracker.py:122`: `from orchestration.jobs.tracking.config.loader import get_tracking_config`
- `src/infrastructure/tracking/mlflow/trackers/benchmark_tracker.py:252`: `from orchestration.jobs.tracking.index.version_counter import commit_run_name_version`
- `src/infrastructure/tracking/mlflow/trackers/benchmark_tracker.py:258`: `from orchestration.jobs.tracking.config.loader import ...`
- `src/infrastructure/tracking/mlflow/finder.py:40`: `from orchestration.jobs.tracking.index.run_index import find_in_mlflow_index`
- `src/infrastructure/tracking/mlflow/finder.py:41`: `from orchestration.jobs.tracking.config.loader import get_run_finder_config`
- `src/infrastructure/tracking/mlflow/artifacts/uploader.py:56`: `from orchestration.jobs.tracking.config.loader import get_tracking_config`

**Status**: ✅ All imports are from ACTIVE modules - No migration needed

### orchestration/ Module

**Status**: ✅ Clean (Expected Internal Usage)  
**Files Checked**: All files in `src/orchestration/` (excluding active submodules)

**Internal Usage** (Expected in Deprecated Facades):
- `src/orchestration/jobs/__init__.py:171`: `from evaluation.selection import selection as selection_func`
  - **Status**: ✅ Expected - This is a deprecated facade file that proxies to replacement modules
  - **Note**: This file will be removed in Phase 3, so no migration needed

### selection/ Module

**Status**: ✅ Clean  
**Files Checked**: All files in `src/selection/`

- No deprecated imports found
- No migration needed

### testing/ Module

**Status**: ✅ Clean  
**Files Checked**: All files in `src/testing/`

- No deprecated imports found
- No migration needed

### training/ Module

**Status**: ✅ Clean (Active Modules Only)  
**Files Checked**: All files in `src/training/`

**Imports Found** (All ACTIVE - No Migration Needed):
- `src/training/execution/mlflow_setup.py:169`: `from orchestration.jobs.tracking.index.run_index import update_mlflow_index`
- `src/training/execution/executor.py:77`: `from orchestration.jobs.tracking.index.run_index import update_mlflow_index`
- `src/training/hpo/execution/local/sweep.py:865`: `from orchestration.jobs.tracking.index.version_counter import cleanup_stale_reservations`
- `src/training/hpo/tracking/runs.py:133`: `from orchestration.jobs.tracking.config.loader import ...`
- `src/training/hpo/tracking/setup.py:271`: `from orchestration.jobs.tracking.config.loader import ...`
- `src/training/hpo/tracking/setup.py:275`: `from orchestration.jobs.tracking.index.version_counter import ...`

**Status**: ✅ All imports are from ACTIVE modules - No migration needed

## Import Type Categories

### Direct `orchestration` Imports

**Status**: ✅ None found

- No direct imports from `orchestration` facade
- All source code uses replacement modules

### `orchestration.jobs` Imports (Facade)

**Status**: ✅ None found

- No imports from deprecated `orchestration.jobs` facade
- All imports are from active submodules (`orchestration.jobs.tracking.*`)

### `orchestration.jobs.final_training` Imports

**Status**: ✅ None found

- No imports from deprecated `orchestration.jobs.final_training` facade

### `orchestration.metadata_manager` Imports

**Status**: ✅ None found

- No imports from deprecated `orchestration.metadata_manager` facade

### `selection` Imports

**Status**: ✅ None found (except in deprecated facade itself)

- No imports from deprecated `selection` facade
- Only usage is in `orchestration/jobs/__init__.py` which is a deprecated facade itself

### `training.cv_utils` Imports

**Status**: ✅ None found

- All imports already migrated to `training.core.cv_utils`

### `orchestration.jobs.local_selection` Imports

**Status**: ⚠️ Documentation Only

- **Found in**: 2 README files (documentation examples)
- **Replacement**: `evaluation.selection`
- **Files**:
  1. `src/benchmarking/README.md:132`
  2. `src/evaluation/benchmarking/README.md:132`

## Dependency Analysis

### Modules with No Dependencies on Deprecated Code

✅ **All modules are clean** - No source code depends on deprecated facades

### Modules Using Active Submodules

The following modules import from **ACTIVE** `orchestration.jobs.tracking.*` modules (NOT deprecated):

- `deployment/` - Uses `orchestration.jobs.tracking.index.run_index`
- `infrastructure/` - Uses multiple `orchestration.jobs.tracking.*` modules
- `training/` - Uses `orchestration.jobs.tracking.*` modules

**Action**: ✅ No migration needed - These are active modules

### Circular Dependency Risks

**Status**: ✅ No risks identified

- No circular dependencies introduced by migration
- All replacement modules are already in use

### Migration Order

**Status**: ✅ Not applicable - No source code migration needed

Since all source code is already migrated, the only work is:
1. Update documentation (README files)
2. Remove deprecated facade modules (Phase 3)

## Summary Statistics

| Category | Count | Status |
|----------|-------|--------|
| Modules audited | 13 | ✅ Complete |
| Source files with deprecated imports | 0 | ✅ Clean |
| Documentation files with deprecated examples | 2 | ⚠️ Needs update |
| Active module imports (correct) | 20+ | ✅ No action needed |
| Deprecated facade imports | 0 | ✅ Clean |

## Migration Complexity Assessment

### Low Complexity (Documentation Only)

**Items**: 2 README files
- `src/benchmarking/README.md`
- `src/evaluation/benchmarking/README.md`

**Action**: Simple find-and-replace in documentation
- Change: `from orchestration.jobs.local_selection import select_best_configuration_across_studies`
- To: `from evaluation.selection import select_best_configuration_across_studies`

**Estimated Time**: 5 minutes

### No Migration Needed

**Items**: All source code files

- All source code already uses correct import paths
- All `orchestration.jobs.tracking.*` imports are from active modules

## Recommendations

1. ✅ **Source Code**: No migration needed - all code is clean
2. ⚠️ **Documentation**: Update 2 README files with correct import examples
3. ✅ **Phase 3**: Proceed with removing deprecated facade modules (they're not used)
4. ✅ **Verification**: Run full test suite to confirm no regressions

## Next Steps

1. **Phase 2**: Update documentation files (2 README files)
2. **Phase 3**: Remove deprecated facade modules (safe to remove - no usage found)
3. **Phase 4**: Verification and testing

## Files Requiring Updates

### Documentation Files

1. **`src/benchmarking/README.md:132`**
   - **Current**: `from orchestration.jobs.local_selection import select_best_configuration_across_studies`
   - **Replace with**: `from evaluation.selection import select_best_configuration_across_studies`

2. **`src/evaluation/benchmarking/README.md:132`**
   - **Current**: `from orchestration.jobs.local_selection import select_best_configuration_across_studies`
   - **Replace with**: `from evaluation.selection import select_best_configuration_across_studies`

## Verification Commands

```bash
# Verify no deprecated imports in source
grep -rn "from orchestration import\|import orchestration" src/ 2>/dev/null | \
  grep -v "orchestration/jobs/tracking\|orchestration/jobs/hpo\|orchestration/__init__.py\|orchestration/jobs/__init__.py\|orchestration/metadata_manager.py\|orchestration/naming.py" && \
  echo "⚠️ Found!" || echo "✅ Clean"

# Verify no deprecated selection imports
grep -rn "from selection import\|import selection" src/ 2>/dev/null | \
  grep -v "selection/__init__.py" && echo "⚠️ Found!" || echo "✅ Clean"

# Verify no deprecated training.cv_utils imports
grep -rn "from training\.cv_utils\|import training\.cv_utils" src/ 2>/dev/null && \
  echo "⚠️ Found!" || echo "✅ Clean"
```

## Conclusion

**Excellent news**: The codebase is in excellent shape! Almost all deprecated imports have already been migrated. Only documentation files need updates, and those are simple find-and-replace operations.

The audit confirms that:
- ✅ All source code uses correct import paths
- ✅ No deprecated facade imports in source code
- ✅ All `orchestration.jobs.tracking.*` imports are from active modules (correct)
- ⚠️ Only 2 documentation files need updates

**Phase 2 can proceed very quickly** - it's essentially just updating documentation examples.


# Consolidate DRY Violations from README Analysis

## Goal

Remove overlapping responsibilities, duplicated logic, and near-duplicate patterns identified across README files in `src/`, following reuse-first principles. This plan addresses inconsistencies in repository root detection, MLflow setup, checkpoint path resolution, selection module deprecation, and function exports.

## Status

**Last Updated**: 2025-01-20

### Completed Steps

- ✅ Step 1: Remove deprecated repository root detection wrappers
- ✅ Step 2: Clarify and document MLflow setup layering
- ✅ Step 3: Consolidate checkpoint path resolution functions
- ✅ Step 4: Remove deprecated `src/selection/` module
- ✅ Step 5: Consolidate `extract_best_config_from_study` exports

### Pending Steps

- ✅ Step 6: Update all README files to reflect consolidated patterns

## Preconditions

- All tests pass: `uvx pytest tests/`
- Mypy passes: `uvx mypy src --show-error-codes`
- No active PRs depend on deprecated functions

## Analysis Summary

### Identified DRY Violations

1. **Repository Root Detection** (Partially Consolidated)
   - **Issue**: Multiple deprecated wrapper functions (`find_project_root`, `infer_root_dir`, `find_repository_root`) still exist alongside unified `detect_repo_root()`
   - **Location**: `infrastructure.paths.utils`, `common.shared.notebook_setup`
   - **Impact**: Confusion about which function to use, maintenance burden
   - **Status**: Unified function exists, but wrappers remain for backward compatibility

2. **MLflow Setup** (Layering Confusion)
   - **Issue**: Two layers exist (`common.shared.mlflow_setup.setup_mlflow_cross_platform` and `infrastructure.tracking.mlflow.setup.setup_mlflow`), but READMEs don't clearly explain the layering
   - **Location**: `common/shared/mlflow_setup.py`, `infrastructure/tracking/mlflow/setup.py`
   - **Impact**: Developers unsure which function to use, potential duplicate setup calls
   - **Status**: Layering is intentional (SSOT pattern), but documentation is unclear

3. **Checkpoint Path Resolution** (Overlapping Functions)
   - **Issue**: Multiple functions with overlapping responsibilities: `resolve_platform_checkpoint_path`, `resolve_checkpoint_path`, `setup_checkpoint_storage`
   - **Location**: `common.shared.platform_detection`, `infrastructure.platform.adapters.checkpoint_resolver`, `training.hpo.checkpoint.storage`
   - **Impact**: Confusion about which function to use, potential inconsistencies
   - **Status**: Functions serve different purposes but boundaries are unclear

4. **Deprecated Selection Module** (Not Removed)
   - **Issue**: `src/selection/` module is marked as deprecated but still exists
   - **Location**: `src/selection/`
   - **Impact**: Confusion, maintenance burden, potential accidental usage
   - **Status**: README says "deprecated (compatibility shim)", but module still present

5. **Function Export Duplication** (Redundant Exports)
   - **Issue**: `extract_best_config_from_study` is exported from multiple places (`training.hpo`, `evaluation.selection`)
   - **Location**: Multiple `__init__.py` files
   - **Impact**: Confusion about canonical import path
   - **Status**: Implementation is unified, but exports are redundant

## Steps

### Step 1: Remove Deprecated Repository Root Detection Wrappers

**Goal**: Remove deprecated wrapper functions and update all call sites to use `detect_repo_root()` directly.

**Actions**:

1. Search for all usages of deprecated functions:
   - `find_project_root()` in `infrastructure.paths.utils`
   - `infer_root_dir()` in `infrastructure.paths.utils`
   - `find_repository_root()` in `common.shared.notebook_setup`
2. Update all call sites to use `detect_repo_root()` from `infrastructure.paths.repo`
3. Remove deprecated wrapper functions from `infrastructure.paths.utils`
4. Update `find_repository_root()` in `common.shared.notebook_setup` to be a simple alias (or remove if no call sites)
5. Update `infrastructure.paths.__init__.py` to remove deprecated exports
6. Update README files to remove references to deprecated functions

**Success criteria**:

- All call sites use `detect_repo_root()` directly
- Deprecated wrapper functions removed
- `uvx mypy src --show-error-codes` passes
- `uvx pytest tests/` passes
- No references to deprecated functions in README files

**Files to modify**:

- `src/infrastructure/paths/utils.py` (remove deprecated functions)
- `src/infrastructure/paths/__init__.py` (remove deprecated exports)
- `src/common/shared/notebook_setup.py` (simplify or remove wrapper)
- All files that import deprecated functions
- `src/infrastructure/paths/README.md` (update documentation)
- `src/common/README.md` (update documentation)

### Step 2: Clarify and Document MLflow Setup Layering

**Goal**: Document the intentional layering between `common.shared.mlflow_setup` and `infrastructure.tracking.mlflow.setup`, and ensure consistent usage patterns.

**Actions**:

1. Review current layering:
   - `common.shared.mlflow_setup.setup_mlflow_cross_platform()` - Low-level platform-specific setup
   - `infrastructure.tracking.mlflow.setup.setup_mlflow()` - High-level SSOT wrapper
2. Verify that `infrastructure.tracking.mlflow.setup.setup_mlflow()` correctly wraps `common.shared.mlflow_setup.setup_mlflow_cross_platform()`
3. Update README files to clearly document:
   - `infrastructure.tracking.mlflow.setup.setup_mlflow()` is the SSOT for MLflow setup
   - `common.shared.mlflow_setup.setup_mlflow_cross_platform()` is an internal implementation detail
   - When to use each function (if `common.shared` should be used directly at all)
4. Search for direct calls to `setup_mlflow_cross_platform()` and update to use `setup_mlflow()` from infrastructure
5. Update all README files that mention MLflow setup to reference the SSOT

**Success criteria**:

- All README files clearly document MLflow setup layering
- All call sites use `infrastructure.tracking.mlflow.setup.setup_mlflow()` (SSOT)
- No direct calls to `common.shared.mlflow_setup.setup_mlflow_cross_platform()` from outside infrastructure layer
- `uvx mypy src --show-error-codes` passes
- `uvx pytest tests/` passes

**Files to modify**:

- `src/infrastructure/tracking/README.md` (clarify SSOT)
- `src/common/README.md` (document internal use only)
- `src/training/README.md` (update MLflow setup references)
- `src/training/execution/README.md` (update MLflow setup references)
- All files that directly call `setup_mlflow_cross_platform()`

### Step 3: Consolidate Checkpoint Path Resolution Functions

**Goal**: Clarify boundaries between checkpoint path resolution functions and consolidate overlapping logic.

**Actions**:

1. Analyze current functions:
   - `resolve_platform_checkpoint_path()` in `common.shared.platform_detection`
   - `resolve_checkpoint_path()` in `infrastructure.platform.adapters.checkpoint_resolver`
   - `setup_checkpoint_storage()` in `training.hpo.checkpoint.storage`
2. Document the intended purpose of each function:
   - Which function handles platform detection?
   - Which function handles path resolution?
   - Which function handles storage setup?
3. Identify overlapping logic and extract to shared utilities if needed
4. Update function documentation to clarify when to use each function
5. Search for all call sites and verify they use the correct function
6. Update README files to document the checkpoint path resolution strategy

**Success criteria**:

- Clear boundaries between functions documented
- No duplicate logic between functions
- All call sites use appropriate functions
- README files document checkpoint path resolution strategy
- `uvx mypy src --show-error-codes` passes
- `uvx pytest tests/` passes

**Files to modify**:

- `src/common/shared/platform_detection.py` (document `resolve_platform_checkpoint_path`)
- `src/infrastructure/platform/adapters/checkpoint_resolver.py` (document `resolve_checkpoint_path`)
- `src/training/hpo/checkpoint/storage.py` (document `setup_checkpoint_storage`)
- `src/common/README.md` (update checkpoint path documentation)
- `src/infrastructure/platform/README.md` (update checkpoint path documentation)
- `src/training/hpo/README.md` (update checkpoint path documentation)

### Step 4: Remove Deprecated `src/selection/` Module

**Goal**: Remove the deprecated `src/selection/` module completely, ensuring all imports are updated to use `evaluation.selection`.

**Actions**:

1. Search for any remaining imports from `src.selection` or `selection.`
2. Update all imports to use `evaluation.selection` instead
3. Verify that `src/selection/__init__.py` only contains compatibility shims (if any)
4. Remove the `src/selection/` directory entirely
5. Update any README files that reference `src/selection/`
6. Update `evaluation/selection/README.md` to remove the note about deprecated module (since it's gone)

**Success criteria**:

- No imports from `src.selection` or `selection.` remain
- `src/selection/` directory removed
- All functionality available through `evaluation.selection`
- `uvx mypy src --show-error-codes` passes
- `uvx pytest tests/` passes
- No references to `src/selection/` in README files

**Files to modify**:

- Remove `src/selection/` directory
- All files that import from `src.selection` or `selection.`
- `src/evaluation/selection/README.md` (remove deprecation note)

### Step 5: Consolidate `extract_best_config_from_study` Exports

**Goal**: Establish a single canonical export path for `extract_best_config_from_study` and remove redundant exports.

**Actions**:

1. Determine canonical location: `training.hpo.core.study.extract_best_config_from_study`
2. Review current exports:
   - `training.hpo.__init__.py` exports it
   - `evaluation.selection.__init__.py` exports it
   - `training.__init__.py` exports it
   - `evaluation.__init__.py` exports it
3. Decide on canonical import path (recommend: `from training.hpo.core.study import extract_best_config_from_study`)
4. Remove redundant exports from `evaluation.selection.__init__.py` and `evaluation.__init__.py`
5. Keep export in `training.hpo.__init__.py` for convenience (since it's the owner)
6. Update all imports to use canonical path or `training.hpo` import
7. Update README files to reference canonical import path

**Success criteria**:

- Single canonical export path established
- Redundant exports removed
- All imports updated to use canonical path
- README files reference canonical import path
- `uvx mypy src --show-error-codes` passes
- `uvx pytest tests/` passes

**Files to modify**:

- `src/evaluation/selection/__init__.py` (remove export)
- `src/evaluation/__init__.py` (remove export if present)
- All files that import `extract_best_config_from_study` from `evaluation.selection`
- `src/training/hpo/README.md` (document canonical import)
- `src/evaluation/selection/README.md` (update import examples)

### Step 6: Update All README Files to Reflect Consolidated Patterns

**Goal**: Ensure all README files accurately document the consolidated patterns and remove references to deprecated functions/modules.

**Actions**:

1. Review all README files in `src/` for:
   - References to deprecated functions
   - References to deprecated modules
   - Inconsistent import examples
   - Unclear documentation about function purposes
2. Update each README to:
   - Use canonical import paths
   - Remove references to deprecated functions/modules
   - Clarify function boundaries and purposes
   - Document layering where applicable
3. Ensure consistency across README files:
   - Same function names used consistently
   - Same import paths recommended
   - Same patterns documented

**Success criteria**:

- All README files updated
- No references to deprecated functions/modules
- Consistent import examples across README files
- Clear documentation of function purposes and boundaries
- All README files reviewed and validated

**Files to modify**:

- All README files in `src/` (22 files total)
- Focus on: `common/README.md`, `infrastructure/README.md`, `infrastructure/paths/README.md`, `infrastructure/tracking/README.md`, `training/README.md`, `evaluation/README.md`, `evaluation/selection/README.md`

## Success Criteria (Overall)

- ✅ All deprecated functions removed
- ✅ All deprecated modules removed
- ✅ MLflow setup layering clearly documented
- ✅ Checkpoint path resolution functions have clear boundaries
- ✅ Single canonical import paths established
- ✅ All README files updated and consistent
- ✅ All tests pass: `uvx pytest tests/`
- ✅ Mypy passes: `uvx mypy src --show-error-codes`
- ✅ No linter errors
- ✅ Code follows reuse-first principles

## Notes

- **Reuse-first principle**: When consolidating, prefer extending existing modules over creating new ones
- **Backward compatibility**: Some deprecated functions may need to remain temporarily if external code depends on them. Document deprecation clearly and provide migration path.
- **Testing**: Ensure comprehensive test coverage for consolidated functions
- **Documentation**: README updates are critical for maintaining clarity after consolidation

## Related Plans

- None currently

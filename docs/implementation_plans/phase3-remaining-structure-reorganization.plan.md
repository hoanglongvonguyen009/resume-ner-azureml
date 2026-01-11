<!-- Phase 3: Remaining Structure Reorganization -->
# Phase 3: Remaining Structure Reorganization - Implementation Plan

## Overview

This plan completes the feature-level folder reorganization by consolidating evaluation and deployment modules. This follows the completion of:
- **Phase 1**: Infrastructure reorganization (complete)
- **Phase 2**: Training module reorganization (complete)

**Remaining Work**:
- **Phase 3**: Evaluation Module (benchmarking/ and selection/ → evaluation/)
- **Phase 4**: Deployment Module (conversion/ and api/ → deployment/)
- **Phase 5**: Remove Orchestration (after 1-2 releases - future breaking change)

**Prerequisites**: 
- Phase 1 (Infrastructure Reorganization) - ✅ Complete
- Phase 2 (Training Module Reorganization) - ✅ Complete

**Migration Strategy**: Consolidate modules while maintaining backward compatibility through compatibility shims. Remove shims after 1-2 releases.

## Target Structure

```
src/
├── infrastructure/          # ✅ Complete - ML-specific infrastructure
├── common/                  # ✅ Complete - Generic shared utilities
├── data/                    # ✅ Complete - Data handling
├── testing/                 # ✅ Complete - Testing framework
├── training/                # ✅ Complete - Training pipeline
│   ├── core/               # Core training logic
│   ├── hpo/                # Hyperparameter optimization
│   ├── execution/           # Training execution
│   └── cli/                 # Command-line interfaces
│
├── evaluation/             # ⏳ Phase 3 - Model evaluation
│   ├── __init__.py
│   ├── benchmarking/       # Benchmarking (from src/benchmarking/)
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── workflow.py
│   │   ├── utils.py
│   │   └── ...
│   └── selection/          # Model selection (from src/selection/)
│       ├── __init__.py
│       ├── selection_logic.py
│       ├── artifact_acquisition.py
│       └── ...
│
├── deployment/             # ⏳ Phase 4 - Model deployment
│   ├── __init__.py
│   ├── conversion/         # Model conversion (from src/conversion/)
│   │   ├── __init__.py
│   │   ├── onnx_converter.py
│   │   ├── model_converter.py
│   │   └── ...
│   └── api/                # Inference API (from src/api/)
│       ├── __init__.py
│       ├── server.py
│       ├── inference.py
│       └── ...
│
└── orchestration/          # ⚠️ Deprecated - Remove in Phase 5 (after 1-2 releases)
    └── [compatibility shims - to be removed]
```

## Important Decisions

1. **Consolidate evaluation features** - `benchmarking/` and `selection/` into unified `evaluation/` module
2. **Consolidate deployment features** - `conversion/` and `api/` into unified `deployment/` module
3. **Maintain backward compatibility** - Create compatibility shims for old imports
4. **Remove orchestration after 1-2 releases** - Breaking change, plan accordingly
5. **Follow training module pattern** - Use same structure and migration approach

## Phase 3: Create Evaluation Module

### Pre-Implementation Analysis

- [ ] **Audit benchmarking/ module structure**
  - [ ] List all files in `src/benchmarking/` and their purposes
  - [ ] Document dependencies on `training/`, `infrastructure/`, `data/`
  - [ ] Identify any code that should move to `common/` or `infrastructure/`
  - [ ] Map files to target structure

- [ ] **Audit selection/ module structure**
  - [ ] List all files in `src/selection/` and their purposes
  - [ ] Document dependencies on `training/`, `infrastructure/`, `data/`
  - [ ] Identify any code that should move to `common/` or `infrastructure/`
  - [ ] Map files to target structure

- [ ] **Audit external dependencies**
  - [ ] Find all imports of `from benchmarking import ...`
  - [ ] Find all imports of `from selection import ...`
  - [ ] Document which modules depend on evaluation functionality
  - [ ] Identify notebooks, scripts, and tests that import evaluation modules

- [ ] **Create dependency graph**
  - [ ] Map all import relationships within evaluation modules
  - [ ] Map dependencies on `infrastructure/`, `common/`, `data/`, `training/`
  - [ ] Identify circular dependencies
  - [ ] Plan import order to avoid cycles

### Create Evaluation Module Structure

- [ ] **Create evaluation/ directory**
  - [ ] Create `src/evaluation/` directory
  - [ ] Create `src/evaluation/__init__.py`
  - [ ] Add module docstring explaining evaluation functionality

- [ ] **Create evaluation/benchmarking/ directory**
  - [ ] Create `src/evaluation/benchmarking/` directory
  - [ ] Create `src/evaluation/benchmarking/__init__.py`
  - [ ] Add module docstring explaining benchmarking functionality

- [ ] **Move benchmarking/ to evaluation/benchmarking/**
  - [ ] Move entire `src/benchmarking/` directory → `src/evaluation/benchmarking/`
  - [ ] Preserve internal structure
  - [ ] Update all internal imports within benchmarking/ to use relative imports
  - [ ] Update imports to use `infrastructure.*`, `common.*`, `data.*`, `training.*`
  - [ ] Update `evaluation/benchmarking/__init__.py` to export public APIs

- [ ] **Create evaluation/selection/ directory**
  - [ ] Create `src/evaluation/selection/` directory
  - [ ] Create `src/evaluation/selection/__init__.py`
  - [ ] Add module docstring explaining selection functionality

- [ ] **Move selection/ to evaluation/selection/**
  - [ ] Move entire `src/selection/` directory → `src/evaluation/selection/`
  - [ ] Preserve internal structure
  - [ ] Update all internal imports within selection/ to use relative imports
  - [ ] Update imports to use `infrastructure.*`, `common.*`, `data.*`, `training.*`
  - [ ] Update `evaluation/selection/__init__.py` to export public APIs

- [ ] **Update evaluation/ imports**
  - [ ] Update all internal imports within evaluation/ to use relative imports
  - [ ] Update imports to use `training.*`, `infrastructure.*`, `common.*`, and `data.*`
  - [ ] Fix any broken imports
  - [ ] Update `evaluation/__init__.py` to export public APIs from submodules

- [ ] **Create compatibility shims**
  - [ ] Create `src/benchmarking/__init__.py` - shim to `evaluation.benchmarking`
  - [ ] Create `src/selection/__init__.py` - shim to `evaluation.selection`
  - [ ] Add deprecation warnings to all shims:
    ```python
    """Compatibility shim for benchmarking module.
    
    Use 'from evaluation.benchmarking import ...' instead.
    This will be removed in 2 releases.
    """
    import warnings
    warnings.warn(
        "benchmarking is deprecated, use evaluation.benchmarking",
        DeprecationWarning,
        stacklevel=2
    )
    from evaluation.benchmarking import *
    ```

### Update External Imports

- [ ] **Update imports in feature modules**
  - [ ] Update `src/training/` imports to use `evaluation.*` instead of `benchmarking.*` or `selection.*`
  - [ ] Update `src/api/` imports if they reference evaluation modules
  - [ ] Update `src/conversion/` imports if they reference evaluation modules
  - [ ] Update `orchestration/jobs/` imports to use `evaluation.*`

- [ ] **Update imports in tests/**
  - [ ] Update test imports to use new module paths
  - [ ] Keep tests working with both old and new imports during transition
  - [ ] Update test fixtures if needed
  - [ ] Update test paths and imports in test files

- [ ] **Update imports in notebooks**
  - [ ] Update notebooks to use new `evaluation.*` imports
  - [ ] Test notebooks work with new structure
  - [ ] Update notebook documentation if needed

- [ ] **Update src/__init__.py**
  - [ ] Update exports to use new evaluation module structure
  - [ ] Maintain backward compatibility
  - [ ] Add deprecation warnings for old imports

## Phase 4: Create Deployment Module

### Pre-Implementation Analysis

- [ ] **Audit conversion/ module structure**
  - [ ] List all files in `src/conversion/` and their purposes
  - [ ] Document dependencies on `training/`, `infrastructure/`, `data/`
  - [ ] Identify any code that should move to `common/` or `infrastructure/`
  - [ ] Map files to target structure

- [ ] **Audit api/ module structure**
  - [ ] List all files in `src/api/` and their purposes
  - [ ] Document dependencies on `training/`, `evaluation/`, `infrastructure/`, `data/`
  - [ ] Identify any code that should move to `common/` or `infrastructure/`
  - [ ] Map files to target structure

- [ ] **Audit external dependencies**
  - [ ] Find all imports of `from conversion import ...`
  - [ ] Find all imports of `from api import ...`
  - [ ] Document which modules depend on deployment functionality
  - [ ] Identify notebooks, scripts, and tests that import deployment modules

- [ ] **Create dependency graph**
  - [ ] Map all import relationships within deployment modules
  - [ ] Map dependencies on `infrastructure/`, `common/`, `data/`, `training/`, `evaluation/`
  - [ ] Identify circular dependencies
  - [ ] Plan import order to avoid cycles

### Create Deployment Module Structure

- [ ] **Create deployment/ directory**
  - [ ] Create `src/deployment/` directory
  - [ ] Create `src/deployment/__init__.py`
  - [ ] Add module docstring explaining deployment functionality

- [ ] **Create deployment/conversion/ directory**
  - [ ] Create `src/deployment/conversion/` directory
  - [ ] Create `src/deployment/conversion/__init__.py`
  - [ ] Add module docstring explaining conversion functionality

- [ ] **Move conversion/ to deployment/conversion/**
  - [ ] Move entire `src/conversion/` directory → `src/deployment/conversion/`
  - [ ] Preserve internal structure
  - [ ] Update all internal imports within conversion/ to use relative imports
  - [ ] Update imports to use `infrastructure.*`, `common.*`, `data.*`, `training.*`, `evaluation.*`
  - [ ] Update `deployment/conversion/__init__.py` to export public APIs

- [ ] **Create deployment/api/ directory**
  - [ ] Create `src/deployment/api/` directory
  - [ ] Create `src/deployment/api/__init__.py`
  - [ ] Add module docstring explaining API functionality

- [ ] **Move api/ to deployment/api/**
  - [ ] Move entire `src/api/` directory → `src/deployment/api/`
  - [ ] Preserve internal structure
  - [ ] Update all internal imports within api/ to use relative imports
  - [ ] Update imports to use `infrastructure.*`, `common.*`, `data.*`, `training.*`, `evaluation.*`
  - [ ] Update `deployment/api/__init__.py` to export public APIs

- [ ] **Update deployment/ imports**
  - [ ] Update all internal imports within deployment/ to use relative imports
  - [ ] Update imports to use `training.*`, `evaluation.*`, `infrastructure.*`, `common.*`, and `data.*`
  - [ ] Fix any broken imports
  - [ ] Update `deployment/__init__.py` to export public APIs from submodules

- [ ] **Create compatibility shims**
  - [ ] Create `src/conversion/__init__.py` - shim to `deployment.conversion`
  - [ ] Create `src/api/__init__.py` - shim to `deployment.api`
  - [ ] Add deprecation warnings to all shims:
    ```python
    """Compatibility shim for conversion module.
    
    Use 'from deployment.conversion import ...' instead.
    This will be removed in 2 releases.
    """
    import warnings
    warnings.warn(
        "conversion is deprecated, use deployment.conversion",
        DeprecationWarning,
        stacklevel=2
    )
    from deployment.conversion import *
    ```

### Update External Imports

- [ ] **Update imports in feature modules**
  - [ ] Update `src/training/` imports to use `deployment.*` instead of `conversion.*` or `api.*`
  - [ ] Update `src/evaluation/` imports to use `deployment.*` if needed
  - [ ] Update `orchestration/jobs/` imports to use `deployment.*`

- [ ] **Update imports in tests/**
  - [ ] Update test imports to use new module paths
  - [ ] Keep tests working with both old and new imports during transition
  - [ ] Update test fixtures if needed
  - [ ] Update test paths and imports in test files

- [ ] **Update imports in notebooks**
  - [ ] Update notebooks to use new `deployment.*` imports
  - [ ] Test notebooks work with new structure
  - [ ] Update notebook documentation if needed

- [ ] **Update src/__init__.py**
  - [ ] Update exports to use new deployment module structure
  - [ ] Maintain backward compatibility
  - [ ] Add deprecation warnings for old imports

## Phase 5: Testing and Verification

### Run Existing Tests

- [ ] **Run all evaluation tests**
  - [ ] Run `tests/benchmarking/` tests
  - [ ] Run `tests/selection/` tests
  - [ ] Verify all tests pass
  - [ ] Fix any test failures

- [ ] **Run all deployment tests**
  - [ ] Run `tests/conversion/` tests
  - [ ] Run `tests/api/` tests
  - [ ] Verify all tests pass
  - [ ] Fix any test failures

- [ ] **Run all integration tests**
  - [ ] Run integration tests that use evaluation modules
  - [ ] Run integration tests that use deployment modules
  - [ ] Verify all tests pass
  - [ ] Fix any test failures

### Test Backward Compatibility

- [ ] **Test shim functionality**
  - [ ] Test that `from benchmarking import ...` works (via shim)
  - [ ] Test that `from selection import ...` works (via shim)
  - [ ] Test that `from conversion import ...` works (via shim)
  - [ ] Test that `from api import ...` works (via shim)
  - [ ] Verify deprecation warnings are shown
  - [ ] Test that notebooks work with shims

- [ ] **Verify no breaking changes**
  - [ ] Test that existing code using old imports still works
  - [ ] Test that external users can still use old import paths
  - [ ] Document any breaking changes (should be none)

### Verify No Circular Dependencies

- [ ] **Run dependency checker**
  - [ ] Run dependency analysis on `evaluation/` module
  - [ ] Run dependency analysis on `deployment/` module
  - [ ] Generate dependency graph
  - [ ] Identify any circular dependencies

- [ ] **Verify module dependencies**
  - [ ] Verify `evaluation/benchmarking/` depends only on:
    - [ ] `training/`
    - [ ] `infrastructure/`
    - [ ] `common/`
    - [ ] `data/`
    - [ ] Standard library
  - [ ] Verify `evaluation/selection/` depends only on:
    - [ ] `training/`
    - [ ] `evaluation/benchmarking/` (if needed)
    - [ ] `infrastructure/`
    - [ ] `common/`
    - [ ] `data/`
    - [ ] Standard library
  - [ ] Verify `deployment/conversion/` depends only on:
    - [ ] `training/`
    - [ ] `infrastructure/`
    - [ ] `common/`
    - [ ] `data/`
    - [ ] Standard library
  - [ ] Verify `deployment/api/` depends only on:
    - [ ] `training/`
    - [ ] `evaluation/`
    - [ ] `deployment/conversion/`
    - [ ] `infrastructure/`
    - [ ] `common/`
    - [ ] `data/`
    - [ ] Standard library
  - [ ] Verify no cycles between modules

### Test Import Performance

- [ ] **Measure import times**
  - [ ] Measure import time for `evaluation.benchmarking`
  - [ ] Measure import time for `evaluation.selection`
  - [ ] Measure import time for `deployment.conversion`
  - [ ] Measure import time for `deployment.api`
  - [ ] Compare with baseline (if available)
  - [ ] Verify no significant regressions (< 2x slowdown)

### Verify Module Isolation

- [ ] **Test submodule independence**
  - [ ] Test that `evaluation/benchmarking/` can be imported independently
  - [ ] Test that `evaluation/selection/` can be imported independently
  - [ ] Test that `deployment/conversion/` can be imported independently
  - [ ] Test that `deployment/api/` can be imported independently

- [ ] **Test separation of concerns**
  - [ ] Test that evaluation logic is isolated from deployment
  - [ ] Test that deployment logic is isolated from evaluation
  - [ ] Verify SRP (Single Responsibility Principle) is maintained

## Phase 6: Documentation and Cleanup

### Update Documentation

- [ ] **Update README.md**
  - [ ] Document new import patterns:
    - [ ] `from evaluation.benchmarking import ...`
    - [ ] `from evaluation.selection import ...`
    - [ ] `from deployment.conversion import ...`
    - [ ] `from deployment.api import ...`
  - [ ] Add examples of new import patterns
  - [ ] Document deprecation timeline for old imports
  - [ ] Add migration guide from old to new imports

- [ ] **Document deprecation timeline**
  - [ ] Document when old imports (`benchmarking.*`, `selection.*`, `conversion.*`, `api.*`) will be removed
  - [ ] Document timeline for removing shims (1-2 releases)
  - [ ] Add clear migration path for users
  - [ ] Update changelog with deprecation notices

- [ ] **Update architecture diagrams**
  - [ ] Create/update diagram showing new module structure
  - [ ] Show relationships between `evaluation/`, `deployment/`, `training/`
  - [ ] Document dependencies between modules
  - [ ] Update any existing architecture documentation

- [ ] **Document migration path**
  - [ ] Create migration guide for internal code
  - [ ] Document step-by-step process for updating imports
  - [ ] Provide examples of common migration patterns
  - [ ] Document any gotchas or common issues

- [ ] **Update API documentation**
  - [ ] Update docstrings to reflect new module locations
  - [ ] Update API reference documentation
  - [ ] Ensure all public APIs are documented
  - [ ] Add deprecation notices to old API docs

### Code Cleanup

- [ ] **Remove unused imports**
  - [ ] Run linter to find unused imports
  - [ ] Remove unused imports from all files
  - [ ] Verify no functionality is broken

- [ ] **Fix linter warnings**
  - [ ] Run linter (pylint, flake8, mypy, etc.)
  - [ ] Fix all linter warnings
  - [ ] Fix type hint issues
  - [ ] Fix code style issues

- [ ] **Ensure consistent code style**
  - [ ] Run code formatter (black, autopep8, etc.)
  - [ ] Ensure consistent formatting across all files
  - [ ] Verify code style matches project standards

- [ ] **Update type hints**
  - [ ] Add type hints where missing
  - [ ] Update type hints to reflect new module structure
  - [ ] Verify type checking passes (mypy)

### Final Verification

- [ ] **Run full test suite**
  - [ ] Run all tests: `pytest tests/`
  - [ ] Verify all tests pass
  - [ ] Fix any test failures
  - [ ] Verify no regressions

- [ ] **Check code coverage**
  - [ ] Run coverage analysis
  - [ ] Verify coverage hasn't decreased
  - [ ] Add tests for uncovered code if needed

- [ ] **Verify all compatibility shims work**
  - [ ] Test all shim modules
  - [ ] Verify deprecation warnings are shown
  - [ ] Test that shims forward to correct modules
  - [ ] Verify no functionality is lost

- [ ] **Verify all workflows function correctly**
  - [ ] Test end-to-end evaluation workflow
  - [ ] Test end-to-end deployment workflow
  - [ ] Verify all workflows produce expected results

## Phase 7: Remove Compatibility Shims (Future - After 1-2 Releases)

**⚠️ IMPORTANT: Do NOT start Phase 7 until after 1-2 releases. This is a breaking change.**

### Prerequisites

- [ ] **Wait for deprecation period**
  - [ ] Wait at least 1-2 releases after Phase 3-6 completion
  - [ ] Monitor usage of old imports
  - [ ] Collect feedback from users
  - [ ] Plan breaking change release

- [ ] **Announce breaking change**
  - [ ] Announce removal of shims in release notes
  - [ ] Provide clear migration guide
  - [ ] Give users sufficient time to migrate
  - [ ] Document breaking change in changelog

### Remove Top-Level Shims

- [ ] **Remove benchmarking/ shims**
  - [ ] Verify all imports have been migrated to `evaluation.benchmarking.*`
  - [ ] Search for any remaining `from benchmarking import` or `import benchmarking`
  - [ ] Update any remaining imports
  - [ ] Remove `src/benchmarking/` directory
  - [ ] Remove all shim files

- [ ] **Remove selection/ shims**
  - [ ] Verify all imports have been migrated to `evaluation.selection.*`
  - [ ] Search for any remaining `from selection import` or `import selection`
  - [ ] Update any remaining imports
  - [ ] Remove `src/selection/` directory
  - [ ] Remove all shim files

- [ ] **Remove conversion/ shims**
  - [ ] Verify all imports have been migrated to `deployment.conversion.*`
  - [ ] Search for any remaining `from conversion import` or `import conversion`
  - [ ] Update any remaining imports
  - [ ] Remove `src/conversion/` directory
  - [ ] Remove all shim files

- [ ] **Remove api/ shims**
  - [ ] Verify all imports have been migrated to `deployment.api.*`
  - [ ] Search for any remaining `from api import` or `import api`
  - [ ] Update any remaining imports
  - [ ] Remove `src/api/` directory
  - [ ] Remove all shim files

- [ ] **Remove orchestration/ directory**
  - [ ] Verify all imports have been migrated from `orchestration.*`
  - [ ] Search for any remaining `from orchestration import` or `import orchestration`
  - [ ] Update any remaining imports
  - [ ] Remove `src/orchestration/` directory
  - [ ] Remove all shim files

- [ ] **Update documentation**
  - [ ] Remove references to old import paths
  - [ ] Update all documentation to use new import paths
  - [ ] Update migration guide
  - [ ] Mark migration as complete

### Final Cleanup

- [ ] **Remove deprecation warnings**
  - [ ] Remove all deprecation warnings from shim files (they're gone)
  - [ ] Remove deprecation warnings from migrated code
  - [ ] Clean up any deprecation-related code

- [ ] **Update all notebooks**
  - [ ] Update all notebooks to use new imports
  - [ ] Remove any shim-related code
  - [ ] Test all notebooks work correctly

- [ ] **Final test run**
  - [ ] Run full test suite
  - [ ] Verify all tests pass
  - [ ] Verify no regressions
  - [ ] Test all workflows end-to-end

- [ ] **Update migration documentation**
  - [ ] Mark migration as complete
  - [ ] Update changelog with breaking changes
  - [ ] Document final module structure
  - [ ] Archive old migration guides

## Quick Reference: File Mapping

### Evaluation Module

- `src/benchmarking/` → `evaluation/benchmarking/` (entire directory, preserve structure)
- `src/selection/` → `evaluation/selection/` (entire directory, preserve structure)

### Deployment Module

- `src/conversion/` → `deployment/conversion/` (entire directory, preserve structure)
- `src/api/` → `deployment/api/` (entire directory, preserve structure)

### Removed Modules (Phase 7)

- `src/benchmarking/` → Remove (after deprecation period)
- `src/selection/` → Remove (after deprecation period)
- `src/conversion/` → Remove (after deprecation period)
- `src/api/` → Remove (after deprecation period)
- `src/orchestration/` → Remove (after deprecation period)
- `src/hpo/` → Remove (already moved to `training/hpo/`, shim remains)
- `src/training_exec/` → Remove (already moved to `training/execution/`, shim remains)

## Final Target Structure

```
src/
├── core/                    # Foundation (no changes)
├── infrastructure/          # ML-specific infrastructure ✅
├── common/                  # Generic shared utilities ✅
├── data/                    # Data handling ✅
├── testing/                 # Testing framework ✅
├── training/                # Training pipeline ✅
│   ├── core/
│   ├── hpo/
│   ├── execution/
│   └── cli/
├── evaluation/             # Model evaluation ⏳
│   ├── benchmarking/
│   └── selection/
├── deployment/             # Model deployment ⏳
│   ├── conversion/
│   └── api/
└── [no deprecated modules] # After Phase 7
```

## Priority Order

1. **Phase 3** (Create Evaluation Module) - High Priority
   - Consolidate evaluation features
   - Critical for feature-level organization
   - Enables better separation of concerns

2. **Phase 4** (Create Deployment Module) - High Priority
   - Consolidate deployment features
   - Critical for feature-level organization
   - Completes the feature structure

3. **Phase 5** (Testing and Verification) - High Priority
   - Verify everything works
   - Catch any issues before release
   - Critical for quality assurance

4. **Phase 6** (Documentation and Cleanup) - Medium Priority
   - Important for maintainability
   - Helps users migrate
   - Can be done incrementally

5. **Phase 7** (Remove Compatibility Shims) - Low Priority (Future)
   - Breaking change - wait 1-2 releases
   - Monitor usage first
   - Plan breaking change release

## Notes

- **Backward Compatibility**: All shims must remain functional until Phase 7
- **Testing**: Test thoroughly after each phase before proceeding
- **Documentation**: Keep documentation updated as work progresses
- **Breaking Changes**: Phase 7 is a breaking change - plan accordingly
- **Migration Path**: Always provide clear migration path for users
- **Follow Training Pattern**: Use same structure and approach as training module reorganization

## Estimated Effort

- **Phase 3**: 4-6 hours (Evaluation Module)
- **Phase 4**: 4-6 hours (Deployment Module)
- **Phase 5**: 3-4 hours (Testing and Verification)
- **Phase 6**: 3-5 hours (Documentation and Cleanup)
- **Phase 7**: 2-3 hours (when ready, after 1-2 releases)

**Total Remaining**: ~16-24 hours of work

## Dependencies

- **Requires**: Phase 1 (Infrastructure) and Phase 2 (Training) completion
- **Depends on**: `infrastructure/`, `common/`, `data/`, `training/` modules
- **Used by**: Notebooks, scripts, external users

## Migration Checklist

- [ ] Phase 3: Create Evaluation Module
- [ ] Phase 4: Create Deployment Module
- [ ] Phase 5: Testing and Verification
- [ ] Phase 6: Documentation and Cleanup
- [ ] Phase 7: Remove Compatibility Shims (Future - After 1-2 Releases)


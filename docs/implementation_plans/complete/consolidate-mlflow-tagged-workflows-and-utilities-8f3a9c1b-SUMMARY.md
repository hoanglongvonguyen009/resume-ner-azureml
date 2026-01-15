# Consolidate MLflow-Tagged Workflows and Utilities Summary

**Date**: 2026-01-15  
**Plan**: `FINISHED-consolidate-mlflow-tagged-workflows-and-utilities-8f3a9c1b.plan.md` (renamed from `consolidate-mlflow-tagged-workflows-and-utilities-8f3a9c1b.plan.md`)  
**Status**: ✅ Complete

## Overview

This document summarizes the consolidation of MLflow-tagged modules by establishing clear single sources of truth (SSOTs) for MLflow setup, selection logic, and artifact acquisition. The refactoring eliminated DRY violations across 33 MLflow-tagged modules while maintaining backward compatibility and preserving existing behavior for local and AzureML runs.

## Statistics

- **Modules inventoried**: 33 Python modules tagged with `mlflow`
- **Files modified**: 8 files across setup, selection, and artifact acquisition
- **SSOTs established**: 6 clear single sources of truth:
  - MLflow setup: `infrastructure.tracking.mlflow.setup.setup_mlflow()`
  - Selection queries: `infrastructure.tracking.mlflow.queries.query_runs_by_tags()`
  - Local selection: `evaluation.selection.mlflow_selection.find_best_model_from_mlflow()`
  - Artifact selection: `evaluation.selection.artifact_unified.selectors.select_artifact_run()`
  - Artifact acquisition: `evaluation.selection.artifact_unified.acquisition.acquire_artifact()`
  - URL building: `infrastructure.tracking.mlflow.urls.get_mlflow_run_url()`
- **DRY violations eliminated**: Duplicate setup logic, query patterns, and artifact selection logic

## Changes Made

### Step 1: Inventory and Classification

**Actions**:
- Searched and cataloged all 33 Python modules tagged with `mlflow` in metadata
- Classified modules into 5 groups: Setup/Context, Tracking/Trackers, Selection/Workflows, Artifact Acquisition, Naming/Tag Utilities
- Cross-referenced with prior FINISHED plans to avoid duplication

**Result**: Complete inventory table with 33 modules, clear grouping, and identification of consolidation targets

### Step 2: Consolidate MLflow Setup and Context Management

**Files Modified**:
- `src/infrastructure/tracking/mlflow/setup.py` - Added `setup_mlflow()` SSOT function
- `src/training/execution/mlflow_setup.py` - Updated to assume MLflow already configured
- `src/training/execution/subprocess_runner.py` - Updated to use SSOT
- `src/selection/selection.py` - Updated to use SSOT
- `src/evaluation/selection/selection.py` - Updated to use SSOT

**Key Changes**:
- Established `infrastructure.tracking.mlflow.setup.setup_mlflow()` as the single source of truth for MLflow configuration
- All orchestration scripts now call this SSOT instead of duplicating setup logic
- `training.execution.mlflow_setup` refocused on run lifecycle (not global setup)

**Result**: Single SSOT for MLflow setup, all orchestration scripts use it, backward compatibility maintained

### Step 3: Centralize MLflow-Based Selection Logic

**Files Modified**:
- `src/evaluation/selection/mlflow_selection.py` - Updated to use queries SSOT, added SSOT documentation
- `src/evaluation/selection/workflows/selection_workflow.py` - Updated diagnostic queries to use queries SSOT
- `src/selection/selection.py` - Added documentation clarifying AzureML wrapper role
- `src/evaluation/selection/selection.py` - Added documentation clarifying AzureML wrapper role

**Key Changes**:
- Made `evaluation.selection.mlflow_selection.find_best_model_from_mlflow()` the SSOT for local MLflow selection
- All MLflow queries now use `infrastructure.tracking.mlflow.queries.query_runs_by_tags()`
- AzureML selection modules documented as thin wrappers that delegate to core selection logic

**Result**: Single SSOT for selection logic, all queries use queries module, AzureML wrappers clearly documented

### Step 4: Align Artifact Acquisition and Run-Selection Flows

**Files Modified**:
- `src/evaluation/selection/trial_finder.py` - Refactored to use `select_artifact_run()` from selectors SSOT

**Files Verified** (already using unified system):
- `src/evaluation/selection/artifact_acquisition.py` - Thin wrapper around unified system
- `src/evaluation/selection/workflows/selection_workflow.py` - Uses unified system
- `src/evaluation/selection/workflows/benchmarking_workflow.py` - Uses unified system
- `src/evaluation/selection/artifact_unified/acquisition.py` - Uses selectors SSOT

**Key Changes**:
- Refactored `trial_finder.py` to use `artifact_unified.selectors.select_artifact_run()` instead of duplicate MLflow queries
- Verified all workflows use unified artifact acquisition system
- Confirmed clear SSOT responsibilities: selectors → acquisition → wrapper → workflows

**Result**: Single SSOT for trial→refit mapping, unified artifact acquisition system properly wired, no duplicate selection logic

### Step 5: Clean Up Residual DRY Issues and Verify Behavior

**Files Reviewed**:
- `src/training/hpo/execution/local/sweep.py` - Verified legitimate tracker usage
- `src/training/execution/tags.py` - Documented acceptable exception for fallback query
- `src/infrastructure/tracking/mlflow/trackers/*` - Verified legitimate tracker operations and SSOT usage
- `src/infrastructure/tracking/mlflow/urls.py` - Confirmed SSOT for URL building
- `src/infrastructure/tracking/mlflow/utils.py` - Confirmed SSOT for retry logic
- `src/infrastructure/tracking/mlflow/queries.py` - Confirmed SSOT for query patterns

**Files Modified**:
- `src/training/execution/tags.py` - Added documentation explaining why direct query is acceptable

**Key Findings**:
- All SSOT modules are properly used where appropriate
- No duplicate patterns found (URL building, retry logic, query patterns, setup logic)
- Acceptable exceptions documented (e.g., `tags.py` fallback query needs RUNNING status)

**Result**: No residual DRY violations, all SSOTs verified, acceptable exceptions documented

## Key Decisions and Trade-offs

1. **Backward Compatibility**: All changes maintain backward compatibility - existing function signatures preserved, wrappers kept where needed
2. **SSOT Layering**: Clear separation between setup (global config), selection (querying), and artifact acquisition (downloading)
3. **AzureML Wrappers**: Kept as thin wrappers that translate AzureML-specific inputs to normalized core selection API
4. **Acceptable Exceptions**: Documented cases where direct MLflow usage is appropriate (e.g., tracker operations, simple fallback queries)

## Verification

- ✅ All modified files compile successfully
- ✅ No breaking changes to public APIs
- ✅ Linter shows only pre-existing import warnings (not errors)
- ✅ All SSOT modules properly used where appropriate
- ✅ Acceptable exceptions documented
- ✅ No duplicate patterns found

## Impact

- **Maintainability**: Clear SSOTs make it easier to modify MLflow behavior in one place
- **Consistency**: All modules use the same setup, query, and acquisition patterns
- **Documentation**: Clear layering and responsibilities documented in module docstrings
- **DRY Compliance**: Eliminated duplicate setup, query, and artifact selection logic

## Follow-up

No follow-up plans required. All consolidation goals achieved. The established SSOTs provide a solid foundation for future MLflow-related work.


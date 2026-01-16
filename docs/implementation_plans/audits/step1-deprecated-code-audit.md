# Step 1: Deprecated Code Usage Audit

**Date**: 2025-01-27  
**Plan**: `remove-deprecated-code.plan.md`  
**Status**: ✅ Complete

## Summary

This audit identifies all files importing from or using deprecated modules, functions, and compatibility shims. The audit distinguishes between:
- **Internal usage**: Within deprecated packages themselves (expected, will be removed with package)
- **External usage**: Files outside deprecated packages that need migration

## 1. Deprecated Naming Package: `orchestration.jobs.tracking.naming.*`

### Internal Usage (Within Deprecated Package)
✅ **Expected - will be removed with package**

| File | Line | Import | Type |
|------|------|--------|------|
| `src/orchestration/jobs/tracking/naming/__init__.py` | 29 | `from orchestration.jobs.tracking.naming.tags import ...` | Internal |
| `src/orchestration/jobs/tracking/naming/__init__.py` | 44 | `from orchestration.jobs.tracking.naming.policy import ...` | Internal |

### External Usage (Needs Migration)
⚠️ **Must update before removing package**

| File | Line | Import | Replacement |
|------|------|--------|-------------|
| `src/orchestration/jobs/tracking/mlflow_naming.py` | 18 | `from orchestration.jobs.tracking.naming.tags import (build_mlflow_tags, sanitize_tag_value)` | `infrastructure.naming.mlflow.tags` |

### Test Files
✅ **No test files import from deprecated naming package**

## 2. Deprecated Compatibility Shim: `training_exec.tags`

### External Usage (Needs Migration)
⚠️ **Must update before removing shim**

| File | Line | Import | Replacement |
|------|------|--------|-------------|
| `src/orchestration/jobs/__init__.py` | 96 | `from training_exec.tags import apply_lineage_tags` | `training.execution.tags` |

**Note**: This is a lazy import (inside try/except block), so it's safe to update.

### Test Files
✅ **No test files import from `training_exec.tags`**

## 3. Deprecated Function: `infer_config_dir_from_path`

### Function Definition
✅ **Will be removed**

| File | Line | Type |
|------|------|------|
| `src/infrastructure/tracking/mlflow/utils.py` | 117 | Function definition (deprecated) |

### External Usage (Needs Migration)
⚠️ **Must update test file before removing function**

| File | Line | Usage | Replacement |
|------|------|-------|-------------|
| `tests/tracking/unit/test_mlflow_utils_config_inference.py` | 13 | `from infrastructure.tracking.mlflow.utils import infer_config_dir_from_path` | `infrastructure.paths.utils.infer_config_dir` |
| `tests/tracking/unit/test_mlflow_utils_config_inference.py` | 33, 48, 65, 76, 93, 118 | Function calls (6 test methods) | Update to use `infer_config_dir` |

**Note**: The test file has 8 total matches (1 import + 6 function calls + 1 in docstring). All test methods in this file test the deprecated function and will need to be updated to test the replacement function.

### Source Files
✅ **No source files use this function** (only the definition exists)

## 4. Deprecated Facade: `orchestration.paths`

### Imports
✅ **No imports found in src/ or tests/**

The facade module exists but is not imported anywhere in the codebase.

### Exported Function: `resolve_output_path_v2`

| File | Line | Type | Status |
|------|------|------|--------|
| `src/orchestration/paths.py` | 47 | Function definition (deprecated wrapper) | Not used |
| `src/orchestration/__init__.py` | 64 | Import from `.paths` | Exported but not used |
| `src/orchestration/__init__.py` | 174 | In `__all__` export list | Exported but not used |

**Usage Search Results**: ✅ **No usage found in src/ or tests/**

The function is exported from `orchestration/__init__.py` but not actually used anywhere.

## Migration Summary

### Files Requiring Updates

1. **Source Files (2 files)**:
   - `src/orchestration/jobs/tracking/mlflow_naming.py` - Update naming imports
   - `src/orchestration/jobs/__init__.py` - Update training_exec.tags import

2. **Test Files (1 file)**:
   - `tests/tracking/unit/test_mlflow_utils_config_inference.py` - Update to test replacement function

3. **Files to Remove (5 files + 1 directory)**:
   - `src/orchestration/jobs/tracking/naming/__init__.py`
   - `src/orchestration/jobs/tracking/naming/policy.py`
   - `src/orchestration/jobs/tracking/naming/run_names.py`
   - `src/orchestration/jobs/tracking/naming/tags.py`
   - `src/training_exec/tags.py`
   - `src/infrastructure/tracking/mlflow/utils.py` (remove function only, or entire file if empty)
   - `src/orchestration/paths.py` (if confirmed unused)

### Replacement Mappings

| Deprecated | Replacement |
|------------|-------------|
| `orchestration.jobs.tracking.naming.tags` | `infrastructure.naming.mlflow.tags` |
| `orchestration.jobs.tracking.naming.policy` | `infrastructure.naming.display_policy` |
| `orchestration.jobs.tracking.naming.run_names` | `infrastructure.naming.mlflow.run_names` |
| `training_exec.tags` | `training.execution.tags` |
| `infer_config_dir_from_path()` | `infrastructure.paths.utils.infer_config_dir()` |

## Verification Commands

```bash
# Verify no external imports from deprecated naming package
grep -r "from orchestration.jobs.tracking.naming\|import.*orchestration.jobs.tracking.naming" src/ tests/ | grep -v "orchestration/jobs/tracking/naming/"

# Verify no imports from training_exec.tags
grep -r "from training_exec.tags\|import.*training_exec.tags" src/ tests/

# Verify no usage of infer_config_dir_from_path (except definition and tests)
grep -r "infer_config_dir_from_path" src/ tests/ | grep -v "def infer_config_dir_from_path\|test_mlflow_utils_config_inference"

# Verify no imports from orchestration.paths
grep -r "from orchestration.paths\|import.*orchestration.paths" src/ tests/
```

## Next Steps

1. ✅ **Step 1 Complete**: Audit finished
2. ⏳ **Step 2**: Update imports from deprecated naming modules
3. ⏳ **Step 3**: Update imports from deprecated training_exec.tags
4. ⏳ **Step 4**: Remove deprecated naming package
5. ⏳ **Step 5**: Remove deprecated training_exec.tags shim
6. ⏳ **Step 6**: Remove deprecated function infer_config_dir_from_path
7. ⏳ **Step 7**: Verify orchestration/paths.py usage and remove if unused
8. ⏳ **Step 8**: Final verification and cleanup


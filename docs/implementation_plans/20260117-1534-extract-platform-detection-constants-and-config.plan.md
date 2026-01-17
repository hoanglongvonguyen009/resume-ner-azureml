# Extract Platform Detection Constants and Load Project Name from Config

## Goal

Eliminate hardcoded magic strings in `platform_detection.py` by:
1. Extracting platform-specific path constants (Colab Drive, Kaggle working dir, etc.)
2. Loading project name from `config/paths.yaml` instead of hardcoding `"resume-ner-azureml"`
3. Maintaining backward compatibility with optional `config_dir` parameter

This follows the workspace rule to avoid magic numbers/strings and use config as single source of truth.

## Status

**Last Updated**: 2026-01-17

**Status**: ⏳ **IN PROGRESS**

### Completed Steps
- ✅ Step 1: Extract platform path constants
- ✅ Step 2: Add helper function to load project name from config
- ✅ Step 3: Refactor `resolve_platform_checkpoint_path()` to use constants and config
- ✅ Step 4: Refactor `is_drive_path()` to use constants
- ✅ Step 5: Update tests and verify backward compatibility

### Pending Steps
- ⏳ Step 6: Run mypy and ensure type safety

## Preconditions

- All existing tests pass: `uvx pytest tests/`
- Mypy passes: `uvx mypy src --show-error-codes`
- `config/paths.yaml` contains `project.name: "resume-ner-azureml"` (already exists)

## Analysis Summary

### Current Hardcoded Values

**Platform-specific paths** (acceptable to hardcode - fixed by platforms):
- `/content/drive/MyDrive` - Google Drive mount (Colab)
- `/content/` - Colab content directory
- `/kaggle/working` - Kaggle working directory
- `/content/drive` - Drive path prefix for detection

**Project-specific values** (should come from config):
- `"resume-ner-azureml"` - Project name (hardcoded 6+ times)
- `"resume-ner-checkpoints"` - Legacy checkpoint directory (fallback)

### Existing Patterns Found

**Reuse-first analysis**:
- ✅ `infrastructure/storage/drive.py` already loads project name from config:
  ```python
  paths_config = load_paths_config(config_dir)
  project_name = paths_config.get("project", {}).get("name", root_dir.name if root_dir else "resume-ner-azureml")
  ```
- ✅ `infrastructure/paths/config.py` provides `load_paths_config()` with caching
- ✅ `infrastructure/paths/repo.py` provides `detect_repo_root()` for config_dir inference
- ❌ No shared utility function for getting project name (each module loads directly)

**Decision**: Follow existing pattern from `drive.py` - load directly using `load_paths_config()`, but extract to a helper function within `platform_detection.py` to avoid duplication within the module. This follows reuse-first by using existing `load_paths_config()` rather than creating new infrastructure.

## Steps

### Step 1: Extract Platform Path Constants

**Location**: `src/common/shared/platform_detection.py`

**Actions**:
1. Add module-level constants at top of file (after imports, before functions):
   ```python
   # Platform-specific path constants (fixed by platforms)
   COLAB_DRIVE_MOUNT = Path("/content/drive/MyDrive")
   COLAB_CONTENT_DIR = Path("/content")
   KAGGLE_WORKING_DIR = Path("/kaggle/working")
   DRIVE_PATH_PREFIX = "/content/drive"
   
   # Legacy checkpoint directory (for backward compatibility fallback)
   LEGACY_CHECKPOINT_DIR = "resume-ner-checkpoints"
   ```

2. Add docstring explaining these are platform-fixed paths

**Success criteria**:
- Constants defined at module level
- Constants use `Path` objects where appropriate
- Constants are typed (mypy-compliant)
- `uvx mypy src/common/shared/platform_detection.py` passes

### Step 2: Add Helper Function to Load Project Name from Config

**Location**: `src/common/shared/platform_detection.py`

**Actions**:
1. Add private helper function `_get_project_name_from_config()`:
   ```python
   def _get_project_name_from_config(
       config_dir: Optional[Path],
       base_path: Optional[Path] = None,
   ) -> str:
       """
       Get project name from config/paths.yaml, with fallback to detection.
       
       Follows pattern from infrastructure/storage/drive.py.
       
       Args:
           config_dir: Optional config directory. If None, attempts to infer.
           base_path: Optional base path used for inference if config_dir not provided.
       
       Returns:
           Project name string (default: "resume-ner-azureml").
       """
       # Try to load from config
       try:
           from infrastructure.paths.config import load_paths_config
           from infrastructure.paths.repo import detect_repo_root
           
           # Infer config_dir if not provided
           if config_dir is None and base_path is not None:
               try:
                   repo_root = detect_repo_root(start_path=base_path)
                   if repo_root:
                       config_dir = repo_root / "config"
               except (ValueError, Exception):
                   pass  # Fallback to default
           
           if config_dir and (config_dir / "paths.yaml").exists():
               paths_config = load_paths_config(config_dir)
               project_name = paths_config.get("project", {}).get("name")
               if project_name:
                   return project_name
       except Exception:
           # Fallback to default if config loading fails
           pass
       
       # Fallback: try to detect from base_path string
       if base_path:
           base_str = str(base_path)
           if "/resume-ner-azureml" in base_str:
               return "resume-ner-azureml"
       
       # Last resort: default constant
       return "resume-ner-azureml"
   ```

2. Add module-level default constant for fallback:
   ```python
   # Default project name (fallback if config not available)
   DEFAULT_PROJECT_NAME = "resume-ner-azureml"
   ```

3. Update helper to use `DEFAULT_PROJECT_NAME` constant

**Success criteria**:
- Helper function follows existing pattern from `drive.py`
- Function handles all error cases gracefully
- Function uses `DEFAULT_PROJECT_NAME` constant for fallback
- `uvx mypy src/common/shared/platform_detection.py` passes
- Function is private (starts with `_`)

### Step 3: Refactor `resolve_platform_checkpoint_path()` to Use Constants and Config

**Location**: `src/common/shared/platform_detection.py`

**Actions**:
1. Update function signature to add optional `config_dir` parameter:
   ```python
   def resolve_platform_checkpoint_path(
       base_path: Path, 
       relative_path: str,
       config_dir: Optional[Path] = None,
   ) -> Path:
   ```

2. Replace all hardcoded strings with constants:
   - `/content/drive/MyDrive` → `COLAB_DRIVE_MOUNT`
   - `/content/` → `COLAB_CONTENT_DIR`
   - `/kaggle/working` → `KAGGLE_WORKING_DIR`
   - `"resume-ner-azureml"` → `_get_project_name_from_config(config_dir, base_path)`
   - `"resume-ner-checkpoints"` → `LEGACY_CHECKPOINT_DIR`

3. Update docstring to document `config_dir` parameter

4. Replace string concatenation with `Path` operations where possible

**Success criteria**:
- All hardcoded strings replaced with constants or config-loaded values
- Function signature includes optional `config_dir` parameter
- Function maintains backward compatibility (works without `config_dir`)
- All string operations use constants
- `uvx mypy src/common/shared/platform_detection.py` passes
- Existing tests still pass: `uvx pytest tests/ -k platform_detection`

### Step 4: Refactor `is_drive_path()` to Use Constants

**Location**: `src/common/shared/platform_detection.py`

**Actions**:
1. Replace hardcoded `/content/drive` with `DRIVE_PATH_PREFIX` constant
2. Update docstring examples to use constant (if needed)

**Success criteria**:
- Hardcoded string replaced with `DRIVE_PATH_PREFIX` constant
- Function behavior unchanged
- `uvx mypy src/common/shared/platform_detection.py` passes
- Existing tests still pass

### Step 5: Update Tests and Verify Backward Compatibility

**Location**: `tests/` (if tests exist for platform_detection)

**Actions**:
1. Search for existing tests: `find tests/ -name "*platform*" -o -name "*detection*"`
2. If tests exist, verify they still pass
3. If no tests exist, document that tests should be added (future work)
4. Test backward compatibility:
   - Call `resolve_platform_checkpoint_path()` without `config_dir` (should work)
   - Call with `config_dir=None` (should infer from base_path)
   - Call with explicit `config_dir` (should use provided config)

**Success criteria**:
- All existing tests pass
- Backward compatibility verified (function works without `config_dir`)
- `uvx pytest tests/` passes

### Step 6: Run Mypy and Ensure Type Safety

**Actions**:
1. Run mypy on modified file: `uvx mypy src/common/shared/platform_detection.py --show-error-codes`
2. Fix any type errors
3. Verify no `Any` types introduced
4. Ensure all imports are properly typed

**Success criteria**:
- `uvx mypy src/common/shared/platform_detection.py --show-error-codes` passes with 0 errors
- No `Any` types in new code
- All type hints are precise

## Success Criteria (Overall)

- ✅ All hardcoded magic strings eliminated from `platform_detection.py`
- ✅ Project name loaded from `config/paths.yaml` (single source of truth)
- ✅ Platform path constants extracted and documented
- ✅ Backward compatibility maintained (optional `config_dir` parameter)
- ✅ All existing tests pass
- ✅ Mypy passes with 0 errors
- ✅ Code follows existing patterns from `infrastructure/storage/drive.py` (reuse-first)
- ✅ No new dependencies or infrastructure created (uses existing `load_paths_config()`)

## Notes

### Reuse-First Decisions

**Existing options considered**:
- `infrastructure/storage/drive.py` - Already loads project name from config using `load_paths_config()`
- `infrastructure/paths/config.py` - Provides `load_paths_config()` with caching
- `infrastructure/paths/repo.py` - Provides `detect_repo_root()` for config_dir inference

**Reason new code was necessary**:
- Helper function `_get_project_name_from_config()` is needed within `platform_detection.py` to avoid code duplication
- Follows existing pattern from `drive.py` rather than creating new infrastructure
- Keeps logic local to module that uses it (SRP)

### Breaking Changes

**None** - All changes are backward compatible:
- `config_dir` parameter is optional
- Function works without config_dir (falls back to hardcoded default)
- Existing call sites continue to work unchanged

### Future Improvements

- Consider adding tests for `platform_detection.py` (currently no tests found)
- Consider extracting project name loading to shared utility if used by 3+ modules (currently only 2: `drive.py` and `platform_detection.py`)


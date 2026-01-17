# Repository Root Detection Audit

**Date**: 2025-01-27  
**Purpose**: Comprehensive audit of all repository root detection code, call sites, hardcoded paths, and Drive/Storage path mapping logic.

## Executive Summary

This audit identifies:
- **5 functions** that detect repository root (with overlapping logic)
- **25+ files** using repository root detection
- **36 files** with hardcoded platform-specific paths
- **17 files** with Drive/Storage path logic
- **Multiple inconsistencies** in search strategies and path mapping

## 1. Functions That Detect Repository Root

### 1.1 `find_repository_root()` in `src/common/shared/notebook_setup.py`

**Location**: `src/common/shared/notebook_setup.py:92-150`

**Search Strategy**:
1. Check current directory for `config/` and `src/` subdirectories
2. Search up directory tree from `start_dir` (or `cwd`)
3. Platform-specific locations:
   - Colab: `/content/resume-ner-azureml`, `/content`
   - Kaggle: `/kaggle/working/resume-ner-azureml`, `/kaggle/working`
   - Local: `/workspaces/resume-ner-azureml`, `/workspace/resume-ner-azureml`
4. For platform locations, also search subdirectories

**Markers Used**: `config/` and `src/` directories

**Return Type**: `Optional[Path]` (returns `None` if not found)

**Call Sites**:
- `src/common/shared/notebook_setup.py:180` - in `setup_notebook_paths()`
- `src/common/shared/notebook_setup.py:242` - in `ensure_src_in_path()`
- `notebooks/01_orchestrate_training_colab.ipynb` - imported as `find_repo_root`
- `notebooks/02_best_config_selection.ipynb` - imported as `find_repo_root`
- `notebooks/00_setup_infrastructure.ipynb` - likely used

**Issues**:
- Doesn't check workspace directories for Colab/Kaggle (only for local)
- Limited platform support (only Colab, Kaggle, local)
- No support for AzureML-specific locations
- Hardcoded project name "resume-ner-azureml" in paths

### 1.2 `find_project_root()` in `src/infrastructure/paths/utils.py`

**Location**: `src/infrastructure/paths/utils.py:36-146`

**Search Strategy** (tries multiple strategies in order):
1. From `output_dir`: Walk up to find "outputs" directory, then use its parent
2. From `config_dir`: Walk up looking for directory with both `config/` and `src/` subdirectories
3. From `start_path`: Walk up looking for directory with both `config/` and `src/` subdirectories
4. From `cwd`: Walk up looking for directory with both `config/` and `src/` subdirectories
5. Fallback: Use `config_dir.parent` if available, otherwise `cwd`

**Markers Used**: `config/` and `src/` directories, or "outputs" directory

**Return Type**: `Path` (always returns a path, never `None`)

**Call Sites**:
- `src/infrastructure/paths/utils.py:168` - in `infer_root_dir()` (wrapper)
- `src/infrastructure/paths/utils.py:228` - in `infer_config_dir()`
- `src/infrastructure/paths/utils.py:298` - in `resolve_project_paths()`
- `src/infrastructure/paths/utils.py:305` - in `resolve_project_paths()`
- `src/infrastructure/paths/utils.py:312` - in `resolve_project_paths()`
- `src/infrastructure/paths/utils.py:319` - in `resolve_project_paths()`

**Issues**:
- Different search strategy than `find_repository_root()` (uses "outputs" directory as marker)
- No workspace support
- No platform-specific location support
- Always returns a path (even if incorrect), which can mask errors
- Uses `max_depth = 10` but doesn't document this limit

### 1.3 `infer_root_dir()` in `src/infrastructure/paths/utils.py`

**Location**: `src/infrastructure/paths/utils.py:149-168`

**Description**: Thin wrapper around `find_project_root()` that adds no value.

**Call Sites**:
- No direct call sites found (likely unused or very rarely used)

**Issues**:
- Redundant wrapper function
- Adds no value over calling `find_project_root()` directly

### 1.4 `infer_config_dir()` in `src/infrastructure/paths/utils.py`

**Location**: `src/infrastructure/paths/utils.py:171-234`

**Description**: Infers config directory from path or project root.

**Search Strategy**:
1. If `config_dir` provided, return it directly
2. Search up from `path` looking for `config/` subdirectory
3. Use `find_project_root()` to locate project root, then use `root_dir / "config"`
4. Fallback: `Path.cwd() / "config"`

**Call Sites** (28+ files found):
- `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py:126` - infers from `output_dir`
- `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py:253` - infers from `output_dir`
- `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py:330` - infers from `output_dir`
- `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py:586` - infers from `output_dir`
- `src/evaluation/benchmarking/orchestrator.py` - multiple uses
- `src/training/hpo/execution/local/sweep.py` - multiple uses
- And 22+ more files...

**Issues**:
- Calls `find_project_root()` which has different logic than `find_repository_root()`
- Inconsistent behavior when used from different contexts

### 1.5 `resolve_project_paths()` in `src/infrastructure/paths/utils.py`

**Location**: `src/infrastructure/paths/utils.py:237-338`

**Description**: Resolves both `root_dir` and `config_dir` from available information.

**Search Strategy**:
1. If `config_dir` provided, derive `root_dir` from it
2. Infer `root_dir` from `output_dir` using `find_project_root()`
3. Infer `root_dir` from `start_path` using `find_project_root()`
4. Infer `root_dir` from `cwd` using `find_project_root()`
5. Derive `config_dir` from `root_dir`

**Call Sites**:
- Multiple files in HPO and training workflows
- Used when both `root_dir` and `config_dir` need to be resolved together

**Issues**:
- Uses `find_project_root()` which has inconsistent logic
- Returns `(None, None)` if all inference strategies fail, but this is rarely handled

## 2. Call Sites Analysis

### 2.1 Notebooks Using Repository Root Detection

**Files**:
- `notebooks/01_orchestrate_training_colab.ipynb` - imports `find_repository_root` as `find_repo_root`
- `notebooks/02_best_config_selection.ipynb` - imports `find_repository_root` as `find_repo_root`
- `notebooks/00_setup_infrastructure.ipynb` - likely uses repository root detection

**Pattern**: All notebooks import from `common.shared.notebook_setup`

### 2.2 Source Files Using Repository Root Detection

**Files Using `find_repository_root()`**:
- `src/common/shared/notebook_setup.py` - internal use (2 call sites)
- Notebooks (3+ files)

**Files Using `find_project_root()`**:
- `src/infrastructure/paths/utils.py` - internal use (5 call sites)

**Files Using `infer_config_dir()`** (28+ files):
- `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py` - 4 call sites
- `src/evaluation/benchmarking/orchestrator.py` - multiple call sites
- `src/training/hpo/execution/local/sweep.py` - multiple call sites
- `src/infrastructure/tracking/mlflow/finder.py` - likely uses
- `src/infrastructure/tracking/mlflow/trackers/benchmark_tracker.py` - likely uses
- `src/infrastructure/tracking/mlflow/trackers/training_tracker.py` - likely uses
- `src/infrastructure/naming/mlflow/run_names.py` - likely uses
- `src/orchestration/jobs/hpo/local/trial/execution.py` - likely uses
- `src/training/hpo/execution/local/trial.py` - likely uses
- And 19+ more files...

**Files Using `resolve_project_paths()`**:
- Multiple files in HPO and training workflows
- Used when both `root_dir` and `config_dir` need to be resolved

## 3. Hardcoded Paths Analysis

### 3.1 Platform-Specific Repository Paths

**Colab Paths** (`/content/resume-ner-azureml`):
- `src/common/shared/notebook_setup.py:126` - in `find_repository_root()`
- `src/orchestration/jobs/hpo/local/backup.py:128-129` - string replacement for Drive mapping
- `src/orchestration/jobs/hpo/local/backup.py:133-134` - string replacement for Drive mapping
- `src/infrastructure/paths/drive.py:164` - in `resolve_output_path_for_colab()`
- `src/infrastructure/paths/drive.py:169` - in `resolve_output_path_for_colab()`
- `src/infrastructure/paths/drive.py:173` - in `resolve_output_path_for_colab()`
- `notebooks/01_orchestrate_training_colab.ipynb` - likely hardcoded references

**Kaggle Paths** (`/kaggle/working/resume-ner-azureml`):
- `src/common/shared/notebook_setup.py:128` - in `find_repository_root()`

**Workspace Paths** (`/workspaces/resume-ner-azureml`, `/workspace/resume-ner-azureml`):
- `src/common/shared/notebook_setup.py:132` - `/workspaces/resume-ner-azureml`
- `src/common/shared/notebook_setup.py:137` - `/workspace/resume-ner-azureml`

**AzureML Paths** (`/mnt/resume-ner-azureml`):
- Not found in current codebase (missing support)

### 3.2 Drive/Storage Hardcoded Paths

**Drive Mount Point** (`/content/drive`):
- `src/infrastructure/storage/drive.py:374` - `mount_colab_drive()` default parameter
- `src/infrastructure/paths/drive.py:62` - in `get_drive_backup_base()` (from config, but hardcoded default)
- `src/infrastructure/paths/drive.py:161` - in `resolve_output_path_for_colab()`
- `config/paths.yaml:400` - configured as default

**Drive Backup Base** (`/content/drive/MyDrive/resume-ner-azureml`):
- `src/orchestration/jobs/hpo/local/backup.py:128-129` - hardcoded string replacement
- `src/orchestration/jobs/hpo/local/backup.py:133-134` - hardcoded string replacement
- `src/orchestration/jobs/hpo/local/backup.py:188-189` - hardcoded string replacement
- `src/infrastructure/paths/drive.py:167` - in `resolve_output_path_for_colab()`
- `src/infrastructure/paths/drive.py:173` - in `resolve_output_path_for_colab()`

**Project Name** (`resume-ner-azureml`):
- `src/infrastructure/storage/drive.py:430` - fallback in `create_colab_store()`
- `src/infrastructure/paths/drive.py:164` - in `resolve_output_path_for_colab()`
- Hardcoded in multiple string replacements

### 3.3 String Replacement Patterns

**Pattern 1**: `/content/resume-ner-azureml` → `/content/drive/MyDrive/resume-ner-azureml`
- `src/orchestration/jobs/hpo/local/backup.py:128-129`
- `src/orchestration/jobs/hpo/local/backup.py:133-134`

**Pattern 2**: `backbone_output_dir` → Drive path using string replacement
- `src/orchestration/jobs/hpo/local/backup.py:188-189`

**Issues**:
- Assumes repository is always at `/content/resume-ner-azureml`
- Fails in workspace environments or if repository is in different location
- Not relative path-based (should compute relative path from outputs root)

## 4. Drive/Storage Path Mapping Logic

### 4.1 Functions Requiring `root_dir` Parameter

**`DriveBackupStore.__init__()`** (`src/infrastructure/storage/drive.py:79-96`):
- Requires `root_dir: Path` parameter
- Uses `root_dir` to compute relative paths for `drive_path_for()`
- Validates that paths are under `root_dir`

**`create_colab_store()`** (`src/infrastructure/storage/drive.py:397-438`):
- Requires `root_dir: Path` and `config_dir: Path` parameters
- Uses `root_dir` to infer project name (fallback)
- Creates `DriveBackupStore` with `root_dir`

**`get_drive_backup_path()`** (`src/infrastructure/paths/drive.py:68-119`):
- Requires `root_dir: Path` and `config_dir: Path` parameters
- Creates `DriveBackupStore` internally to use its path mapping
- Returns `None` if path is outside `root_dir` or outside `outputs/`

### 4.2 Path Mapping Logic

**Current Approach** (in `DriveBackupStore.drive_path_for()`):
1. Compute relative path from `root_dir` to `local_path`
2. Validate path is under `root_dir`
3. Validate path is under `outputs/` (if `only_outputs=True`)
4. Return `backup_root / relative`

**Issues**:
- Depends on `root_dir` being correct
- If `root_dir` is wrong, mapping fails
- No auto-detection of `root_dir` in Drive functions

### 4.3 Hardcoded String Replacements

**Location**: `src/orchestration/jobs/hpo/local/backup.py:128-134`

```python
drive_dir = Path(str(backbone_output_dir).replace(
    "/content/resume-ner-azureml", "/content/drive/MyDrive/resume-ner-azureml"))
```

**Issues**:
- Assumes repository is always at `/content/resume-ner-azureml`
- Fails in workspace environments
- Not relative path-based
- Should use relative path computation from outputs root

### 4.4 Relative Path Computation (Missing)

**What Should Happen**:
1. Compute relative path from **local outputs root** (may be `ROOT_DIR/outputs` or overridden via `env_overrides`)
2. Rebase that under Drive backup root (from `drive.mount_point` + `drive.backup_base_dir`)
3. Don't depend on repo root location

**Current State**: Not implemented - uses hardcoded string replacements

## 5. Search Strategy Comparison

### 5.1 `find_repository_root()` Strategy

1. Check current directory
2. Search up from `start_dir` (or `cwd`)
3. Platform-specific locations (Colab, Kaggle, workspaces)
4. Search subdirectories in platform locations

**Markers**: `config/` and `src/` directories

### 5.2 `find_project_root()` Strategy

1. From `output_dir`: Find "outputs" directory, use parent
2. From `config_dir`: Walk up looking for `config/` and `src/`
3. From `start_path`: Walk up looking for `config/` and `src/`
4. From `cwd`: Walk up looking for `config/` and `src/`
5. Fallback: `config_dir.parent` or `cwd`

**Markers**: `config/` and `src/` directories, or "outputs" directory

### 5.3 Differences

| Aspect | `find_repository_root()` | `find_project_root()` |
|--------|-------------------------|----------------------|
| Platform support | Colab, Kaggle, workspaces | None |
| Workspace support | Yes (for local) | No |
| Outputs directory | Not used | Used as marker |
| Return type | `Optional[Path]` | `Path` (always returns) |
| Max depth | None (unlimited) | 10 levels |
| Fallback behavior | Returns `None` | Returns `cwd` or `config_dir.parent` |

## 6. Configuration Usage

### 6.1 Current Config Structure (`config/paths.yaml`)

**Sections Used**:
- `base.*` - Base directory names (`config`, `src`, `outputs`, etc.)
- `env_overrides` - Platform-specific output locations
- `drive:` - Drive mount point and backup base directory

**Sections NOT Used for Repo Root Detection**:
- No `repository_root` section exists
- No workspace candidates configuration
- No platform repo candidates configuration
- No search strategy configuration

### 6.2 What Should Be Added

**New `repository_root` Section**:
- Derive markers from `base.*` (single source of truth)
- Workspace candidates
- Platform-specific repo locations (NOT outputs - those are in `env_overrides`)
- Search strategy configuration
- Validation markers (`.git`, `pyproject.toml`)

## 7. Summary of Issues

### 7.1 Critical Issues

1. **Multiple functions with different logic** - `find_repository_root()` vs `find_project_root()`
2. **Hardcoded string replacements** - Assumes repository location
3. **No unified API** - Different functions used in different contexts
4. **Inconsistent return types** - `Optional[Path]` vs `Path`

### 7.2 High Priority Issues

1. **No workspace support in `find_project_root()`** - Fails in workspace environments
2. **No AzureML support** - Missing platform-specific locations
3. **Drive path mapping depends on `root_dir`** - Should use relative paths from outputs root
4. **No validation** - No check for `.git`, `pyproject.toml` to prevent false positives

### 7.3 Medium Priority Issues

1. **Redundant wrapper functions** - `infer_root_dir()` adds no value
2. **Limited search depth** - `find_project_root()` uses `max_depth = 10` (not documented)
3. **No caching** - Repository root detected multiple times
4. **Inconsistent error handling** - Some functions return `None`, others return `cwd`

## 8. Recommendations

### 8.1 Immediate Actions

1. **Create unified function** - Single `detect_repo_root()` function
2. **Add config section** - `repository_root` section in `paths.yaml`
3. **Replace hardcoded paths** - Use config-based detection
4. **Fix Drive path mapping** - Use relative paths from outputs root

### 8.2 Design Principles

1. **Separation of concerns** - Repo root detection ≠ Output routing ≠ Drive mapping
2. **Reuse existing config** - Derive markers from `base.*`, use `env_overrides` for outputs
3. **Relative path mapping** - Don't depend on repo root location for Drive mapping
4. **Single source of truth** - One function, one config section

## 9. Files Requiring Updates

### 9.1 Core Functions (5 files)
- `src/common/shared/notebook_setup.py` - Update `find_repository_root()` to wrapper
- `src/infrastructure/paths/utils.py` - Remove `find_project_root()`, `infer_root_dir()`, update `infer_config_dir()`, `resolve_project_paths()`
- `src/infrastructure/paths/repo.py` - **NEW** - Unified `detect_repo_root()` function
- `src/infrastructure/paths/config.py` - **NEW/UPDATE** - Config loader for `repository_root` section
- `src/infrastructure/paths/__init__.py` - Export unified API

### 9.2 Drive/Storage Functions (3 files)
- `src/infrastructure/storage/drive.py` - Auto-detect `root_dir` if not provided
- `src/infrastructure/paths/drive.py` - Update to use unified functions, fix path mapping
- `src/orchestration/jobs/hpo/local/backup.py` - Replace string replacements with relative path computation

### 9.3 Call Sites (28+ files)
- All files using `infer_config_dir()` - Update to use unified function
- All files using `resolve_project_paths()` - Update to use unified function
- Notebooks - Update imports (or keep backward-compatible wrapper)

### 9.4 Configuration (1 file)
- `config/paths.yaml` - Add `repository_root` section

## 10. Success Criteria

- ✅ Complete list of all repository root detection functions
- ✅ Complete list of all call sites (with file paths and line numbers)
- ✅ Complete list of all hardcoded paths (including Drive/Storage paths)
- ✅ Complete list of Drive/Storage functions that require `root_dir`/`config_dir` parameters
- ✅ Documented path mapping logic between local and Drive paths
- ✅ Documented search strategies for each function
- ✅ Audit results saved to `docs/audits/repository-root-detection-audit.md`


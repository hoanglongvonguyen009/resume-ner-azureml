# Infrastructure Paths

Filesystem path management and resolution with pattern-based path building.

## TL;DR / Quick Start

Detect repository root and resolve output paths using patterns and placeholders.

```python
from pathlib import Path
from infrastructure.paths.repo import detect_repo_root
from infrastructure.paths.resolve import resolve_output_path, build_output_path

# Detect repository root (unified function)
root_dir = detect_repo_root()
config_dir = root_dir / "config"

# Resolve output path from config
output_path = resolve_output_path(
    root_dir=root_dir,
    config_dir=config_dir,
    category="hpo",
    backbone="distilbert",
    study_hash="abc123"
)

# Build path from pattern
path = build_output_path(
    pattern="outputs/hpo/{backbone}/study_{study_hash}",
    backbone="distilbert",
    study_hash="abc123"
)
```

## Overview

The `paths` module provides path resolution and management:

- **Repository root detection**: Unified `detect_repo_root()` function with configurable search strategies
- **Path resolution**: Resolve output paths from configuration patterns
- **Path building**: Build paths from patterns with placeholders
- **Path validation**: Validate paths before creation
- **Path parsing**: Parse paths to extract components (study hash, trial hash, etc.)
- **Cache management**: Manage cache file paths and strategies
- **Drive integration**: Handle Google Drive paths for Colab
- **Project path utilities**: Infer config directories and resolve project paths

## Module Structure

- `resolve.py`: Main path resolution functions
- `config.py`: Path configuration loading
- `repo.py`: Unified repository root detection
- `parse.py`: Path parsing utilities
- `validation.py`: Path validation
- `cache.py`: Cache file path management
- `drive.py`: Google Drive path resolution
- `utils.py`: Project path utilities (includes deprecated wrappers)

## Usage

### Basic Example: Resolve Output Path

```python
from pathlib import Path
from src.infrastructure.paths.resolve import resolve_output_path

# Resolve HPO output path
hpo_path = resolve_output_path(
    root_dir=Path("."),
    config_dir=Path("config/"),
    category="hpo",
    backbone="distilbert",
    study_hash="abc123"
)
# Returns: Path("outputs/hpo/distilbert/study_abc123")
```

### Basic Example: Build Path from Pattern

```python
from src.infrastructure.paths.resolve import build_output_path

# Build path from pattern
path = build_output_path(
    pattern="outputs/final_training/{backbone}/{run_id}",
    backbone="distilbert",
    run_id="20251227_220407"
)
# Returns: Path("outputs/final_training/distilbert/20251227_220407")
```

### Basic Example: Parse Path

```python
from src.infrastructure.paths.parse import parse_hpo_path_v2, find_study_by_hash

# Parse HPO path
components = parse_hpo_path_v2(Path("outputs/hpo/distilbert/study_abc123/trial_xyz"))
# Returns: {"backbone": "distilbert", "study_hash": "abc123", "trial_hash": "xyz"}

# Find study by hash
study_path = find_study_by_hash(Path("outputs/hpo"), "abc123")
```

### Basic Example: Cache Management

```python
from src.infrastructure.paths.cache import get_cache_file_path, save_cache_with_dual_strategy

# Get cache file path
cache_path = get_cache_file_path(
    cache_dir=Path("outputs/cache"),
    category="best_configurations",
    key="distilbert"
)

# Save cache with dual strategy (local + drive backup)
save_cache_with_dual_strategy(
    data={"best_config": {...}},
    cache_path=cache_path,
    drive_backup_path=Path("drive/backup/cache")
)
```

## API Reference

- `resolve_output_path(root_dir: Path, config_dir: Path, category: str, **kwargs) -> Path`: Resolve output path from config
- `build_output_path(pattern: str, **kwargs) -> Path`: Build path from pattern
- `detect_repo_root(...) -> Path`: **Unified repository root detection** (canonical function, uses configurable search strategies from `config/paths.yaml`)
- `resolve_project_paths_with_fallback(...) -> tuple[Path, Path]`: **Preferred SSOT** for path resolution with standardized fallback logic (use for most call sites)
- `resolve_project_paths(...) -> tuple[Path, Path]`: SSOT for resolving both root_dir and config_dir (use when fallback logic not desired)
- `parse_hpo_path_v2(path: Path) -> Dict[str, str]`: Parse HPO path v2 format
- `find_study_by_hash(base_dir: Path, study_hash: str) -> Optional[Path]`: Find study by hash
- `get_cache_file_path(...) -> Path`: Get cache file path
- `save_cache_with_dual_strategy(...)`: Save cache with dual strategy (timestamped, latest, and index files)
- `validate_output_path(path: Path) -> None`: Validate output path

**Pattern**: All path utilities follow the "trust provided config_dir" pattern - if `config_dir` is provided (not `None`), it's used directly without inference.

For detailed signatures and additional utilities (path parsing, cache management, validation), see source code.

**Usage Example**:
```python
from infrastructure.paths.utils import resolve_project_paths_with_fallback

# Resolve paths with standardized fallback
# Trust provided config_dir (DRY principle)
root_dir, config_dir = resolve_project_paths_with_fallback(
    output_dir=Path("outputs/hpo/local/distilbert"),
    config_dir=config_dir,  # Use provided value, don't re-infer
)
```

**See Also**: 
- [`docs/architecture/mlflow-utilities.md`](../../../docs/architecture/mlflow-utilities.md) - Consolidated patterns including path resolution patterns

For detailed signatures, see source code.

## Repository Root Detection

The unified `detect_repo_root()` function provides configurable repository root detection across all platforms:

```python
from infrastructure.paths.repo import detect_repo_root

# Auto-detect from current directory
root_dir = detect_repo_root()

# From config directory
root_dir = detect_repo_root(config_dir=Path("config"))

# From output directory
root_dir = detect_repo_root(output_dir=Path("outputs/hpo/local/distilbert"))

# From start path
root_dir = detect_repo_root(start_path=Path("src/training/core/trainer.py"))
```

**Search Strategy** (from config):
1. From `config_dir` (if provided)
2. From `output_dir` (find "outputs" directory, use parent)
3. From `start_path` (search up directory tree)
4. Workspace directories (from config)
5. Platform-specific repo locations (Colab, Kaggle, AzureML)
6. Current directory and parents (using markers from `base.*`)
7. Fallback to cwd with warning

**Configuration**: Repository root detection is configured in `config/paths.yaml` under the `repository_root` section. Markers are derived from the `base.*` section (single source of truth).

#### Colab-Specific Behavior

When running in Colab, checkpoints and outputs are often stored in Google Drive (`/content/drive/MyDrive/...`) while the project code is at `/content/resume-ner-azureml/`. The unified `detect_repo_root()` function handles this automatically by checking platform-specific locations from config.

**Drive Path Detection**: Use `is_drive_path()` from `common.shared.platform_detection` to check if a path is already in Google Drive before calling `restore_from_drive()` functions. This prevents path resolution errors when checkpoints are already mapped to Drive paths.

**Best Practice:** When calling functions that use path inference (e.g., `infer_config_dir()`, `detect_repo_root()`), prefer passing explicit `config_dir` or `root_dir` parameters instead of relying on inference from checkpoint/output paths.

**Example:**
```python
# ❌ May fail in Colab if checkpoint_dir is in Drive
config_dir = infer_config_dir(path=checkpoint_dir)  # checkpoint_dir = /content/drive/MyDrive/...

# ✅ Preferred: Pass explicit config_dir
root_dir = detect_repo_root()  # Uses platform-specific locations from config
config_dir = root_dir / "config"
```

**Trust Provided Parameters Pattern**: All path resolution functions follow the "trust provided parameter" pattern:
- Functions that accept `config_dir: Optional[Path] = None` will **trust the provided value** and use it directly
- Inference only occurs when the parameter is explicitly `None`
- This follows DRY principles and avoids redundant inference

Functions that accept explicit `config_dir` or `root_dir` parameters will use them directly, avoiding inference issues.

## Integration Points

### Used By

- **Training modules**: Use path resolution for output directories
- **Orchestration modules**: Use path resolution for job outputs
- **Evaluation modules**: Use path resolution for artifact discovery

### Depends On

- `core/`: Normalization and placeholder extraction
- `common/`: YAML utilities, file utilities

## Path Patterns

Path patterns use placeholders like `{backbone}`, `{study_hash}`, `{run_id}`, etc. These are resolved from:
1. Configuration files (`paths.yaml`)
2. Keyword arguments to resolution functions
3. Naming contexts

## Testing

```bash
uvx pytest tests/infrastructure/paths/
```

## Related Modules

- [`../README.md`](../README.md) - Main infrastructure module
- [`../naming/README.md`](../naming/README.md) - Naming uses path resolution
- [`../../core/README.md`](../../core/README.md) - Core utilities for normalization


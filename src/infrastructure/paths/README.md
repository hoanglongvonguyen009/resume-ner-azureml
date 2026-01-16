# Infrastructure Paths

Filesystem path management and resolution with pattern-based path building.

## TL;DR / Quick Start

Resolve output paths using patterns and placeholders.

```python
from src.infrastructure.paths.resolve import resolve_output_path, build_output_path

# Resolve output path from config
output_path = resolve_output_path(
    root_dir=Path("."),
    config_dir=Path("config/"),
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

- **Path resolution**: Resolve output paths from configuration patterns
- **Path building**: Build paths from patterns with placeholders
- **Path validation**: Validate paths before creation
- **Path parsing**: Parse paths to extract components (study hash, trial hash, etc.)
- **Cache management**: Manage cache file paths and strategies
- **Drive integration**: Handle Google Drive paths for Colab
- **Project path resolution**: Find and resolve project root and config directories

## Module Structure

- `resolve.py`: Main path resolution functions
- `config.py`: Path configuration loading
- `parse.py`: Path parsing utilities
- `validation.py`: Path validation
- `cache.py`: Cache file path management
- `drive.py`: Google Drive path resolution
- `utils.py`: Project path utilities

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

### Path Resolution

- `resolve_output_path(root_dir: Path, config_dir: Path, category: str, **kwargs) -> Path`: Resolve output path from config
- `build_output_path(pattern: str, **kwargs) -> Path`: Build path from pattern
- `PROCESS_PATTERN_KEYS`: Mapping from process_type to pattern keys

### Path Validation

- `validate_output_path(path: Path) -> None`: Validate output path
- `validate_path_before_mkdir(path: Path) -> None`: Validate path before creating directory

### Path Parsing

- `parse_hpo_path_v2(path: Path) -> Dict[str, str]`: Parse HPO path v2 format
- `is_v2_path(path: Path) -> bool`: Check if path is v2 format
- `find_study_by_hash(base_dir: Path, study_hash: str) -> Optional[Path]`: Find study by hash
- `find_trial_by_hash(base_dir: Path, trial_hash: str) -> Optional[Path]`: Find trial by hash

### Cache Management

- `get_cache_file_path(...)`: Get cache file path
- `save_cache_with_dual_strategy(...)`: Save cache with local + drive backup
- `load_cache_file(...)`: Load cache file

### Project Paths

- `find_project_root(...)`: Find project root directory
- `infer_config_dir(...)`: Infer config directory
- `resolve_project_paths(...)`: Resolve project paths

For detailed signatures, see source code.

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


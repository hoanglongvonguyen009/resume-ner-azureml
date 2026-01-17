# Unified Repository Root Detection Design

**Date**: 2025-01-27  
**Purpose**: Design document for unified repository root detection API and implementation.

## Executive Summary

This design consolidates all repository root detection logic into a single, centralized system that:
- Uses a unified function `detect_repo_root()` with configurable search strategies
- Reuses existing `config/paths.yaml` structure (derives markers from `base.*`)
- Separates concerns: repo root detection ≠ output routing ≠ Drive mapping
- Uses relative paths for Drive mapping (not string replacement)
- Provides backward compatibility through wrapper functions

## 1. Unified Function Signature

### 1.1 Main Function: `detect_repo_root()`

**Location**: `src/infrastructure/paths/repo.py` (new module)

**Signature**:
```python
def detect_repo_root(
    start_path: Optional[Path] = None,
    config_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Path:
    """
    Unified repository root detection with configurable search strategies.
    
    Search order (from config):
    1. If config_dir provided: derive from config_dir
    2. If output_dir provided: find "outputs" directory, use parent
    3. If start_path provided: search up from start_path
    4. Workspace directories (from config)
    5. Platform-specific repo locations (from config, NOT outputs - those are in env_overrides)
    6. Current directory and parents (using markers from base.*)
    7. Fallback to cwd with warning
    
    Note: This function detects the repository root only. Output routing
    is handled separately via env_overrides in paths.yaml.
    
    Args:
        start_path: Optional starting path for search (strategy 3).
        config_dir: Optional config directory path (strategy 1).
        output_dir: Optional output directory path (strategy 2).
    
    Returns:
        Path to repository root directory.
    
    Raises:
        ValueError: If repository root cannot be found and fallback is disabled.
    
    Examples:
        >>> # From config_dir
        >>> detect_repo_root(config_dir=Path("/workspace/config"))
        Path("/workspace")
        
        >>> # From output_dir
        >>> detect_repo_root(output_dir=Path("/workspace/outputs/hpo/local/distilbert"))
        Path("/workspace")
        
        >>> # From start_path
        >>> detect_repo_root(start_path=Path("/workspace/src/training/core/trainer.py"))
        Path("/workspace")
        
        >>> # Auto-detect from cwd
        >>> detect_repo_root()
        Path("/workspace")
    """
```

**Key Design Decisions**:
- **Canonical name**: `detect_repo_root()` (not `find_repository_root()` or `find_project_root()`)
- **Always returns Path**: Never returns `None` (raises `ValueError` if not found and fallback disabled)
- **Configurable search**: Search order and strategies from config
- **Platform-aware**: Supports Colab, Kaggle, AzureML, workspaces, local

### 1.2 Backward Compatibility Wrapper

**Location**: `src/common/shared/notebook_setup.py` (update existing function)

**Signature**:
```python
def find_repository_root(start_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Backward-compatible wrapper for detect_repo_root().
    
    .. deprecated:: 
        Use `detect_repo_root()` from `infrastructure.paths` instead.
        This function is kept for backward compatibility with notebooks.
    
    Args:
        start_dir: Directory to start searching from (mapped to start_path).
    
    Returns:
        Path to repository root directory, or None if not found.
    """
    from infrastructure.paths.repo import detect_repo_root
    
    try:
        return detect_repo_root(start_path=start_dir)
    except ValueError:
        return None
```

**Key Design Decisions**:
- **Backward compatible**: Returns `Optional[Path]` (not `Path`)
- **Thin wrapper**: Delegates to unified function
- **Deprecation notice**: Points to canonical function

## 2. Configuration Structure

### 2.1 New Section: `repository_root`

**Location**: `config/paths.yaml`

**Structure**:
```yaml
repository_root:
  # Derive markers from existing base section (single source of truth)
  # Uses base.config, base.src, etc. - no duplication
  markers_from_base: true
  
  # Optional extra markers for stricter validation
  extra_markers:
    - ".git"
    - "pyproject.toml"
  
  # Workspace candidates (not in YAML yet)
  workspace_candidates:
    - "/workspaces/resume-ner-azureml"
    - "/workspace/resume-ner-azureml"
  
  # Platform-specific REPO locations (NOT outputs - those are in env_overrides)
  # These are where the repository code itself lives, not where outputs go
  platform_candidates:
    colab:
      - "/content/resume-ner-azureml"
    kaggle:
      - "/kaggle/working/resume-ner-azureml"
    azureml:
      - "/mnt/resume-ner-azureml"
  
  # Search strategy configuration
  search:
    max_depth: 10
    fallback_to_cwd: true
    warn_on_fallback: true
  
  # Optional caching
  cache:
    enabled: true
```

**Key Design Principles**:
- **Reuse existing config**: Derive markers from `base.*` (no duplication)
- **Separation of concerns**: Platform repo locations ≠ output locations (outputs in `env_overrides`)
- **No Drive config here**: Drive mount points and backup base in `drive:` section
- **Focus on repo root**: Only repo root discovery, not output routing

### 2.2 Config Loader Function

**Location**: `src/infrastructure/paths/config.py` (new or update existing)

**Signature**:
```python
def load_repository_root_config(config_dir: Path) -> dict[str, Any]:
    """
    Load and validate repository root detection configuration.
    
    Args:
        config_dir: Config directory path.
    
    Returns:
        Dictionary with repository root config (validated).
    
    Raises:
        FileNotFoundError: If config/paths.yaml not found.
        ValueError: If config is invalid.
    """
```

**Responsibilities**:
- Load `repository_root` section from `config/paths.yaml`
- Derive markers from `base.*` section (single source of truth)
- Validate all required fields present
- Validate path formats
- Validate platform names
- Return structured config object

## 3. Validation Policy

### 3.1 Validation Function: `validate_repo_root()`

**Location**: `src/infrastructure/paths/repo.py`

**Signature**:
```python
def validate_repo_root(candidate: Path, config: dict[str, Any]) -> bool:
    """
    Validate candidate directory is actually repository root.
    
    Prevents false positives in monorepos or nested copies.
    
    Args:
        candidate: Candidate directory to validate.
        config: Repository root config (from load_repository_root_config()).
    
    Returns:
        True if candidate is valid repository root, False otherwise.
    
    Validation Rules:
        - Required markers (from base.*): config/ and src/ directories must exist
        - Optional markers (from extra_markers): At least one of .git, pyproject.toml, or setup.cfg
    """
```

**Validation Rules**:
1. **Required markers** (from `base.*`): `config/` and `src/` directories must exist
2. **Optional markers** (from `extra_markers`): At least one of `.git`, `pyproject.toml`, or `setup.cfg`
3. **Prevents false positives**: In monorepos or nested copies

## 4. Helper Functions

### 4.1 `infer_config_dir()` - Updated

**Location**: `src/infrastructure/paths/utils.py` (update existing)

**New Signature**:
```python
def infer_config_dir(
    config_dir: Optional[Path] = None,
    path: Optional[Path] = None,
    root_dir: Optional[Path] = None,
) -> Path:
    """
    Infer config directory, with optional provided config_dir or by searching from path.
    
    Updated to use unified detect_repo_root() function.
    
    Args:
        config_dir: Optional config directory (if provided, returned directly).
        path: Starting path to search from (e.g., output_dir, checkpoint_dir).
        root_dir: Optional repository root directory (if provided, uses root_dir / "config").
    
    Returns:
        Path to config directory.
    """
    # If config_dir provided, return it directly
    if config_dir is not None:
        return config_dir
    
    # If root_dir provided, use root_dir / "config"
    if root_dir is not None:
        return root_dir / "config"
    
    # Otherwise, use unified detect_repo_root() to find root, then derive config_dir
    from infrastructure.paths.repo import detect_repo_root
    root = detect_repo_root(start_path=path, output_dir=path)
    return root / "config"
```

### 4.2 `resolve_project_paths()` - Updated

**Location**: `src/infrastructure/paths/utils.py` (update existing)

**New Signature**:
```python
def resolve_project_paths(
    output_dir: Optional[Path] = None,
    config_dir: Optional[Path] = None,
    start_path: Optional[Path] = None,
) -> tuple[Path, Path]:
    """
    Resolve project root_dir and config_dir from available information.
    
    Updated to use unified detect_repo_root() function.
    
    Args:
        output_dir: Optional output directory path.
        config_dir: Optional config directory path (if provided, returned directly).
        start_path: Optional starting path for search.
    
    Returns:
        Tuple of (root_dir, config_dir). Both are Path (never None).
    """
    from infrastructure.paths.repo import detect_repo_root
    
    # Priority 1: Trust provided config_dir if available
    if config_dir is not None:
        root_dir = detect_repo_root(config_dir=config_dir)
        return root_dir, config_dir
    
    # Priority 2: Infer root_dir from output_dir or start_path
    root_dir = detect_repo_root(output_dir=output_dir, start_path=start_path)
    config_dir = root_dir / "config"
    
    return root_dir, config_dir
```

## 5. Drive/Storage Path Mapping

### 5.1 Design Principles

**Key Principle**: Don't depend on repo root location for backup mapping.

**Approach**:
1. Compute relative path from **local outputs root** (may be `ROOT_DIR/outputs` or overridden via `env_overrides`)
2. Rebase that under Drive backup root (from `drive.mount_point` + `drive.backup_base_dir`)
3. Works across all platforms (Colab, Kaggle, workspaces, local)

### 5.2 New Functions

**Location**: `src/infrastructure/paths/drive.py` (update existing)

**Function 1: `map_local_to_drive()`**
```python
def map_local_to_drive(
    local_path: Path,
    config_dir: Path,
    root_dir: Optional[Path] = None,
) -> Optional[Path]:
    """
    Map local output path to Drive backup path using relative paths.
    
    Computes relative path from local outputs root, then rebases under Drive backup root.
    Does NOT depend on repo root location.
    
    Args:
        local_path: Local file or directory path (must be within outputs/).
        config_dir: Config directory path.
        root_dir: Optional repository root (auto-detected if not provided).
    
    Returns:
        Equivalent Drive backup path, or None if Drive not configured or path outside outputs/.
    
    Examples:
        Local: /workspace/outputs/hpo/local/distilbert/trial_0/checkpoint/
        Drive:  /content/drive/MyDrive/resume-ner-azureml/outputs/hpo/local/distilbert/trial_0/checkpoint/
    """
```

**Function 2: `map_drive_to_local()`**
```python
def map_drive_to_local(
    drive_path: Path,
    config_dir: Path,
    root_dir: Optional[Path] = None,
) -> Optional[Path]:
    """
    Map Drive backup path to local output path using relative paths.
    
    Computes relative path from Drive backup root, then rebases under local outputs root.
    Does NOT depend on repo root location.
    
    Args:
        drive_path: Drive backup path (must be within Drive backup outputs/).
        config_dir: Config directory path.
        root_dir: Optional repository root (auto-detected if not provided).
    
    Returns:
        Equivalent local output path, or None if path outside Drive backup outputs/.
    """
```

### 5.3 Updated Functions

**`DriveBackupStore.__init__()`** - Auto-detect `root_dir`:
```python
def __init__(
    self,
    root_dir: Optional[Path] = None,  # Now optional
    backup_root: Optional[Path] = None,
    config_dir: Optional[Path] = None,
    only_outputs: bool = True,
    dry_run: bool = False,
) -> None:
    """
    Initialize DriveBackupStore with optional auto-detection.
    
    Args:
        root_dir: Optional repository root (auto-detected if not provided).
        backup_root: Optional backup root (loaded from config if not provided).
        config_dir: Optional config directory (required if root_dir or backup_root not provided).
        only_outputs: Enforce outputs/ restriction.
        dry_run: Dry run mode for testing.
    """
    # Auto-detect root_dir if not provided
    if root_dir is None:
        from infrastructure.paths.repo import detect_repo_root
        root_dir = detect_repo_root(config_dir=config_dir)
    
    # Load backup_root from config if not provided
    if backup_root is None:
        if config_dir is None:
            config_dir = root_dir / "config"
        backup_root = get_drive_backup_base(config_dir)
        if backup_root is None:
            raise ValueError("Drive backup not configured")
    
    self.root_dir = root_dir
    self.backup_root = backup_root
    # ... rest of initialization
```

**`create_colab_store()`** - Auto-detect `root_dir`:
```python
def create_colab_store(
    root_dir: Optional[Path] = None,  # Now optional
    config_dir: Optional[Path] = None,  # Now optional
    mount_point: str = "/content/drive",
) -> Optional[DriveBackupStore]:
    """
    Factory function to create DriveBackupStore for Colab environment.
    
    Auto-detects root_dir and config_dir if not provided.
    
    Args:
        root_dir: Optional repository root (auto-detected if not provided).
        config_dir: Optional config directory (auto-detected if not provided).
        mount_point: Drive mount point.
    
    Returns:
        DriveBackupStore if configured, None if backup disabled.
    """
    # Auto-detect root_dir and config_dir if not provided
    if root_dir is None or config_dir is None:
        from infrastructure.paths.repo import detect_repo_root
        if root_dir is None:
            root_dir = detect_repo_root()
        if config_dir is None:
            config_dir = root_dir / "config"
    
    # ... rest of function
```

**`get_drive_backup_path()`** - Auto-detect `root_dir`:
```python
def get_drive_backup_path(
    root_dir: Optional[Path] = None,  # Now optional
    config_dir: Optional[Path] = None,  # Now optional
    local_path: Path,
) -> Optional[Path]:
    """
    Convert local output path to Drive backup path, mirroring structure.
    
    Auto-detects root_dir and config_dir if not provided.
    
    Args:
        root_dir: Optional repository root (auto-detected if not provided).
        config_dir: Optional config directory (auto-detected if not provided).
        local_path: Local file or directory path to backup (must be within outputs/).
    
    Returns:
        Equivalent Drive backup path, or None if Drive not configured or path outside outputs/.
    """
    # Auto-detect root_dir and config_dir if not provided
    if root_dir is None or config_dir is None:
        from infrastructure.paths.repo import detect_repo_root
        if root_dir is None:
            root_dir = detect_repo_root()
        if config_dir is None:
            config_dir = root_dir / "config"
    
    # Use map_local_to_drive() for relative path computation
    return map_local_to_drive(local_path, config_dir, root_dir)
```

### 5.4 Replace Hardcoded String Replacements

**Location**: `src/orchestration/jobs/hpo/local/backup.py`

**Old Code** (hardcoded string replacement):
```python
drive_dir = Path(str(backbone_output_dir).replace(
    "/content/resume-ner-azureml", "/content/drive/MyDrive/resume-ner-azureml"))
```

**New Code** (relative path computation):
```python
from infrastructure.paths import get_outputs_dir, map_local_to_drive

# Get local outputs root (may be overridden via env_overrides)
local_outputs_root = get_outputs_dir(root_dir, config_dir, environment)

# Compute relative path from local outputs root
relative_path = backbone_output_dir.relative_to(local_outputs_root)

# Map to Drive using relative path
drive_dir = map_local_to_drive(backbone_output_dir, config_dir, root_dir)
```

## 6. Module Structure

### 6.1 New Module: `src/infrastructure/paths/repo.py`

**Purpose**: Repository root detection (single import surface)

**Exports**:
- `detect_repo_root()` - Main unified function
- `validate_repo_root()` - Validation function

### 6.2 Updated Module: `src/infrastructure/paths/__init__.py`

**Public API**:
```python
# Repository root detection
from .repo import detect_repo_root, validate_repo_root

# Config directory inference
from .utils import infer_config_dir, resolve_project_paths

# Output directories (from env_overrides)
from .outputs import get_outputs_dir  # If this module exists

# Drive path mapping
from .drive import (
    get_drive_backup_path,
    map_local_to_drive,
    map_drive_to_local,
    get_drive_backup_base,
)
```

**Single Import Surface**:
```python
from infrastructure.paths import (
    detect_repo_root,
    infer_config_dir,
    resolve_project_paths,
    get_drive_backup_path,
    map_local_to_drive,
    map_drive_to_local,
)
```

## 7. Migration Strategy

### 7.1 Phase 1: Implement Unified Function (Non-Breaking)

1. Create `src/infrastructure/paths/repo.py` with `detect_repo_root()`
2. Add `repository_root` section to `config/paths.yaml`
3. Create config loader function
4. Update `find_repository_root()` to wrapper (backward compatible)
5. Keep existing functions (`find_project_root()`, `infer_root_dir()`) for now

### 7.2 Phase 2: Migrate Call Sites (Gradual)

1. Update `infer_config_dir()` to use `detect_repo_root()`
2. Update `resolve_project_paths()` to use `detect_repo_root()`
3. Update Drive/Storage functions to auto-detect `root_dir`
4. Replace hardcoded string replacements with relative path computation
5. Update notebooks (or keep using backward-compatible wrapper)

### 7.3 Phase 3: Remove Deprecated Functions

1. Mark `find_project_root()` and `infer_root_dir()` as deprecated
2. Remove after all migrations complete
3. Keep `find_repository_root()` as wrapper (for backward compatibility)

### 7.4 Phase 4: Update Documentation

1. Update `src/infrastructure/paths/README.md`
2. Update `src/common/README.md`
3. Update notebook setup guides

## 8. Success Criteria

### 8.1 Function Design

- ✅ Unified function signature designed
- ✅ Config structure designed and documented
- ✅ Helper function signatures designed
- ✅ Validation policy designed
- ✅ Drive path mapping designed (relative paths)

### 8.2 Module Structure

- ✅ New module structure designed (`repo.py`, `outputs.py`, updated `drive.py`)
- ✅ Single import surface designed
- ✅ Public API documented

### 8.3 Migration Strategy

- ✅ Migration phases defined
- ✅ Backward compatibility strategy defined
- ✅ Deprecation strategy defined

### 8.4 Documentation

- ✅ Design document saved to `docs/design/repository-root-detection-design.md`
- ✅ Review and approval of design

## 9. Open Questions

### 9.1 Caching

**Question**: Should we cache detected repository root?

**Options**:
- Option A: Cache per process (module-level variable)
- Option B: No caching (always detect fresh)
- Option C: Configurable caching (from config)

**Recommendation**: Option C (configurable caching) - Default enabled, can be disabled for testing

### 9.2 Environment Variable Override

**Question**: Should we support `REPO_ROOT` environment variable?

**Options**:
- Option A: Yes, check `REPO_ROOT` env var first (highest priority)
- Option B: No, rely on config-based detection only

**Recommendation**: Option A (future enhancement) - Not in initial implementation

### 9.3 Error Handling

**Question**: Should `detect_repo_root()` raise `ValueError` or return `None`?

**Decision**: Raise `ValueError` (always returns `Path`) - More explicit, forces error handling

## 10. Implementation Notes

### 10.1 Type Hints

All functions must have complete type hints (mypy compliance):
- Use `Path` from `pathlib`
- Use `Optional[Path]` for optional parameters
- Use `dict[str, Any]` for config dictionaries

### 10.2 Logging

Use structured logging for debugging:
- Log search strategies attempted
- Log candidates found and validated
- Log final result

### 10.3 Testing

Create unit tests for:
- Each search strategy
- Validation function
- Config loading
- Edge cases (monorepos, nested copies, missing markers)

### 10.4 Performance

- Cache detected root (if enabled)
- Limit search depth (from config)
- Early return when markers found

## 11. Related Documents

- Audit: `docs/audits/repository-root-detection-audit.md`
- Implementation Plan: `docs/implementation_plans/consolidate-repository-root-detection.plan.md`
- Config Reference: `config/paths.yaml`


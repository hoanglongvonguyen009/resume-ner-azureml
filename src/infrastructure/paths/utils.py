from __future__ import annotations

"""
@meta
name: paths_utils
type: utility
domain: paths
responsibility:
  - Path utility functions
  - Find project root directory
inputs:
  - Configuration directory paths
outputs:
  - Project root directory paths
tags:
  - utility
  - paths
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Path utility functions."""

from pathlib import Path
from typing import Optional

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def infer_config_dir(
    config_dir: Optional[Path] = None,
    path: Optional[Path] = None,
    root_dir: Optional[Path] = None,
) -> Path:
    """
    Infer config directory, with optional provided config_dir or by searching from path.
    
    Updated to use unified detect_repo_root() function.
    
    If config_dir is provided, returns it directly (no inference needed).
    If root_dir is provided, uses root_dir / "config".
    Otherwise, uses unified detect_repo_root() to find root, then derives config_dir.
    
    Args:
        config_dir: Optional config directory (if provided, returned directly).
        path: Starting path to search from (e.g., output_dir, checkpoint_dir).
              If None, searches from current working directory.
        root_dir: Optional repository root directory (if provided, uses root_dir / "config").
    
    Returns:
        Path to config directory.
    
    Examples:
        >>> # Use provided config_dir (no inference)
        >>> infer_config_dir(config_dir=Path("/workspace/config"))
        Path("/workspace/config")
        
        >>> # Use provided root_dir
        >>> infer_config_dir(root_dir=Path("/workspace"))
        Path("/workspace/config")
        
        >>> # Typical structure: /workspace/outputs/hpo/...
        >>> # Will find: /workspace/config
        >>> infer_config_dir(path=Path("/workspace/outputs/hpo/local/distilbert"))
        Path("/workspace/config")
        
        >>> # Deep structure: /workspace/outputs/hpo/local/distilbert/study-abc/trial-xyz
        >>> # Will still find: /workspace/config
        >>> infer_config_dir(path=Path("/workspace/outputs/hpo/local/distilbert/study-abc/trial-xyz"))
        Path("/workspace/config")
        
        >>> # When running from notebook: /workspace/notebooks/
        >>> # Will find: /workspace/config (by searching up from cwd)
        >>> infer_config_dir()
        Path("/workspace/config")
    """
    # If config_dir provided, return it directly
    if config_dir is not None:
        return config_dir
    
    # If root_dir provided, use root_dir / "config"
    if root_dir is not None:
        return root_dir / "config"
    
    # Otherwise, use unified detect_repo_root() to find root, then derive config_dir
    from infrastructure.paths.repo import detect_repo_root
    
    # If path is provided, search directly from that path to avoid workspace directory checks
    # that might find the actual project root instead of the test's temporary directory
    if path is not None:
        # Search up from the provided path looking for config/ directory
        # This is more direct and avoids loading config that might point to workspace directories
        current = path.resolve() if path.is_absolute() else path
        if current.is_file():
            current = current.parent
        
        max_depth = 20
        depth = 0
        while depth < max_depth:
            candidate_config = current / "config"
            if candidate_config.exists() and candidate_config.is_dir():
                # Found config directory - check if parent has src/ to confirm it's repo root
                candidate_root = current
                if (candidate_root / "src").exists():
                    return candidate_config
            
            if current.parent == current:  # Reached filesystem root
                break
            current = current.parent
            depth += 1
        
        # If not found by direct search, fall back to detect_repo_root()
        # This handles cases where config might be in a different location
        root = detect_repo_root(start_path=path, output_dir=path)
    else:
        # No path provided, use default detection
        root = detect_repo_root()
    
    return root / "config"


def resolve_project_paths(
    output_dir: Optional[Path] = None,
    config_dir: Optional[Path] = None,
    start_path: Optional[Path] = None,
) -> tuple[Path, Path]:
    """
    Resolve project root_dir and config_dir from available information.
    
    Updated to use unified detect_repo_root() function.
    
    This function consolidates the common pattern of inferring project paths
    across HPO and training scripts. It trusts provided `config_dir` if not None,
    otherwise infers from `output_dir` or `start_path`.
    
    **Key principle**: Trusts provided `config_dir` parameter to avoid re-inference
    when the caller already has the correct value (DRY principle).
    
    **When to use**:
    - Use `resolve_project_paths_with_fallback()` for most call sites (provides standardized fallback logic)
    - Use `resolve_project_paths()` only when fallback logic is explicitly not desired
    
    Args:
        output_dir: Optional output directory path (e.g., `outputs/hpo/local/distilbert`).
                    Used to infer project root by finding "outputs" directory.
        config_dir: Optional config directory path (e.g., `config/`).
                   If provided, returned directly without inference (trusts caller).
        start_path: Optional starting path for search (fallback if output_dir not available).
    
    Returns:
        Tuple of `(root_dir, config_dir)`. Both are Path (never None).
        - If `config_dir` is provided: returns `(root_dir_from_config_dir, config_dir)`
        - If `config_dir` is None: infers both from `output_dir` or `start_path`
    
    Examples:
        >>> # Trust provided config_dir (no inference)
        >>> root_dir, config_dir = resolve_project_paths(
        ...     output_dir=Path("/workspace/outputs/hpo/local/distilbert"),
        ...     config_dir=Path("/workspace/config")
        ... )
        >>> assert config_dir == Path("/workspace/config")
        >>> assert root_dir == Path("/workspace")
        
        >>> # Infer from output_dir when config_dir not provided
        >>> root_dir, config_dir = resolve_project_paths(
        ...     output_dir=Path("/workspace/outputs/hpo/local/distilbert")
        ... )
        >>> assert root_dir == Path("/workspace")
        >>> assert config_dir == Path("/workspace/config")
        
        >>> # Infer from start_path as fallback
        >>> root_dir, config_dir = resolve_project_paths(
        ...     start_path=Path("/workspace/src/training/core/trainer.py")
        ... )
        >>> assert root_dir == Path("/workspace")
        >>> assert config_dir == Path("/workspace/config")
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


def resolve_project_paths_with_fallback(
    output_dir: Optional[Path] = None,
    config_dir: Optional[Path] = None,
) -> tuple[Path, Path]:
    """
    Resolve project paths with standardized fallback logic.
    
    **Primary function for most call sites** - use this unless you explicitly don't want fallback logic.
    
    This function consolidates the common "standardized fallback" pattern used
    across HPO and training execution scripts. It:
    1. Calls `resolve_project_paths()` to resolve paths
    2. Applies standardized fallback logic:
       - If root_dir is None, uses Path.cwd()
       - If config_dir is None after resolution, infers it using `infer_config_dir()`
    
    **Key principle**: Trusts provided `config_dir` if not None, following DRY principles.
    Only infers when explicitly None.
    
    **When to use**:
    - **Primary function**: Use this for most call sites (provides standardized fallback)
    - Use `resolve_project_paths()` only when fallback logic is explicitly not desired
    - Use `infer_config_dir()` only for direct inference without needing root_dir
    
    Args:
        output_dir: Optional output directory path (e.g., `outputs/hpo/local/distilbert`).
        config_dir: Optional config directory path (e.g., `config/`).
                   If provided, trusted and used directly without inference.
    
    Returns:
        Tuple of `(root_dir, config_dir)`. Both are Path (never None).
    
    Examples:
        >>> # Trust provided config_dir (no inference)
        >>> root_dir, config_dir = resolve_project_paths_with_fallback(
        ...     output_dir=Path("/workspace/outputs/hpo/local/distilbert"),
        ...     config_dir=Path("/workspace/config")
        ... )
        >>> assert config_dir == Path("/workspace/config")
        >>> assert root_dir == Path("/workspace")
        
        >>> # Infer from output_dir when config_dir not provided
        >>> root_dir, config_dir = resolve_project_paths_with_fallback(
        ...     output_dir=Path("/workspace/outputs/hpo/local/distilbert")
        ... )
        >>> assert root_dir == Path("/workspace")
        >>> assert config_dir == Path("/workspace/config")
    """
    root_dir, resolved_config_dir = resolve_project_paths(
        output_dir=output_dir,
        config_dir=config_dir,
    )
    
    # Standardized fallback: use resolved value, or provided parameter, or infer
    if root_dir is None:
        root_dir = Path.cwd()
    
    # Use resolved config_dir, or provided config_dir, or infer as last resort
    config_dir = resolved_config_dir or config_dir
    if config_dir is None:
        config_dir = infer_config_dir(path=root_dir) if root_dir else infer_config_dir()
    
    return root_dir, config_dir





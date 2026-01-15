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


def find_project_root(
    config_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    start_path: Optional[Path] = None,
) -> Path:
    """
    Find project root directory using multiple strategies.
    
    Tries multiple strategies in order:
    1. From `output_dir`: Walk up to find "outputs" directory, then use its parent
    2. From `config_dir`: Walk up looking for directory with both `config/` and `src/` subdirectories
    3. From `start_path`: Walk up looking for directory with both `config/` and `src/` subdirectories
    4. From current working directory: Walk up looking for directory with both `config/` and `src/` subdirectories
    
    Args:
        config_dir: Optional config directory path (strategy 2).
        output_dir: Optional output directory path (strategy 1).
        start_path: Optional starting path for search (strategy 3).
    
    Returns:
        Path to project root directory.
    
    Examples:
        >>> # From output_dir: outputs/hpo/local/distilbert -> project_root
        >>> find_project_root(output_dir=Path("/workspace/outputs/hpo/local/distilbert"))
        Path("/workspace")
        
        >>> # From config_dir: config/ -> project_root
        >>> find_project_root(config_dir=Path("/workspace/config"))
        Path("/workspace")
        
        >>> # From any path: src/training/core/trainer.py -> project_root
        >>> find_project_root(start_path=Path("/workspace/src/training/core/trainer.py"))
        Path("/workspace")
    """
    max_depth = 10
    
    # Strategy 1: From output_dir - find "outputs" directory, then use its parent
    if output_dir is not None:
        current = output_dir
        depth = 0
        while current.parent != current and depth < max_depth:
            if current.name == "outputs":
                root_dir = current.parent
                logger.debug(
                    f"Found project root from output_dir: {root_dir} (outputs dir: {current})"
                )
                return root_dir
            current = current.parent
            depth += 1
    
    # Strategy 2: From config_dir - walk up looking for directory with both config/ and src/
    if config_dir is not None:
        candidate_root = config_dir.parent if config_dir.name == "config" else config_dir
        depth = 0
        while depth < max_depth:
            # Check if this directory has both config/ and src/ subdirectories
            if (candidate_root / "config").exists() and (candidate_root / "src").exists():
                logger.debug(
                    f"Found project root from config_dir: {candidate_root} (config_dir: {config_dir})"
                )
                return candidate_root
            if candidate_root.parent == candidate_root:  # Reached filesystem root
                break
            candidate_root = candidate_root.parent
            depth += 1
    
    # Strategy 3: From start_path - walk up looking for directory with both config/ and src/
    if start_path is not None:
        candidate_root = start_path.parent if start_path.is_file() else start_path
        depth = 0
        while depth < max_depth:
            if (candidate_root / "config").exists() and (candidate_root / "src").exists():
                logger.debug(
                    f"Found project root from start_path: {candidate_root} (start_path: {start_path})"
                )
                return candidate_root
            if candidate_root.parent == candidate_root:  # Reached filesystem root
                break
            candidate_root = candidate_root.parent
            depth += 1
    
    # Strategy 4: From current working directory
    current = Path.cwd()
    depth = 0
    while depth < max_depth:
        if (current / "config").exists() and (current / "src").exists():
            logger.debug(
                f"Found project root from cwd: {current}"
            )
            return current
        if current.parent == current:  # Reached filesystem root
            break
        current = current.parent
        depth += 1
    
    # Fallback: use config_dir.parent if available, otherwise cwd
    if config_dir is not None:
        root_dir = config_dir.parent
        logger.warning(
            f"Could not find project root after {max_depth} levels. "
            f"Using {root_dir} as root_dir (from config_dir: {config_dir})"
        )
        return root_dir
    
    # Last resort: current working directory
    root_dir = Path.cwd()
    logger.warning(
        f"Could not find project root. Using {root_dir} as fallback."
    )
    return root_dir


def infer_root_dir(
    config_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    start_path: Optional[Path] = None,
) -> Path:
    """
    Infer project root directory using the best available strategy.
    
    This is a convenience wrapper around `find_project_root()` that tries
    multiple strategies automatically.
    
    Args:
        config_dir: Optional config directory path.
        output_dir: Optional output directory path.
        start_path: Optional starting path for search.
    
    Returns:
        Path to project root directory.
    """
    return find_project_root(config_dir=config_dir, output_dir=output_dir, start_path=start_path)


def infer_config_dir(
    config_dir: Optional[Path] = None,
    path: Optional[Path] = None,
) -> Path:
    """
    Infer config directory, with optional provided config_dir or by searching from path.
    
    If config_dir is provided, returns it directly (no inference needed).
    Otherwise, searches up the directory tree from the given path to find
    a parent directory that contains a "config" subdirectory.
    
    When path is None or no config is found in the path's parent chain, it searches
    from the current working directory up to find the project root (where both
    config/ and src/ exist), ensuring correct behavior when running from notebooks
    or subdirectories.
    
    Args:
        config_dir: Optional config directory (if provided, returned directly).
        path: Starting path to search from (e.g., output_dir, checkpoint_dir).
              If None, searches from current working directory.
    
    Returns:
        Path to config directory. Falls back to Path.cwd() / "config" if not found.
    
    Examples:
        >>> # Use provided config_dir (no inference)
        >>> infer_config_dir(config_dir=Path("/workspace/config"))
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
    # If config_dir is provided, return it directly (no inference needed)
    if config_dir is not None:
        return config_dir
    
    # First, try searching from the provided path
    if path is not None:
        for parent in path.parents:
            candidate = parent / "config"
            if candidate.exists():
                return candidate
    
    # If path is None or no config found in path's parent chain,
    # use find_project_root to locate project root, then use its config/ subdirectory
    root_dir = find_project_root(start_path=path)
    candidate = root_dir / "config"
    if candidate.exists():
        return candidate
    
    # Last resort: fall back to cwd/config if not found
    return Path.cwd() / "config"


def resolve_project_paths(
    output_dir: Optional[Path] = None,
    config_dir: Optional[Path] = None,
    start_path: Optional[Path] = None,
) -> tuple[Optional[Path], Optional[Path]]:
    """
    Resolve project root_dir and config_dir from available information.
    
    This function consolidates the common pattern of inferring project paths
    across HPO and training scripts. It trusts provided `config_dir` if not None,
    otherwise infers from `output_dir` or `start_path`.
    
    **Key principle**: Trusts provided `config_dir` parameter to avoid re-inference
    when the caller already has the correct value (DRY principle).
    
    Args:
        output_dir: Optional output directory path (e.g., `outputs/hpo/local/distilbert`).
                    Used to infer project root by finding "outputs" directory.
        config_dir: Optional config directory path (e.g., `config/`).
                   If provided, returned directly without inference (trusts caller).
        start_path: Optional starting path for search (fallback if output_dir not available).
    
    Returns:
        Tuple of `(root_dir, config_dir)`. Both may be `None` if inference fails.
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
        
        >>> # Both None if inference fails
        >>> root_dir, config_dir = resolve_project_paths()
        >>> # May return (Path.cwd(), Path.cwd() / "config") as fallback
    """
    # Priority 1: Trust provided config_dir if available
    if config_dir is not None:
        # Derive root_dir from config_dir (config_dir is typically root_dir / "config")
        if config_dir.name == "config" and config_dir.parent.exists():
            root_dir = config_dir.parent
        else:
            # Try to find project root from config_dir location
            root_dir = find_project_root(config_dir=config_dir)
        return root_dir, config_dir
    
    # Priority 2: Infer root_dir from output_dir if available
    root_dir: Optional[Path] = None
    if output_dir is not None:
        try:
            root_dir = find_project_root(output_dir=output_dir)
        except Exception as e:
            logger.debug(f"Could not infer root_dir from output_dir {output_dir}: {e}")
    
    # Priority 3: Infer root_dir from start_path if output_dir didn't work
    if root_dir is None and start_path is not None:
        try:
            root_dir = find_project_root(start_path=start_path)
        except Exception as e:
            logger.debug(f"Could not infer root_dir from start_path {start_path}: {e}")
    
    # Priority 4: Try to infer root_dir from current working directory
    if root_dir is None:
        try:
            root_dir = find_project_root()
        except Exception as e:
            logger.debug(f"Could not infer root_dir from cwd: {e}")
    
    # Derive config_dir from root_dir if we have it
    if root_dir is not None:
        config_dir = root_dir / "config"
        # Verify config_dir exists (or at least root_dir has expected structure)
        if not config_dir.exists():
            logger.debug(
                f"Config directory {config_dir} does not exist, but root_dir {root_dir} was found"
            )
        return root_dir, config_dir
    
    # Fallback: return None for both if all inference strategies failed
    logger.warning(
        "Could not resolve project paths. All inference strategies failed. "
        f"output_dir={output_dir}, start_path={start_path}"
    )
    return None, None






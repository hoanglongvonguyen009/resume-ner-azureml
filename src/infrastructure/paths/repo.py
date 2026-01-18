"""
@meta
name: paths_repo
type: utility
domain: paths
responsibility:
  - Unified repository root detection
  - Repository root validation
inputs:
  - Configuration directories
  - Starting paths
  - Output directories
outputs:
  - Repository root directory paths
tags:
  - utility
  - paths
  - repo
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Unified repository root detection with configurable search strategies.

**Single Source of Truth (SSOT)**:
This module is the SSOT for repository root detection. All call sites should use
`detect_repo_root()` from this module rather than manually searching for repository markers.

**Related Modules**:
- `infrastructure.paths.utils` - Path resolution utilities (uses this module internally)
- `infrastructure.paths.config` - Repository root configuration loading
"""

from pathlib import Path
from typing import Any, Optional

from common.shared.logging_utils import get_logger
from common.shared.platform_detection import detect_platform
from infrastructure.paths.config import load_repository_root_config

logger = get_logger(__name__)

# Module-level cache for detected repository root (if caching enabled)
_detected_root_cache: Optional[Path] = None


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
    # Check cache first (if enabled)
    if _detected_root_cache is not None and _detected_root_cache.exists():
        logger.debug(f"Using cached repository root: {_detected_root_cache}")
        return _detected_root_cache
    
    # Try to load config (may fail if config_dir not provided and we can't find it)
    config: Optional[dict[str, Any]] = None
    config_dir_for_config: Optional[Path] = None
    
    if config_dir is not None:
        try:
            config = load_repository_root_config(config_dir)
            config_dir_for_config = config_dir
        except Exception as e:
            logger.debug(f"Could not load config from provided config_dir {config_dir}: {e}")
    
    # Strategy 1: From config_dir
    if config_dir is not None:
        candidate_root = config_dir.parent if config_dir.name == "config" else config_dir
        if _validate_candidate(candidate_root, config, config_dir_for_config):
            _cache_result(candidate_root, config)
            logger.debug(f"Found repository root from config_dir: {candidate_root}")
            return candidate_root
    
    # Strategy 2: From output_dir - find "outputs" directory, use parent
    if output_dir is not None:
        candidate_root = _find_from_output_dir(output_dir, config, config_dir_for_config)
        if candidate_root is not None:
            _cache_result(candidate_root, config)
            logger.debug(f"Found repository root from output_dir: {candidate_root}")
            return candidate_root
    
    # Strategy 3: From start_path - search up from start_path
    if start_path is not None:
        candidate_root = _find_from_start_path(start_path, config, config_dir_for_config)
        if candidate_root is not None:
            _cache_result(candidate_root, config)
            logger.debug(f"Found repository root from start_path: {candidate_root}")
            return candidate_root
    
    # Strategy 4: Workspace directories (from config)
    if config is None:
        # Try to load config from a potential config_dir we might find
        config, config_dir_for_config = _try_load_config()
    
    if config is not None:
        candidate_root = _find_in_workspace_candidates(config)
        if candidate_root is not None:
            _cache_result(candidate_root, config)
            logger.debug(f"Found repository root in workspace: {candidate_root}")
            return candidate_root
    
    # Strategy 5: Platform-specific repo locations (from config)
    if config is not None:
        candidate_root = _find_in_platform_candidates(config)
        if candidate_root is not None:
            _cache_result(candidate_root, config)
            logger.debug(f"Found repository root in platform location: {candidate_root}")
            return candidate_root
    
    # Strategy 6: Current directory and parents (using markers from base.*)
    candidate_root = _find_from_cwd(config, config_dir_for_config)
    if candidate_root is not None:
        _cache_result(candidate_root, config)
        logger.debug(f"Found repository root from cwd: {candidate_root}")
        return candidate_root
    
    # Strategy 7: Fallback to cwd with warning
    if config is None:
        config, _ = _try_load_config()
    
    fallback_enabled = config.get("search", {}).get("fallback_to_cwd", True) if config else True
    warn_on_fallback = config.get("search", {}).get("warn_on_fallback", True) if config else True
    
    if fallback_enabled:
        cwd = Path.cwd()
        if warn_on_fallback:
            logger.warning(
                f"Could not find repository root. Falling back to current working directory: {cwd}"
            )
        _cache_result(cwd, config)
        return cwd
    
    # All strategies failed and fallback disabled
    raise ValueError(
        "Could not find repository root. All search strategies failed and fallback is disabled."
    )


def validate_repo_root(candidate: Path, config: Optional[dict[str, Any]] = None) -> bool:
    """
    Validate candidate directory is actually repository root.
    
    Prevents false positives in monorepos or nested copies.
    
    Args:
        candidate: Candidate directory to validate.
        config: Optional repository root config (loaded automatically if not provided).
    
    Returns:
        True if candidate is valid repository root, False otherwise.
    
    Validation Rules:
        - Required markers (from base.*): config/ and src/ directories must exist
        - Optional markers (from extra_markers): At least one of .git, pyproject.toml, or setup.cfg
    """
    if not candidate.exists() or not candidate.is_dir():
        return False
    
    # Load config if not provided
    if config is None:
        try:
            # Try to find config_dir from candidate
            potential_config_dir = candidate / "config"
            if potential_config_dir.exists():
                config = load_repository_root_config(potential_config_dir)
            else:
                # Can't validate without config, but check basic markers
                return (candidate / "config").exists() and (candidate / "src").exists()
        except Exception:
            # If we can't load config, fall back to basic validation
            return (candidate / "config").exists() and (candidate / "src").exists()
    
    # Check required markers (from base.*)
    required_markers = config.get("required_markers", ["config", "src"])
    for marker in required_markers:
        marker_path = candidate / marker
        if not marker_path.exists():
            logger.debug(f"Required marker '{marker}' not found in {candidate}")
            return False
    
    # Check optional markers (at least one should exist)
    extra_markers = config.get("extra_markers", [".git", "pyproject.toml"])
    if extra_markers:
        found_extra = False
        for marker in extra_markers:
            marker_path = candidate / marker
            if marker_path.exists():
                found_extra = True
                break
        if not found_extra:
            logger.debug(f"No optional markers found in {candidate} (checked: {extra_markers})")
            # Don't fail validation if no extra markers - they're optional
            # But log it for debugging
    
    return True


def _validate_candidate(
    candidate: Path, config: Optional[dict[str, Any]], config_dir: Optional[Path]
) -> bool:
    """Validate a candidate directory using config if available."""
    if config is not None:
        return validate_repo_root(candidate, config)
    # Fall back to basic validation if config not available
    return (candidate / "config").exists() and (candidate / "src").exists()


def _find_from_output_dir(
    output_dir: Path, config: Optional[dict[str, Any]], config_dir: Optional[Path]
) -> Optional[Path]:
    """Find repository root from output_dir by finding 'outputs' directory."""
    max_depth = config.get("search", {}).get("max_depth", 10) if config else 10
    current = Path(output_dir).resolve()
    depth = 0
    
    while current.parent != current and depth < max_depth:
        if current.name == "outputs" and current.is_dir():
            candidate_root = current.parent
            if _validate_candidate(candidate_root, config, config_dir):
                return candidate_root
        current = current.parent
        depth += 1
    
    return None


def _find_from_start_path(
    start_path: Path, config: Optional[dict[str, Any]], config_dir: Optional[Path]
) -> Optional[Path]:
    """Find repository root by searching up from start_path."""
    max_depth = config.get("search", {}).get("max_depth", 10) if config else 10
    candidate_root = start_path.parent if start_path.is_file() else Path(start_path).resolve()
    depth = 0
    
    while depth < max_depth:
        if _validate_candidate(candidate_root, config, config_dir):
            return candidate_root
        if candidate_root.parent == candidate_root:  # Reached filesystem root
            break
        candidate_root = candidate_root.parent
        depth += 1
    
    return None


def _find_in_workspace_candidates(config: dict[str, Any]) -> Optional[Path]:
    """Find repository root in workspace candidates."""
    workspace_candidates = config.get("workspace_candidates", [])
    for candidate_str in workspace_candidates:
        candidate = Path(candidate_str)
        if candidate.exists() and validate_repo_root(candidate, config):
            return candidate
    return None


def _find_in_platform_candidates(config: dict[str, Any]) -> Optional[Path]:
    """Find repository root in platform-specific candidates."""
    platform = detect_platform()
    platform_candidates = config.get("platform_candidates", {}).get(platform, [])
    
    for candidate_str in platform_candidates:
        candidate = Path(candidate_str)
        if candidate.exists():
            if validate_repo_root(candidate, config):
                return candidate
            # Also check subdirectories (for cases where repo is in subdirectory)
            if candidate.is_dir():
                for subdir in candidate.iterdir():
                    if subdir.is_dir() and validate_repo_root(subdir, config):
                        return subdir
    
    return None


def _find_from_cwd(
    config: Optional[dict[str, Any]], config_dir: Optional[Path]
) -> Optional[Path]:
    """Find repository root by searching up from current working directory."""
    max_depth = config.get("search", {}).get("max_depth", 10) if config else 10
    current = Path.cwd()
    depth = 0
    
    # Check current directory first
    if _validate_candidate(current, config, config_dir):
        return current
    
    # Search up
    while depth < max_depth:
        if current.parent == current:  # Reached filesystem root
            break
        current = current.parent
        if _validate_candidate(current, config, config_dir):
            return current
        depth += 1
    
    return None


def _try_load_config() -> tuple[Optional[dict[str, Any]], Optional[Path]]:
    """Try to load config by searching for config directory."""
    # Try to find config directory from cwd
    current = Path.cwd()
    max_depth = 10
    
    for _ in range(max_depth):
        config_dir = current / "config"
        if config_dir.exists() and config_dir.is_dir():
            try:
                config = load_repository_root_config(config_dir)
                return config, config_dir
            except Exception:
                pass
        if current.parent == current:
            break
        current = current.parent
    
    return None, None


def _cache_result(root: Path, config: Optional[dict[str, Any]]) -> None:
    """Cache detected repository root if caching is enabled."""
    if config is None:
        return
    
    cache_enabled = config.get("cache", {}).get("enabled", True)
    if cache_enabled:
        global _detected_root_cache
        _detected_root_cache = root
        logger.debug(f"Cached repository root: {root}")


"""
@meta
name: notebook_setup
type: utility
domain: shared
responsibility:
  - Detect execution environment (Colab, Kaggle, local)
  - Find repository root directory
  - Setup paths for notebook execution
inputs:
  - Environment variables
  - Current working directory
outputs:
  - Platform information
  - Repository root path
  - Configuration directory path
  - Source directory path
tags:
  - utility
  - shared
  - notebook
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Notebook setup utilities for environment detection and path resolution.

This module provides reusable functions for notebook initialization:
- Platform detection (Colab, Kaggle, local)
- Repository root detection
- Path setup for config and source directories
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from common.shared.platform_detection import detect_platform


@dataclass
class NotebookEnvironment:
    """Notebook execution environment information."""

    platform: str  # 'colab', 'kaggle', 'azure', or 'local'
    is_colab: bool
    is_kaggle: bool
    is_local: bool
    base_dir: Optional[Path]  # Platform-specific base directory (None for local)
    backup_enabled: bool  # Whether backup to Drive is enabled


def detect_notebook_environment() -> NotebookEnvironment:
    """
    Detect notebook execution environment and return environment information.

    Returns:
        NotebookEnvironment with platform detection and platform-specific settings
    """
    platform = detect_platform()
    is_colab = platform == "colab"
    is_kaggle = platform == "kaggle"
    is_local = platform == "local"

    # Set platform-specific base directory
    if is_colab:
        base_dir = Path("/content")
        backup_enabled = True
    elif is_kaggle:
        base_dir = Path("/kaggle/working")
        backup_enabled = False
    else:
        base_dir = None
        backup_enabled = False

    return NotebookEnvironment(
        platform=platform,
        is_colab=is_colab,
        is_kaggle=is_kaggle,
        is_local=is_local,
        base_dir=base_dir,
        backup_enabled=backup_enabled,
    )


def find_repository_root(start_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Backward-compatible wrapper for detect_repo_root().
    
    .. deprecated::
        Use `detect_repo_root()` from `infrastructure.paths.repo` instead.
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


@dataclass
class NotebookPaths:
    """Notebook path configuration."""

    root_dir: Path
    config_dir: Path
    src_dir: Path


def setup_notebook_paths(
    root_dir: Optional[Path] = None, add_src_to_path: bool = True
) -> NotebookPaths:
    """
    Setup notebook paths (root, config, src) and optionally add src to Python path.

    Args:
        root_dir: Repository root directory. If None, will be detected automatically.
        add_src_to_path: Whether to add src_dir to sys.path (default: True).

    Returns:
        NotebookPaths with root_dir, config_dir, and src_dir.

    Raises:
        ValueError: If repository root cannot be found or required directories don't exist.
    """
    # Find repository root if not provided
    if root_dir is None:
        root_dir = find_repository_root()
        if root_dir is None:
            raise ValueError(
                "Could not find repository root. Please ensure you're running from within the repository or a subdirectory."
            )

    root_dir = Path(root_dir).resolve()
    config_dir = root_dir / "config"
    src_dir = root_dir / "src"

    # Verify required directories exist
    if not config_dir.exists():
        raise ValueError(f"Required directory not found: {config_dir}")
    if not src_dir.exists():
        raise ValueError(f"Required directory not found: {src_dir}")

    # Add src to Python path if requested
    if add_src_to_path:
        src_str = str(src_dir)
        if src_str not in sys.path:
            sys.path.insert(0, src_str)

    return NotebookPaths(root_dir=root_dir, config_dir=config_dir, src_dir=src_dir)


def get_platform_vars() -> dict[str, str | bool | Optional[Path]]:
    """
    Get platform variables as a dict (convenience function).

    Returns:
        Dictionary with keys: platform, is_colab, is_kaggle, is_local, base_dir, backup_enabled
    """
    env = detect_notebook_environment()
    return {
        "platform": env.platform,
        "is_colab": env.is_colab,
        "is_kaggle": env.is_kaggle,
        "is_local": env.is_local,
        "base_dir": env.base_dir,
        "backup_enabled": env.backup_enabled,
    }


def ensure_mlflow_installed() -> None:
    """Install mlflow if needed (Colab/Kaggle only)."""
    import subprocess

    env = detect_notebook_environment()
    if not env.is_local:
        try:
            import mlflow  # noqa: F401
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "mlflow", "--quiet"])


def ensure_src_in_path() -> Optional[Path]:
    """
    Ensure src/ is in Python path.

    Returns:
        Repository root Path if found and added to path, None otherwise.
    """
    repo_root = find_repository_root()
    if repo_root is None:
        return None
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    return repo_root


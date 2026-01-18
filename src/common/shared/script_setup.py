"""
@meta
name: script_setup
type: utility
domain: shared
responsibility:
  - Provide shared utilities for script path setup
  - Setup Python path for scripts to enable absolute imports
inputs:
  - Script file path
outputs:
  - Root directory and source directory paths
tags:
  - utility
  - shared
  - script
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Script setup utilities for path configuration.

This module provides reusable functions for script initialization:
- Setup Python path for scripts (add src/ to sys.path)
- Detect repository root directory
- Return root and source directory paths
"""

import sys
from pathlib import Path
from typing import Optional, Tuple


def setup_script_paths(script_file: Optional[Path] = None) -> Tuple[Path, Path]:
    """
    Setup Python path for script execution and return root and source directories.
    
    This function:
    1. Detects repository root directory by searching for marker files (.git, pyproject.toml)
    2. Adds src/ directory to sys.path (if not already present)
    3. Returns (root_dir, src_dir) tuple
    
    Args:
        script_file: Path to the script file. If None, attempts to detect from sys.argv[0].
    
    Returns:
        Tuple of (root_dir, src_dir) Path objects.
    
    Raises:
        ValueError: If repository root cannot be found or src/ directory doesn't exist.
    """
    # Determine starting path
    if script_file is None:
        if len(sys.argv) > 0:
            script_file = Path(sys.argv[0]).resolve()
        else:
            script_file = Path.cwd()
    else:
        script_file = Path(script_file).resolve()
    
    # Detect repository root by looking for marker files
    # Start from script file's directory and walk up
    current = script_file.parent if script_file.is_file() else script_file
    root_dir = None
    
    # Marker files that indicate repository root
    markers = [".git", "pyproject.toml", "setup.py", "README.md"]
    
    while current != current.parent:  # Stop at filesystem root
        # Check if any marker exists
        if any((current / marker).exists() for marker in markers):
            # Verify src/ directory exists
            src_candidate = current / "src"
            if src_candidate.exists() and src_candidate.is_dir():
                root_dir = current
                break
        current = current.parent
    
    if root_dir is None:
        raise ValueError(
            f"Could not find repository root starting from {script_file}. "
            "Please ensure you're running from within the repository."
        )
    
    root_dir = root_dir.resolve()
    src_dir = root_dir / "src"
    
    # Verify src directory exists
    if not src_dir.exists():
        raise ValueError(f"Source directory not found: {src_dir}")
    
    # Add src to Python path if not already present
    src_str = str(src_dir)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)
    
    return root_dir, src_dir


def get_script_root(script_file: Optional[Path] = None) -> Path:
    """
    Get repository root directory for a script.
    
    Args:
        script_file: Path to the script file. If None, attempts to detect from sys.argv[0].
    
    Returns:
        Repository root Path object.
    
    Raises:
        ValueError: If repository root cannot be found.
    """
    root_dir, _ = setup_script_paths(script_file)
    return root_dir


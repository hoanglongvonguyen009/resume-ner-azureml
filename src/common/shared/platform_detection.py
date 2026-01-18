"""
@meta
name: shared_platform_detection
type: utility
domain: shared
responsibility:
  - Detect execution platform (Colab, Kaggle, Azure, local)
  - Resolve platform-specific checkpoint paths
inputs:
  - Environment variables
outputs:
  - Platform identifiers
  - Resolved checkpoint paths
tags:
  - utility
  - shared
  - platform
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Platform detection utilities for Colab, Kaggle, and local environments."""

import os
from pathlib import Path
from typing import Optional

# Platform-specific path constants (fixed by platforms)
# These paths are determined by the platform environments and should not be changed
COLAB_DRIVE_MOUNT = Path("/content/drive/MyDrive")
COLAB_CONTENT_DIR = Path("/content")
KAGGLE_WORKING_DIR = Path("/kaggle/working")
DRIVE_PATH_PREFIX = "/content/drive"

# Legacy checkpoint directory (deprecated - kept for migration purposes)
# TODO: Remove after confirming no old Colab runs use this path
LEGACY_CHECKPOINT_DIR = "resume-ner-checkpoints"

# Default project name (fallback if config not available)
DEFAULT_PROJECT_NAME = "resume-ner-azureml"


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
        if f"/{DEFAULT_PROJECT_NAME}" in base_str:
            return DEFAULT_PROJECT_NAME

    # Last resort: default constant
    return DEFAULT_PROJECT_NAME


def detect_platform() -> str:
    """
    Detect execution platform: 'colab', 'kaggle', 'azure', or 'local'.

    Returns:
        Platform identifier string: 'colab', 'kaggle', 'azure', or 'local'
    """
    # Check for Google Colab
    if "COLAB_GPU" in os.environ or "COLAB_TPU" in os.environ:
        return "colab"

    # Check for Kaggle
    if "KAGGLE_KERNEL_RUN_TYPE" in os.environ:
        return "kaggle"

    # Check for Azure ML
    if "AZURE_ML_RUN_ID" in os.environ or "AZURE_ML_OUTPUT_DIR" in os.environ:
        return "azure"

    # Default to local
    return "local"


def resolve_platform_checkpoint_path(
    base_path: Path,
    relative_path: str,
    config_dir: Optional[Path] = None,
) -> Path:
    """
    Resolve checkpoint path with platform-specific optimizations.

    For Colab: Prefers Drive mount path if available (/content/drive/MyDrive/...)
               Preserves directory structure relative to project root
    For Kaggle: Uses /kaggle/working/ (automatically persisted)
    For Local: Uses provided base path

    Args:
        base_path: Base path for checkpoint storage
        relative_path: Relative path from base (e.g., "hpo/distilbert/study.db")
        config_dir: Optional config directory to load project name from paths.yaml.
                   If not provided, attempts to infer from base_path.

    Returns:
        Resolved absolute Path for checkpoint storage
    """
    platform = detect_platform()

    if platform == "colab":
        # Check if Google Drive is mounted
        if COLAB_DRIVE_MOUNT.exists() and COLAB_DRIVE_MOUNT.is_dir():
            # Preserve directory structure relative to project root
            # Map /content/resume-ner-azureml/... to /content/drive/MyDrive/resume-ner-azureml/...
            base_str = str(base_path)
            project_name = _get_project_name_from_config(config_dir, base_path)
            project_name_with_slash = f"/{project_name}"

            # Try to detect project root (common patterns: /content/resume-ner-azureml, /content/...)
            if project_name_with_slash in base_str:
                # Extract path relative to /content/resume-ner-azureml
                # e.g., /content/resume-ner-azureml/outputs/hpo/colab/distilbert
                # -> outputs/hpo/colab/distilbert
                if base_str.endswith(project_name_with_slash) or base_str.endswith(f"{project_name_with_slash}/"):
                    # Base path is exactly the project root
                    drive_base = COLAB_DRIVE_MOUNT / project_name
                    return drive_base / relative_path
                else:
                    # Base path has subdirectories under project root
                    parts = base_str.split(f"{project_name_with_slash}/")
                    if len(parts) == 2 and parts[1]:
                        # Project root is /content/resume-ner-azureml
                        project_relative = parts[1]
                        # Map to Drive: /content/drive/MyDrive/resume-ner-azureml/...
                        drive_base = COLAB_DRIVE_MOUNT / project_name / project_relative
                        return drive_base / relative_path
                    else:
                        # Fallback: use full path from /content
                        # e.g., /content/resume-ner-azureml -> /content/drive/MyDrive/resume-ner-azureml
                        content_prefix = f"{COLAB_CONTENT_DIR}/"
                        if base_str.startswith(content_prefix):
                            content_relative = base_str[len(content_prefix):]
                            drive_base = COLAB_DRIVE_MOUNT / content_relative
                            return drive_base / relative_path

            # Fallback: if base_path is under /content, preserve structure
            content_prefix = f"{COLAB_CONTENT_DIR}/"
            if base_str.startswith(content_prefix):
                content_relative = base_str[len(content_prefix):]
                drive_base = COLAB_DRIVE_MOUNT / content_relative
                return drive_base / relative_path
            else:
                # Legacy fallback (deprecated - kept for migration)
                # TODO: Remove after confirming no old Colab runs use legacy checkpoint paths
                checkpoint_base = COLAB_DRIVE_MOUNT / LEGACY_CHECKPOINT_DIR
                return checkpoint_base / relative_path
        else:
            # Fallback to /content/ if Drive not mounted
            return COLAB_CONTENT_DIR / relative_path

    elif platform == "kaggle":
        # Kaggle outputs in /kaggle/working/ are automatically persisted
        # If base_path is already under /kaggle/working, use it
        base_str = str(base_path)
        kaggle_prefix = str(KAGGLE_WORKING_DIR)
        if base_str.startswith(kaggle_prefix):
            return base_path / relative_path
        else:
            # Otherwise, use /kaggle/working as base
            return KAGGLE_WORKING_DIR / relative_path

    else:
        # Local: use provided base path
        return base_path / relative_path


def is_drive_path(path: Path | str) -> bool:
    """
    Check if a path is already in Google Drive.

    This utility function detects if a path string represents a Google Drive path
    (starts with `/content/drive`). Useful for avoiding redundant Drive operations
    when paths are already mapped to Drive.

    Args:
        path: Path to check (can be Path object or string).

    Returns:
        True if path is in Google Drive (absolute path starting with `/content/drive`),
        False otherwise (local paths, relative paths, or non-Drive paths).

    Raises:
        TypeError: If path is None.

    Examples:
        >>> is_drive_path("/content/drive/MyDrive/resume-ner-azureml/outputs/hpo/study.db")
        True
        >>> is_drive_path(Path("/content/drive/MyDrive/resume-ner-azureml/outputs/hpo/study.db"))
        True
        >>> is_drive_path("/content/resume-ner-azureml/outputs/hpo/study.db")
        False
        >>> is_drive_path("outputs/hpo/study.db")
        False
        >>> is_drive_path(None)
        Traceback (most recent call last):
            ...
        TypeError: path cannot be None
    """
    if path is None:
        raise TypeError("path cannot be None")

    # Convert Path to string if needed
    path_str = str(path) if isinstance(path, Path) else path

    # Only check absolute paths (relative paths are not Drive paths)
    if not path_str.startswith("/"):
        return False

    # Check if path is in Google Drive
    return path_str.startswith(DRIVE_PATH_PREFIX)

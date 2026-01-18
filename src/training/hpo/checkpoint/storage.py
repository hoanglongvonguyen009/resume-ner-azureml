"""
@meta
name: checkpoint_storage
type: utility
domain: hpo
responsibility:
  - Checkpoint manager for HPO study persistence
  - Resolve checkpoint storage paths with platform awareness
inputs:
  - Output directories
  - Checkpoint configuration
  - Backbone names
outputs:
  - Resolved checkpoint storage paths
tags:
  - utility
  - hpo
  - checkpoint
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Checkpoint manager for HPO study persistence."""

from pathlib import Path
from typing import Any, Dict, Optional

from common.shared.platform_detection import detect_platform, resolve_platform_checkpoint_path


def resolve_storage_path(
    output_dir: Path,
    checkpoint_config: Dict[str, Any],
    backbone: str,
    study_key_hash: str,
    study_name: Optional[str] = None,
    create_dirs: bool = True,
) -> Optional[Path]:
    """
    Resolve checkpoint storage path with platform awareness.

    Uses v2 hash-based folder structure (study-{hash}). Legacy study_name format
    is no longer supported.

    Args:
        output_dir: Base output directory for HPO trials
        checkpoint_config: Checkpoint configuration from HPO config
        backbone: Model backbone name (for placeholder substitution)
        study_key_hash: Study key hash for v2 folder structure (study-{hash}) - REQUIRED
        study_name: Optional resolved study name (deprecated, kept for compatibility)
        create_dirs: Whether to create parent directories (default: True)
                    Set to False for read-only path resolution

    Returns:
        Resolved Path for checkpoint storage, or None if checkpointing disabled

    Raises:
        ValueError: If study_key_hash is not provided
    """
    # Check if checkpointing is enabled
    enabled = checkpoint_config.get("enabled", False)
    if not enabled:
        return None

    # Require study_key_hash for v2 folder structure
    if not study_key_hash:
        raise ValueError(
            "study_key_hash is required for v2 folder structure. "
            "Legacy study_name format is no longer supported."
        )

    # Compute study8 token (first 8 characters of hash)
    study8 = study_key_hash[:8] if len(study_key_hash) >= 8 else study_key_hash
    # Build v2 path: {backbone}/study-{study8}/study.db
    storage_path_str = f"{backbone}/study-{study8}/study.db"

    # Resolve with platform-specific optimizations
    platform = detect_platform()
    storage_path = resolve_platform_checkpoint_path(output_dir, storage_path_str)

    # Ensure parent directory exists (only if create_dirs is True)
    if create_dirs:
        storage_path.parent.mkdir(parents=True, exist_ok=True)

    return storage_path


def get_storage_uri(storage_path: Optional[Path]) -> Optional[str]:
    """
    Convert storage path to Optuna storage URI.

    Args:
        storage_path: Path to SQLite database file, or None for in-memory

    Returns:
        Optuna storage URI string (e.g., "sqlite:///path/to/study.db"), or None
    """
    if storage_path is None:
        return None

    # Convert to absolute path and use 3 slashes for absolute paths
    abs_path = storage_path.resolve()
    return f"sqlite:///{abs_path}"

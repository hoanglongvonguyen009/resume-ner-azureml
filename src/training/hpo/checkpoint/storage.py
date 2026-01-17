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
    study_name: Optional[str] = None,
    study_key_hash: Optional[str] = None,
    create_dirs: bool = True,
) -> Optional[Path]:
    """
    Resolve checkpoint storage path with platform awareness.

    Supports both v2 hash-based folder structure (study-{hash}) and legacy
    study_name format. When study_key_hash is provided, uses v2 structure.
    Otherwise falls back to legacy study_name format for backward compatibility.

    Args:
        output_dir: Base output directory for HPO trials
        checkpoint_config: Checkpoint configuration from HPO config
        backbone: Model backbone name (for placeholder substitution)
        study_name: Optional resolved study name (for {study_name} placeholder in legacy mode)
        study_key_hash: Optional study key hash for v2 folder structure (study-{hash})
        create_dirs: Whether to create parent directories (default: True)
                    Set to False for read-only path resolution

    Returns:
        Resolved Path for checkpoint storage, or None if checkpointing disabled
    """
    # Check if checkpointing is enabled
    enabled = checkpoint_config.get("enabled", False)
    if not enabled:
        return None

    # V2 mode: Use hash-based folder structure when study_key_hash is provided
    if study_key_hash:
        # Compute study8 token (first 8 characters of hash)
        study8 = study_key_hash[:8] if len(study_key_hash) >= 8 else study_key_hash
        # Build v2 path: {backbone}/study-{study8}/study.db
        storage_path_str = f"{backbone}/study-{study8}/study.db"
    else:
        # Legacy mode: Use study_name format
        # Get storage path from config or use default
        storage_path_template = checkpoint_config.get(
            "storage_path",
            f"{{backbone}}/study.db"  # Default: relative to output_dir
        )

        # Replace placeholders in order: {backbone} first, then {study_name}
        storage_path_str = storage_path_template.replace("{backbone}", backbone)
        if study_name:
            storage_path_str = storage_path_str.replace("{study_name}", study_name)

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

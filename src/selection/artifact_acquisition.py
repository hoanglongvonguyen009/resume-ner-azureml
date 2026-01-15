"""
@meta
name: artifact_acquisition
type: utility
domain: selection
responsibility:
  - Artifact acquisition utilities for best model selection
  - Checkpoint acquisition with local-first priority
  - Checkpoint validation and Azure ML compatibility
inputs:
  - Best run information
  - Acquisition configuration
  - MLflow run IDs
outputs:
  - Checkpoint directory paths
tags:
  - utility
  - selection
  - artifacts
  - mlflow
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Artifact acquisition utilities for best model selection.

DEPRECATED: This module is a backward-compatibility wrapper around
`evaluation.selection.artifact_acquisition`. Use `evaluation.selection.artifact_acquisition`
directly for new code.

This module will be removed in a future release.

This module provides robust checkpoint acquisition with local-first priority,
checkpoint validation, and graceful handling of Azure ML compatibility issues.

NOTE: Both this module and `evaluation.selection.artifact_acquisition` now use
the unified artifact acquisition system (`evaluation.selection.artifact_unified.compat`)
under the hood. The API remains the same for backward compatibility.
"""

import warnings
from pathlib import Path
from typing import Any, Dict, Optional, Callable

from .types import BestModelInfo

# Import from SSOT
from evaluation.selection import artifact_acquisition as _eval_artifact_acquisition


def acquire_best_model_checkpoint(
    best_run_info: BestModelInfo,
    root_dir: Path,
    config_dir: Path,
    acquisition_config: Dict[str, Any],
    selection_config: Dict[str, Any],
    platform: str,
    restore_from_drive: Optional[Callable[[Path, bool], bool]] = None,
    drive_store: Optional[Any] = None,
    in_colab: bool = False,
) -> Path:
    """
    Acquire checkpoint using unified acquisition system (backward compatibility wrapper).

    DEPRECATED: Use `evaluation.selection.artifact_acquisition.acquire_best_model_checkpoint`
    directly instead.

    This function now uses the unified artifact acquisition system under the hood.
    The API remains the same for backward compatibility.

    Priority order (from config):
    1. Local disk (by config + backbone) - PREFERRED to avoid Azure ML issues
    2. Drive restore (Colab only) - scans Drive metadata, restores only checkpoint
    3. MLflow download

    Args:
        best_run_info: Dictionary with best run information (must include study_key_hash, trial_key_hash, run_id, backbone)
        root_dir: Project root directory
        config_dir: Config directory
        acquisition_config: Artifact acquisition configuration
        selection_config: Best model selection configuration
        platform: Platform name (local, colab, kaggle)
        restore_from_drive: Optional function to restore from Drive backup
        drive_store: Optional DriveBackupStore instance for direct Drive access
        in_colab: Whether running in Google Colab

    Returns:
        Path to validated checkpoint directory

    Raises:
        ValueError: If all fallback strategies fail
    """
    warnings.warn(
        "selection.artifact_acquisition is deprecated. "
        "Use evaluation.selection.artifact_acquisition instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Convert BestModelInfo TypedDict to Dict[str, Any] for evaluation version
    best_run_info_dict: Dict[str, Any] = dict(best_run_info)  # type: ignore[arg-type]

    return _eval_artifact_acquisition.acquire_best_model_checkpoint(
        best_run_info=best_run_info_dict,
        root_dir=root_dir,
        config_dir=config_dir,
        acquisition_config=acquisition_config,
        selection_config=selection_config,
        platform=platform,
        restore_from_drive=restore_from_drive,
        drive_store=drive_store,
        in_colab=in_colab,
    )

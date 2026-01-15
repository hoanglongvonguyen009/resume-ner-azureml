from __future__ import annotations

"""
@meta
name: local_selection_v2
type: utility
domain: selection
responsibility:
  - Improved best configuration selection from local Optuna HPO studies
  - Config-aware study folder discovery
  - CV-based trial selection with deterministic fold ordering
inputs:
  - HPO study directories
  - HPO configuration
  - Trial metadata files
outputs:
  - Best selected configuration
tags:
  - utility
  - selection
  - hpo
  - optuna
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Improved best configuration selection from local Optuna HPO studies.

DEPRECATED: This module is a backward-compatibility wrapper around
`evaluation.selection.local_selection_v2`. Use `evaluation.selection.local_selection_v2`
directly for new code.

This module will be removed in a future release.

This module provides config-aware study folder discovery and CV-based trial selection.
It replaces the previous approach with:
- Config pattern matching for study folders
- CV-only trial selection (refit used only as artifact)
- Deterministic fold ordering
- Safe version parsing
- Fast path via .active_study.json marker files
"""

import warnings
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .types import TrialInfo

# Import from SSOT
from evaluation.selection import local_selection_v2 as _eval_local_selection_v2

# Re-export constant for backward compatibility
# Note: evaluation version uses private _INVALID_FOLD_INDEX, but we keep public constant
FOLD_INDEX_NOT_FOUND = 10**9


def parse_version_from_name(name: str) -> Optional[Tuple[int, int, int]]:
    """
    Parse version from folder name like 'hpo_distilbert_smoke_test_3.69' or 'hpo_distilbert_smoke_test_3.69_1'.

    DEPRECATED: Use `evaluation.selection.local_selection_v2.parse_version_from_name`
    directly instead.

    Returns:
        Tuple of (major, minor, suffix) or None if no version found.
        suffix is -1 if not present.
    """
    warnings.warn(
        "selection.local_selection_v2 is deprecated. "
        "Use evaluation.selection.local_selection_v2 instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    return _eval_local_selection_v2.parse_version_from_name(name=name)


def fold_index(name: str) -> int:
    """
    Extract numeric fold index from folder name (e.g., 'fold0' -> 0, 'fold10' -> 10).

    DEPRECATED: Use `evaluation.selection.local_selection_v2.fold_index`
    directly instead.

    Args:
        name: Folder name containing fold identifier

    Returns:
        Numeric fold index, or FOLD_INDEX_NOT_FOUND if not found
    """
    warnings.warn(
        "selection.local_selection_v2 is deprecated. "
        "Use evaluation.selection.local_selection_v2 instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    return _eval_local_selection_v2.fold_index(name=name)


def find_study_folder_by_config(
    backbone_dir: Path,
    hpo_config: Dict[str, Any],
    backbone: str
) -> Optional[Path]:
    """
    Find study folder matching the study name pattern from HPO config.

    DEPRECATED: Use `evaluation.selection.local_selection_v2.find_study_folder_by_config`
    directly instead.

    Args:
        backbone_dir: Backbone directory containing study folders
        hpo_config: HPO configuration dictionary
        backbone: Model backbone name

    Returns:
        Study folder with highest version matching the config pattern, or None if not found
    """
    warnings.warn(
        "selection.local_selection_v2 is deprecated. "
        "Use evaluation.selection.local_selection_v2 instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    return _eval_local_selection_v2.find_study_folder_by_config(
        backbone_dir=backbone_dir,
        hpo_config=hpo_config,
        backbone=backbone,
    )


def load_best_trial_from_study_folder(
    study_folder: Path,
    objective_metric: str = "macro-f1",
) -> Optional[TrialInfo]:
    """
    Load best trial from a specific study folder.

    DEPRECATED: Use `evaluation.selection.local_selection_v2.load_best_trial_from_study_folder`
    directly instead.

    IMPORTANT: Selects best trial based on CV metrics ONLY (not refit).
    Refit is only used as the preferred checkpoint artifact after selection.

    Args:
        study_folder: Path to study folder (e.g., outputs/hpo/colab/distilbert/hpo_distilbert_smoke_test_3.69)
        objective_metric: Name of the objective metric

    Returns:
        TrialInfo dict with best trial info, or None if not found
    """
    warnings.warn(
        "selection.local_selection_v2 is deprecated. "
        "Use evaluation.selection.local_selection_v2 instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    result = _eval_local_selection_v2.load_best_trial_from_study_folder(
        study_folder=study_folder,
        objective_metric=objective_metric,
    )
    
    # Convert return type from Dict[str, Any] to TrialInfo TypedDict
    if result is None:
        return None
    
    return TrialInfo(**result)  # type: ignore[arg-type]


def write_active_study_marker(
    backbone_dir: Path,
    study_folder: Path,
    study_name: str,
    study_key_hash: Optional[str] = None
) -> None:
    """
    Write .active_study.json marker file for fast lookup.

    DEPRECATED: Use `evaluation.selection.local_selection_v2.write_active_study_marker`
    directly instead.

    This makes finding the current study folder instant and unambiguous.

    Args:
        backbone_dir: Backbone directory where marker should be written
        study_folder: Path to the study folder
        study_name: Name of the study
        study_key_hash: Optional study key hash for tracking
    """
    warnings.warn(
        "selection.local_selection_v2 is deprecated. "
        "Use evaluation.selection.local_selection_v2 instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    return _eval_local_selection_v2.write_active_study_marker(
        backbone_dir=backbone_dir,
        study_folder=study_folder,
        study_name=study_name,
        study_key_hash=study_key_hash,
    )


def find_trial_checkpoint_by_hash(
    hpo_backbone_dir: Path,
    study_key_hash: str,
    trial_key_hash: str,
) -> Optional[Path]:
    """
    Find trial checkpoint by study_key_hash and trial_key_hash.

    DEPRECATED: Use `evaluation.selection.local_selection_v2.find_trial_checkpoint_by_hash`
    directly instead.

    Scans trial folders and reads trial_meta.json files to match by hash.
    This avoids Optuna DB dependencies and hash recomputation issues.

    Args:
        hpo_backbone_dir: Backbone directory containing study folders
        study_key_hash: Target study key hash (64 hex chars)
        trial_key_hash: Target trial key hash (64 hex chars)

    Returns:
        Path to checkpoint directory (prefers refit, else best CV fold), or None if not found
    """
    warnings.warn(
        "selection.local_selection_v2 is deprecated. "
        "Use evaluation.selection.local_selection_v2 instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    return _eval_local_selection_v2.find_trial_checkpoint_by_hash(
        hpo_backbone_dir=hpo_backbone_dir,
        study_key_hash=study_key_hash,
        trial_key_hash=trial_key_hash,
    )

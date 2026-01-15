"""
@meta
name: trial_finder
type: utility
domain: selection
responsibility:
  - Find best trials from HPO studies or disk
  - Extract trial information from Optuna studies
  - Locate trial directories by hash or number
inputs:
  - Optuna study objects
  - HPO output directories
  - Trial metadata files
outputs:
  - Best trial information dictionaries
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

"""Find best trials from HPO studies or disk.

DEPRECATED: This module is a backward-compatibility wrapper around
`evaluation.selection.trial_finder`. Use `evaluation.selection.trial_finder`
directly for new code.

This module will be removed in a future release.

This module provides utilities to locate and extract best trial information
from Optuna studies or from saved outputs on disk.
"""

import warnings
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING

from .types import TrialInfo

# Import from SSOT
from evaluation.selection import trial_finder as _eval_trial_finder

if TYPE_CHECKING:
    from optuna import Study

# Re-export all public functions with type conversions where needed

def find_best_trial_in_study_folder(
    study_folder: Path,
    objective_metric: str = "macro-f1",
) -> Optional[TrialInfo]:
    """
    Find best trial in a specific study folder by reading metrics.json files.

    DEPRECATED: Use `evaluation.selection.trial_finder.find_best_trial_in_study_folder`
    directly instead.

    Args:
        study_folder: Path to study folder containing trials
        objective_metric: Name of the objective metric to optimize

    Returns:
        TrialInfo dict with best trial info, or None if no trials found
    """
    warnings.warn(
        "selection.trial_finder is deprecated. "
        "Use evaluation.selection.trial_finder instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    result = _eval_trial_finder.find_best_trial_in_study_folder(
        study_folder=study_folder,
        objective_metric=objective_metric,
    )
    
    # Convert return type from Dict[str, Any] to TrialInfo TypedDict
    if result is None:
        return None
    
    return TrialInfo(**result)  # type: ignore[arg-type]


def format_trial_identifier(trial_dir: Path, trial_number: Optional[int] = None) -> str:
    """
    Format trial identifier using hash-based naming if available.

    DEPRECATED: Use `evaluation.selection.trial_finder.format_trial_identifier`
    directly instead.

    Args:
        trial_dir: Path to trial directory
        trial_number: Optional trial number to include in identifier

    Returns:
        Formatted identifier string
    """
    warnings.warn(
        "selection.trial_finder is deprecated. "
        "Use evaluation.selection.trial_finder instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    return _eval_trial_finder.format_trial_identifier(
        trial_dir=trial_dir,
        trial_number=trial_number,
    )


def find_study_folder_in_backbone_dir(backbone_dir: Path) -> Optional[Path]:
    """
    Find v2 study folder inside backbone directory.

    DEPRECATED: Use `evaluation.selection.trial_finder.find_study_folder_in_backbone_dir`
    directly instead.

    Args:
        backbone_dir: Backbone directory containing study folders

    Returns:
        Path to study folder if found, else None
    """
    warnings.warn(
        "selection.trial_finder is deprecated. "
        "Use evaluation.selection.trial_finder instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    return _eval_trial_finder.find_study_folder_in_backbone_dir(backbone_dir=backbone_dir)


def find_best_trial_from_study(
    study: "Study",
    backbone_name: str,
    dataset_version: str,
    objective_metric: str,
    hpo_backbone_dir: Path,
    hpo_config: Optional[Dict[str, Any]] = None,
    data_config: Optional[Dict[str, Any]] = None,
) -> Optional[TrialInfo]:
    """
    Find best trial from an Optuna study object.

    DEPRECATED: Use `evaluation.selection.trial_finder.find_best_trial_from_study`
    directly instead.

    Args:
        study: Optuna study object
        backbone_name: Model backbone name
        dataset_version: Dataset version string
        objective_metric: Objective metric name
        hpo_backbone_dir: HPO backbone output directory
        hpo_config: HPO configuration (needed to compute trial_key_hash)
        data_config: Data configuration (needed to compute trial_key_hash)

    Returns:
        TrialInfo dict with best trial info, or None if not found
    """
    warnings.warn(
        "selection.trial_finder is deprecated. "
        "Use evaluation.selection.trial_finder instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    result = _eval_trial_finder.find_best_trial_from_study(
        study=study,  # type: ignore[arg-type]
        backbone_name=backbone_name,
        dataset_version=dataset_version,
        objective_metric=objective_metric,
        hpo_backbone_dir=hpo_backbone_dir,
        hpo_config=hpo_config,
        data_config=data_config,
    )
    
    # Convert return type from Dict[str, Any] to TrialInfo TypedDict
    if result is None:
        return None
    
    return TrialInfo(**result)  # type: ignore[arg-type]


def find_best_trials_for_backbones(
    backbone_values: list[str],
    hpo_studies: Optional[Dict[str, "Study"]],
    hpo_config: Dict[str, Any],
    data_config: Dict[str, Any],
    root_dir: Path,
    environment: str,
) -> Dict[str, TrialInfo]:
    """
    Find best trials for multiple backbones.

    DEPRECATED: Use `evaluation.selection.trial_finder.find_best_trials_for_backbones`
    directly instead.

    Args:
        backbone_values: List of backbone names
        hpo_studies: Optional dictionary mapping backbone -> Optuna study
        hpo_config: HPO configuration dictionary
        data_config: Data configuration dictionary
        root_dir: Project root directory
        environment: Platform environment (e.g., "local", "colab")

    Returns:
        Dictionary mapping backbone -> TrialInfo dict
    """
    warnings.warn(
        "selection.trial_finder is deprecated. "
        "Use evaluation.selection.trial_finder instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    result = _eval_trial_finder.find_best_trials_for_backbones(
        backbone_values=backbone_values,
        hpo_studies=hpo_studies,  # type: ignore[arg-type]
        hpo_config=hpo_config,
        data_config=data_config,
        root_dir=root_dir,
        environment=environment,
    )
    
    # Convert return type from Dict[str, Dict[str, Any]] to Dict[str, TrialInfo]
    return {k: TrialInfo(**v) for k, v in result.items()}  # type: ignore[arg-type]

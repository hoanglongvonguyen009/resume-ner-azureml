from __future__ import annotations

"""
@meta
name: study_summary
type: utility
domain: selection
responsibility:
  - Display and summarize HPO study results
  - Load Optuna studies from disk
  - Format trial summaries for display
inputs:
  - Optuna study objects
  - HPO output directories
  - Trial metadata files
outputs:
  - Formatted study summaries
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

"""Utilities for displaying and summarizing HPO study results.

DEPRECATED: This module is a backward-compatibility wrapper around
`evaluation.selection.study_summary`. Use `evaluation.selection.study_summary`
directly for new code.

This module will be removed in a future release.

This module provides functions to load Optuna studies, extract trial information,
and format summaries for display in notebooks or logs.
"""

import warnings
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING

# Import from SSOT
from evaluation.selection import study_summary as _eval_study_summary

if TYPE_CHECKING:
    from optuna import Study, Trial


def extract_cv_statistics(best_trial: "Trial") -> Optional[Tuple[float, float]]:
    """
    Extract CV statistics from Optuna trial user attributes.

    DEPRECATED: Use `evaluation.selection.study_summary.extract_cv_statistics`
    directly instead.

    Args:
        best_trial: Optuna trial object with user_attrs.

    Returns:
        Tuple of (cv_mean, cv_std) if available, else None.
    """
    warnings.warn(
        "selection.study_summary is deprecated. "
        "Use evaluation.selection.study_summary instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    # Type cast: selection version expects Trial, evaluation version accepts Any
    return _eval_study_summary.extract_cv_statistics(best_trial=best_trial)  # type: ignore[arg-type]


def get_trial_hash_info(trial_dir: Path) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    """
    Extract study_key_hash, trial_key_hash, and trial_number from trial_meta.json if available.

    DEPRECATED: Use `evaluation.selection.study_summary.get_trial_hash_info`
    directly instead.

    Args:
        trial_dir: Path to trial directory containing trial_meta.json.

    Returns:
        Tuple of (study_key_hash, trial_key_hash, trial_number), or (None, None, None) if not found.
    """
    warnings.warn(
        "selection.study_summary is deprecated. "
        "Use evaluation.selection.study_summary instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    return _eval_study_summary.get_trial_hash_info(trial_dir=trial_dir)


def load_study_from_disk(
    backbone_name: str,
    root_dir: Path,
    environment: str,
    hpo_config: Dict[str, Any],
) -> Optional["Study"]:
    """
    Load Optuna study from disk if not in memory.

    DEPRECATED: Use `evaluation.selection.study_summary.load_study_from_disk`
    directly instead.

    Args:
        backbone_name: Model backbone name (e.g., "distilbert" or "distilbert-base-uncased").
        root_dir: Project root directory.
        environment: Platform environment (e.g., "local", "colab").
        hpo_config: HPO configuration dictionary.

    Returns:
        Optuna study object if found, else None.
    """
    warnings.warn(
        "selection.study_summary is deprecated. "
        "Use evaluation.selection.study_summary instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    result = _eval_study_summary.load_study_from_disk(
        backbone_name=backbone_name,
        root_dir=root_dir,
        environment=environment,
        hpo_config=hpo_config,
    )
    
    # Type cast: evaluation version returns Optional[Any], selection version expects Optional[Study]
    return result  # type: ignore[return-value]


def find_trial_hash_info_for_study(
    backbone_name: str,
    trial_number: int,
    root_dir: Path,
    environment: str,
) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    """
    Find trial hash info for a specific trial number in a study.

    DEPRECATED: Use `evaluation.selection.study_summary.find_trial_hash_info_for_study`
    directly instead.

    Args:
        backbone_name: Model backbone name (e.g., "distilbert" or "distilbert-base-uncased").
        trial_number: Optuna trial number.
        root_dir: Project root directory.
        environment: Platform environment (e.g., "local", "colab").

    Returns:
        Tuple of (study_key_hash, trial_key_hash, trial_number), or (None, None, None) if not found.
    """
    warnings.warn(
        "selection.study_summary is deprecated. "
        "Use evaluation.selection.study_summary instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    return _eval_study_summary.find_trial_hash_info_for_study(
        backbone_name=backbone_name,
        trial_number=trial_number,
        root_dir=root_dir,
        environment=environment,
    )


def format_study_summary_line(
    backbone: str,
    num_trials: int,
    best_metric_value: float,
    objective_metric: str,
    study_key_hash: Optional[str] = None,
    trial_key_hash: Optional[str] = None,
    trial_number: Optional[int] = None,
    cv_stats: Optional[Tuple[float, float]] = None,
) -> str:
    """
    Format a single line summary for an HPO study.

    DEPRECATED: Use `evaluation.selection.study_summary.format_study_summary_line`
    directly instead.

    Note: The evaluation version has an additional `from_disk` parameter that is not
    exposed in this wrapper. If you need that functionality, use the evaluation version directly.

    Args:
        backbone: Model backbone name.
        num_trials: Number of trials in the study.
        best_metric_value: Best metric value from the study.
        objective_metric: Name of the objective metric.
        study_key_hash: Optional study key hash (first 8 chars).
        trial_key_hash: Optional trial key hash (first 8 chars).
        trial_number: Optional trial number.
        cv_stats: Optional tuple of (cv_mean, cv_std).

    Returns:
        Formatted summary line string.
    """
    warnings.warn(
        "selection.study_summary is deprecated. "
        "Use evaluation.selection.study_summary instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    # Note: evaluation version has `from_disk` parameter, but we don't expose it here
    # to maintain backward compatibility with selection API
    return _eval_study_summary.format_study_summary_line(
        backbone=backbone,
        num_trials=num_trials,
        best_metric_value=best_metric_value,
        objective_metric=objective_metric,
        study_key_hash=study_key_hash,
        trial_key_hash=trial_key_hash,
        trial_number=trial_number,
        cv_stats=cv_stats,
        from_disk=False,  # Default value for backward compatibility
    )


def print_study_summaries(
    hpo_studies: Optional[Dict[str, "Study"]],
    backbone_values: list[str],
    hpo_config: Dict[str, Any],
    root_dir: Path,
    environment: str,
) -> None:
    """
    Print formatted summaries for HPO studies.

    DEPRECATED: Use `evaluation.selection.study_summary.print_study_summaries`
    directly instead.

    Processes both in-memory studies and studies loaded from disk,
    displaying hash-based identifiers and CV statistics when available.

    Args:
        hpo_studies: Optional dictionary mapping backbone -> Optuna study.
        backbone_values: List of backbone model names to process.
        hpo_config: HPO configuration dictionary.
        root_dir: Project root directory.
        environment: Platform environment (e.g., "local", "colab").
    """
    warnings.warn(
        "selection.study_summary is deprecated. "
        "Use evaluation.selection.study_summary instead. "
        "This module will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    # Type cast: selection version expects Dict[str, Study], evaluation version accepts Dict[str, Any]
    hpo_studies_any: Optional[Dict[str, Any]] = hpo_studies  # type: ignore[assignment]
    
    return _eval_study_summary.print_study_summaries(
        hpo_studies=hpo_studies_any,
        backbone_values=backbone_values,
        hpo_config=hpo_config,
        root_dir=root_dir,
        environment=environment,
    )

from __future__ import annotations

"""
@meta
name: tag_helpers
type: utility
domain: training
responsibility:
  - Add training-specific tags to MLflow runs
  - Handle lineage tags for final training from HPO
inputs:
  - Base tags from build_mlflow_tags()
  - Lineage dictionaries
  - Config directories
outputs:
  - Combined tags dictionaries
tags:
  - utility
  - training
  - mlflow
  - tags
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Tag building helpers for training execution.

This module provides consolidated tag building logic for training runs.
It handles both simple training tags and complex lineage tags for final
training runs that originate from HPO.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def add_training_tags(
    tags: Dict[str, str],
    training_type: str = "final",
    config_dir: Optional[Path] = None,
) -> Dict[str, str]:
    """
    Add simple training tags to base tags dictionary.

    Args:
        tags: Base tags dictionary (from `build_mlflow_tags()`).
        training_type: Type of training ("final" or "continued").
        config_dir: Optional config directory (for tag key retrieval).

    Returns:
        Combined tags dictionary with training tags added.

    Examples:
        # Add training tags to base tags:
        base_tags = build_mlflow_tags(context, output_dir, config_dir=config_dir)
        final_tags = add_training_tags(base_tags, training_type="final", config_dir=config_dir)
    """
    # Add simple training tags
    tags["mlflow.runType"] = "training"
    tags["training_type"] = training_type

    return tags


def add_training_tags_with_lineage(
    tags: Dict[str, str],
    lineage: Dict[str, Any],
    run_name: Optional[str] = None,
    config_dir: Optional[Path] = None,
) -> Dict[str, str]:
    """
    Add training tags with lineage information for final training from HPO.

    This function adds:
    - Simple training tags (via `add_training_tags()`)
    - `trained_on_full_data = "true"`
    - Lineage tags (`code.study_key_hash`, `code.trial_key_hash`, `code.lineage.*`)
    - `code.lineage.source = "hpo_best_selected"` if lineage present

    Args:
        tags: Base tags dictionary (from `build_mlflow_tags()`).
        lineage: Lineage dictionary from `extract_lineage_from_best_model()`.
                 Expected keys:
                 - hpo_study_key_hash (optional)
                 - hpo_trial_key_hash (optional)
                 - hpo_trial_run_id (optional)
                 - hpo_refit_run_id (optional)
                 - hpo_sweep_run_id (optional)
        run_name: Optional run name (added as `mlflow.runName` tag).
        config_dir: Optional config directory (for tag key retrieval).

    Returns:
        Combined tags dictionary with training and lineage tags added.

    Examples:
        # Add training tags with lineage:
        base_tags = build_mlflow_tags(context, output_dir, config_dir=config_dir)
        lineage = extract_lineage_from_best_model(best_model)
        final_tags = add_training_tags_with_lineage(
            base_tags,
            lineage=lineage,
            run_name=run_name,
            config_dir=config_dir
        )
    """
    # Add simple training tags first
    tags = add_training_tags(tags, training_type="final", config_dir=config_dir)

    # Get tag keys from registry (consolidated helper)
    tag_keys = _get_training_tag_keys(config_dir)

    # Add trained_on_full_data tag
    tags[tag_keys["trained_on_full_data"]] = "true"

    # Add run name if provided
    if run_name:
        tags["mlflow.runName"] = run_name

    # Add primary grouping tags if lineage information is present
    # (These are separate from lineage tags for backward compatibility)
    if lineage.get("hpo_study_key_hash"):
        tags[tag_keys["study_key_hash"]] = lineage["hpo_study_key_hash"]

    if lineage.get("hpo_trial_key_hash"):
        tags[tag_keys["trial_key_hash"]] = lineage["hpo_trial_key_hash"]

    # Add lineage tags using shared helper
    lineage_tags = _build_lineage_tags_dict(lineage, config_dir)
    tags.update(lineage_tags)

    return tags


def _build_lineage_tags_dict(
    lineage: Dict[str, Any],
    config_dir: Optional[Path] = None,
) -> Dict[str, str]:
    """
    Build lineage tags dictionary from lineage dict.

    Returns dictionary with lineage tags (code.lineage.*) if lineage data present.
    This helper consolidates the lineage tag building logic used in both
    `add_training_tags_with_lineage()` and `apply_lineage_tags()`.

    Args:
        lineage: Lineage dictionary from `extract_lineage_from_best_model()`.
                 Expected keys:
                 - hpo_study_key_hash (optional)
                 - hpo_trial_key_hash (optional)
                 - hpo_trial_run_id (optional)
                 - hpo_refit_run_id (optional)
                 - hpo_sweep_run_id (optional)
        config_dir: Optional config directory (for tag key retrieval).

    Returns:
        Dictionary with lineage tags. Always includes `code.lineage.source = "hpo_best_selected"`
        if any lineage data is present. Includes other lineage tags if corresponding
        keys are present in lineage dict.

    Examples:
        lineage = {"hpo_study_key_hash": "abc123", "hpo_trial_key_hash": "def456"}
        lineage_tags = _build_lineage_tags_dict(lineage, config_dir)
        # Returns: {
        #     "code.lineage.source": "hpo_best_selected",
        #     "code.lineage.hpo_study_key_hash": "abc123",
        #     "code.lineage.hpo_trial_key_hash": "def456",
        # }
    """
    from infrastructure.naming.mlflow.tag_keys import (
        get_lineage_hpo_refit_run_id,
        get_lineage_hpo_study_key_hash,
        get_lineage_hpo_sweep_run_id,
        get_lineage_hpo_trial_key_hash,
        get_lineage_hpo_trial_run_id,
        get_lineage_source,
    )

    lineage_tags: Dict[str, str] = {}

    # Check if any lineage data is present
    has_lineage_data = any(
        lineage.get(key)
        for key in [
            "hpo_study_key_hash",
            "hpo_trial_key_hash",
            "hpo_trial_run_id",
            "hpo_refit_run_id",
            "hpo_sweep_run_id",
        ]
    )

    if has_lineage_data:
        # Always set source tag if any lineage data is present
        lineage_tags[get_lineage_source(config_dir)] = "hpo_best_selected"

        # Add HPO lineage tags if available
        if lineage.get("hpo_study_key_hash"):
            lineage_tags[
                get_lineage_hpo_study_key_hash(config_dir)
            ] = lineage["hpo_study_key_hash"]

        if lineage.get("hpo_trial_key_hash"):
            lineage_tags[
                get_lineage_hpo_trial_key_hash(config_dir)
            ] = lineage["hpo_trial_key_hash"]

        if lineage.get("hpo_trial_run_id"):
            lineage_tags[
                get_lineage_hpo_trial_run_id(config_dir)
            ] = lineage["hpo_trial_run_id"]

        if lineage.get("hpo_refit_run_id"):
            lineage_tags[
                get_lineage_hpo_refit_run_id(config_dir)
            ] = lineage["hpo_refit_run_id"]

        if lineage.get("hpo_sweep_run_id"):
            lineage_tags[
                get_lineage_hpo_sweep_run_id(config_dir)
            ] = lineage["hpo_sweep_run_id"]

    return lineage_tags


def _get_training_tag_keys(config_dir: Optional[Path] = None) -> Dict[str, str]:
    """
    Get training-related tag keys from registry.

    Consolidates tag key retrieval pattern used in executor.py and other places.

    Args:
        config_dir: Optional config directory (for tag key retrieval).

    Returns:
        Dictionary mapping tag key names to their actual tag key strings.

    Examples:
        tag_keys = _get_training_tag_keys(config_dir)
        tags[tag_keys["study_key_hash"]] = "abc123"
    """
    from infrastructure.naming.mlflow.tag_keys import (
        get_lineage_hpo_refit_run_id,
        get_lineage_hpo_study_key_hash,
        get_lineage_hpo_sweep_run_id,
        get_lineage_hpo_trial_key_hash,
        get_lineage_hpo_trial_run_id,
        get_lineage_source,
        get_mlflow_run_type,
        get_study_key_hash,
        get_trained_on_full_data,
        get_trial_key_hash,
    )

    return {
        "mlflow_run_type": get_mlflow_run_type(config_dir),
        "trained_on_full_data": get_trained_on_full_data(config_dir),
        "study_key_hash": get_study_key_hash(config_dir),
        "trial_key_hash": get_trial_key_hash(config_dir),
        "lineage_source": get_lineage_source(config_dir),
        "lineage_hpo_study_key_hash": get_lineage_hpo_study_key_hash(config_dir),
        "lineage_hpo_trial_key_hash": get_lineage_hpo_trial_key_hash(config_dir),
        "lineage_hpo_trial_run_id": get_lineage_hpo_trial_run_id(config_dir),
        "lineage_hpo_refit_run_id": get_lineage_hpo_refit_run_id(config_dir),
        "lineage_hpo_sweep_run_id": get_lineage_hpo_sweep_run_id(config_dir),
    }


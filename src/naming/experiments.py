"""Experiment and stage naming helpers (dict-based interface)."""

from __future__ import annotations

from typing import Any, Dict, Optional


def get_stage_config(experiment_cfg: dict, stage: str) -> Dict[str, Any]:
    """
    Return the configuration block for a given stage, if present.

    This is a thin, read-only helper around experiment config stages.
    Uses dict interface instead of ExperimentConfig to avoid dependency on orchestration.config_loader.

    Args:
        experiment_cfg: Experiment configuration dictionary with 'stages' key.
        stage: Stage name to retrieve.

    Returns:
        Stage configuration dictionary, or empty dict if not found.
    """
    stages = experiment_cfg.get("stages", {})
    return stages.get(stage, {}) or {}


def build_aml_experiment_name(
    experiment_name: str,
    stage: str,
    backbone: Optional[str] = None,
) -> str:
    """Build a simple, stable AML experiment name.

    This intentionally accepts only the minimum information required to build
    the name and leaves more complex context handling (full configs, hashes,
    etc.) to the caller.

    Args:
        experiment_name: Base experiment name.
        stage: Stage name (e.g., "hpo", "training").
        backbone: Optional model backbone name.

    Returns:
        Formatted experiment name.
    """
    parts = [experiment_name, stage]
    if backbone:
        parts.append(backbone)
    return "-".join(parts)


def build_mlflow_experiment_name(experiment_name: str, stage: str, backbone: str) -> str:
    """Build MLflow experiment name from components.

    Args:
        experiment_name: Base experiment name.
        stage: Stage name (e.g., "hpo", "training").
        backbone: Model backbone name (required).

    Returns:
        Formatted experiment name: "{experiment_name}-{stage}-{backbone}".
    """
    return build_aml_experiment_name(experiment_name, stage, backbone)


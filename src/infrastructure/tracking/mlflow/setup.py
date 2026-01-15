from __future__ import annotations

"""
@meta
name: setup
type: utility
domain: tracking
responsibility:
  - MLflow experiment setup utilities
  - Set up MLflow tracking for different stages
inputs:
  - Experiment names
  - Tracking URIs
outputs:
  - Configured MLflow tracking
tags:
  - utility
  - tracking
  - mlflow
  - setup
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""MLflow experiment setup utilities.

This module provides the **single source of truth (SSOT)** for MLflow setup and
configuration across the codebase. All orchestration scripts (training orchestrator,
HPO sweep, selection workflows) should use functions from this module rather than
directly calling mlflow.set_tracking_uri() or mlflow.set_experiment().

**Layering**:
- This module wraps `common.shared.mlflow_setup.setup_mlflow_cross_platform()` to
  provide a unified interface for MLflow configuration.
- Higher-level scripts (training.orchestrator, training.hpo.execution.local.sweep,
  selection workflows) should call `setup_mlflow()` from this module.
- Run lifecycle management (creating runs, tags, parent/child relationships) is
  handled by `infrastructure.tracking.mlflow.runs` and trackers, which assume
  MLflow has already been configured by this module.
"""

from typing import Optional, Any

import mlflow

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def setup_mlflow(
    experiment_name: str,
    ml_client: Optional[Any] = None,
    tracking_uri: Optional[str] = None,
    fallback_to_local: bool = True,
) -> str:
    """
    Setup MLflow tracking (SSOT for MLflow configuration).

    This is the **single source of truth** for MLflow setup. All orchestration
    scripts should use this function instead of directly calling mlflow APIs.

    Args:
        experiment_name: MLflow experiment name (will be created if doesn't exist).
        ml_client: Optional Azure ML client for unified tracking. If provided,
                  uses Azure ML workspace tracking URI.
        tracking_uri: Optional explicit tracking URI. If provided, uses this URI
                     directly (overrides ml_client). If None and ml_client is None,
                     falls back to local tracking.
        fallback_to_local: If True, fallback to local tracking when Azure ML fails.

    Returns:
        Tracking URI string that was configured.

    Examples:
        # Local tracking:
        setup_mlflow("my_experiment")

        # Azure ML tracking:
        from common.shared.mlflow_setup import create_ml_client_from_config
        ml_client = create_ml_client_from_config(config_dir)
        setup_mlflow("my_experiment", ml_client=ml_client)

        # Explicit tracking URI:
        setup_mlflow("my_experiment", tracking_uri="file:///path/to/mlruns")
    """
    # If explicit tracking URI provided, use it directly
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name)
        logger.debug(f"Set MLflow tracking URI: {tracking_uri[:50]}...")
        return tracking_uri

    # Otherwise, use cross-platform setup (handles Azure ML vs local)
    from common.shared.mlflow_setup import setup_mlflow_cross_platform
    return setup_mlflow_cross_platform(
        experiment_name=experiment_name,
        ml_client=ml_client,
        fallback_to_local=fallback_to_local,
    )


def setup_mlflow_for_stage(
    experiment_name: str,
    tracking_uri: Optional[str] = None
) -> None:
    """Setup MLflow tracking for a specific stage (legacy wrapper).

    **Deprecated**: Use `setup_mlflow()` instead for new code. This function
    is kept for backward compatibility but delegates to `setup_mlflow()`.

    Args:
        experiment_name: MLflow experiment name.
        tracking_uri: Optional tracking URI (uses default if None).
    """
    setup_mlflow(
        experiment_name=experiment_name,
        tracking_uri=tracking_uri,
        fallback_to_local=True,
    )







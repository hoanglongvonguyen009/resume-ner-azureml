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

import os
import sys
from typing import Optional, Any

import mlflow

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)

# Azure ML artifact upload timeout constant (in seconds)
AZUREML_ARTIFACTS_DEFAULT_TIMEOUT_SECONDS = 600


def setup_mlflow(
    experiment_name: Optional[str] = None,
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
                         If None, reads from MLFLOW_EXPERIMENT_NAME environment variable.
        ml_client: Optional Azure ML client for unified tracking. If provided,
                  uses Azure ML workspace tracking URI.
        tracking_uri: Optional explicit tracking URI. If provided, uses this URI
                     directly (overrides ml_client). If None, reads from MLFLOW_TRACKING_URI
                     environment variable or uses ml_client/local fallback.
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

        # Read from environment variables:
        setup_mlflow()  # Reads MLFLOW_EXPERIMENT_NAME and MLFLOW_TRACKING_URI
    """
    # Read experiment name from environment if not provided
    if experiment_name is None:
        experiment_name = os.environ.get("MLFLOW_EXPERIMENT_NAME")
        if not experiment_name:
            raise ValueError(
                "experiment_name must be provided or MLFLOW_EXPERIMENT_NAME must be set"
            )

    # Read tracking URI from environment if not provided
    if tracking_uri is None:
        tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")

    # Handle Azure ML compatibility: if tracking_uri contains "azureml" but azureml.mlflow
    # is not available, fallback to local tracking and clear Azure ML run IDs
    if tracking_uri and "azureml" in tracking_uri.lower():
        tracking_uri = _ensure_azureml_compatibility(tracking_uri, fallback_to_local)

    # If explicit tracking URI provided (after compatibility check), use it directly
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
        try:
            mlflow.set_experiment(experiment_name)
        except Exception as e:
            # Handle Alembic database migration errors gracefully
            # This can happen when MLflow database is in inconsistent state
            if "alembic" in str(e).lower() or "revision" in str(e).lower():
                logger.warning(
                    f"MLflow database migration error (likely test environment issue): {e}. "
                    f"Attempting to continue with existing experiment."
                )
                # Try to get experiment without creating it
                try:
                    from mlflow.tracking import MlflowClient
                    client = MlflowClient(tracking_uri=tracking_uri)
                    client.get_experiment_by_name(experiment_name)
                except Exception:
                    # If we can't get experiment, log warning but continue
                    logger.warning(
                        f"Could not access MLflow experiment '{experiment_name}'. "
                        f"Tests may fail if experiment access is required."
                    )
            else:
                # Re-raise non-Alembic errors
                raise

        # Set Azure ML artifact upload timeout if using Azure ML
        if "azureml" in tracking_uri.lower():
            _set_azureml_artifact_timeout()

        logger.debug(f"Set MLflow tracking URI: {tracking_uri[:50]}...")
        if experiment_name:
            logger.debug(f"Set MLflow experiment: {experiment_name}")
        return tracking_uri

    # Otherwise, use cross-platform setup (handles Azure ML vs local)
    from common.shared.mlflow_setup import setup_mlflow_cross_platform
    final_tracking_uri = setup_mlflow_cross_platform(
        experiment_name=experiment_name,
        ml_client=ml_client,
        fallback_to_local=fallback_to_local,
    )

    # Set Azure ML artifact upload timeout if using Azure ML
    if "azureml" in final_tracking_uri.lower():
        _set_azureml_artifact_timeout()

    return final_tracking_uri


def _ensure_azureml_compatibility(
    tracking_uri: str,
    fallback_to_local: bool = True,
) -> str:
    """
    Ensure Azure ML compatibility by checking if azureml.mlflow is available.

    If Azure ML URI is detected but azureml.mlflow is not available, falls back
    to local tracking and clears Azure ML run IDs from environment.

    Args:
        tracking_uri: Tracking URI (may contain "azureml").
        fallback_to_local: If True, fallback to local tracking when Azure ML unavailable.

    Returns:
        Tracking URI (original or fallback to local).
    """
    if "azureml" not in tracking_uri.lower():
        return tracking_uri

    # Try to import azureml.mlflow early to register the 'azureml' URI scheme
    # This must happen before mlflow is imported to ensure the scheme is registered
    try:
        from common.shared.mlflow_setup import _check_azureml_mlflow_available

        if _check_azureml_mlflow_available():
            # Azure ML is available, return original URI
            return tracking_uri
    except Exception:
        pass

    # Azure ML not available - fallback to local if enabled
    if fallback_to_local:
        logger.info(
            "azureml.mlflow not available, but Azure ML URI detected. "
            "Falling back to local tracking. (This is normal if azureml-mlflow is not installed)"
        )

        from common.shared.mlflow_setup import _get_local_tracking_uri

        local_tracking_uri = _get_local_tracking_uri()

        # Clear Azure ML run IDs - they won't exist in local SQLite database
        # This forces creation of a new run in local tracking
        if "MLFLOW_RUN_ID" in os.environ:
            old_run_id = os.environ.pop("MLFLOW_RUN_ID")
            logger.debug(
                f"Cleared Azure ML run ID {old_run_id[:12]}... "
                "(will create new run in local tracking)"
            )
        if "MLFLOW_USE_RUN_ID" in os.environ:
            os.environ.pop("MLFLOW_USE_RUN_ID")

        return local_tracking_uri

    # Fallback disabled, return original URI (will fail later if azureml.mlflow not available)
    return tracking_uri


def _set_azureml_artifact_timeout() -> None:
    """
    Set Azure ML artifact upload timeout if not already set.

    This ensures large artifacts can be uploaded without timing out.
    """
    if "AZUREML_ARTIFACTS_DEFAULT_TIMEOUT" not in os.environ:
        os.environ["AZUREML_ARTIFACTS_DEFAULT_TIMEOUT"] = str(
            AZUREML_ARTIFACTS_DEFAULT_TIMEOUT_SECONDS
        )
        logger.debug(
            f"Set AZUREML_ARTIFACTS_DEFAULT_TIMEOUT={AZUREML_ARTIFACTS_DEFAULT_TIMEOUT_SECONDS} "
            "for artifact uploads"
        )





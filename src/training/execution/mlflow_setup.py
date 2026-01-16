from __future__ import annotations

"""
@meta
name: mlflow_setup
type: utility
domain: training
responsibility:
  - Create MLflow runs for training execution
  - Set up MLflow tracking for training subprocesses
  - Manage MLflow run lifecycle
inputs:
  - Experiment names
  - Run names and tags
  - Parent run IDs (for child runs)
outputs:
  - MLflow run IDs and run objects
tags:
  - utility
  - training
  - mlflow
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""MLflow run lifecycle management for training execution.

This module provides functions for creating MLflow runs and managing run lifecycle
for training workflows. It does NOT handle MLflow setup/configuration.

**Layering**:
- MLflow setup/configuration is handled by `infrastructure.tracking.mlflow.setup.setup_mlflow()`
  (SSOT). Training modules should call this before using functions in this module.
- This module focuses on run lifecycle management (creating runs, tags, parent/child relationships).
- All functions in this module assume MLflow has already been configured via infrastructure setup.

**Usage Pattern**:
    1. Call `infrastructure.tracking.mlflow.setup.setup_mlflow()` first (in orchestrator/subprocess runner)
    2. Then use functions from this module to create and manage runs
"""

from pathlib import Path
from typing import Any, Dict, Optional
import sys

import mlflow
from mlflow.tracking import MlflowClient

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def create_training_mlflow_run(
    experiment_name: str,
    run_name: str,
    tags: Optional[Dict[str, str]] = None,
    parent_run_id: Optional[str] = None,
    run_id: Optional[str] = None,
    root_dir: Optional[Path] = None,
    config_dir: Optional[Path] = None,
    context: Optional[Any] = None,
    tracking_uri: Optional[str] = None,
    trial_number: Optional[int] = None,
    fold_idx: Optional[int] = None,
    create_as_child: bool = False,
) -> tuple[str, Any]:
    """
    Create MLflow run for training execution.

    **Note**: This function assumes MLflow has already been configured by
    `infrastructure.tracking.mlflow.setup.setup_mlflow()`. It focuses solely
    on run lifecycle management (creating runs, tags, parent/child relationships).

    Args:
        experiment_name: MLflow experiment name (must match current experiment).
        run_name: Run name.
        tags: Optional tags dictionary.
        parent_run_id: Optional parent run ID (for creating as child run).
        run_id: Optional existing run ID (if run already exists).
        root_dir: Optional project root directory (for index updating).
        config_dir: Optional config directory (for index updating).
        context: Optional naming context (for index updating).
        tracking_uri: Optional tracking URI (if None, uses current MLflow config).
        trial_number: Optional trial number (for HPO trials).
        fold_idx: Optional fold index (for k-fold CV).
        create_as_child: If True, create child run via client API (for HPO trials).
                        If False, create standalone run or use parent_run_id tag.

    Returns:
        Tuple of (run_id, run_object)

    Examples:
        # Create run as child of parent (refit usage):
        run_id, run = create_training_mlflow_run(
            experiment_name="my_experiment",
            run_name="refit_trial_0",
            tags={"mlflow.runType": "refit"},
            parent_run_id="parent_run_123"
        )

        # Create standalone run (final training usage):
        run_id, run = create_training_mlflow_run(
            experiment_name="my_experiment",
            run_name="final_training",
            tags={"training_type": "final"},
            root_dir=Path("."),
            config_dir=Path("config"),
            context=training_context
        )

        # Create child run via client API (HPO trial usage):
        run_id, run = create_training_mlflow_run(
            experiment_name="my_experiment",
            run_name="trial_0",
            parent_run_id="parent_run_123",
            trial_number=0,
            fold_idx=0,
            create_as_child=True
        )
    """
    if run_id:
        # Run already exists, just return it
        client = MlflowClient(tracking_uri=tracking_uri)
        run = client.get_run(run_id)
        return run_id, run

    # If create_as_child is True, use child run creation function
    if create_as_child and parent_run_id:
        return create_training_child_run(
            experiment_name=experiment_name,
            run_name=run_name,
            parent_run_id=parent_run_id,
            tags=tags,
            trial_number=trial_number,
            fold_idx=fold_idx,
            tracking_uri=tracking_uri,
        )

    # Get or create experiment using SSOT function
    from infrastructure.tracking.mlflow.runs import get_or_create_experiment, resolve_experiment_id

    # Resolve experiment ID (prefer parent run if provided)
    experiment_id = resolve_experiment_id(
        experiment_name=experiment_name,
        parent_run_id=parent_run_id,
    )

    # If resolution failed, try get_or_create
    if not experiment_id:
        experiment_id = get_or_create_experiment(experiment_name)
        if not experiment_id:
            raise RuntimeError(
                f"Could not get or create experiment: {experiment_name}. "
                f"Ensure MLflow is configured via infrastructure.tracking.mlflow.setup.setup_mlflow()"
            )

    # Create run
    client = MlflowClient(tracking_uri=tracking_uri)
    try:
        created_run = client.create_run(
            experiment_id=experiment_id,
            run_name=run_name,
            tags=tags or {},
        )
        run_id = created_run.info.run_id

        # Update local index if context provided
        if root_dir and config_dir and context:
            try:
                from infrastructure.naming.mlflow.run_keys import (
                    build_mlflow_run_key,
                    build_mlflow_run_key_hash,
                )
                from orchestration.jobs.tracking.index.run_index import update_mlflow_index

                run_key = build_mlflow_run_key(context)
                run_key_hash = build_mlflow_run_key_hash(run_key)
                update_mlflow_index(
                    root_dir=root_dir,
                    run_key_hash=run_key_hash,
                    run_id=run_id,
                    experiment_id=experiment_id,
                    tracking_uri=tracking_uri or mlflow.get_tracking_uri(),
                    config_dir=config_dir,
                )
            except Exception as e:
                logger.debug(f"Could not update MLflow index: {e}")

        # Log run URL if available
        try:
            from infrastructure.tracking.mlflow import get_mlflow_run_url

            refit_url = get_mlflow_run_url(experiment_id, run_id)
            logger.info(f"🏃 View run {run_name} at: {refit_url}")
        except Exception:
            pass  # URL construction is optional

        logger.info(f"Created MLflow run: {run_name} ({run_id[:12]}...)")
        return run_id, created_run
    except Exception as e:
        logger.warning(f"Could not create MLflow run: {e}", exc_info=True)
        raise


def setup_mlflow_tracking_env(
    experiment_name: str,
    tracking_uri: Optional[str] = None,
    parent_run_id: Optional[str] = None,
    run_id: Optional[str] = None,
    trial_number: Optional[int] = None,
    additional_vars: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """
    Set up MLflow tracking environment variables for subprocess execution.

    **Note**: This function assumes MLflow has already been configured by
    `infrastructure.tracking.mlflow.setup.setup_mlflow()`. It reads the current
    MLflow configuration and sets environment variables for subprocesses.

    Args:
        experiment_name: MLflow experiment name (must match current experiment).
        tracking_uri: Optional explicit tracking URI. If None, reads from current MLflow config.
        parent_run_id: Optional parent run ID (for child runs).
        run_id: Optional run ID (for resuming existing runs).
        trial_number: Optional trial number (for HPO trials).
        additional_vars: Optional additional environment variables.

    Returns:
        Dictionary of environment variables to pass to subprocess.
    """
    import mlflow

    env_vars: Dict[str, str] = {}

    # Set experiment name
    env_vars["MLFLOW_EXPERIMENT_NAME"] = experiment_name

    # Set tracking URI (read from current config if not provided)
    if tracking_uri:
        env_vars["MLFLOW_TRACKING_URI"] = tracking_uri
    else:
        # Read current tracking URI (assumes MLflow already configured)
        current_uri = mlflow.get_tracking_uri()
        if current_uri:
            env_vars["MLFLOW_TRACKING_URI"] = current_uri

    # Set parent run ID
    if parent_run_id:
        env_vars["MLFLOW_PARENT_RUN_ID"] = parent_run_id

    # Set run ID
    if run_id:
        env_vars["MLFLOW_RUN_ID"] = run_id

    # Set trial number
    if trial_number is not None:
        env_vars["MLFLOW_TRIAL_NUMBER"] = str(trial_number)

    # Add any additional variables
    if additional_vars:
        env_vars.update(additional_vars)

    return env_vars


def create_training_child_run(
    experiment_name: str,
    run_name: str,
    parent_run_id: str,
    tags: Optional[Dict[str, str]] = None,
    trial_number: Optional[int] = None,
    fold_idx: Optional[int] = None,
    tracking_uri: Optional[str] = None,
) -> tuple[str, Any]:
    """
    Create MLflow child run via client API (for HPO trials).

    This function creates a child run using the MLflow client API (not active run context),
    which is required for HPO trials where the run should remain RUNNING until the parent
    process explicitly terminates it.

    **Note**: This function delegates to `infrastructure.tracking.mlflow.runs.create_child_run_core()`
    (SSOT) for the actual run creation logic. It adds training-specific logging and error handling.

    **Note**: This function assumes MLflow has already been configured by
    `infrastructure.tracking.mlflow.setup.setup_mlflow()`.

    Args:
        experiment_name: MLflow experiment name (used for fallback if parent lookup fails).
        run_name: Run name for the child run.
        parent_run_id: Parent run ID (required).
        tags: Optional base tags dictionary (will be merged with child run tags).
        trial_number: Optional trial number (added to tags).
        fold_idx: Optional fold index for k-fold CV (added to tags).
        tracking_uri: Optional tracking URI (if None, uses current MLflow config).

    Returns:
        Tuple of (run_id, run_object)

    Examples:
        # Create HPO trial child run:
        run_id, run = create_training_child_run(
            experiment_name="my_experiment",
            run_name="trial_0",
            parent_run_id="parent_run_123",
            trial_number=0,
            fold_idx=0
        )
    """
    # Delegate to SSOT core function
    from infrastructure.tracking.mlflow.runs import create_child_run_core

    try:
        run_id, created_run = create_child_run_core(
            parent_run_id=parent_run_id,
            run_name=run_name,
            experiment_name=experiment_name,
            trial_number=str(trial_number) if trial_number is not None else None,
            fold_idx=fold_idx,
            additional_tags=tags,
            tracking_uri=tracking_uri,
        )

        # Training-specific logging
        print(
            f"  [Training] ✓ Created child run: {run_id[:12]}...",
            file=sys.stderr,
            flush=True,
        )

        return run_id, created_run
    except Exception as e:
        logger.error(f"Could not create child run: {e}", exc_info=True)
        print(
            f"  [Training] Error creating child run: {e}",
            file=sys.stderr,
            flush=True,
        )
        raise

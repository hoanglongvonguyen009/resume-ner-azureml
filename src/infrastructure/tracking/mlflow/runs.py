from __future__ import annotations

"""
@meta
name: tracking_mlflow_runs
type: utility
domain: tracking
responsibility:
  - Create MLflow runs including child runs
  - Resolve experiments and manage run lifecycle
inputs:
  - Parent run IDs
  - Experiment names
outputs:
  - MLflow run contexts
tags:
  - utility
  - tracking
  - mlflow
  - runs
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""MLflow run creation utilities.

This module provides utilities for creating MLflow runs, including
child runs, experiment resolution, and run management.

**Single Source of Truth (SSOT)**: This module is the SSOT for MLflow run creation.
Higher-level modules (e.g., `training.execution.mlflow_setup`) should delegate to
functions in this module rather than duplicating run creation logic.
"""
from contextlib import contextmanager
from typing import Any, Optional, Tuple

import mlflow
from infrastructure.tracking.mlflow.client import create_mlflow_client
from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def create_child_run_core(
    parent_run_id: str,
    run_name: str,
    experiment_name: Optional[str] = None,
    trial_number: Optional[str] = None,
    fold_idx: Optional[int] = None,
    additional_tags: Optional[dict[str, str]] = None,
    tracking_uri: Optional[str] = None,
) -> Tuple[str, Any]:
    """
    Core child run creation logic (SSOT for child run creation).
    
    This function contains the shared logic for creating child runs. It is used by
    both `create_child_run()` (context manager) and `training.execution.mlflow_setup.create_training_child_run()`
    (tuple return) to avoid duplication.
    
    **Note**: This is the single source of truth for child run creation. All child run
    creation should delegate to this function or use `create_child_run()` context manager.
    
    Args:
        parent_run_id: ID of the parent MLflow run.
        run_name: Name for the child run.
        experiment_name: Optional experiment name (used for fallback if parent lookup fails).
        trial_number: Optional trial number identifier (e.g., "0", "1", "unknown").
        fold_idx: Optional fold index for k-fold CV.
        additional_tags: Optional additional tags to set on the child run.
        tracking_uri: Optional tracking URI (if None, uses current MLflow config).
    
    Returns:
        Tuple of (run_id, run_object)
    
    Raises:
        RuntimeError: If experiment ID cannot be determined.
    """
    # CRITICAL: Validate run_name before creating run
    # MLflow will auto-generate names (e.g., dynamic_duck_32f4qb48) if run_name is None/empty
    if not run_name or not run_name.strip():
        error_msg = (
            f"CRITICAL: Cannot create child run: run_name is None or empty. "
            f"This would cause MLflow to auto-generate a name like 'dynamic_duck_32f4qb48'. "
            f"run_name={run_name}, parent_run_id={parent_run_id[:12] if parent_run_id else 'None'}..., "
            f"experiment_name={experiment_name}, trial_number={trial_number}, fold_idx={fold_idx}"
        )
        logger.error(error_msg)
        import traceback
        logger.error(f"Call stack:\n{''.join(traceback.format_stack()[-10:-1])}")
        raise ValueError(
            f"Cannot create child run: run_name is None or empty. "
            f"This would cause MLflow to auto-generate a name. "
            f"Check that run_name is provided and not empty."
        )
    
    logger.debug(f"[create_child_run_core] Creating child run with name: '{run_name}' (parent: {parent_run_id[:12] if parent_run_id else 'None'}..., experiment: {experiment_name})")
    
    client = create_mlflow_client(tracking_uri=tracking_uri)
    tracking_uri_actual = tracking_uri or mlflow.get_tracking_uri()
    is_azure_ml = tracking_uri_actual and "azureml" in tracking_uri_actual.lower()

    # Get experiment ID - CRITICAL: Get from parent run FIRST to ensure same experiment
    experiment_id = None

    # First, try to get from parent run (most reliable for Azure ML)
    try:
        parent_run_info = client.get_run(parent_run_id)
        experiment_id = parent_run_info.info.experiment_id
        logger.debug(f"Using parent's experiment ID: {experiment_id} (parent: {parent_run_id[:12]}...)")
    except Exception as e:
        logger.warning(f"Could not get parent run {parent_run_id}, trying experiment name: {e}")

    # Fallback: try to get from experiment name
    if not experiment_id and experiment_name:
        try:
            experiment = client.get_experiment_by_name(experiment_name)
            if experiment:
                experiment_id = experiment.experiment_id
                logger.debug(f"Using experiment ID from name: {experiment_id}")
        except Exception as e:
            logger.debug(f"Could not get experiment by name: {e}")

    if not experiment_id:
        raise RuntimeError(
            f"Could not determine experiment ID from parent run {parent_run_id} "
            f"or experiment name {experiment_name}"
        )

    # Build tags for child run
    tags: dict[str, str] = {
        "mlflow.parentRunId": parent_run_id,
    }

    # Add trial number if provided
    if trial_number is not None:
        tags["trial_number"] = str(trial_number)

    # Add fold index if k-fold CV is enabled
    if fold_idx is not None:
        tags["fold_idx"] = str(fold_idx)

    # Add Azure ML-specific tags if using Azure ML
    if is_azure_ml:
        tags["azureml.runType"] = "trial"
        tags["azureml.trial"] = "true"

    # CRITICAL: Set mlflow.runName tag (required for proper run name display in Azure ML)
    tags["mlflow.runName"] = run_name

    # Add any additional tags (provided tags take precedence)
    if additional_tags:
        tags.update(additional_tags)

    # For Azure ML, double-check we're using the parent's experiment ID
    # This ensures child runs appear nested in Azure ML UI
    if is_azure_ml:
        try:
            parent_run_info = client.get_run(parent_run_id)
            # Always use parent's experiment ID for Azure ML
            if parent_run_info.info.experiment_id != experiment_id:
                logger.info(
                    f"Using parent's experiment ID for Azure ML: {parent_run_info.info.experiment_id}"
                )
                experiment_id = parent_run_info.info.experiment_id
        except Exception as e:
            logger.warning(f"Could not verify parent run for Azure ML: {e}")

    # Create child run via client API
    try:
        created_run = client.create_run(
            experiment_id=experiment_id,
            run_name=run_name,
            tags=tags,
        )
        run_id = created_run.info.run_id

        logger.info(
            f"Created child run: {run_name} ({run_id[:12]}...) "
            f"(parent: {parent_run_id[:12]}..., experiment: {experiment_id})"
        )

        # For Azure ML, verify the parent tag was set correctly
        if is_azure_ml:
            run_info = client.get_run(run_id)
            parent_tag = run_info.data.tags.get("mlflow.parentRunId")
            if parent_tag != parent_run_id:
                logger.warning(
                    f"Parent tag mismatch! Expected {parent_run_id[:12]}..., "
                    f"got {parent_tag[:12] if parent_tag else 'None'}..."
                )
                # Force set it
                client.set_tag(run_id, "mlflow.parentRunId", parent_run_id)
                logger.info("Re-set parent tag for Azure ML")

        return run_id, created_run
    except Exception as e:
        logger.warning(f"Error creating child run with tags: {e}")
        # CRITICAL: Validate run_name before fallback
        if not run_name or not run_name.strip():
            error_msg = (
                f"CRITICAL: Cannot create fallback run: run_name is None or empty. "
                f"This would cause MLflow to auto-generate a name like 'dynamic_duck_32f4qb48'. "
                f"run_name={run_name}, parent_run_id={parent_run_id[:12] if parent_run_id else 'None'}..., "
                f"experiment_id={experiment_id}"
            )
            logger.error(error_msg)
            import traceback
            logger.error(f"Call stack:\n{''.join(traceback.format_stack()[-10:-1])}")
            raise ValueError(
                f"Cannot create fallback run: run_name is None or empty. "
                f"This would cause MLflow to auto-generate a name. "
                f"Original error: {e}"
            ) from e
        # Fallback: create run without tags, then set them
        logger.warning(f"[create_child_run_core] Fallback: Creating run without tags, then setting them (name: '{run_name}')")
        run = client.create_run(
            experiment_id=experiment_id,
            run_name=run_name,
        )
        # Set tags after creation
        for tag_key, tag_value in tags.items():
            try:
                client.set_tag(run.info.run_id, tag_key, tag_value)
            except Exception as tag_error:
                logger.warning(f"Could not set tag {tag_key}: {tag_error}")
        logger.info(f"Created child run and set tags: {run.info.run_id[:12]}...")
        return run.info.run_id, run


@contextmanager
def create_child_run(
    parent_run_id: str,
    trial_number: str,
    experiment_name: Optional[str] = None,
    additional_tags: Optional[dict[str, str]] = None,
) -> Any:
    """
    Create and start a child MLflow run for HPO trials (context manager).

    This function consolidates the child run creation logic that was duplicated
    between mlflow_context.py and training/orchestrator.py.

    **Note**: This function delegates to `_create_child_run_core()` (SSOT) for the
    actual run creation logic, then starts the run and manages its lifecycle.

    Args:
        parent_run_id: ID of the parent MLflow run.
        trial_number: Trial number identifier (e.g., "0", "1", "unknown").
        experiment_name: Optional experiment name. If not provided, will try to get from parent run.
        additional_tags: Optional additional tags to set on the child run.

    Yields:
        Active MLflow run context.

    Note:
        The child run is automatically ended when the context exits.
    """
    run_name = f"trial_{trial_number}"

    # Use core creation logic (SSOT)
    try:
        run_id, run = create_child_run_core(
            parent_run_id=parent_run_id,
            run_name=run_name,
            experiment_name=experiment_name,
            trial_number=trial_number,
            additional_tags=additional_tags,
        )
    except RuntimeError as e:
        # If core creation fails, fallback to creating independent run
        logger.error(
            f"Could not determine experiment ID for child run! "
            f"Parent: {parent_run_id[:12]}..., Trial: {trial_number}, Experiment name: {experiment_name}"
        )
        logger.error("This will create an independent run instead of a child run!")
        # CRITICAL: Validate run_name before fallback
        if not run_name or not run_name.strip():
            error_msg = (
                f"CRITICAL: Cannot create fallback run: run_name is None or empty. "
                f"This would cause MLflow to auto-generate a name like 'dynamic_duck_32f4qb48'. "
                f"run_name={run_name}, parent_run_id={parent_run_id[:12] if parent_run_id else 'None'}..."
            )
            logger.error(error_msg)
            import traceback
            logger.error(f"Call stack:\n{''.join(traceback.format_stack()[-10:-1])}")
            raise ValueError(
                f"Cannot create fallback run: run_name is None or empty. "
                f"This would cause MLflow to auto-generate a name. "
                f"Original error: {e}"
            ) from e
        # Still try to create a run, but it won't be nested
        logger.warning(f"[create_child_run] Fallback: Creating independent run with name: '{run_name}' (parent lookup failed)")
        with mlflow.start_run(run_name=run_name) as run:
            # Try to set parent tag anyway
            try:
                mlflow.set_tag("mlflow.parentRunId", parent_run_id)
                mlflow.set_tag("trial_number", str(trial_number))
                logger.warning("Set parent tag on independent run as fallback")
            except Exception as tag_error:
                logger.warning(f"Could not set parent tag: {tag_error}")
            yield run
        return

    # Start the run using the created run_id
    try:
        mlflow.start_run(run_id=run_id)
        logger.info(f"Started child run: {run_id[:12]}... (parent: {parent_run_id[:12]}...)")

        # Final verification for Azure ML
        tracking_uri = mlflow.get_tracking_uri()
        is_azure_ml = tracking_uri and "azureml" in tracking_uri.lower()
        if is_azure_ml:
            from infrastructure.tracking.mlflow.client import create_mlflow_client
            client = create_mlflow_client()
            current_run = mlflow.active_run()
            if current_run:
                run_info = client.get_run(run_id)
                parent_tag = run_info.data.tags.get("mlflow.parentRunId")
                if parent_tag == parent_run_id:
                    logger.info("✓ Verified parent-child relationship for Azure ML")
                else:
                    logger.warning(
                        f"⚠ Parent tag verification failed! "
                        f"Expected: {parent_run_id[:12]}..., Got: {parent_tag[:12] if parent_tag else 'None'}..."
                    )
    except Exception as e:
        logger.warning(f"Error starting child run: {e}")
        # CRITICAL: Validate run_name before fallback
        if not run_name or not run_name.strip():
            error_msg = (
                f"CRITICAL: Cannot create fallback run: run_name is None or empty. "
                f"This would cause MLflow to auto-generate a name like 'dynamic_duck_32f4qb48'. "
                f"run_name={run_name}, run_id={run_id[:12] if run_id else 'None'}..., "
                f"parent_run_id={parent_run_id[:12] if parent_run_id else 'None'}..."
            )
            logger.error(error_msg)
            import traceback
            logger.error(f"Call stack:\n{''.join(traceback.format_stack()[-10:-1])}")
            raise ValueError(
                f"Cannot create fallback run: run_name is None or empty. "
                f"This would cause MLflow to auto-generate a name. "
                f"Original error: {e}"
            ) from e
        # Fallback: create new run
        logger.warning(f"[create_child_run] Fallback: Creating independent run with name: '{run_name}' (run start failed)")
        with mlflow.start_run(run_name=run_name) as fallback_run:
            yield fallback_run
        return

    try:
        yield
    finally:
        mlflow.end_run()
        logger.debug(f"Ended child run: {run_id[:12]}...")

def create_run_safe(
    experiment_id: str,
    run_name: str,
    tags: Optional[dict[str, str]] = None,
    parent_run_id: Optional[str] = None,
) -> Optional[str]:
    """
    Safely create an MLflow run with error handling.

    Args:
        experiment_id: MLflow experiment ID.
        run_name: Name for the run.
        tags: Optional dictionary of tags to set on the run.
        parent_run_id: Optional parent run ID for child runs.

    Returns:
        Run ID if successful, None otherwise.
    """
    # CRITICAL: Validate run_name before creating run
    # MLflow will auto-generate names (e.g., dynamic_duck_32f4qb48) if run_name is None/empty
    if not run_name or not run_name.strip():
        error_msg = (
            f"CRITICAL: Cannot create run: run_name is None or empty. "
            f"This would cause MLflow to auto-generate a name like 'dynamic_duck_32f4qb48'. "
            f"run_name={run_name}, experiment_id={experiment_id}, parent_run_id={parent_run_id[:12] if parent_run_id else 'None'}..."
        )
        logger.error(error_msg)
        import traceback
        logger.error(f"Call stack:\n{''.join(traceback.format_stack()[-10:-1])}")
        # Return None instead of raising to maintain "safe" behavior, but log error
        return None
    
    logger.debug(f"[create_run_safe] Creating run with name: '{run_name}' (experiment_id: {experiment_id}, parent: {parent_run_id[:12] if parent_run_id else 'None'}...)")
    
    try:
        from infrastructure.tracking.mlflow.client import create_mlflow_client
        client = create_mlflow_client()

        # Build tags
        run_tags = tags.copy() if tags else {}
        if parent_run_id:
            run_tags["mlflow.parentRunId"] = parent_run_id

        # Create run
        run = client.create_run(
            experiment_id=experiment_id,
            tags=run_tags,
            run_name=run_name
        )

        logger.info(
            f"Created run: {run.info.run_id[:12]}... "
            f"(experiment: {experiment_id}, name: {run_name})"
        )
        return run.info.run_id

    except Exception as e:
        logger.warning(f"Failed to create run: {e}", exc_info=True)
        return None

def get_or_create_experiment(experiment_name: str) -> Optional[str]:
    """
    Get existing experiment or create new one.

    Args:
        experiment_name: Name of the experiment.

    Returns:
        Experiment ID if successful, None otherwise.
    """
    try:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment:
            logger.debug(f"Found existing experiment: {experiment_name}")
            return experiment.experiment_id

        # Create new experiment
        experiment_id = mlflow.create_experiment(experiment_name)
        logger.info(f"Created new experiment: {experiment_name} ({experiment_id})")
        return experiment_id

    except Exception as e:
        logger.warning(f"Failed to get or create experiment {experiment_name}: {e}")
        return None

def resolve_experiment_id(
    experiment_name: Optional[str] = None,
    parent_run_id: Optional[str] = None,
    active_run: Optional[Any] = None,
) -> Optional[str]:
    """
    Resolve experiment ID using multiple strategies.

    Tries multiple strategies in order:
    1. From parent run (if provided)
    2. From experiment name (if provided)
    3. From active run (if provided)

    Args:
        experiment_name: Optional experiment name.
        parent_run_id: Optional parent run ID.
        active_run: Optional active MLflow run.

    Returns:
        Experiment ID if resolved, None otherwise.
    """
    from infrastructure.tracking.mlflow.client import create_mlflow_client
    client = create_mlflow_client()

    # Strategy 1: Get from parent run
    if parent_run_id:
        try:
            parent_run = client.get_run(parent_run_id)
            experiment_id = parent_run.info.experiment_id
            logger.debug(f"Resolved experiment ID from parent run: {experiment_id}")
            return experiment_id
        except Exception as e:
            logger.debug(f"Could not get experiment ID from parent run: {e}")

    # Strategy 2: Get from experiment name
    if experiment_name:
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment:
                experiment_id = experiment.experiment_id
                logger.debug(f"Resolved experiment ID from name: {experiment_id}")
                return experiment_id
        except Exception as e:
            logger.debug(f"Could not get experiment by name: {e}")

    # Strategy 3: Get from active run
    if active_run:
        try:
            if hasattr(active_run, 'info') and hasattr(active_run.info, 'experiment_id'):
                experiment_id = active_run.info.experiment_id
                logger.debug(f"Resolved experiment ID from active run: {experiment_id}")
                return experiment_id
        except Exception as e:
            logger.debug(f"Could not get experiment ID from active run: {e}")

    logger.warning("Could not resolve experiment ID using any strategy")
    return None


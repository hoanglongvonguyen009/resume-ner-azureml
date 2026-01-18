"""
@meta
name: platform_mlflow_context
type: utility
domain: platform_adapters
responsibility:
  - Manage MLflow context for different platforms
  - Handle Azure ML and local MLflow run lifecycle
inputs:
  - Platform identifiers
outputs:
  - MLflow context managers
tags:
  - utility
  - platform_adapters
  - mlflow
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""MLflow context management for different platforms."""

# CRITICAL: Import MLflow patch BEFORE importing mlflow to catch all run creation
import sys
try:
    from infrastructure.tracking.mlflow.patches import apply_patch
    apply_patch()
except Exception as e:
    print(f"  [MLflow Context] WARNING: Could not apply MLflow patch: {e}", file=sys.stderr, flush=True)

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import Any


class MLflowContextManager(ABC):
    """Abstract interface for MLflow context management."""

    @abstractmethod
    def get_context(self) -> AbstractContextManager[Any]:
        """
        Get the MLflow context manager for this platform.

        Returns:
            Context manager that handles MLflow run lifecycle.
        """
        pass


class AzureMLMLflowContextManager(MLflowContextManager):
    """MLflow context manager for Azure ML jobs.

    Azure ML automatically creates an MLflow run context for each job.
    We should NOT call mlflow.start_run() when running in Azure ML, as it creates
    a nested/separate run, causing metrics to be logged to the wrong run.
    """

    def get_context(self) -> AbstractContextManager[Any]:
        """Return a no-op context manager (Azure ML handles MLflow automatically)."""
        from contextlib import nullcontext
        return nullcontext()


class LocalMLflowContextManager(MLflowContextManager):
    """MLflow context manager for local execution."""

    def get_context(self) -> AbstractContextManager[Any]:
        """Return MLflow start_run context manager for local execution."""
        import mlflow
        import os
        from contextlib import contextmanager

        # Set up MLflow from environment variables (CRITICAL for subprocesses)
        tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
        experiment_name = os.environ.get("MLFLOW_EXPERIMENT_NAME")

        if tracking_uri or experiment_name:
            from shared.mlflow_setup import setup_mlflow_cross_platform
            try:
                if tracking_uri:
                    mlflow.set_tracking_uri(tracking_uri)
                if experiment_name:
                    setup_mlflow_cross_platform(
                        experiment_name=experiment_name,
                        ml_client=None,  # Will use local tracking or env vars
                        fallback_to_local=True,
                    )
            except Exception as e:
                import sys
                print(
                    f"  [MLflow Context] Warning: Could not set up MLflow: {e}", file=sys.stderr, flush=True)

        # Check if we should use an existing child run ID (created in parent process)
        child_run_id = os.environ.get("MLFLOW_CHILD_RUN_ID")
        if child_run_id:
            @contextmanager
            def existing_child_run_context():
                mlflow.start_run(run_id=child_run_id)
                try:
                    yield
                finally:
                    mlflow.end_run()
            return existing_child_run_context()

        # Check if we should create a nested child run (for HPO trials)
        parent_run_id = os.environ.get("MLFLOW_PARENT_RUN_ID")
        trial_number = os.environ.get("MLFLOW_TRIAL_NUMBER", "unknown")
        if parent_run_id:
            from infrastructure.tracking.mlflow.runs import create_child_run
            return create_child_run(
                parent_run_id=parent_run_id,
                trial_number=trial_number,
                experiment_name=experiment_name,
            )
        
        # Create an independent run - MLFLOW_RUN_NAME must be set
        # The patch will validate run_name and raise error if None/empty
        run_name = os.environ.get("MLFLOW_RUN_NAME")
        if not run_name or not run_name.strip():
            import sys
            import traceback
            error_msg = (
                f"CRITICAL: Cannot create MLflow run: MLFLOW_RUN_NAME is None or empty. "
                f"This would cause MLflow to auto-generate a name. "
                f"MLFLOW_RUN_NAME={run_name}, "
                f"MLFLOW_PARENT_RUN_ID={os.environ.get('MLFLOW_PARENT_RUN_ID')}, "
                f"MLFLOW_CHILD_RUN_ID={os.environ.get('MLFLOW_CHILD_RUN_ID')}"
            )
            print(error_msg, file=sys.stderr, flush=True)
            print("Call stack:", file=sys.stderr, flush=True)
            for line in traceback.format_stack()[-10:-1]:
                print(f"  {line.rstrip()}", file=sys.stderr, flush=True)
            raise ValueError(
                f"Cannot create MLflow run: MLFLOW_RUN_NAME is None or empty. "
                f"Set MLFLOW_RUN_NAME environment variable or ensure parent/child run IDs are set."
            )
        
        # Use MLflow client to create run with explicit name
        from infrastructure.tracking.mlflow.client import create_mlflow_client
        client = create_mlflow_client()
        experiment_id = None
        if experiment_name:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment:
                experiment_id = experiment.experiment_id
        
        if experiment_id:
            # Create run with explicit name using client
            run = client.create_run(
                experiment_id=experiment_id,
                run_name=run_name
            )
            @contextmanager
            def named_run_context():
                mlflow.start_run(run_id=run.info.run_id)
                try:
                    yield
                finally:
                    mlflow.end_run()
            return named_run_context()
        else:
            # Fallback to standard start_run with name
            # Patch will validate run_name
            return mlflow.start_run(run_name=run_name)

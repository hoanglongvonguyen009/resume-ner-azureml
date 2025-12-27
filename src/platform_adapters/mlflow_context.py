"""MLflow context management for different platforms."""

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
        import sys
        from contextlib import contextmanager

        # CRITICAL DEBUG: Print immediately to confirm this method is being called
        debug_msg = "=" * 80 + "\n  [MLflow Context Manager] get_context() CALLED\n" + "=" * 80
        print(debug_msg, file=sys.stderr, flush=True)

        # Set up MLflow from environment variables (CRITICAL for subprocesses)
        tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
        experiment_name = os.environ.get("MLFLOW_EXPERIMENT_NAME")

        if tracking_uri or experiment_name:
            from shared.mlflow_setup import setup_mlflow_cross_platform
            try:
                if not tracking_uri:
                    print(f"  [MLflow Context] WARNING: MLFLOW_TRACKING_URI not set in environment!",
                          file=sys.stderr, flush=True)

                if experiment_name:
                    # setup_mlflow_cross_platform handles both tracking URI and experiment setup
                    setup_mlflow_cross_platform(
                        experiment_name=experiment_name,
                        ml_client=None,  # Will use local tracking or env vars
                        fallback_to_local=True,
                    )
                    print(
                        f"  [MLflow Context] Set experiment from env: {experiment_name}", file=sys.stderr, flush=True)
                elif tracking_uri:
                    # If only tracking URI is set, set it manually
                    mlflow.set_tracking_uri(tracking_uri)
                    print(
                        f"  [MLflow Context] Set tracking URI from env: {tracking_uri[:50]}...", file=sys.stderr, flush=True)
            except Exception as e:
                print(
                    f"  [MLflow Context] Warning: Could not set up MLflow: {e}", file=sys.stderr, flush=True)

        # Debug: Print all MLflow-related environment variables
        mlflow_child = os.environ.get("MLFLOW_CHILD_RUN_ID")
        mlflow_parent = os.environ.get("MLFLOW_PARENT_RUN_ID")
        mlflow_trial = os.environ.get("MLFLOW_TRIAL_NUMBER")
        mlflow_experiment = os.environ.get("MLFLOW_EXPERIMENT_NAME")
        mlflow_tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")

        # Always print MLflow environment variables for debugging
        # Print to stderr to ensure visibility in subprocess logs
        debug_msg = "  [MLflow Context] Environment variables:"
        print(debug_msg, file=sys.stderr, flush=True)

        for var_name, var_value in [
            ("MLFLOW_CHILD_RUN_ID", mlflow_child),
            ("MLFLOW_PARENT_RUN_ID", mlflow_parent),
            ("MLFLOW_TRIAL_NUMBER", mlflow_trial),
            ("MLFLOW_EXPERIMENT_NAME", mlflow_experiment),
            ("MLFLOW_TRACKING_URI", mlflow_tracking_uri),
        ]:
            if var_name == "MLFLOW_TRACKING_URI" and var_value:
                display_value = f"{var_value[:50]}..."
            elif var_name in ["MLFLOW_CHILD_RUN_ID", "MLFLOW_PARENT_RUN_ID"] and var_value:
                display_value = f"{var_value[:12]}..."
            else:
                display_value = var_value if var_value else 'None'

            msg = f"    {var_name}: {display_value}"
            print(msg, file=sys.stderr, flush=True)

        # Check if we should use an existing child run ID (created in parent process)
        # This is the preferred method - child run was created with nested=True in parent
        child_run_id = os.environ.get("MLFLOW_CHILD_RUN_ID")
        if child_run_id:
            # Use the existing child run that was created in the parent process
            # This ensures proper parent-child relationship with Azure ML Workspace
            print(f"  [MLflow] Resuming child run: {child_run_id[:8]}...")

            @contextmanager
            def existing_child_run_context():
                # Resume the child run - MLflow allows resuming ended runs
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
            print(
                f"  [MLflow] Creating child run with parent: {parent_run_id[:12]}... (trial {trial_number})")
            # Use shared child run creation function
            from orchestration.jobs.tracking.mlflow_helpers import create_child_run
            return create_child_run(
                parent_run_id=parent_run_id,
                trial_number=trial_number,
                experiment_name=experiment_name,
            )
        else:
            # Create an independent run
            return mlflow.start_run()

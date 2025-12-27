"""MLflow tracking utilities for HPO sweeps.

Handles parent run creation, child run tracking, and best trial identification.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Optional

import mlflow
from shared.logging_utils import get_logger

logger = get_logger(__name__)


class MLflowSweepTracker:
    """Tracks MLflow runs for HPO sweeps."""

    def __init__(self, experiment_name: str):
        """
        Initialize sweep tracker.

        Args:
            experiment_name: MLflow experiment name.
        """
        self.experiment_name = experiment_name
        self._setup_experiment()

    def _setup_experiment(self) -> None:
        """Set up MLflow experiment."""
        try:
            # Check if MLflow tracking URI is already set (e.g., by notebook setup)
            current_tracking_uri = mlflow.get_tracking_uri()
            is_azure_ml = current_tracking_uri and "azureml" in current_tracking_uri.lower()

            if is_azure_ml:
                # Azure ML tracking is already configured, just set the experiment
                logger.debug(
                    f"Using existing Azure ML tracking URI: {current_tracking_uri[:50]}...")
                mlflow.set_experiment(self.experiment_name)
            else:
                # No Azure ML tracking set, use cross-platform setup
                from shared.mlflow_setup import setup_mlflow_cross_platform
                setup_mlflow_cross_platform(
                    experiment_name=self.experiment_name,
                    ml_client=None,  # Will use local tracking or env vars
                    fallback_to_local=True,
                )
        except Exception as e:
            logger.warning(f"Could not set MLflow experiment: {e}")
            logger.warning("Continuing without MLflow tracking...")

    @contextmanager
    def start_sweep_run(
        self,
        run_name: str,
        hpo_config: Dict[str, Any],
        backbone: str,
        study_name: str,
        checkpoint_config: Dict[str, Any],
        storage_path: Optional[Any],
        should_resume: bool,
    ):
        """
        Start a parent MLflow run for HPO sweep.

        Args:
            run_name: Name for the parent run.
            hpo_config: HPO configuration dictionary.
            backbone: Model backbone name.
            study_name: Optuna study name.
            checkpoint_config: Checkpoint configuration.
            storage_path: Path to checkpoint storage.
            should_resume: Whether this is a resumed run.

        Yields:
            Active MLflow run context.
        """
        try:
            with mlflow.start_run(run_name=run_name) as parent_run:
                self._log_sweep_metadata(
                    hpo_config, backbone, study_name, checkpoint_config, storage_path, should_resume
                )
                yield parent_run
        except Exception as e:
            logger.warning(f"MLflow tracking failed: {e}")
            logger.warning("Continuing HPO without MLflow tracking...")
            # Yield a dummy context manager that does nothing
            from contextlib import nullcontext
            with nullcontext():
                yield None

    def _log_sweep_metadata(
        self,
        hpo_config: Dict[str, Any],
        backbone: str,
        study_name: str,
        checkpoint_config: Dict[str, Any],
        storage_path: Optional[Any],
        should_resume: bool,
    ) -> None:
        """Log sweep metadata to MLflow."""
        objective_metric = hpo_config["objective"]["metric"]
        goal = hpo_config.get("objective", {}).get("goal", "maximize")
        max_trials = hpo_config["sampling"]["max_trials"]

        # Mark parent run as sweep job for Azure ML UI
        mlflow.set_tag("azureml.runType", "sweep")
        mlflow.set_tag("mlflow.runType", "sweep")
        mlflow.set_tag("azureml.sweep", "true")

        # Log primary metric and goal for Azure ML UI to identify best trial
        mlflow.log_param("primary_metric", objective_metric)
        mlflow.log_param("objective_goal", goal)

        # Log HPO parameters
        mlflow.log_param("backbone", backbone)
        mlflow.log_param("max_trials", max_trials)
        mlflow.log_param("study_name", study_name)
        mlflow.log_param("objective_metric", objective_metric)
        mlflow.log_param("checkpoint_enabled",
                         checkpoint_config.get("enabled", False))

        # Log checkpoint path (even if disabled, log None)
        if storage_path is not None:
            mlflow.log_param("checkpoint_path", str(storage_path.resolve()))
        else:
            mlflow.log_param("checkpoint_path", None)

        # Log checkpoint storage type
        mlflow.log_param(
            "checkpoint_storage_type", "sqlite" if storage_path else None
        )

        # Log resume status
        mlflow.log_param("resumed_from_checkpoint", should_resume)

    def log_final_metrics(
        self, study: Any, objective_metric: str, parent_run_id: str
    ) -> None:
        """
        Log final metrics and best trial information to parent run.

        Args:
            study: Completed Optuna study.
            objective_metric: Name of the objective metric.
            parent_run_id: ID of the parent MLflow run.
        """
        # Use optuna module to check trial state properly
        try:
            import optuna
            completed_trials = len([
                t for t in study.trials
                if t.state == optuna.trial.TrialState.COMPLETE
            ])
        except ImportError:
            # Fallback: count all trials as completed if we can't check state
            completed_trials = len(study.trials)

        mlflow.log_metric("n_trials", len(study.trials))
        mlflow.log_metric("n_completed_trials", completed_trials)

        if study.best_trial is not None and study.best_value is not None:
            # Log only the metric-specific name to avoid duplication
            mlflow.log_metric(f"best_{objective_metric}", study.best_value)

            # Log best hyperparameters
            for param_name, param_value in study.best_params.items():
                mlflow.log_param(f"best_{param_name}", param_value)

            # Find and log the best trial's MLflow run ID
            self._log_best_trial_id(study, parent_run_id)

    def _log_best_trial_id(self, study: Any, parent_run_id: str) -> None:
        """
        Find and log the best trial's MLflow run ID.

        Args:
            study: Completed Optuna study.
            parent_run_id: ID of the parent MLflow run.
        """
        try:
            client = mlflow.tracking.MlflowClient()
            active_run = mlflow.active_run()
            if active_run is None:
                raise ValueError("No active MLflow run")

            experiment_id = active_run.info.experiment_id

            # Query all child runs of this parent
            # Use both the tag filter and also search by experiment
            logger.debug(
                f"Searching for child runs with parent: {parent_run_id[:12]}... in experiment: {experiment_id}")

            all_runs = client.search_runs(
                experiment_ids=[experiment_id],
                filter_string=f"tags.mlflow.parentRunId = '{parent_run_id}'",
                max_results=1000,
            )

            logger.info(
                f"Found {len(all_runs)} child runs for parent {parent_run_id[:12]}...")

            # Map trial numbers to run IDs
            trial_to_run_id = {}
            for run in all_runs:
                trial_num_tag = run.data.tags.get("trial_number")
                parent_tag = run.data.tags.get("mlflow.parentRunId")
                logger.debug(
                    f"Child run {run.info.run_id[:12]}... - trial_number: {trial_num_tag}, "
                    f"parent: {parent_tag[:12] if parent_tag else 'None'}..."
                )
                if trial_num_tag:
                    try:
                        trial_num = int(trial_num_tag)
                        trial_to_run_id[trial_num] = run.info.run_id
                    except (ValueError, TypeError):
                        pass

            # Get the best trial's run ID
            best_trial_number = study.best_trial.number
            best_run_id = trial_to_run_id.get(best_trial_number)

            if best_run_id:
                # Log best trial run ID as both parameter and tag for Azure ML UI
                mlflow.log_param("best_trial_run_id", best_run_id)
                mlflow.set_tag("best_trial_run_id", best_run_id)
                mlflow.set_tag("best_trial_number", str(best_trial_number))
                logger.info(
                    f"Best trial: {best_trial_number} (run ID: {best_run_id[:12]}...)"
                )
            else:
                logger.warning(
                    f"Could not find MLflow run ID for best trial {best_trial_number}. "
                    f"Available trial numbers: {sorted(trial_to_run_id.keys())}"
                )
        except Exception as e:
            # Don't fail if we can't find the best trial run ID
            logger.warning(f"Could not retrieve best trial run ID: {e}")

    def log_tracking_info(self) -> None:
        """Log MLflow tracking URI information for user visibility."""
        tracking_uri = mlflow.get_tracking_uri()
        if tracking_uri:
            # Check if it's actually Azure ML (starts with azureml://)
            if tracking_uri.lower().startswith("azureml://"):
                logger.info("Using Azure ML Workspace for MLflow tracking")
                logger.debug(f"Tracking URI: {tracking_uri}")
            elif tracking_uri.startswith("sqlite://") or tracking_uri.startswith("file://"):
                logger.warning("Using LOCAL MLflow tracking (not Azure ML)")
                logger.debug(f"Tracking URI: {tracking_uri}")
                logger.info(
                    "To use Azure ML, ensure:\n"
                    "  1. config/mlflow.yaml has azure_ml.enabled: true\n"
                    "  2. Environment variables are set: AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP\n"
                    "  3. Azure ML SDK is installed: pip install azure-ai-ml azure-identity azureml-mlflow"
                )
            else:
                logger.info(f"Using MLflow tracking: {tracking_uri}")
        else:
            logger.warning("MLflow tracking URI not set")

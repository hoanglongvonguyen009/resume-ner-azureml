"""Trial execution utilities for HPO training runs.

Handles subprocess execution, environment setup, and metrics reading.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from shared.logging_utils import get_logger

logger = get_logger(__name__)


class TrialExecutor:
    """Executes a single training trial via subprocess and returns metrics."""

    def __init__(
        self,
        config_dir: Path,
        mlflow_experiment_name: str,
    ):
        """
        Initialize trial executor.

        Args:
            config_dir: Configuration directory path (ROOT_DIR / "config").
            mlflow_experiment_name: MLflow experiment name.
        """
        # Derive project root from config_dir (config_dir is ROOT_DIR / "config")
        self.root_dir = config_dir.parent
        self.config_dir = config_dir
        self.mlflow_experiment_name = mlflow_experiment_name

    def execute(
        self,
        trial_params: Dict[str, Any],
        dataset_path: str,
        backbone: str,
        output_dir: Path,
        train_config: Dict[str, Any],
        objective_metric: str = "macro-f1",
        fold_idx: Optional[int] = None,
        fold_splits_file: Optional[Path] = None,
    ) -> float:
        """
        Execute a single training trial with given hyperparameters.

        Args:
            trial_params: Hyperparameters for this trial.
            dataset_path: Path to dataset directory.
            backbone: Model backbone name.
            output_dir: Output directory for checkpoint.
            train_config: Training configuration dictionary.
            objective_metric: Name of the objective metric to optimize.
            fold_idx: Optional fold index for cross-validation.
            fold_splits_file: Optional path to fold splits file.

        Returns:
            Objective metric value (e.g., macro-f1).

        Raises:
            RuntimeError: If training trial fails.
        """
        # Build command and environment
        args = self._build_command(
            trial_params, dataset_path, backbone, train_config, fold_idx, fold_splits_file
        )
        env = self._setup_environment(trial_params, output_dir, fold_idx)

        # Execute training subprocess
        result = subprocess.run(
            args,
            cwd=self.root_dir,
            env=env,
            capture_output=True,
            text=True,
        )

        # Handle subprocess output
        self._log_subprocess_output(result)

        if result.returncode != 0:
            logger.error(f"Trial failed with return code {result.returncode}")
            logger.error(f"STDOUT:\n{result.stdout}")
            logger.error(f"STDERR:\n{result.stderr}")
            raise RuntimeError(f"Training trial failed: {result.stderr}")

        # Read metrics
        trial_output_dir = self._get_trial_output_dir(
            trial_params, output_dir, fold_idx)
        return self._read_metrics(trial_output_dir, objective_metric)

    def _build_command(
        self,
        trial_params: Dict[str, Any],
        dataset_path: str,
        backbone: str,
        train_config: Dict[str, Any],
        fold_idx: Optional[int],
        fold_splits_file: Optional[Path],
    ) -> list[str]:
        """Build command arguments for training subprocess."""
        args = [
            sys.executable,
            "-m",
            "training.train",
            "--data-asset",
            dataset_path,
            "--config-dir",
            str(self.config_dir),
            "--backbone",
            backbone,
        ]

        # Add hyperparameters from trial
        if "learning_rate" in trial_params:
            args.extend(
                ["--learning-rate", str(trial_params["learning_rate"])])
        if "batch_size" in trial_params:
            args.extend(["--batch-size", str(trial_params["batch_size"])])
        if "dropout" in trial_params:
            args.extend(["--dropout", str(trial_params["dropout"])])
        if "weight_decay" in trial_params:
            args.extend(["--weight-decay", str(trial_params["weight_decay"])])

        # Use minimal epochs for HPO (from train config or default to 1)
        epochs = train_config.get("training", {}).get("epochs", 1)
        args.extend(["--epochs", str(epochs)])

        # Enable early stopping for HPO
        args.extend(["--early-stopping-enabled", "true"])

        # Add fold-specific arguments if CV is enabled
        if fold_idx is not None:
            args.extend(["--fold-idx", str(fold_idx)])
        if fold_splits_file is not None:
            args.extend(["--fold-splits-file", str(fold_splits_file)])

        return args

    def _setup_environment(
        self,
        trial_params: Dict[str, Any],
        output_dir: Path,
        fold_idx: Optional[int],
    ) -> Dict[str, str]:
        """Set up environment variables for subprocess."""
        env = os.environ.copy()

        # Set output directory
        trial_output_dir = self._get_trial_output_dir(
            trial_params, output_dir, fold_idx)
        trial_output_dir.mkdir(parents=True, exist_ok=True)

        # Note: AzureMLOutputPathResolver converts output_name to uppercase, so use CHECKPOINT
        env["AZURE_ML_OUTPUT_CHECKPOINT"] = str(trial_output_dir)
        # Also set lowercase for backward compatibility
        env["AZURE_ML_OUTPUT_checkpoint"] = str(trial_output_dir)

        # Pass MLflow tracking URI and experiment name to subprocess
        try:
            import mlflow

            mlflow_tracking_uri = mlflow.get_tracking_uri()
            if mlflow_tracking_uri:
                env["MLFLOW_TRACKING_URI"] = mlflow_tracking_uri
            env["MLFLOW_EXPERIMENT_NAME"] = self.mlflow_experiment_name

            # Pass parent run ID to subprocess - subprocess will create child run
            # This is the correct approach for Azure ML nested runs
            active_run = mlflow.active_run()
            if active_run is not None:
                parent_run_id = active_run.info.run_id
                trial_number = str(trial_params.get("trial_number", "unknown"))
                
                # Pass parent run ID and trial number to subprocess
                # The subprocess will create the child run using create_child_run helper
                env["MLFLOW_PARENT_RUN_ID"] = parent_run_id
                env["MLFLOW_TRIAL_NUMBER"] = trial_number
                logger.debug(
                    f"Passing parent run ID to trial: {parent_run_id[:12]}... "
                    f"(trial {trial_number})"
                )
            else:
                logger.warning(
                    "No active MLflow run - trials will be independent runs"
                )
        except Exception as e:
            logger.warning(f"Could not get active run ID: {e}")

        # Add src directory to PYTHONPATH to allow relative imports in train.py
        src_dir = str(self.root_dir / "src")
        current_pythonpath = env.get("PYTHONPATH", "")
        if current_pythonpath:
            env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{current_pythonpath}"
        else:
            env["PYTHONPATH"] = src_dir

        return env

    def _get_trial_output_dir(
        self,
        trial_params: Dict[str, Any],
        output_dir: Path,
        fold_idx: Optional[int],
    ) -> Path:
        """Get trial-specific output directory path."""
        run_id = trial_params.get("run_id", "")
        run_suffix = f"_{run_id}" if run_id else ""
        fold_suffix = f"_fold{fold_idx}" if fold_idx is not None else ""
        trial_output_dir = output_dir / (
            f"trial_{trial_params.get('trial_number', 'unknown')}"
            f"{run_suffix}{fold_suffix}"
        )
        return trial_output_dir

    def _log_subprocess_output(self, result: subprocess.CompletedProcess) -> None:
        """Log relevant subprocess output for debugging."""
        mlflow_lines_found = False

        if result.stdout:
            for line in result.stdout.split("\n"):
                line_lower = line.lower()
                if any(
                    keyword in line_lower
                    for keyword in ["[mlflow", "mlflow", "mlflow_context"]
                ):
                    logger.debug(f"[Subprocess STDOUT] {line}")
                    mlflow_lines_found = True

        if result.stderr:
            for line in result.stderr.split("\n"):
                line_lower = line.lower()
                if any(
                    keyword in line_lower
                    for keyword in ["[mlflow", "mlflow", "mlflow_context"]
                ):
                    logger.debug(f"[Subprocess STDERR] {line}")
                    mlflow_lines_found = True

        if not mlflow_lines_found and result.returncode == 0:
            logger.debug("No MLflow debug output found in subprocess")
            logger.debug(
                "This may indicate the context manager isn't being called")
            if result.stderr:
                stderr_lines = [l for l in result.stderr.split(
                    "\n") if l.strip()][:10]
                if stderr_lines:
                    logger.debug("First 10 lines of stderr:")
                    for line in stderr_lines:
                        logger.debug(f"  {line}")

    def _read_metrics(
        self, trial_output_dir: Path, objective_metric: str
    ) -> float:
        """
        Read metrics from trial output directory.

        Args:
            trial_output_dir: Directory containing trial outputs.
            objective_metric: Name of the objective metric to read.

        Returns:
            Metric value, or 0.0 if not found.

        Raises:
            RuntimeError: If metrics file cannot be read and MLflow fallback fails.
        """
        metrics_file = trial_output_dir / "metrics.json"

        # If trial-specific file doesn't exist, check default location
        if not metrics_file.exists():
            default_metrics = self.root_dir / "outputs" / "metrics.json"
            if default_metrics.exists():
                logger.warning(
                    f"Trial-specific metrics not found at {metrics_file}. "
                    f"Falling back to default location: {default_metrics}. "
                    "This may read metrics from a different trial!"
                )
                metrics_file = default_metrics

        if metrics_file.exists():
            try:
                with open(metrics_file, "r") as f:
                    metrics = json.load(f)
                    if objective_metric in metrics:
                        return float(metrics[objective_metric])
                    else:
                        logger.warning(
                            f"Objective metric '{objective_metric}' not found in metrics.json. "
                            f"Available metrics: {list(metrics.keys())}"
                        )
            except Exception as e:
                logger.warning(
                    f"Could not read metrics.json from {metrics_file}: {e}")

        # Fallback: try to read from MLflow
        try:
            import mlflow

            mlflow.set_experiment(self.mlflow_experiment_name)
            experiment = mlflow.get_experiment_by_name(
                self.mlflow_experiment_name)
            if experiment:
                runs = mlflow.search_runs(
                    experiment_ids=[experiment.experiment_id],
                    max_results=1,
                    order_by=["start_time DESC"],
                )
                if not runs.empty:
                    run_id = runs.iloc[0]["run_id"]
                    run = mlflow.get_run(run_id)
                    metrics = run.data.metrics
                    if objective_metric in metrics:
                        return float(metrics[objective_metric])

            logger.warning(
                f"Objective metric '{objective_metric}' not found in MLflow"
            )
            return 0.0
        except Exception as e:
            logger.warning(f"Could not retrieve metrics from MLflow: {e}")
            return 0.0

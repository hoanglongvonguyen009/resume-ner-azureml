
"""Local hyperparameter optimization using Optuna."""

from __future__ import annotations
import logging
from shared.json_cache import save_json
from shared.logging_utils import get_logger

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional, List, Tuple

import mlflow
import numpy as np

from .checkpoint_manager import resolve_storage_path, get_storage_uri
from .search_space import translate_search_space_to_optuna
from ..tracking.mlflow_tracker import MLflowSweepTracker
from .hpo_helpers import (
    generate_run_id,
    setup_checkpoint_storage,
    create_study_name,
    create_mlflow_run_name,
)

logger = get_logger(__name__)

# Suppress Optuna's verbose output to reduce log clutter
logging.getLogger("optuna").setLevel(logging.WARNING)

# Lazy import optuna - only import when actually needed for local execution
# This prevents optuna from being required when using Azure ML orchestration


def _import_optuna():
    """Lazy import optuna and related modules."""
    try:
        import optuna
        from optuna.pruners import MedianPruner
        from optuna.samplers import RandomSampler
        from optuna.trial import Trial
        return optuna, MedianPruner, RandomSampler, Trial
    except ImportError as e:
        raise ImportError(
            "optuna is required for local HPO execution. "
            "Install it with: pip install optuna"
        ) from e


def create_optuna_pruner(hpo_config: Dict[str, Any]) -> Optional[Any]:
    """
    Create Optuna pruner from HPO config early termination policy.

    Args:
        hpo_config: HPO configuration dictionary.

    Returns:
        Optuna pruner instance or None if no early termination configured.
    """
    if "early_termination" not in hpo_config:
        return None

    # Lazy import optuna
    _, MedianPruner, _, _ = _import_optuna()

    et_cfg = hpo_config["early_termination"]
    policy = et_cfg.get("policy", "").lower()

    if policy == "bandit":
        # Optuna doesn't have exact bandit pruner, use MedianPruner as closest alternative
        # Bandit policy: stop if trial is worse than best by slack_factor
        # MedianPruner: stop if trial is worse than median
        return MedianPruner(
            n_startup_trials=et_cfg.get("delay_evaluation", 2),
            n_warmup_steps=et_cfg.get("evaluation_interval", 1),
        )
    elif policy == "median":
        return MedianPruner(
            n_startup_trials=et_cfg.get("delay_evaluation", 2),
            n_warmup_steps=et_cfg.get("evaluation_interval", 1),
        )
    else:
        return None


def run_training_trial(
    trial_params: Dict[str, Any],
    dataset_path: str,
    config_dir: Path,
    backbone: str,
    output_dir: Path,
    train_config: Dict[str, Any],
    mlflow_experiment_name: str,
    objective_metric: str = "macro-f1",
    fold_idx: Optional[int] = None,
    fold_splits_file: Optional[Path] = None,
    parent_run_id: Optional[str] = None,
) -> float:
    """
    Execute a single training trial with given hyperparameters.

    Args:
        trial_params: Hyperparameters for this trial.
        dataset_path: Path to dataset directory.
        config_dir: Path to configuration directory.
        backbone: Model backbone name.
        output_dir: Output directory for checkpoint.
        train_config: Training configuration dictionary.
        mlflow_experiment_name: MLflow experiment name.
        objective_metric: Name of the objective metric to optimize.
        fold_idx: Optional fold index for cross-validation.
        fold_splits_file: Optional path to fold splits file.

    Returns:
        Objective metric value (e.g., macro-f1).
    """
    import json
    import subprocess

    # Build command arguments
    # Derive project root from config_dir (config_dir is ROOT_DIR / "config")
    root_dir = config_dir.parent
    # Run train.py as a module to allow relative imports to work
    # This requires src/ to be in PYTHONPATH (set in env below)
    args = [
        sys.executable,
        "-m",
        "training.train",
        "--data-asset",
        dataset_path,
        "--config-dir",
        str(config_dir),
        "--backbone",
        backbone,
    ]

    # Add hyperparameters from trial
    if "learning_rate" in trial_params:
        args.extend(["--learning-rate", str(trial_params["learning_rate"])])
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

    # Set output directory with unique run ID to prevent overwriting
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = trial_params.get('run_id', '')
    run_suffix = f"_{run_id}" if run_id else ""
    fold_suffix = f"_fold{fold_idx}" if fold_idx is not None else ""
    trial_output_dir = output_dir / \
        f"trial_{trial_params.get('trial_number', 'unknown')}{run_suffix}{fold_suffix}"
    trial_output_dir.mkdir(parents=True, exist_ok=True)

    # Create MLflow experiment if it doesn't exist
    mlflow.set_experiment(mlflow_experiment_name)

    # Set environment variables for output and MLflow (train.py will use these)
    env = os.environ.copy()
    # Note: AzureMLOutputPathResolver converts output_name to uppercase, so use CHECKPOINT
    env["AZURE_ML_OUTPUT_CHECKPOINT"] = str(trial_output_dir)
    # Also set lowercase for backward compatibility
    env["AZURE_ML_OUTPUT_checkpoint"] = str(trial_output_dir)

    # Pass MLflow tracking URI and experiment name to subprocess
    mlflow_tracking_uri = mlflow.get_tracking_uri()
    if mlflow_tracking_uri:
        env["MLFLOW_TRACKING_URI"] = mlflow_tracking_uri
    env["MLFLOW_EXPERIMENT_NAME"] = mlflow_experiment_name

    # Pass parent run ID to subprocess
    # If parent_run_id is provided (e.g., from trial run), use it
    # Otherwise, try to get from active MLflow run
    try:
        if parent_run_id:
            # Use provided parent run ID (e.g., from trial run for k-fold CV)
            env["MLFLOW_PARENT_RUN_ID"] = parent_run_id
            logger.debug(
                f"Using provided parent run ID: {parent_run_id[:12]}... (trial {trial_params.get('trial_number', 'unknown')}, fold {fold_idx if fold_idx is not None else 'N/A'})")
        else:
            # Try to get from active MLflow run (for single training without CV)
            active_run = mlflow.active_run()
            if active_run is not None:
                parent_run_id = active_run.info.run_id
                env["MLFLOW_PARENT_RUN_ID"] = parent_run_id
                logger.debug(
                    f"Using active run as parent: {parent_run_id[:12]}... (trial {trial_params.get('trial_number', 'unknown')})")

        # Always pass trial number and fold index for run naming
        env["MLFLOW_TRIAL_NUMBER"] = str(
            trial_params.get("trial_number", "unknown"))
        if fold_idx is not None:
            env["MLFLOW_FOLD_IDX"] = str(fold_idx)
    except Exception as e:
        # If MLflow is not available or no active run, continue without parent run ID
        logger.warning(f"Could not get parent run ID: {e}")

    # Add src directory to PYTHONPATH to allow relative imports in train.py
    src_dir = str(root_dir / "src")
    current_pythonpath = env.get("PYTHONPATH", "")
    if current_pythonpath:
        env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{current_pythonpath}"
    else:
        env["PYTHONPATH"] = src_dir

    # Run training (train.py will handle MLflow logging internally)
    result = subprocess.run(
        args,
        cwd=root_dir,
        env=env,
        capture_output=True,
        text=True,
    )

    # Log subprocess output for debugging (simplified - only errors)
    if result.returncode != 0:
        logger.error(f"Trial failed with return code {result.returncode}")
        logger.error(f"STDOUT:\n{result.stdout}")
        logger.error(f"STDERR:\n{result.stderr}")
        raise RuntimeError(f"Training trial failed: {result.stderr}")

    # Try to read metrics from metrics.json file (created by train.py)
    # This is more reliable than querying MLflow
    # IMPORTANT: Always check trial-specific location first to avoid reading wrong metrics
    metrics_file = trial_output_dir / "metrics.json"

    # If trial-specific file doesn't exist, check if metrics were saved to default location
    # This can happen if the platform adapter doesn't properly detect AZURE_ML_OUTPUT_checkpoint
    if not metrics_file.exists():
        # Check if train.py saved to default outputs directory (due to platform adapter behavior)
        default_metrics = Path(root_dir) / "outputs" / "metrics.json"
        if default_metrics.exists():
            # Only use this as a last resort - it might be from a different trial!
            logger.warning(
                f"Trial-specific metrics not found at {metrics_file}. "
                f"Falling back to default location: {default_metrics}. "
                f"This may read metrics from a different trial!"
            )
            metrics_file = default_metrics

    # Try to read from metrics.json file first
    from shared.metrics_utils import read_metrics_from_file, read_metric_from_mlflow
    from orchestration.constants import METRICS_FILENAME

    default_metrics = Path(root_dir) / "outputs" / METRICS_FILENAME
    metric_value = read_metrics_from_file(
        metrics_file=metrics_file,
        objective_metric=objective_metric,
        fallback_file=default_metrics if not metrics_file.exists() else None,
    )

    if metric_value is not None:
        return metric_value

    # Log error if file doesn't exist
    if not metrics_file.exists() and not default_metrics.exists():
        logger.error(
            f"metrics.json not found at expected location: {trial_output_dir / METRICS_FILENAME}. "
            f"Trial output dir: {trial_output_dir}, Root dir: {root_dir}, "
            f"AZURE_ML_OUTPUT_checkpoint env var: {os.environ.get('AZURE_ML_OUTPUT_checkpoint', 'NOT SET')}"
        )

    # Fallback: try to read from MLflow
    metric_value = read_metric_from_mlflow(
        experiment_name=mlflow_experiment_name,
        objective_metric=objective_metric,
    )

    return metric_value if metric_value is not None else 0.0


def run_training_trial_with_cv(
    trial_params: Dict[str, Any],
    dataset_path: str,
    config_dir: Path,
    backbone: str,
    output_dir: Path,
    train_config: Dict[str, Any],
    mlflow_experiment_name: str,
    objective_metric: str,
    fold_splits: List[Tuple[List[int], List[int]]],
    fold_splits_file: Path,
    hpo_parent_run_id: Optional[str] = None,
) -> Tuple[float, List[float]]:
    """
    Run training trial with k-fold cross-validation.

    Creates a nested structure:
    - Trial run (child of HPO parent) - contains aggregated metrics
    - Fold runs (children of trial run) - one per fold

    Args:
        trial_params: Hyperparameters for this trial.
        dataset_path: Path to dataset directory.
        config_dir: Path to configuration directory.
        backbone: Model backbone name.
        output_dir: Output directory for checkpoints.
        train_config: Training configuration dictionary.
        mlflow_experiment_name: MLflow experiment name.
        objective_metric: Name of the objective metric to optimize.
        fold_splits: List of (train_indices, val_indices) tuples for each fold.
        fold_splits_file: Path to file containing fold splits (for train.py).
        hpo_parent_run_id: Optional HPO parent run ID to create trial run as child.

    Returns:
        Tuple of (average_metric, fold_metrics) where:
        - average_metric: Average metric across all folds
        - fold_metrics: List of metrics for each fold
    """
    # Create trial-level run (child of HPO parent) if parent is provided
    trial_run_id = None
    if hpo_parent_run_id:
        try:
            client = mlflow.tracking.MlflowClient()
            active_run = mlflow.active_run()
            if active_run:
                experiment_id = active_run.info.experiment_id
                trial_number = trial_params.get("trial_number", "unknown")

                # Create trial run as child of HPO parent
                trial_run = client.create_run(
                    experiment_id=experiment_id,
                    tags={
                        "mlflow.parentRunId": hpo_parent_run_id,
                        "azureml.runType": "trial",
                        "azureml.trial": "true",
                        "trial_number": str(trial_number),
                    },
                    run_name=f"trial_{trial_number}"
                )
                trial_run_id = trial_run.info.run_id
                logger.debug(
                    f"Created trial run: {trial_run_id[:12]}... (trial {trial_number})")
        except Exception as e:
            logger.warning(f"Could not create trial run: {e}")
            # Continue without trial run - folds will be children of HPO parent

    fold_metrics = []

    for fold_idx, (train_indices, val_indices) in enumerate(fold_splits):
        # Run training for this fold
        # Pass trial_run_id as parent (if available), otherwise use hpo_parent_run_id
        fold_parent_id = trial_run_id if trial_run_id else hpo_parent_run_id
        fold_metric = run_training_trial(
            trial_params=trial_params,
            dataset_path=dataset_path,
            config_dir=config_dir,
            backbone=backbone,
            output_dir=output_dir,
            train_config=train_config,
            mlflow_experiment_name=mlflow_experiment_name,
            objective_metric=objective_metric,
            fold_idx=fold_idx,
            fold_splits_file=fold_splits_file,
            parent_run_id=fold_parent_id,  # Use trial run as parent for folds
        )
        fold_metrics.append(fold_metric)

    # Calculate average metric
    average_metric = np.mean(fold_metrics)

    # Log aggregated metrics to trial run using client (no need to start run)
    if trial_run_id:
        try:
            client = mlflow.tracking.MlflowClient()

            # Log aggregated metrics
            client.log_metric(trial_run_id, objective_metric, average_metric)
            client.log_metric(trial_run_id, "cv_std",
                              float(np.std(fold_metrics)))
            client.log_metric(trial_run_id, "cv_mean", average_metric)

            # Log individual fold metrics
            for i, fold_metric in enumerate(fold_metrics):
                client.log_metric(
                    trial_run_id, f"fold_{i}_{objective_metric}", fold_metric)

            # Log hyperparameters to trial run
            for param_name, param_value in trial_params.items():
                if param_name not in ["trial_number", "run_id", "backbone"]:
                    client.log_param(trial_run_id, param_name, param_value)

            # End the trial run to mark it as completed
            client.set_terminated(trial_run_id, status="FINISHED")

            logger.debug(
                f"Logged aggregated metrics to trial run: {trial_run_id[:12]}... and marked as completed")
        except Exception as e:
            logger.warning(f"Could not log metrics to trial run: {e}")

    return average_metric, fold_metrics


def create_local_hpo_objective(
    dataset_path: str,
    config_dir: Path,
    backbone: str,
    hpo_config: Dict[str, Any],
    train_config: Dict[str, Any],
    output_base_dir: Path,
    mlflow_experiment_name: str,
    objective_metric: str = "macro-f1",
    k_folds: Optional[int] = None,
    fold_splits_file: Optional[Path] = None,
    run_id: Optional[str] = None,
) -> Tuple[Callable[[Any], float], Callable[[], None]]:
    # Global state for checkpoint cleanup
    # Use lists/dicts to allow modification in closure
    best_trial_id = [None]  # Current best trial number
    best_score = [None]  # Current best score
    # trial_id -> list of checkpoint paths (one per fold for CV, single for non-CV)
    checkpoint_map = {}
    completed_trials = []  # Ordered list of completed trial numbers

    """
    Create Optuna objective function for local HPO.

    Args:
        dataset_path: Path to dataset directory.
        config_dir: Path to configuration directory.
        backbone: Model backbone name.
        hpo_config: HPO configuration dictionary.
        train_config: Training configuration dictionary.
        output_base_dir: Base output directory for all trials.
        mlflow_experiment_name: MLflow experiment name.

    Returns:
        Objective function that takes an Optuna trial and returns metric value.
    """
    # Load or create fold splits if k-fold CV is enabled
    fold_splits = None
    if k_folds is not None and k_folds > 1:
        if fold_splits_file and fold_splits_file.exists():
            # Load existing splits
            from training.cv_utils import load_fold_splits
            fold_splits, _ = load_fold_splits(fold_splits_file)
        elif fold_splits_file:
            # Create new splits and save them
            from training.data import load_dataset
            from training.cv_utils import create_kfold_splits, save_fold_splits

            dataset = load_dataset(dataset_path)
            train_data = dataset.get("train", [])

            k_fold_config = hpo_config.get("k_fold", {})
            random_seed = k_fold_config.get("random_seed", 42)
            shuffle = k_fold_config.get("shuffle", True)
            stratified = k_fold_config.get("stratified", False)

            fold_splits = create_kfold_splits(
                dataset=train_data,
                k=k_folds,
                random_seed=random_seed,
                shuffle=shuffle,
                stratified=stratified,
            )

            # Save splits for reproducibility
            save_fold_splits(
                fold_splits,
                fold_splits_file,
                metadata={
                    "k": k_folds,
                    "random_seed": random_seed,
                    "shuffle": shuffle,
                    "stratified": stratified,
                }
            )

    def objective(trial: Any) -> float:
        # Sample hyperparameters
        # Exclude "backbone" from search space since it's fixed per study
        trial_params = translate_search_space_to_optuna(
            hpo_config, trial, exclude_params=["backbone"])
        # Set the fixed backbone for this study
        trial_params["backbone"] = backbone
        trial_params["trial_number"] = trial.number
        trial_params["run_id"] = run_id  # Pass run_id to trial functions

        # Don't create child runs in parent process - let subprocess create them
        # This avoids issues with ended runs and ensures training logs to the correct run
        # We'll pass the parent run ID and let the subprocess create nested child runs

        # Get HPO parent run ID for nested structure (trial -> folds)
        hpo_parent_run_id = None
        try:
            active_run = mlflow.active_run()
            if active_run:
                hpo_parent_run_id = active_run.info.run_id
        except Exception:
            pass

        # Run training with or without CV
        if fold_splits is not None:
            # Run k-fold CV with nested structure
            average_metric, fold_metrics = run_training_trial_with_cv(
                trial_params=trial_params,
                dataset_path=dataset_path,
                config_dir=config_dir,
                backbone=backbone,
                output_dir=output_base_dir,
                train_config=train_config,
                mlflow_experiment_name=mlflow_experiment_name,
                objective_metric=objective_metric,
                fold_splits=fold_splits,
                fold_splits_file=fold_splits_file,
                hpo_parent_run_id=hpo_parent_run_id,  # Pass HPO parent to create trial run
            )

            # Log CV statistics to trial user attributes
            trial.set_user_attr("cv_mean", float(average_metric))
            trial.set_user_attr("cv_std", float(np.std(fold_metrics)))
            trial.set_user_attr("cv_fold_metrics", [
                                float(m) for m in fold_metrics])

            metric_value = average_metric
        else:
            # Run single training (no CV)
            metric_value = run_training_trial(
                trial_params=trial_params,
                dataset_path=dataset_path,
                config_dir=config_dir,
                backbone=backbone,
                output_dir=output_base_dir,
                train_config=train_config,
                mlflow_experiment_name=mlflow_experiment_name,
                objective_metric=objective_metric,
            )

        # Store additional metrics in trial user attributes for callback display
        # Try to read full metrics from the trial output directory
        # Use run_id from closure (parameter) - it was set in trial_params at line 432
        # Use closure variable directly to avoid UnboundLocalError
        run_suffix = f"_{run_id}" if run_id else ""
        if fold_splits is not None:
            # CV: read from last fold's output (fold indices are 0-based, so last is len(fold_splits)-1)
            # Fold output directory format: trial_{number}_{run_id}_fold{fold_idx}
            last_fold_idx = len(fold_splits) - 1
            trial_output_dir = output_base_dir / \
                f"trial_{trial.number}{run_suffix}_fold{last_fold_idx}"
            metrics_file = trial_output_dir / "metrics.json"
        else:
            # Single training: read from trial output directory
            # Format: trial_{number}_{run_id}
            trial_output_dir = output_base_dir / \
                f"trial_{trial.number}{run_suffix}"
            metrics_file = trial_output_dir / "metrics.json"

        if metrics_file.exists():
            try:
                import json
                with open(metrics_file, "r") as f:
                    all_metrics = json.load(f)
                    # Store key metrics in user attributes for callback
                    if "macro-f1-span" in all_metrics:
                        trial.set_user_attr("macro_f1_span", float(
                            all_metrics["macro-f1-span"]))
                    if "loss" in all_metrics:
                        trial.set_user_attr("loss", float(all_metrics["loss"]))
                    if "per_entity" in all_metrics and isinstance(all_metrics["per_entity"], dict):
                        entity_count = len(all_metrics["per_entity"])
                        trial.set_user_attr("entity_count", entity_count)
                        # Store average entity F1
                        entity_f1s = [
                            v.get("f1", 0.0)
                            for v in all_metrics["per_entity"].values()
                            if isinstance(v, dict) and isinstance(v.get("f1"), (int, float))
                        ]
                        if entity_f1s:
                            trial.set_user_attr("avg_entity_f1", float(
                                sum(entity_f1s) / len(entity_f1s)))
            except Exception:
                pass  # Silently fail if we can't read metrics

        # Report to Optuna
        trial.report(metric_value, step=0)

        # Check if we should clean up non-best checkpoints
        # This happens after trial completes, so we can check if it's best
        checkpoint_config = hpo_config.get("checkpoint", {})
        save_only_best = checkpoint_config.get("save_only_best", False)

        if save_only_best:
            # Helper function to get checkpoint paths for a trial
            def get_checkpoint_paths(trial_num: int) -> List[Path]:
                """Get all checkpoint paths for a trial (all folds for CV, single for non-CV)."""
                run_suffix = f"_{run_id}" if run_id else ""
                paths = []
                if fold_splits is not None:
                    # CV: get checkpoints from all folds
                    for fold_idx in range(len(fold_splits)):
                        checkpoint_dir = (
                            output_base_dir /
                            f"trial_{trial_num}{run_suffix}_fold{fold_idx}" /
                            "checkpoint"
                        )
                        if checkpoint_dir.exists():
                            paths.append(checkpoint_dir)
                else:
                    # Single training: get single checkpoint
                    checkpoint_dir = (
                        output_base_dir /
                        f"trial_{trial_num}{run_suffix}" /
                        "checkpoint"
                    )
                    if checkpoint_dir.exists():
                        paths.append(checkpoint_dir)
                return paths

            # Helper function to delete checkpoint paths
            def delete_checkpoint_paths(paths: List[Path], trial_num: int) -> None:
                """Delete checkpoint paths and log the operation."""
                import shutil
                for path in paths:
                    try:
                        shutil.rmtree(path)
                        logger.debug(
                            f"Deleted checkpoint for trial {trial_num}: {path}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Could not delete checkpoint for trial {trial_num} at {path}: {e}"
                        )

            try:
                # 1. Register checkpoint
                trial_checkpoint_paths = get_checkpoint_paths(trial.number)
                if trial_checkpoint_paths:
                    checkpoint_map[trial.number] = trial_checkpoint_paths
                completed_trials.append(trial.number)

                # 2. Initialize state from existing study (for resume scenarios)
                if best_trial_id[0] is None:
                    # Check if study has existing completed trials (resume scenario)
                    optuna_module, _, _, _ = _import_optuna()
                    try:
                        study = trial.study
                        goal = hpo_config["objective"]["goal"]

                        # Find best completed trial from existing study
                        best_existing_trial = None
                        best_existing_value = None

                        for t in study.trials:
                            if (t.state == optuna_module.trial.TrialState.COMPLETE and
                                t.value is not None and
                                    t.number != trial.number):  # Exclude current trial

                                # Register existing trial's checkpoint if it exists
                                existing_paths = get_checkpoint_paths(t.number)
                                if existing_paths:
                                    checkpoint_map[t.number] = existing_paths
                                # Note: Don't add to completed_trials - those are already in the study,
                                # we just need to track checkpoints and find the best

                                # Track best existing trial
                                if best_existing_value is None:
                                    best_existing_trial = t.number
                                    best_existing_value = t.value
                                else:
                                    if goal == "maximize":
                                        if t.value > best_existing_value:
                                            best_existing_trial = t.number
                                            best_existing_value = t.value
                                    else:  # minimize
                                        if t.value < best_existing_value:
                                            best_existing_trial = t.number
                                            best_existing_value = t.value

                        # Initialize state with best existing trial if found
                        if best_existing_trial is not None:
                            best_trial_id[0] = best_existing_trial
                            best_score[0] = best_existing_value
                            logger.debug(
                                f"Resumed: Found existing best trial {best_existing_trial} "
                                f"(metric={best_existing_value:.6f}) from {len([t for t in study.trials if t.state == optuna_module.trial.TrialState.COMPLETE])} completed trials"
                            )
                        else:
                            # No existing completed trials - this is truly the first trial
                            best_trial_id[0] = trial.number
                            best_score[0] = metric_value
                            logger.debug(
                                f"First trial {trial.number} is best (metric={metric_value:.6f})"
                            )
                            return metric_value
                    except (AttributeError, Exception) as e:
                        # If we can't access study, assume this is the first trial
                        best_trial_id[0] = trial.number
                        best_score[0] = metric_value
                        logger.debug(
                            f"Could not access study, assuming first trial {trial.number} "
                            f"(metric={metric_value:.6f}): {e}"
                        )
                        return metric_value

                # 3. Check if this is a new best trial
                goal = hpo_config["objective"]["goal"]
                is_new_best = False

                if goal == "maximize":
                    is_new_best = metric_value > best_score[0]
                else:  # minimize
                    is_new_best = metric_value < best_score[0]

                if is_new_best:
                    # New best trial found - delete ALL non-best checkpoints
                    old_best = best_trial_id[0]
                    best_trial_id[0] = trial.number
                    best_score[0] = metric_value

                    logger.debug(
                        f"New best trial {trial.number} (metric={metric_value:.6f}, "
                        f"previous best: trial {old_best})"
                    )

                    # Delete all non-best checkpoints
                    for trial_id, checkpoint_paths in list(checkpoint_map.items()):
                        if trial_id != best_trial_id[0]:
                            delete_checkpoint_paths(checkpoint_paths, trial_id)
                            del checkpoint_map[trial_id]

                    return metric_value

                # 4. Not a new best - delete this trial's checkpoint immediately
                # Since we know the best trial, we can safely delete non-best checkpoints
                logger.debug(
                    f"Trial {trial.number} is not best (metric={metric_value:.6f}, "
                    f"best: trial {best_trial_id[0]} with {best_score[0]:.6f})"
                )

                # Delete this non-best trial's checkpoint
                if trial.number in checkpoint_map:
                    delete_checkpoint_paths(
                        checkpoint_map[trial.number], trial.number)
                    del checkpoint_map[trial.number]

            except Exception as e:
                # Don't fail HPO if checkpoint cleanup fails
                logger.warning(
                    f"Error during checkpoint cleanup for trial {trial.number}: {e}"
                )

        return metric_value

    def cleanup_non_best_checkpoints() -> None:
        """Final cleanup: delete all non-best checkpoints after HPO completes."""
        checkpoint_config = hpo_config.get("checkpoint", {})
        save_only_best = checkpoint_config.get("save_only_best", False)

        if not save_only_best:
            return

        if best_trial_id[0] is None:
            return

        # Helper function to delete checkpoint paths
        def delete_checkpoint_paths(paths: List[Path], trial_num: int) -> None:
            """Delete checkpoint paths and log the operation."""
            import shutil
            for path in paths:
                try:
                    shutil.rmtree(path)
                    logger.debug(
                        f"Deleted checkpoint for trial {trial_num}: {path}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Could not delete checkpoint for trial {trial_num} at {path}: {e}"
                    )

        # Delete all non-best checkpoints
        for trial_id, checkpoint_paths in list(checkpoint_map.items()):
            if trial_id != best_trial_id[0]:
                delete_checkpoint_paths(checkpoint_paths, trial_id)
                del checkpoint_map[trial_id]

        logger.info(
            f"Final cleanup: kept checkpoint for best trial {best_trial_id[0]} "
            f"(metric={best_score[0]:.6f}), deleted {len(completed_trials) - 1} non-best checkpoints"
        )

    return objective, cleanup_non_best_checkpoints


def run_local_hpo_sweep(
    dataset_path: str,
    config_dir: Path,
    backbone: str,
    hpo_config: Dict[str, Any],
    train_config: Dict[str, Any],
    output_dir: Path,
    mlflow_experiment_name: str,
    k_folds: Optional[int] = None,
    fold_splits_file: Optional[Path] = None,
    checkpoint_config: Optional[Dict[str, Any]] = None,
    restore_from_drive: Optional[Callable[[Path], bool]] = None,
) -> Any:
    """
    Run a local hyperparameter optimization sweep using Optuna.

    Args:
        dataset_path: Path to dataset directory.
        config_dir: Path to configuration directory.
        backbone: Model backbone name.
        hpo_config: HPO configuration dictionary.
        train_config: Training configuration dictionary.
        output_dir: Base output directory for all trials.
        mlflow_experiment_name: MLflow experiment name.
        k_folds: Optional number of k-folds for cross-validation.
        fold_splits_file: Optional path to fold splits file.
        checkpoint_config: Optional checkpoint configuration dict with 'enabled', 
                          'storage_path', and 'auto_resume' keys.
        restore_from_drive: Optional function to restore checkpoint from Drive if missing.
                          Function should take a Path and return bool (True if restored).

    Returns:
        Optuna study object with completed trials.
    """
    # Lazy import optuna
    optuna, _, RandomSampler, _ = _import_optuna()

    objective_metric = hpo_config["objective"]["metric"]
    goal = hpo_config["objective"]["goal"]
    direction = "maximize" if goal == "maximize" else "minimize"

    # Create pruner
    pruner = create_optuna_pruner(hpo_config)

    # Create sampler
    algorithm = hpo_config["sampling"]["algorithm"].lower()
    if algorithm == "random":
        sampler = RandomSampler()
    else:
        sampler = RandomSampler()  # Default to random

    # Check if checkpointing is enabled
    checkpoint_enabled = checkpoint_config is not None and checkpoint_config.get(
        "enabled", False)

    # Generate unique run ID
    run_id = generate_run_id()

    # Resolve study_name FIRST (needed for {study_name} placeholder in storage_path)
    # Use temporary should_resume=False for initial study_name resolution
    # We'll recalculate should_resume after checking if study exists
    study_name = create_study_name(
        backbone, run_id, should_resume=False, checkpoint_config=checkpoint_config, hpo_config=hpo_config
    )

    # Set up checkpoint storage with resolved study_name
    storage_path, storage_uri, should_resume = setup_checkpoint_storage(
        output_dir, checkpoint_config, backbone, study_name, restore_from_drive=restore_from_drive
    )

    if should_resume:
        logger.info(
            f"[HPO] Resuming optimization for {backbone} from checkpoint...")
        logger.debug(f"Checkpoint: {storage_path}")
        try:
            study = optuna.create_study(
                direction=direction,
                sampler=sampler,
                pruner=pruner,
                study_name=study_name,
                storage=storage_uri,
                load_if_exists=True,
            )

            # Check if HPO is already complete
            user_attrs = study.user_attrs if hasattr(
                study, 'user_attrs') else {}
            hpo_complete = user_attrs.get(
                "hpo_complete", "false").lower() == "true"
            checkpoint_uploaded = user_attrs.get(
                "checkpoint_uploaded", "false").lower() == "true"

            if hpo_complete and checkpoint_uploaded:
                best_trial_num = user_attrs.get("best_trial_number", "unknown")
                completion_time = user_attrs.get(
                    "completion_timestamp", "unknown")
                logger.info(
                    f"✓ HPO already completed and checkpoint uploaded (best trial: {best_trial_num}, "
                    f"completed: {completion_time}). Skipping HPO execution."
                )
                return study

            # Mark any RUNNING trials as FAILED (they were interrupted)
            running_trials = [
                t for t in study.trials
                if t.state == optuna.trial.TrialState.RUNNING
            ]
            if running_trials:
                logger.warning(
                    f"Found {len(running_trials)} RUNNING trials from previous session. "
                    f"Marking them as FAILED (interrupted)."
                )
                for trial in running_trials:
                    study.tell(
                        trial.number, state=optuna.trial.TrialState.FAIL)

            # Count completed trials
            completed_trials = len([
                t for t in study.trials
                if t.state == optuna.trial.TrialState.COMPLETE
            ])
            logger.info(
                f"Loaded {len(study.trials)} existing trials ({completed_trials} completed, "
                f"{len(running_trials)} marked as failed)")
        except Exception as e:
            logger.warning(f"Could not load checkpoint: {e}")
            logger.info("Creating new study instead...")
            # Use unique study name when resume fails
            study_name = f"hpo_{backbone}_{run_id}"
            study = optuna.create_study(
                direction=direction,
                sampler=sampler,
                pruner=pruner,
                study_name=study_name,
                storage=storage_uri,
                load_if_exists=False,
            )
            should_resume = False
    else:
        if storage_uri:
            logger.info(
                f"[HPO] Starting optimization for {backbone} with checkpointing...")
            logger.debug(f"Checkpoint: {storage_path}")
            # When checkpointing is enabled, use load_if_exists=True so we can resume
            # if the study already exists in the database (even if file was just created)
            load_if_exists = checkpoint_enabled
        else:
            logger.info(f"[HPO] Starting optimization for {backbone}...")
            load_if_exists = False

        study = optuna.create_study(
            direction=direction,
            sampler=sampler,
            pruner=pruner,
            study_name=study_name,
            storage=storage_uri,
            load_if_exists=load_if_exists,
        )

        # If checkpointing is enabled and we loaded an existing study, check auto_resume
        if checkpoint_enabled and load_if_exists and len(study.trials) > 0:
            auto_resume = checkpoint_config.get("auto_resume", True)

            if auto_resume:
                # User wants to resume - update should_resume
                should_resume = True

                # Mark any RUNNING trials as FAILED (they were interrupted)
                running_trials = [
                    t for t in study.trials
                    if t.state == optuna.trial.TrialState.RUNNING
                ]
                if running_trials:
                    logger.warning(
                        f"Found {len(running_trials)} RUNNING trials from previous session. "
                        f"Marking them as FAILED (interrupted)."
                    )
                    for trial in running_trials:
                        study.tell(
                            trial.number, state=optuna.trial.TrialState.FAIL)

                completed_trials = len([
                    t for t in study.trials
                    if t.state == optuna.trial.TrialState.COMPLETE
                ])
                logger.info(
                    f"Loaded existing study with {len(study.trials)} trials "
                    f"({completed_trials} completed, {len(running_trials)} marked as failed)")
            else:
                # auto_resume: false but existing study found - require new study_name
                completed_trials = len([
                    t for t in study.trials
                    if t.state == optuna.trial.TrialState.COMPLETE
                ])
                raise ValueError(
                    f"❌ Found existing study '{study_name}' with {len(study.trials)} trials "
                    f"({completed_trials} completed), but auto_resume=false.\n"
                    f"   To start fresh, you must use a different study_name.\n"
                    f"   Current study_name: '{study_name}'\n"
                    f"   Solution: Add 'study_name: \"hpo_{backbone}_new_name\"' to checkpoint config."
                )

    # Get objective metric name
    objective_metric = hpo_config["objective"]["metric"]

    # Run ID was already generated above for study naming
    # Print it here for user visibility
    logger.debug(f"Run ID: {run_id} (prevents overwriting on reruns)")

    # Set MLflow experiment (safe to call even if already set)
    try:
        mlflow.set_experiment(mlflow_experiment_name)
    except Exception as e:
        logger.warning(f"Could not set MLflow experiment: {e}")
        logger.warning("Continuing without MLflow tracking...")

    # Create objective function and cleanup function
    objective, cleanup_checkpoints = create_local_hpo_objective(
        dataset_path=dataset_path,
        config_dir=config_dir,
        backbone=backbone,
        hpo_config=hpo_config,
        train_config=train_config,
        output_base_dir=output_dir,
        mlflow_experiment_name=mlflow_experiment_name,
        objective_metric=objective_metric,
        k_folds=k_folds,
        fold_splits_file=fold_splits_file,
        run_id=run_id,
    )

    # Create callback factory to capture parent_run_id
    def create_trial_callback(parent_run_id: Optional[str] = None):
        """Create a trial completion callback with parent run ID captured in closure."""
        def trial_complete_callback(study: Any, trial: Any) -> None:
            """Callback to display consolidated metrics and parameters after trial completes."""
            optuna_module, _, _, _ = _import_optuna()
            if trial.state == optuna_module.trial.TrialState.COMPLETE:
                # Get best trial info
                best_trial = study.best_trial
                is_best = trial.number == best_trial.number

                attrs = trial.user_attrs
                parts = [f"{objective_metric}={trial.value:.6f}"]

                if "macro_f1_span" in attrs:
                    parts.append(f"span={attrs['macro_f1_span']:.6f}")
                if "loss" in attrs:
                    parts.append(f"loss={attrs['loss']:.6f}")
                if "avg_entity_f1" in attrs:
                    entity_count = attrs.get("entity_count", "?")
                    parts.append(
                        f"entity_f1={attrs['avg_entity_f1']:.6f} ({entity_count} entities)")

                # Format parameters for display
                param_parts = []
                for param_name, param_value in trial.params.items():
                    if isinstance(param_value, float):
                        # Format floats with appropriate precision
                        if param_name == "learning_rate":
                            param_parts.append(
                                f"{param_name}={param_value:.2e}")
                        else:
                            param_parts.append(
                                f"{param_name}={param_value:.6f}")
                    else:
                        param_parts.append(f"{param_name}={param_value}")

                # Try to get child run ID (just for reference, no URL needed)
                # MLflow already prints the run links, so we don't need to duplicate
                run_id_short = ""
                try:
                    if parent_run_id:
                        client = mlflow.tracking.MlflowClient()
                        active_run = mlflow.active_run()
                        if active_run:
                            experiment_id = active_run.info.experiment_id
                            # Query child runs with matching trial number
                            # With nested structure, we want the trial run (not fold runs)
                            all_runs = client.search_runs(
                                experiment_ids=[experiment_id],
                                filter_string=f"tags.mlflow.parentRunId = '{parent_run_id}' AND tags.trial_number = '{trial.number}'",
                                max_results=100,
                            )
                            if all_runs:
                                # Find the trial run (has trial_number but no fold_idx tag)
                                trial_run = None
                                for run in all_runs:
                                    fold_tag = run.data.tags.get("fold_idx")
                                    if not fold_tag:
                                        # This is the trial run (no fold_idx = trial level)
                                        trial_run = run
                                        break

                                # If no trial run found, use first run (backward compatibility)
                                if not trial_run:
                                    trial_run = all_runs[0]

                                child_run_id = trial_run.info.run_id
                                run_id_short = f" (Run ID: {child_run_id[:12]}...)"
                except Exception as e:
                    logger.debug(
                        f"Could not get run ID for trial {trial.number}: {e}")

                # Add empty line before each trial for clarity
                logger.info("")  # Empty line to separate trials

                # Format output for better readability
                status = "[BEST]" if is_best else f"[Trial {trial.number}]"
                trial_name = f"trial_{trial.number}"
                metrics_str = ' | '.join(parts)
                params_str = ' | '.join(param_parts)

                # Log in a more readable format
                logger.info(f"{status}: {trial_name}")
                logger.info(f"  Metrics: {metrics_str}")
                logger.info(f"  Params: {params_str}{run_id_short}")

        return trial_complete_callback

    # Calculate remaining trials
    max_trials = hpo_config["sampling"]["max_trials"]
    timeout_seconds = hpo_config["sampling"]["timeout_minutes"] * 60

    # Create MLflow parent run for HPO sweep
    mlflow_run_name = create_mlflow_run_name(
        backbone, run_id, study_name, should_resume, checkpoint_enabled)

    # Initialize MLflow tracker
    tracker = MLflowSweepTracker(mlflow_experiment_name)
    tracker.log_tracking_info()

    # Run optimization with MLflow tracking
    try:
        with tracker.start_sweep_run(
            run_name=mlflow_run_name,
            hpo_config=hpo_config,
            backbone=backbone,
            study_name=study_name,
            checkpoint_config=checkpoint_config,
            storage_path=storage_path,
            should_resume=should_resume,
        ) as parent_run:
            parent_run_id = parent_run.info.run_id if parent_run else None

            # Mark interrupted runs AFTER parent run is created (MLflow is definitely ready now)
            if (should_resume or checkpoint_enabled) and parent_run_id:
                try:
                    # mlflow is already imported at module level
                    client = mlflow.tracking.MlflowClient()
                    experiment = mlflow.get_experiment_by_name(
                        mlflow_experiment_name)

                    if not experiment:
                        # Try alternative lookup
                        try:
                            all_experiments = client.search_experiments()
                            experiment = next(
                                (exp for exp in all_experiments if exp.name ==
                                 mlflow_experiment_name),
                                None
                            )
                        except Exception:
                            pass

                    if experiment:
                        # Search for all RUNNING runs with matching name
                        all_running_runs = client.search_runs(
                            experiment_ids=[experiment.experiment_id],
                            filter_string="attributes.status = 'RUNNING'",
                            max_results=1000,
                        )

                        # Find parent runs with matching name (excluding current one)
                        matching_parent_runs = [
                            run for run in all_running_runs
                            if run.info.run_name == mlflow_run_name
                            and run.info.run_id != parent_run_id
                        ]

                        # Find all parent runs with matching name (any status) to check their child runs
                        all_runs = client.search_runs(
                            experiment_ids=[experiment.experiment_id],
                            max_results=1000,
                        )
                        parent_runs_with_name = [
                            run for run in all_runs
                            if run.info.run_name == mlflow_run_name
                            and run.info.run_id != parent_run_id
                        ]

                        # Mark matching parent runs as FAILED
                        if matching_parent_runs:
                            logger.warning(
                                f"Found {len(matching_parent_runs)} interrupted parent run(s) with name '{mlflow_run_name}'. "
                                f"Marking them as FAILED."
                            )
                            for run in matching_parent_runs:
                                try:
                                    client.set_terminated(
                                        run.info.run_id, status="FAILED")
                                    updated_run = client.get_run(
                                        run.info.run_id)
                                    if updated_run.info.status == "FAILED":
                                        logger.info(
                                            f"Marked interrupted parent run {run.info.run_id[:12]}... as FAILED"
                                        )
                                    else:
                                        logger.warning(
                                            f"Parent run {run.info.run_id[:12]}... status is still {updated_run.info.status}"
                                        )
                                except Exception as e:
                                    logger.warning(
                                        f"Could not mark parent run {run.info.run_id[:12]}... as FAILED: {e}"
                                    )

                        # Mark all RUNNING child runs from any parent run with matching name as FAILED
                        all_running_child_runs = []
                        for parent_run in parent_runs_with_name:
                            child_runs = client.search_runs(
                                experiment_ids=[experiment.experiment_id],
                                filter_string=f"tags.mlflow.parentRunId = '{parent_run.info.run_id}' AND attributes.status = 'RUNNING'",
                                max_results=1000,
                            )
                            all_running_child_runs.extend(child_runs)

                        if all_running_child_runs:
                            logger.warning(
                                f"Found {len(all_running_child_runs)} RUNNING child run(s) from parent run(s) with name '{mlflow_run_name}'. "
                                f"Marking them as FAILED."
                            )
                            for child_run in all_running_child_runs:
                                try:
                                    trial_num = child_run.data.tags.get(
                                        "trial_number", "unknown")
                                    client.set_terminated(
                                        child_run.info.run_id, status="FAILED")
                                    updated_run = client.get_run(
                                        child_run.info.run_id)
                                    if updated_run.info.status == "FAILED":
                                        logger.info(
                                            f"Marked interrupted child run {child_run.info.run_id[:12]}... (trial {trial_num}) as FAILED"
                                        )
                                    else:
                                        logger.warning(
                                            f"Child run {child_run.info.run_id[:12]}... (trial {trial_num}) status is still {updated_run.info.status}"
                                        )
                                except Exception as e:
                                    logger.warning(
                                        f"Could not mark child run {child_run.info.run_id[:12]}... as FAILED: {e}"
                                    )
                except Exception as e:
                    logger.warning(
                        f"Could not mark interrupted runs after parent run creation: {e}")

            trial_callback = create_trial_callback(parent_run_id)

            if should_resume:
                # Count only completed trials (not FAILED, PRUNED, etc.)
                completed_trials = len([
                    t for t in study.trials
                    if t.state == optuna.trial.TrialState.COMPLETE
                ])
                remaining_trials = max(0, max_trials - completed_trials)

                if remaining_trials > 0:
                    logger.info(
                        f"Running {remaining_trials} more trials (already completed {completed_trials}/{max_trials})"
                    )
                    study.optimize(
                        objective,
                        n_trials=remaining_trials,
                        timeout=timeout_seconds,
                        show_progress_bar=True,
                        callbacks=[trial_callback],
                    )
                else:
                    logger.info(f"All {max_trials} trials already completed!")
            else:
                # Run all trials
                study.optimize(
                    objective,
                    n_trials=max_trials,
                    timeout=timeout_seconds,
                    show_progress_bar=True,
                    callbacks=[trial_callback],
                )

            # Log final metrics and best trial info
            if parent_run is not None:
                parent_run_id = parent_run.info.run_id

                # Load fold splits if k-fold CV was used (needed for checkpoint path resolution)
                fold_splits_for_logging = None
                if k_folds is not None and k_folds > 1 and fold_splits_file and fold_splits_file.exists():
                    try:
                        from training.cv_utils import load_fold_splits
                        fold_splits_for_logging, _ = load_fold_splits(
                            fold_splits_file)
                    except Exception as e:
                        logger.warning(
                            f"Could not load fold splits for checkpoint logging: {e}")

                tracker.log_final_metrics(
                    study=study,
                    objective_metric=objective_metric,
                    parent_run_id=parent_run_id,
                    run_name=mlflow_run_name,
                    should_resume=should_resume,
                    hpo_output_dir=output_dir,
                    backbone=backbone,
                    run_id=run_id,
                    fold_splits=fold_splits_for_logging,
                    hpo_config=hpo_config,
                )
    except Exception as e:
        # Gracefully handle MLflow failures - don't fail HPO if MLflow is unavailable
        logger.warning(f"MLflow tracking failed: {e}")
        logger.warning("Continuing HPO without MLflow tracking...")

        # Run optimization without MLflow context
        trial_callback = create_trial_callback(None)

        if should_resume:
            completed_trials = len([
                t for t in study.trials
                if t.state == optuna.trial.TrialState.COMPLETE
            ])
            remaining_trials = max(0, max_trials - completed_trials)

            if remaining_trials > 0:
                logger.info(
                    f"Running {remaining_trials} more trials (already completed {completed_trials}/{max_trials})"
                )
                study.optimize(
                    objective,
                    n_trials=remaining_trials,
                    timeout=timeout_seconds,
                    show_progress_bar=True,
                    callbacks=[trial_callback],
                )
            else:
                logger.info(f"All {max_trials} trials already completed!")

            # Final cleanup: delete all non-best checkpoints
            try:
                cleanup_checkpoints()
            except Exception as e:
                logger.warning(f"Error during final checkpoint cleanup: {e}")
        else:
            study.optimize(
                objective,
                n_trials=max_trials,
                timeout=timeout_seconds,
                show_progress_bar=True,
                callbacks=[trial_callback],
            )

            # Final cleanup: delete all non-best checkpoints
            try:
                cleanup_checkpoints()
            except Exception as e:
                logger.warning(f"Error during final checkpoint cleanup: {e}")

    return study

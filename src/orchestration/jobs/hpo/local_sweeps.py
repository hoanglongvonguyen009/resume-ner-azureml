
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

                # Build systematic run name using NamingContext
                run_name = None
                try:
                    from orchestration.naming_centralized import create_naming_context
                    from orchestration.jobs.tracking.mlflow_naming import build_mlflow_run_name
                    from shared.platform_detection import detect_platform

                    # Extract backbone short name
                    backbone_full = trial_params.get("backbone", "unknown")
                    backbone_short = backbone_full.split(
                        "-")[0] if "-" in backbone_full else backbone_full

                    # Build trial_id from trial_number and run_id if available
                    run_id = trial_params.get("run_id")
                    if run_id:
                        trial_id = f"trial_{trial_number}_{run_id}"
                    else:
                        trial_id = f"trial_{trial_number}"

                    # Create NamingContext for HPO trial
                    trial_context = create_naming_context(
                        process_type="hpo",
                        model=backbone_short,
                        environment=detect_platform(),
                        trial_id=trial_id,
                    )

                    # Build systematic run name
                    run_name = build_mlflow_run_name(trial_context, config_dir)

                    # Build tags including project identity tags
                    from orchestration.jobs.tracking.mlflow_naming import build_mlflow_tags
                    trial_tags = build_mlflow_tags(
                        context=trial_context,
                        output_dir=output_dir,
                        config_dir=config_dir,
                    )
                    # Merge with trial-specific tags
                    trial_tags.update({
                        "mlflow.parentRunId": hpo_parent_run_id,
                        "azureml.runType": "trial",
                        "azureml.trial": "true",
                        "trial_number": str(trial_number),
                    })
                except Exception as e:
                    logger.warning(
                        f"Could not build systematic run name and tags: {e}, using fallback")
                    # Fallback to simple name
                    run_name = f"trial_{trial_number}"
                    # Fallback to minimal tags - still try to get project name from config
                    try:
                        from orchestration.jobs.tracking.mlflow_config_loader import get_naming_config
                        naming_config = get_naming_config(config_dir)
                        project_name = naming_config.get(
                            "project_name", "resume-ner")
                    except Exception:
                        project_name = "resume-ner"
                    trial_tags = {
                        "mlflow.parentRunId": hpo_parent_run_id,
                        "azureml.runType": "trial",
                        "azureml.trial": "true",
                        "trial_number": str(trial_number),
                        "code.project": project_name,  # Always include project identity
                    }

                # Create trial run as child of HPO parent
                trial_run = client.create_run(
                    experiment_id=experiment_id,
                    tags=trial_tags,
                    run_name=run_name
                )
                trial_run_id = trial_run.info.run_id

                # DO NOT mark trial run as FINISHED here - it should remain RUNNING until all folds complete
                # The run will be used by training subprocesses and marked as FINISHED after all folds complete
                logger.info(
                    f"[TRIAL_RUN_CV] Created trial run (CV): {trial_run_id[:12]}... (trial {trial_number}). Run remains RUNNING until all folds complete.")
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

            # End the trial run to mark it as completed (CV case - after all folds complete)
            trial_number = trial_params.get('trial_number', 'unknown')
            logger.info(
                f"[TRIAL_RUN_CV] All folds completed. Marking trial run {trial_run_id[:12]}... as FINISHED (trial {trial_number})")
            client.set_terminated(trial_run_id, status="FINISHED")
            logger.info(
                f"[TRIAL_RUN_CV] Successfully marked trial run {trial_run_id[:12]}... as FINISHED")
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

    # Capture run_id in closure to avoid UnboundLocalError
    captured_run_id = run_id

    def objective(trial: Any) -> float:
        # Sample hyperparameters
        # Exclude "backbone" from search space since it's fixed per study
        trial_params = translate_search_space_to_optuna(
            hpo_config, trial, exclude_params=["backbone"])
        # Set the fixed backbone for this study
        trial_params["backbone"] = backbone
        trial_params["trial_number"] = trial.number
        # Pass run_id to trial functions (use captured value from outer scope)
        trial_params["run_id"] = captured_run_id

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
            # Create trial-level run as child of HPO parent for consistency
            # This ensures trial runs are properly linked and can be found later
            trial_run_id_for_no_cv = None
            if hpo_parent_run_id:
                try:
                    client = mlflow.tracking.MlflowClient()
                    active_run = mlflow.active_run()
                    if active_run:
                        experiment_id = active_run.info.experiment_id
                        trial_number = trial_params.get(
                            "trial_number", "unknown")

                        # Build systematic run name using NamingContext
                        run_name = None
                        try:
                            from orchestration.naming_centralized import create_naming_context
                            from orchestration.jobs.tracking.mlflow_naming import build_mlflow_run_name
                            from shared.platform_detection import detect_platform

                            # Extract backbone short name
                            backbone_full = trial_params.get(
                                "backbone", "unknown")
                            backbone_short = backbone_full.split(
                                "-")[0] if "-" in backbone_full else backbone_full

                            # Build trial_id from trial_number and run_id if available
                            run_id = trial_params.get("run_id")
                            if run_id:
                                trial_id = f"trial_{trial_number}_{run_id}"
                            else:
                                trial_id = f"trial_{trial_number}"

                            # Create NamingContext for HPO trial
                            trial_context = create_naming_context(
                                process_type="hpo",
                                model=backbone_short,
                                environment=detect_platform(),
                                trial_id=trial_id,
                            )

                            # Build systematic run name
                            run_name = build_mlflow_run_name(
                                trial_context, config_dir)

                            # Build tags including project identity tags
                            from orchestration.jobs.tracking.mlflow_naming import build_mlflow_tags
                            trial_tags = build_mlflow_tags(
                                context=trial_context,
                                output_dir=output_base_dir,
                                config_dir=config_dir,
                            )
                            # Merge with trial-specific tags
                            trial_tags.update({
                                "mlflow.parentRunId": hpo_parent_run_id,
                                "azureml.runType": "trial",
                                "azureml.trial": "true",
                                "trial_number": str(trial_number),
                            })
                        except Exception as e:
                            logger.warning(
                                f"Could not build systematic run name and tags (no CV): {e}, using fallback")
                            # Fallback to simple name
                            run_name = f"trial_{trial_number}"
                            # Fallback to minimal tags - still try to get project name from config
                            try:
                                from orchestration.jobs.tracking.mlflow_config_loader import get_naming_config
                                naming_config = get_naming_config(config_dir)
                                project_name = naming_config.get(
                                    "project_name", "resume-ner")
                            except Exception:
                                project_name = "resume-ner"
                            trial_tags = {
                                "mlflow.parentRunId": hpo_parent_run_id,
                                "azureml.runType": "trial",
                                "azureml.trial": "true",
                                "trial_number": str(trial_number),
                                "code.project": project_name,  # Always include project identity
                            }

                        # Create trial run as child of HPO parent
                        trial_run = client.create_run(
                            experiment_id=experiment_id,
                            tags=trial_tags,
                            run_name=run_name
                        )
                        trial_run_id_for_no_cv = trial_run.info.run_id

                        # DO NOT mark trial run as FINISHED here - it should remain RUNNING until training completes
                        # The run will be used by training subprocess and marked as FINISHED after training completes
                        logger.info(
                            f"[TRIAL_RUN_NO_CV] Created trial run (no CV): {trial_run_id_for_no_cv[:12]}... (trial {trial_number}). Run remains RUNNING until training completes.")
                except Exception as e:
                    logger.warning(f"Could not create trial run (no CV): {e}")

            metric_value = run_training_trial(
                trial_params=trial_params,
                dataset_path=dataset_path,
                config_dir=config_dir,
                backbone=backbone,
                output_dir=output_base_dir,
                train_config=train_config,
                mlflow_experiment_name=mlflow_experiment_name,
                objective_metric=objective_metric,
                parent_run_id=trial_run_id_for_no_cv if trial_run_id_for_no_cv else hpo_parent_run_id,
            )

            # Mark trial run as FINISHED after training completes (no CV case)
            if trial_run_id_for_no_cv:
                try:
                    logger.info(
                        f"[TRIAL_RUN_NO_CV] Training completed. Marking trial run {trial_run_id_for_no_cv[:12]}... as FINISHED (trial {trial_number})")
                    client = mlflow.tracking.MlflowClient()
                    client.set_terminated(
                        trial_run_id_for_no_cv, status="FINISHED")
                    logger.info(
                        f"[TRIAL_RUN_NO_CV] Successfully marked trial run {trial_run_id_for_no_cv[:12]}... as FINISHED")
                except Exception as e:
                    logger.warning(
                        f"[TRIAL_RUN_NO_CV] Could not mark trial run as FINISHED: {e}")

        # Store additional metrics in trial user attributes for callback display
        # Try to read full metrics from the trial output directory
        # Use captured_run_id from closure to avoid UnboundLocalError
        run_suffix = f"_{captured_run_id}" if captured_run_id else ""
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
                run_suffix = f"_{captured_run_id}" if captured_run_id else ""
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

    # Load fold splits for logging (if k-fold CV is enabled)
    fold_splits_for_logging = None
    if k_folds is not None and k_folds > 1 and fold_splits_file and fold_splits_file.exists():
        try:
            from training.cv_utils import load_fold_splits
            fold_splits_for_logging, _ = load_fold_splits(fold_splits_file)
            logger.debug(
                f"Loaded {len(fold_splits_for_logging)} fold splits for logging")
        except Exception as e:
            logger.warning(f"Could not load fold splits for logging: {e}")

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
                        f"entity_f1={attrs['avg_entity_f1']:.6f} ({entity_count} entities)"
                    )

                param_parts = []
                for param_name, param_value in trial.params.items():
                    if isinstance(param_value, float):
                        if param_name == "learning_rate":
                            param_parts.append(
                                f"{param_name}={param_value:.2e}")
                        else:
                            param_parts.append(
                                f"{param_name}={param_value:.6f}")
                    else:
                        param_parts.append(f"{param_name}={param_value}")

                run_id_short = ""
                try:
                    if parent_run_id:
                        client = mlflow.tracking.MlflowClient()
                        active_run = mlflow.active_run()
                        if active_run:
                            experiment_id = active_run.info.experiment_id
                            all_runs = client.search_runs(
                                experiment_ids=[experiment_id],
                                filter_string=(
                                    f"tags.mlflow.parentRunId = '{parent_run_id}' "
                                    f"AND tags.trial_number = '{trial.number}'"
                                ),
                                max_results=100,
                            )
                            if all_runs:
                                trial_run = None
                                for run in all_runs:
                                    if not run.data.tags.get("fold_idx"):
                                        trial_run = run
                                        break
                                if not trial_run:
                                    trial_run = all_runs[0]
                                run_id_short = f" (Run ID: {trial_run.info.run_id[:12]}...)"
                except Exception as e:
                    logger.debug(
                        f"Could not get run ID for trial {trial.number}: {e}"
                    )

                logger.info("")
                status = "[BEST]" if is_best else f"[Trial {trial.number}]"
                trial_name = f"trial_{trial.number}"
                logger.info(f"{status}: {trial_name}")
                logger.info(f"  Metrics: {' | '.join(parts)}")
                logger.info(
                    f"  Params: {' | '.join(param_parts)}{run_id_short}")

        return trial_complete_callback

    # Calculate remaining trials
    max_trials = hpo_config["sampling"]["max_trials"]
    timeout_seconds = hpo_config["sampling"]["timeout_minutes"] * 60

    # Cleanup stale reservations from crashed processes
    try:
        from orchestration.jobs.tracking.mlflow_index import cleanup_stale_reservations
        root_dir = output_dir.parent.parent if output_dir else Path.cwd()
        config_dir = output_dir.parent.parent / "config" if output_dir else None
        cleaned_count = cleanup_stale_reservations(root_dir, config_dir, stale_minutes=30)
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} stale run name reservations")
    except Exception as e:
        logger.debug(f"Could not cleanup stale reservations: {e}")

    # Create NamingContext for HPO parent run
    try:
        from orchestration.naming_centralized import create_naming_context
        from orchestration.jobs.tracking.mlflow_naming import build_mlflow_run_name
        from shared.platform_detection import detect_platform

        hpo_parent_context = create_naming_context(
            process_type="hpo",
            model=backbone,
            environment=detect_platform(),
            trial_id=study_name,
        )

        config_dir = output_dir.parent.parent / "config" if output_dir else None
        root_dir = output_dir.parent.parent if output_dir else Path.cwd()
        mlflow_run_name = build_mlflow_run_name(
            hpo_parent_context, config_dir, root_dir=root_dir, output_dir=output_dir
        )
    except Exception as e:
        logger.debug(
            f"Could not create NamingContext for HPO parent run: {e}, using fallback"
        )
        hpo_parent_context = None
        mlflow_run_name = create_mlflow_run_name(
            backbone,
            run_id,
            study_name,
            should_resume,
            checkpoint_enabled,
        )

    tracker = MLflowSweepTracker(mlflow_experiment_name)
    tracker.log_tracking_info()

    parent_run_id = None
    parent_run_handle = None

    try:
        with tracker.start_sweep_run(
            run_name=mlflow_run_name,
            context=hpo_parent_context,
            output_dir=output_dir,
            hpo_config=hpo_config,
            backbone=backbone,
            study_name=study_name,
            checkpoint_config=checkpoint_config,
            storage_path=storage_path,
            should_resume=should_resume,
        ) as parent_run:

            parent_run_handle = parent_run
            parent_run_id = parent_run.run_id if parent_run else None

            # Commit reserved version if auto-increment was used
            if parent_run_id and hpo_parent_context and mlflow_run_name:
                try:
                    import re
                    from orchestration.jobs.tracking.mlflow_naming import (
                        build_mlflow_run_key,
                        build_mlflow_run_key_hash,
                        build_counter_key,
                    )
                    from orchestration.jobs.tracking.mlflow_config_loader import (
                        get_naming_config,
                        get_auto_increment_config,
                    )
                    from orchestration.jobs.tracking.mlflow_index import commit_run_name_version

                    # Check if auto-increment was used (run name has version suffix like .{number})
                    version_match = re.search(r'\.(\d+)$', mlflow_run_name)
                    if version_match:
                        version = int(version_match.group(1))
                        
                        # Check if auto-increment is enabled for HPO
                        auto_inc_config = get_auto_increment_config(config_dir, "hpo")
                        if auto_inc_config.get("enabled_for_process", False):
                            # Rebuild counter_key from context
                            run_key = build_mlflow_run_key(hpo_parent_context)
                            run_key_hash = build_mlflow_run_key_hash(run_key)
                            naming_config = get_naming_config(config_dir)
                            counter_key = build_counter_key(
                                naming_config.get("project_name", "resume-ner"),
                                "hpo",
                                run_key_hash,
                                hpo_parent_context.environment or "",
                            )
                            
                            # Commit the reserved version
                            commit_run_name_version(
                                counter_key, parent_run_id, version, root_dir, config_dir
                            )
                            logger.debug(
                                f"Committed version {version} for HPO parent run {parent_run_id[:12]}..."
                            )
                except Exception as e:
                    logger.warning(
                        f"Could not commit reserved version for HPO parent run: {e}"
                    )

            # Cleanup: Tag interrupted runs from previous sessions
            if parent_run_id and hpo_parent_context:
                try:
                    logger.info(
                        f"[CLEANUP] Starting cleanup check: should_resume={should_resume}, "
                        f"checkpoint_enabled={checkpoint_enabled}, parent_run_id={parent_run_id[:12]}..."
                    )

                    import mlflow
                    from mlflow.tracking import MlflowClient
                    client = MlflowClient()

                    # Get current environment for filtering
                    from shared.platform_detection import detect_platform
                    current_env = detect_platform()

                    # Get run_key_hash from context for tag-based search
                    from orchestration.jobs.tracking.mlflow_naming import build_mlflow_run_key_hash, build_mlflow_run_key
                    run_key = build_mlflow_run_key(hpo_parent_context)
                    run_key_hash = build_mlflow_run_key_hash(
                        run_key) if run_key else None

                    # Load naming config for project name comparison
                    from orchestration.jobs.tracking.mlflow_config_loader import get_naming_config
                    config_dir = output_dir.parent.parent / "config" if output_dir else None
                    naming_config = get_naming_config(config_dir)

                    # Get current run start_time for legacy run validation
                    current_start_time = None
                    try:
                        current_run_info = client.get_run(parent_run_id)
                        current_start_time = current_run_info.info.start_time
                    except Exception as e:
                        logger.warning(
                            f"[CLEANUP] Could not get current run start_time: {e}. "
                            f"Legacy run validation will be skipped."
                        )

                    logger.info(
                        f"[CLEANUP] MLflow imported successfully. Current env: {current_env}, "
                        f"run_key_hash: {run_key_hash[:12] if run_key_hash else 'None'}..."
                    )

                    # Find interrupted parent runs (RUNNING status, same run_key_hash, different run_id, same env)
                    experiment = mlflow.get_experiment_by_name(
                        mlflow_experiment_name)
                    if experiment:
                        logger.info(
                            f"[CLEANUP] Retrieved experiment: {experiment.experiment_id}"
                        )

                        # Optimized cleanup strategy: Single bulk fetch with pagination
                        # Strategy: Tag-based filtering (primary) with name fallback (legacy runs only)
                        # - Fetch all runs with pagination (no 100-run cap)
                        # - Build parent→children map in one pass (eliminates N+1 queries)
                        # - Use tag-based matching as primary (more reliable than name matching)
                        # - Strict validation for legacy runs (start_time comparison)

                        import re
                        base_run_name = re.sub(
                            r'\s*\(\d+\)\s*$', '', mlflow_run_name).strip()

                        logger.info(
                            f"[CLEANUP] Fetching all runs in experiment (may paginate for large experiments)..."
                        )

                        # Fetch all runs (MLflow's search_runs returns a list, not paginated)
                        # Use max_results=10000 as safety limit (most experiments have <1000 runs)
                        try:
                            all_runs = client.search_runs(
                                experiment_ids=[experiment.experiment_id],
                                filter_string="",
                                max_results=10000,  # Safety limit
                                order_by=["attributes.start_time DESC"],
                            )

                            if len(all_runs) >= 10000:
                                logger.warning(
                                    f"[CLEANUP] Fetched {len(all_runs)} runs (safety limit reached). "
                                    f"Some older runs may not be processed."
                                )
                        except Exception as e:
                            logger.warning(
                                f"[CLEANUP] Error fetching runs: {e}. Cleanup may be incomplete."
                            )
                            all_runs = []

                        logger.info(
                            f"[CLEANUP] Fetched {len(all_runs)} total runs from experiment")

                        # Build parent→children map in one pass (eliminates N+1 queries)
                        parent_to_children = {}
                        for run in all_runs:
                            parent_id = run.data.tags.get("mlflow.parentRunId")
                            if parent_id:
                                if parent_id not in parent_to_children:
                                    parent_to_children[parent_id] = []
                                parent_to_children[parent_id].append(run)

                        logger.info(
                            f"[CLEANUP] Built parent→children map: {len(parent_to_children)} parents have children"
                        )

                        # Find interrupted parent runs using tag-based filtering (primary)
                        interrupted_parents = []
                        status_counts = {}
                        tag_based_matches = 0
                        name_fallback_matches = 0

                        for run in all_runs:
                            # Track status breakdown
                            status = run.info.status
                            status_counts[status] = status_counts.get(
                                status, 0) + 1

                            # Skip if not RUNNING
                            if status != "RUNNING":
                                continue

                            # Skip if already tagged
                            if run.data.tags.get("code.interrupted") == "true":
                                continue

                            # Skip if current run
                            if run.info.run_id == parent_run_id:
                                continue

                            # Primary strategy: Tag-based filtering (most reliable)
                            run_hash = run.data.tags.get("code.run_key_hash")
                            run_project = run.data.tags.get("code.project")
                            run_env = run.data.tags.get("code.env")
                            run_stage = run.data.tags.get("code.stage")
                            run_run_type = run.data.tags.get("mlflow.runType")

                            is_tag_based_match = False
                            is_name_fallback_match = False

                            # Check if run has required tags for tag-based matching
                            if run_hash and run_project and run_env:
                                # Tag-based match: hash matches, project matches, env matches, stage is hpo/sweep
                                expected_project = naming_config.get(
                                    "project_name", "resume-ner")
                                if (run_hash == run_key_hash and
                                    run_project == expected_project and
                                    run_env == current_env and
                                        (run_stage in ["hpo", "sweep"] or run_run_type == "sweep")):
                                    is_tag_based_match = True
                                    tag_based_matches += 1
                                    logger.debug(
                                        f"[CLEANUP] Tag-based match: {run.info.run_name} "
                                        f"(run_id: {run.info.run_id[:12]}..., hash: {run_hash[:12]}...)"
                                    )

                            # Fallback strategy: Name-based matching (only for legacy runs without tags)
                            if not is_tag_based_match:
                                # Only use name fallback if run is missing critical tags (legacy run)
                                if not run_hash and run_project and run_env:
                                    run_name = run.info.run_name
                                    if run_name.startswith(base_run_name):
                                        # Additional safety checks for legacy runs:
                                        # - Same project
                                        # - Same environment
                                        # - Same stage (if present)
                                        # - Older start time than current run (interrupted before current started)
                                        expected_project = naming_config.get(
                                            "project_name", "resume-ner")
                                        if (run_project == expected_project and
                                            run_env == current_env and
                                                (not run_stage or run_stage in ["hpo", "sweep"])):

                                            # Get current run start time for comparison
                                            if current_start_time is not None:
                                                run_start_time = run.info.start_time

                                                # Only tag if run started before current run (safety check)
                                                if run_start_time < current_start_time:
                                                    is_name_fallback_match = True
                                                    name_fallback_matches += 1
                                                    logger.info(
                                                        f"[CLEANUP] Name fallback match (legacy run): {run_name} "
                                                        f"(run_id: {run.info.run_id[:12]}..., "
                                                        f"start_time: {run_start_time}, "
                                                        f"current_start_time: {current_start_time})"
                                                    )
                                            else:
                                                logger.debug(
                                                    f"[CLEANUP] Skipping legacy run {run.info.run_id[:12]}... "
                                                    f"(name: {run_name}) - cannot validate start_time"
                                                )

                            # Add to interrupted list if matched by either strategy
                            if is_tag_based_match or is_name_fallback_match:
                                interrupted_parents.append(run)
                                logger.info(
                                    f"[CLEANUP] Found interrupted parent run: {run.info.run_name} "
                                    f"(run_id: {run.info.run_id[:12]}..., strategy: "
                                    f"{'tag-based' if is_tag_based_match else 'name-fallback'})"
                                )

                        logger.info(
                            f"[CLEANUP] Status breakdown: {status_counts}"
                        )
                        logger.info(
                            f"[CLEANUP] Found {tag_based_matches} tag-based matches, "
                            f"{name_fallback_matches} name-fallback matches (legacy), "
                            f"{len(interrupted_parents)} total eligible for tagging"
                        )

                        # Helper function to safely tag runs as interrupted (uses cached run data)
                        def should_tag_as_interrupted(run_data, current_run_id: str) -> tuple[bool, str]:
                            """Check if a run should be tagged as interrupted using cached run data."""
                            run_id = run_data.info.run_id
                            if run_id == current_run_id:
                                return False, "is_current_run"

                            if run_data.data.tags.get("code.interrupted") == "true":
                                return False, "already_tagged_interrupted"

                            # Only tag runs that have project identity tags
                            if run_data.data.tags.get("code.project") is None:
                                return False, "no_project_identity"

                            return True, "ok"

                        # Tag interrupted parent runs and their children (using pre-built map)
                        if interrupted_parents:
                            total_tagged_parents = 0
                            total_tagged_children = 0

                            for run in interrupted_parents:
                                run_id_to_mark = run.info.run_id
                                run_name = run.info.run_name

                                should_tag, reason = should_tag_as_interrupted(
                                    run, parent_run_id)
                                if not should_tag:
                                    logger.debug(
                                        f"[CLEANUP] Skipping parent run {run_id_to_mark[:12]}... (reason: {reason})"
                                    )
                                    continue

                                logger.info(
                                    f"[CLEANUP] Tagging interrupted parent run {run_id_to_mark[:12]}... "
                                    f"(name: {run_name}, status: {run.info.status})"
                                )

                                try:
                                    client.set_tag(
                                        run_id_to_mark, "code.interrupted", "true")
                                    total_tagged_parents += 1
                                    logger.info(
                                        f"[CLEANUP] Successfully tagged interrupted parent run {run_id_to_mark[:12]}... as interrupted"
                                    )

                                    # Get child runs from pre-built map (no additional API call!)
                                    child_runs = parent_to_children.get(
                                        run_id_to_mark, [])

                                    logger.info(
                                        f"[CLEANUP] Found {len(child_runs)} child runs for parent {run_id_to_mark[:12]}... "
                                        f"(from pre-built map, no API call)"
                                    )

                                    # Tag non-terminal child runs in a single pass
                                    tagged_children = 0
                                    skipped_children = 0

                                    for child_run in child_runs:
                                        child_run_id = child_run.info.run_id
                                        child_status = child_run.info.status
                                        child_name = child_run.info.run_name

                                        # Skip if already tagged
                                        if child_run.data.tags.get("code.interrupted") == "true":
                                            skipped_children += 1
                                            continue

                                        # Only tag non-terminal runs
                                        if child_status not in ["RUNNING", "SCHEDULED", "QUEUED"]:
                                            skipped_children += 1
                                            continue

                                        # Check project identity (must have code.project)
                                        if child_run.data.tags.get("code.project") is None:
                                            skipped_children += 1
                                            logger.debug(
                                                f"[CLEANUP] Skipping child run {child_run_id[:12]}... "
                                                f"(name: {child_name}, reason: no_project_identity)"
                                            )
                                            continue

                                        # Tag the child run
                                        logger.info(
                                            f"[CLEANUP] Tagging interrupted child run {child_run_id[:12]}... "
                                            f"(name: {child_name}, status: {child_status})"
                                        )
                                        try:
                                            client.set_tag(
                                                child_run_id, "code.interrupted", "true")
                                            tagged_children += 1
                                            total_tagged_children += 1
                                            logger.info(
                                                f"[CLEANUP] Successfully tagged interrupted child run {child_run_id[:12]}... as interrupted"
                                            )
                                        except Exception as e:
                                            logger.warning(
                                                f"[CLEANUP] Could not tag child run {child_run_id[:12]}... as interrupted: {e}"
                                            )
                                            skipped_children += 1

                                    logger.info(
                                        f"[CLEANUP] Tagged {tagged_children} interrupted child runs, "
                                        f"skipped {skipped_children} child runs (terminal or filtered) "
                                        f"for parent {run_id_to_mark[:12]}..."
                                    )

                                except Exception as e:
                                    logger.warning(
                                        f"[CLEANUP] Could not tag parent run {run_id_to_mark[:12]}... as interrupted: {e}"
                                    )

                            logger.info(
                                f"[CLEANUP] Completed cleanup: tagged {total_tagged_parents} parent runs "
                                f"and {total_tagged_children} child runs"
                            )
                        else:
                            logger.info(
                                "[CLEANUP] No interrupted parent runs found to tag"
                            )
                        
                        # Store parent_to_children map for reuse in log_final_metrics
                        # Key: (tracking_uri, experiment_id, parent_run_id) for safe scoping
                        tracking_uri = mlflow.get_tracking_uri()
                        child_runs_map_key = (tracking_uri, experiment.experiment_id, parent_run_id)
                        child_runs_map = parent_to_children.get(parent_run_id, [])
                        logger.debug(
                            f"[CLEANUP] Stored child runs map for reuse: "
                            f"{len(child_runs_map)} child runs for parent {parent_run_id[:12]}..."
                        )
                    else:
                        logger.warning(
                            f"[CLEANUP] Could not retrieve experiment: {mlflow_experiment_name}"
                        )
                except Exception as e:
                    logger.warning(
                        f"[CLEANUP] Error during cleanup of interrupted runs: {e}"
                    )
                    import traceback
                    logger.debug(
                        f"[CLEANUP] Cleanup traceback: {traceback.format_exc()}")

            trial_callback = create_trial_callback(parent_run_id)

            if should_resume:
                completed_trials = len(
                    [
                        t for t in study.trials
                        if t.state == optuna.trial.TrialState.COMPLETE
                    ]
                )
                remaining_trials = max(0, max_trials - completed_trials)

                if remaining_trials > 0:
                    study.optimize(
                        objective,
                        n_trials=remaining_trials,
                        timeout=timeout_seconds,
                        show_progress_bar=True,
                        callbacks=[trial_callback],
                    )
            else:
                study.optimize(
                    objective,
                    n_trials=max_trials,
                    timeout=timeout_seconds,
                    show_progress_bar=True,
                    callbacks=[trial_callback],
                )

            if parent_run_id and parent_run_handle:
                try:
                    # Pass child_runs_map if available from cleanup
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
                        child_runs_map=child_runs_map if 'child_runs_map' in locals() else None,
                    )
                except Exception as e:
                    logger.error(
                        f"[HPO] Error in log_final_metrics: {e}"
                    )
                    import traceback
                    logger.error(traceback.format_exc())

    except Exception as e:
        logger.warning(f"MLflow tracking failed: {e}")
        logger.warning("Continuing HPO without MLflow tracking...")

        trial_callback = create_trial_callback(None)

        study.optimize(
            objective,
            n_trials=max_trials,
            timeout=timeout_seconds,
            show_progress_bar=True,
            callbacks=[trial_callback],
        )

        try:
            cleanup_checkpoints()
        except Exception as e:
            logger.warning(
                f"Error during final checkpoint cleanup: {e}"
            )

    return study

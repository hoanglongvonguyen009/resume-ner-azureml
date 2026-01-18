"""Metric logging utilities for sweep tracker."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import mlflow

from common.shared.logging_utils import get_logger
from infrastructure.paths.utils import infer_config_dir

logger = get_logger(__name__)


def log_sweep_metadata(
    hpo_config: Dict[str, Any],
    backbone: str,
    study_name: str,
    checkpoint_config: Optional[Dict[str, Any]],
    storage_path: Optional[Any],
    should_resume: bool,
    output_dir: Optional[Path] = None,
) -> None:
    """Log sweep metadata to MLflow."""
    objective_metric = hpo_config["objective"]["metric"]
    goal = hpo_config.get("objective", {}).get("goal", "maximize")
    max_trials = hpo_config["sampling"]["max_trials"]

    # Infer config_dir from output_dir
    config_dir = infer_config_dir(path=output_dir)

    # Mark parent run as sweep job for Azure ML UI
    from infrastructure.naming.mlflow.tag_keys import (
        get_azureml_run_type,
        get_azureml_sweep,
        get_mlflow_run_type,
    )
    azureml_run_type = get_azureml_run_type(config_dir)
    mlflow_run_type = get_mlflow_run_type(config_dir)
    azureml_sweep = get_azureml_sweep(config_dir)
    mlflow.set_tag(azureml_run_type, "sweep")
    mlflow.set_tag(mlflow_run_type, "sweep")
    mlflow.set_tag(azureml_sweep, "true")

    # Log primary metric and goal for Azure ML UI to identify best trial
    mlflow.log_param("primary_metric", objective_metric)
    mlflow.log_param("objective_goal", goal)

    # Log HPO parameters
    mlflow.log_param("backbone", backbone)
    mlflow.log_param("max_trials", max_trials)
    mlflow.log_param("study_name", study_name)
    mlflow.log_param("objective_metric", objective_metric)
    mlflow.log_param("checkpoint_enabled",
                     checkpoint_config.get("enabled", False) if checkpoint_config else False)

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


def log_sweep_metrics(
    study: Any,
    objective_metric: str,
) -> None:
    """Log sweep metrics (trial counts, best trial metrics)."""
    try:
        import optuna
        completed_trials = len(
            [
                t for t in study.trials
                if t.state == optuna.trial.TrialState.COMPLETE
            ]
        )
        logger.info(
            f"[LOG_FINAL_METRICS] Found {completed_trials} completed trials "
            f"out of {len(study.trials)} total"
        )
    except ImportError:
        completed_trials = len(study.trials)
        logger.warning(
            f"[LOG_FINAL_METRICS] Could not import optuna, "
            f"counting all {completed_trials} trials as completed"
        )

    logger.info(
        f"[LOG_FINAL_METRICS] Logging metrics: "
        f"n_trials={len(study.trials)}, "
        f"n_completed_trials={completed_trials}"
    )
    mlflow.log_metric("n_trials", len(study.trials))
    mlflow.log_metric("n_completed_trials", completed_trials)

    if study.best_trial is not None and study.best_value is not None:
        logger.info(
            f"[LOG_FINAL_METRICS] Logging best trial metrics: "
            f"{objective_metric}={study.best_value}"
        )

        mlflow.log_metric(
            f"best_{objective_metric}", study.best_value
        )

        logger.info(
            f"[LOG_FINAL_METRICS] Logging best hyperparameters: "
            f"{study.best_params}"
        )
        for param_name, param_value in study.best_params.items():
            mlflow.log_param(f"best_{param_name}", param_value)


def log_sweep_parameters(
    study: Any,
) -> None:
    """Log best trial hyperparameters."""
    if study.best_trial is None:
        return
    
    logger.info(
        f"[LOG_FINAL_METRICS] Logging best hyperparameters: "
        f"{study.best_params}"
    )
    for param_name, param_value in study.best_params.items():
        mlflow.log_param(f"best_{param_name}", param_value)


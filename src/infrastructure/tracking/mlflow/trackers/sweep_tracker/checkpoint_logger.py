"""Checkpoint logging utilities for sweep tracker."""

import glob
from pathlib import Path
from typing import Any, List, Optional

import mlflow

from common.shared.logging_utils import get_logger
from infrastructure.tracking.mlflow.artifacts.uploader import ArtifactUploader
from infrastructure.tracking.mlflow.utils import get_mlflow_run_id
from infrastructure.paths.utils import infer_config_dir

logger = get_logger(__name__)


def find_checkpoint_directory(
    study: Any,
    hpo_output_dir: Path,
    backbone: str,
    run_id: Optional[str] = None,
    fold_splits: Optional[List] = None,
) -> Optional[Path]:
    """
    Find checkpoint directory for best trial.
    
    Returns:
        Path to checkpoint directory if found, None otherwise
    """
    if study.best_trial is None:
        return None

    best_trial_number = study.best_trial.number

    # Check if hpo_output_dir already includes backbone
    if hpo_output_dir.name == backbone:
        base_dir = hpo_output_dir
    else:
        base_dir = hpo_output_dir / backbone

    checkpoint_dir = None

    # Strategy 1: Search for refit checkpoint (preferred)
    if run_id:
        run_suffix = f"_{run_id}"
        refit_pattern = str(
            base_dir / f"trial_{best_trial_number}{run_suffix}" / "refit" / "checkpoint")
        refit_matches = glob.glob(refit_pattern)
        if refit_matches:
            checkpoint_dir = Path(refit_matches[0])

    # If not found, search for any refit checkpoint
    if not checkpoint_dir or not checkpoint_dir.exists():
        refit_pattern = str(
            base_dir / f"trial_{best_trial_number}_*" / "refit" / "checkpoint")
        refit_matches = glob.glob(refit_pattern)
        if refit_matches:
            checkpoint_dir = Path(refit_matches[0])

    # Strategy 2: If no refit checkpoint, try CV fold checkpoints
    if not checkpoint_dir or not checkpoint_dir.exists():
        if fold_splits is not None and len(fold_splits) > 0:
            # K-fold CV: use last fold's checkpoint
            last_fold_idx = len(fold_splits) - 1
            if run_id:
                run_suffix = f"_{run_id}"
                checkpoint_dir = (
                    base_dir /
                    f"trial_{best_trial_number}{run_suffix}" /
                    "cv" /
                    f"fold{last_fold_idx}" /
                    "checkpoint"
                )

            if not checkpoint_dir or not checkpoint_dir.exists():
                pattern = str(
                    base_dir / f"trial_{best_trial_number}_*" / "cv" / f"fold{last_fold_idx}" / "checkpoint")
                matches = glob.glob(pattern)
                if matches:
                    checkpoint_dir = Path(matches[0])
        else:
            # Single training (no CV)
            if run_id:
                run_suffix = f"_{run_id}"
                checkpoint_dir = (
                    base_dir /
                    f"trial_{best_trial_number}{run_suffix}" /
                    "checkpoint"
                )

            if not checkpoint_dir or not checkpoint_dir.exists():
                pattern = str(
                    base_dir / f"trial_{best_trial_number}_*" / "checkpoint")
                matches = glob.glob(pattern)
                if matches:
                    checkpoint_dir = Path(matches[0])

    if not checkpoint_dir or not checkpoint_dir.exists():
        logger.warning(
            f"Best trial checkpoint not found for trial {best_trial_number}. "
            f"Searched in: {base_dir}."
        )
        return None

    return checkpoint_dir


def upload_checkpoint_to_mlflow(
    checkpoint_dir: Path,
    best_trial_number: int,
    run_id: Optional[str] = None,
    config_dir: Optional[Path] = None,
) -> bool:
    """
    Upload checkpoint to MLflow.
    
    Returns:
        True if upload succeeded, False otherwise
    """
    if config_dir is None:
        config_dir = infer_config_dir(path=checkpoint_dir)

    try:
        active_run = mlflow.active_run()
        if not active_run:
            raise ValueError("No active MLflow run for artifact logging")

        if not hasattr(active_run, 'info') or not hasattr(active_run.info, 'run_id'):
            raise ValueError("Active MLflow run does not have 'info.run_id' attribute")

        uploader = ArtifactUploader(
            run_id=run_id,  # Use provided run_id or active run
            stage=None,  # HPO doesn't have a specific stage config
            config_dir=config_dir,
        )

        logger.info("Uploading checkpoint archive...")
        artifact_logged = uploader.upload_checkpoint(
            checkpoint_dir=checkpoint_dir,
            artifact_path="best_trial_checkpoint.tar.gz",
            trial_number=best_trial_number,
        )

        return artifact_logged
    except Exception as archive_error:
        error_type = type(archive_error).__name__
        error_msg = str(archive_error)
        logger.warning(
            f"Failed to upload checkpoint archive: {error_type}: {error_msg}"
        )
        return False


def mark_study_complete(
    study: Any,
    best_trial_number: int,
) -> None:
    """Mark study as complete with checkpoint uploaded."""
    try:
        from datetime import datetime
        study.set_user_attr("hpo_complete", "true")
        study.set_user_attr("checkpoint_uploaded", "true")
        study.set_user_attr("completion_timestamp", datetime.now().isoformat())
        study.set_user_attr("best_trial_number", str(best_trial_number))
        logger.info(
            f"Marked study as complete with checkpoint uploaded (best trial: {best_trial_number})"
        )
    except Exception as attr_error:
        logger.warning(f"Could not mark study as complete: {attr_error}")


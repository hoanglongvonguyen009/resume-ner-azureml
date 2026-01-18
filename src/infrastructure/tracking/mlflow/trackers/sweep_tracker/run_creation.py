"""Run creation utilities for sweep tracker."""

from pathlib import Path
from typing import Any, Dict, Optional

import mlflow

from common.shared.logging_utils import get_logger
from infrastructure.tracking.mlflow.types import RunHandle
from infrastructure.tracking.mlflow.index import update_mlflow_index
from infrastructure.paths.utils import infer_config_dir

from infrastructure.tracking.mlflow.trackers.sweep_tracker.tagging import (
    build_sweep_tags,
    compute_grouping_hashes,
)

logger = get_logger(__name__)


def create_mlflow_sweep_run(
    run_name: str,
    hpo_config: Dict[str, Any],
    backbone: str,
    context: Optional[Any],  # NamingContext
    output_dir: Optional[Path],
    group_id: Optional[str],
    data_config: Optional[Dict[str, Any]],
    benchmark_config: Optional[Dict[str, Any]],
    train_config: Optional[Dict[str, Any]],
    config_dir: Optional[Path],
    experiment_name: str,
) -> tuple[RunHandle, Optional[str], Optional[str]]:
    """
    Create MLflow sweep run and return RunHandle with grouping hashes.
    
    Returns:
        Tuple of (RunHandle, study_key_hash, study_family_hash)
    """
    with mlflow.start_run(run_name=run_name) as parent_run:
        run_id = parent_run.info.run_id
        experiment_id = parent_run.info.experiment_id
        tracking_uri = mlflow.get_tracking_uri()

        # Trust provided config_dir parameter (DRY principle)
        if config_dir is None:
            config_dir = infer_config_dir(path=output_dir)

        # Compute grouping hashes
        study_key_hash, study_family_hash = compute_grouping_hashes(
            hpo_config=hpo_config,
            data_config=data_config,
            train_config=train_config,
            context=context,
            config_dir=config_dir,
        )

        # Build and set tags
        tags = build_sweep_tags(
            context=context,
            output_dir=output_dir,
            group_id=group_id,
            config_dir=config_dir,
            study_key_hash=study_key_hash,
            study_family_hash=study_family_hash,
        )

        mlflow.set_tags(tags)

        handle = RunHandle(
            run_id=run_id,
            run_key=tags.get("code.run_key", ""),
            run_key_hash=tags.get("code.run_key_hash", ""),
            experiment_id=experiment_id,
            experiment_name=experiment_name,
            tracking_uri=tracking_uri,
            artifact_uri=parent_run.info.artifact_uri,
            study_key_hash=study_key_hash,
            study_family_hash=study_family_hash,
        )

        # Update local index
        run_key_hash = tags.get("code.run_key_hash")
        if run_key_hash:
            try:
                root_dir = output_dir.parent.parent if output_dir else Path.cwd()
                update_mlflow_index(
                    root_dir=root_dir,
                    run_key_hash=run_key_hash,
                    run_id=run_id,
                    experiment_id=experiment_id,
                    tracking_uri=tracking_uri,
                    config_dir=config_dir,
                )
            except Exception as e:
                logger.debug(f"Could not update MLflow index: {e}")

        return handle, study_key_hash, study_family_hash


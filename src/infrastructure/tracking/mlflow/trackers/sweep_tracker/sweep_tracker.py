"""
@meta
name: tracking_mlflow_sweep_tracker
type: utility
domain: tracking
responsibility:
  - Track MLflow runs for HPO sweep stage
  - Manage sweep and trial run lifecycle
inputs:
  - Sweep configurations
  - Run names and contexts
outputs:
  - MLflow run handles
tags:
  - utility
  - tracking
  - mlflow
  - tracker
  - hpo
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""MLflow tracker for sweep stage.

This module has been refactored into focused submodules:
- sweep_tracker.config: Parameter Objects (TypedDicts)
- sweep_tracker.run_creation: Run creation logic
- sweep_tracker.tagging: Tagging logic
- sweep_tracker.metrics: Metric logging logic
- sweep_tracker.checkpoint_logger: Checkpoint logging
- sweep_tracker.trial_finder: Trial finding utilities

This file maintains backward compatibility by re-exporting all public APIs.
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

import mlflow

from common.shared.logging_utils import get_logger

from infrastructure.tracking.mlflow.trackers.base_tracker import BaseTracker
from infrastructure.tracking.mlflow.types import RunHandle

# Import from extracted modules
from infrastructure.tracking.mlflow.trackers.sweep_tracker.run_creation import (
    create_mlflow_sweep_run,
)
from infrastructure.tracking.mlflow.trackers.sweep_tracker.tagging import (
    build_sweep_tags,
    compute_grouping_hashes,
)
from infrastructure.tracking.mlflow.trackers.sweep_tracker.metrics import (
    log_sweep_metadata,
    log_sweep_metrics,
    log_sweep_parameters,
)
from infrastructure.tracking.mlflow.trackers.sweep_tracker.checkpoint_logger import (
    find_checkpoint_directory,
    upload_checkpoint_to_mlflow,
    mark_study_complete,
)
from infrastructure.tracking.mlflow.trackers.sweep_tracker.trial_finder import (
    extract_trial_number,
    find_best_trial_run_id,
)

# Import original methods that haven't been fully extracted yet
# TODO: Complete migration - extract remaining methods and remove sweep_tracker_original.py
# Migration Status: IN PROGRESS
# See: MASTER-20260118-1608-consolidate-remaining-dry-violations-src-unified.plan.md
# 
# Remaining methods to extract:
# - log_final_metrics() - delegates to _original
# - log_best_checkpoint() - delegates to _original  
# - log_tracking_info() - delegates to _original
from infrastructure.tracking.mlflow.trackers.sweep_tracker_original import (
    MLflowSweepTracker as _MLflowSweepTrackerOriginal,
)

logger = get_logger(__name__)


class MLflowSweepTracker(BaseTracker):
    """Tracks MLflow runs for HPO sweeps."""

    def __init__(self, experiment_name: str):
        """
        Initialize tracker.

        Args:
            experiment_name: MLflow experiment name.
        """
        super().__init__(experiment_name)
        # Use original implementation for methods not yet extracted
        # TODO: Complete migration - extract log_final_metrics, log_best_checkpoint, log_tracking_info
        self._original = _MLflowSweepTrackerOriginal(experiment_name)

    @contextmanager
    def start_sweep_run(
        self,
        run_name: str,
        hpo_config: Dict[str, Any],
        backbone: str,
        study_name: str,
        checkpoint_config: Optional[Dict[str, Any]],
        storage_path: Optional[Any],
        should_resume: bool,
        context: Optional[Any] = None,  # NamingContext
        output_dir: Optional[Path] = None,
        group_id: Optional[str] = None,
        data_config: Optional[Dict[str, Any]] = None,
        benchmark_config: Optional[Dict[str, Any]] = None,
        train_config: Optional[Dict[str, Any]] = None,
        config_dir: Optional[Path] = None,
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
            context: Optional NamingContext for tag-based identification.
            output_dir: Optional output directory for metadata persistence.
            group_id: Optional group/session identifier.
            data_config: Optional data configuration dictionary (for grouping tags).
            benchmark_config: Optional benchmark configuration dictionary (for grouping tags).
            train_config: Optional training configuration dictionary (for v2 hash computation).
            config_dir: Optional config directory path. If provided, used directly without inference.

        Yields:
            RunHandle with run information.
        """
        try:
            handle, study_key_hash, study_family_hash = create_mlflow_sweep_run(
                run_name=run_name,
                hpo_config=hpo_config,
                backbone=backbone,
                context=context,
                output_dir=output_dir,
                group_id=group_id,
                data_config=data_config,
                benchmark_config=benchmark_config,
                train_config=train_config,
                config_dir=config_dir,
                experiment_name=self.experiment_name,
            )

            # Log sweep metadata
            log_sweep_metadata(
                hpo_config=hpo_config,
                backbone=backbone,
                study_name=study_name,
                checkpoint_config=checkpoint_config,
                storage_path=storage_path,
                should_resume=should_resume,
                output_dir=output_dir,
            )

            logger.info(
                f"[START_SWEEP_RUN] Yielding RunHandle. run_id={handle.run_id[:12]}...")
            yield handle
            logger.info(
                f"[START_SWEEP_RUN] Context manager exiting normally. run_id={handle.run_id[:12]}...")
        except Exception as e:
            import traceback
            logger.error(f"[START_SWEEP_RUN] MLflow tracking failed: {e}")
            logger.error(
                f"[START_SWEEP_RUN] Traceback: {traceback.format_exc()}")
            logger.warning("Continuing HPO without MLflow tracking...")
            # Yield a dummy context manager that does nothing
            from contextlib import nullcontext
            with nullcontext():
                yield None

    def log_final_metrics(
        self,
        study: Any,
        objective_metric: str,
        parent_run_id: str,
        run_name: Optional[str] = None,
        should_resume: bool = False,
        hpo_output_dir: Optional[Path] = None,
        backbone: Optional[str] = None,
        run_id: Optional[str] = None,
        fold_splits: Optional[List] = None,
        hpo_config: Optional[Dict[str, Any]] = None,
        child_runs_map: Optional[List] = None,
        upload_checkpoint: bool = True,
        output_dir: Optional[Path] = None,
        config_dir: Optional[Path] = None,
    ) -> None:
        """
        Log final metrics and best trial information to parent run.

        Args:
            upload_checkpoint: If True, upload checkpoint immediately. If False, 
                             defer checkpoint upload (e.g., until after refit completes).
        """
        logger.info(
            f"[LOG_FINAL_METRICS] Starting log_final_metrics for "
            f"parent_run_id={parent_run_id[:12] if parent_run_id else 'None'}..."
        )

        # Use original implementation for now (will be refactored incrementally)
        return self._original.log_final_metrics(
            study=study,
            objective_metric=objective_metric,
            parent_run_id=parent_run_id,
            run_name=run_name,
            should_resume=should_resume,
            hpo_output_dir=hpo_output_dir,
            backbone=backbone,
            run_id=run_id,
            fold_splits=fold_splits,
            hpo_config=hpo_config,
            child_runs_map=child_runs_map,
            upload_checkpoint=upload_checkpoint,
            output_dir=output_dir,
            config_dir=config_dir,
        )

    def log_best_checkpoint(
        self,
        study: Any,
        hpo_output_dir: Path,
        backbone: str,
        run_id: Optional[str] = None,
        fold_splits: Optional[List] = None,
        prefer_checkpoint_dir: Optional[Path] = None,
        refit_ok: Optional[bool] = None,
        parent_run_id: Optional[str] = None,
        refit_run_id: Optional[str] = None,
        config_dir: Optional[Path] = None,
    ) -> None:
        """Log best trial checkpoint to MLflow run."""
        # Use original implementation for now (will be refactored incrementally)
        return self._original.log_best_checkpoint(
            study=study,
            hpo_output_dir=hpo_output_dir,
            backbone=backbone,
            run_id=run_id,
            fold_splits=fold_splits,
            prefer_checkpoint_dir=prefer_checkpoint_dir,
            refit_ok=refit_ok,
            parent_run_id=parent_run_id,
            refit_run_id=refit_run_id,
            config_dir=config_dir,
        )

    def log_tracking_info(self) -> None:
        """Log MLflow tracking URI information for user visibility."""
        return self._original.log_tracking_info()

    def _log_best_trial_id(
        self,
        study: Any,
        parent_run_id: str,
        run_name: Optional[str] = None,
        should_resume: bool = False,
        cached_child_runs: Optional[List] = None,
        output_dir: Optional[Path] = None,
    ) -> None:
        """
        Find and log the best trial's MLflow run ID.
        
        This method delegates to the original implementation during migration.
        TODO: Extract to sweep_tracker module when migration completes.
        """
        return self._original._log_best_trial_id(
            study=study,
            parent_run_id=parent_run_id,
            run_name=run_name,
            should_resume=should_resume,
            cached_child_runs=cached_child_runs,
            output_dir=output_dir,
        )

    def _log_sweep_metadata(
        self,
        hpo_config: Dict[str, Any],
        backbone: str,
        study_name: str,
        checkpoint_config: Optional[Dict[str, Any]],
        storage_path: Optional[Any],
        should_resume: bool,
        output_dir: Optional[Path] = None,
    ) -> None:
        """
        Log sweep metadata to MLflow run.
        
        This method delegates to the original implementation during migration.
        TODO: Remove when migration completes - use log_sweep_metadata from metrics module instead.
        """
        return self._original._log_sweep_metadata(
            hpo_config=hpo_config,
            backbone=backbone,
            study_name=study_name,
            checkpoint_config=checkpoint_config,
            storage_path=storage_path,
            should_resume=should_resume,
            output_dir=output_dir,
        )


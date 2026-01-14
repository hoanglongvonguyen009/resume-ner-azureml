from __future__ import annotations

"""
@meta
name: artifact_unified_compat
type: utility
domain: selection
responsibility:
  - Backward compatibility wrapper for existing artifact acquisition API
  - Wrap unified acquisition system for legacy code
inputs:
  - Best run information
  - Acquisition and selection configuration
outputs:
  - Checkpoint paths
tags:
  - utility
  - selection
  - artifacts
  - compatibility
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Backward compatibility wrapper for existing artifact acquisition API.

This module provides compatibility functions that wrap the unified acquisition system
to maintain backward compatibility with existing code.
"""
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from mlflow.tracking import MlflowClient

from common.shared.logging_utils import get_logger
from evaluation.selection.artifact_unified.acquisition import acquire_artifact
from evaluation.selection.artifact_unified.types import ArtifactKind, ArtifactRequest

logger = get_logger(__name__)


def acquire_best_model_checkpoint(
    best_run_info: Dict[str, Any],
    root_dir: Path,
    config_dir: Path,
    acquisition_config: Dict[str, Any],
    selection_config: Dict[str, Any],
    platform: str,
    restore_from_drive: Optional[Callable[[Path, bool], bool]] = None,
    drive_store: Optional[Any] = None,
    in_colab: bool = False,
) -> Path:
    """
    Acquire checkpoint using unified acquisition system (backward compatibility wrapper).
    
    This function wraps the unified acquisition API to maintain backward compatibility
    with existing code that calls `acquire_best_model_checkpoint()`.
    
    Args:
        best_run_info: Dictionary with best run information (must include study_key_hash, trial_key_hash, run_id, backbone)
        root_dir: Project root directory
        config_dir: Config directory
        acquisition_config: Artifact acquisition configuration
        selection_config: Best model selection configuration (unused, kept for compatibility)
        platform: Platform name (local, colab, kaggle)
        restore_from_drive: Optional function to restore from Drive backup
        drive_store: Optional DriveBackupStore instance for direct Drive access
        in_colab: Whether running in Google Colab
        
    Returns:
        Path to validated checkpoint directory
        
    Raises:
        ValueError: If all fallback strategies fail
    """
    # Extract required fields from best_run_info
    refit_run_id = best_run_info.get("refit_run_id")
    trial_run_id = best_run_info.get("trial_run_id") or best_run_info.get("run_id")
    study_key_hash = best_run_info.get("study_key_hash")
    trial_key_hash = best_run_info.get("trial_key_hash")
    backbone = best_run_info.get("backbone", "unknown")
    experiment_name = best_run_info.get("experiment_name")
    
    if not trial_run_id:
        raise ValueError(
            "trial_run_id or run_id is required in best_run_info"
        )
    
    # Note: refit_run_id is optional - unified system will look it up if not provided
    
    # Check if output_base_dir is specified in config (for different use cases like benchmarking)
    output_base_dir = acquisition_config.get("output_base_dir")
    
    # Get artifact_run_id (prefer refit, fallback to trial)
    artifact_run_id = refit_run_id or trial_run_id
    
    # Get search roots from config (configurable list of directories to search)
    search_roots = acquisition_config.get("search_roots", ["artifacts", "best_model_selection"])
    
    logger.info(
        f"Using search_roots from config: {search_roots} "
        f"(from artifact_acquisition.yaml: {'yes' if 'search_roots' in acquisition_config else 'no, using defaults'})"
    )
    
    # Create artifact request
    request = ArtifactRequest(
        artifact_kind=ArtifactKind.CHECKPOINT,
        run_id=trial_run_id,
        backbone=backbone,
        study_key_hash=study_key_hash,
        trial_key_hash=trial_key_hash,
        refit_run_id=refit_run_id,
        experiment_name=experiment_name,
        metadata={
            "config_dir": config_dir,
            "output_base_dir": output_base_dir,  # Pass through for path construction
            "artifact_run_id": artifact_run_id,  # Primary key for refit-aware discovery
            "search_roots": search_roots,  # Configurable search roots
        },
    )
    
    # Get MLflow client and experiment ID
    mlflow_client = MlflowClient()
    experiment_id = None
    
    if experiment_name:
        try:
            experiment = mlflow_client.get_experiment_by_name(experiment_name)
            if experiment:
                experiment_id = experiment.experiment_id
        except Exception as e:
            logger.debug(f"Could not get experiment by name: {e}")
    
    if not experiment_id and refit_run_id:
        try:
            run = mlflow_client.get_run(refit_run_id)
            experiment_id = run.info.experiment_id
        except Exception:
            pass
    
    if not experiment_id and trial_run_id:
        try:
            run = mlflow_client.get_run(trial_run_id)
            experiment_id = run.info.experiment_id
        except Exception:
            pass
    
    # Acquire artifact using unified system
    result = acquire_artifact(
        request=request,
        root_dir=root_dir,
        config_dir=config_dir,
        acquisition_config=acquisition_config,
        mlflow_client=mlflow_client,
        experiment_id=experiment_id,
        restore_from_drive=restore_from_drive,
        drive_store=drive_store,
        in_colab=in_colab,
    )
    
    if not result.success or result.path is None:
        # Generate helpful error message (similar to original)
        error_msg = (
            f"\n[ERROR] Could not acquire checkpoint for run {trial_run_id[:8]}...\n"
            f"   Experiment: {experiment_name or 'unknown'}\n"
            f"   Backbone: {backbone}\n"
            f"\n[TRIED] Strategies attempted:\n"
        )
        
        priority = acquisition_config.get("artifact_kinds", {}).get("checkpoint", {}).get("priority") or \
                   acquisition_config.get("priority", ["local", "drive", "mlflow"])
        
        for i, source in enumerate(priority, 1):
            error_msg += f"   {i}. {source.capitalize()}\n"
        
        error_msg += f"\n[ERROR] {result.error}\n"
        
        raise ValueError(error_msg)
    
    # Backup to Drive if in Colab and checkpoint was successfully acquired
    if result.path and in_colab and drive_store and acquisition_config.get("drive", {}).get("enabled", False):
        try:
            checkpoint_path = Path(result.path).resolve()
            
            if checkpoint_path.exists() and checkpoint_path.is_dir():
                print(f"\n📦 Backing up best model checkpoint to Google Drive...")
                result_backup = drive_store.backup(checkpoint_path, expect="dir")
                if result_backup.ok:
                    print(f"✓ Successfully backed up checkpoint to Google Drive")
                    print(f"  Drive path: {result_backup.dst}")
                else:
                    print(f"⚠ Drive backup failed: {result_backup.reason}")
                    if result_backup.error:
                        print(f"  Error: {result_backup.error}")
                    print(f"  Checkpoint is still available locally at: {checkpoint_path}")
        except Exception as e:
            print(f"⚠ Drive backup error: {e}")
            print(f"  Checkpoint is still available locally at: {result.path}")
    
    # At this point, result.path is non-None (guarded above)
    return Path(result.path)


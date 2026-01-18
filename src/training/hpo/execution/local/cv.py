from __future__ import annotations

"""
@meta
name: hpo_cv_orchestration
type: script
domain: hpo
responsibility:
  - Orchestrate k-fold cross-validation for HPO trials
  - Create nested MLflow run structure
  - Aggregate fold metrics
inputs:
  - Trial hyperparameters
  - Fold splits
outputs:
  - Average CV metric
  - Fold metrics
tags:
  - orchestration
  - hpo
  - cross-validation
ci:
  runnable: true
  needs_gpu: true
  needs_cloud: false
lifecycle:
  status: active
"""

"""Cross-validation orchestration for HPO trials."""
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypedDict
import json
from datetime import datetime

import mlflow
import numpy as np
from common.shared.logging_utils import get_logger

from .trial import run_training_trial

logger = get_logger(__name__)


class CVTrialConfig(TypedDict):
    """Configuration for CV trial workflow."""
    trial_params: Dict[str, Any]
    dataset_path: str
    config_dir: Path
    backbone: str
    output_dir: Path
    train_config: Dict[str, Any]
    mlflow_experiment_name: str
    objective_metric: str
    fold_splits: List[Tuple[List[int], List[int]]]
    fold_splits_file: Path
    hpo_parent_run_id: Optional[str]
    study_key_hash: Optional[str]
    study_family_hash: Optional[str]
    data_config: Optional[Dict[str, Any]]
    hpo_config: Optional[Dict[str, Any]]
    benchmark_config: Optional[Dict[str, Any]]


def _compute_trial_hashes(
    trial_params: Dict[str, Any],
    study_key_hash: Optional[str],
    hpo_parent_run_id: Optional[str],
    data_config: Optional[Dict[str, Any]],
    hpo_config: Optional[Dict[str, Any]],
    train_config: Optional[Dict[str, Any]],
    backbone: str,
    config_dir: Path,
) -> tuple[Optional[str], Optional[str]]:
    """
    Compute study_key_hash and trial_key_hash for CV trial.

    Returns:
        Tuple of (computed_study_key_hash, computed_trial_key_hash).
    """
    from infrastructure.tracking.mlflow.hash_utils import (
        get_or_compute_study_key_hash,
        get_or_compute_trial_key_hash,
    )

    computed_study_key_hash = get_or_compute_study_key_hash(
        study_key_hash=study_key_hash,
        hpo_parent_run_id=hpo_parent_run_id,
        data_config=data_config,
        hpo_config=hpo_config,
        train_config=train_config,
        backbone=backbone,
        config_dir=config_dir,
    )

    computed_trial_key_hash = None
    if computed_study_key_hash:
        # Extract hyperparameters (excluding metadata fields)
        hyperparameters = {
            k: v for k, v in trial_params.items()
            if k not in ("backbone", "trial_number", "run_id")
        }
        computed_trial_key_hash = get_or_compute_trial_key_hash(
            trial_key_hash=None,
            trial_run_id=None,
            study_key_hash=computed_study_key_hash,
            hyperparameters=hyperparameters,
            config_dir=config_dir,
        )
        if not computed_trial_key_hash:
            logger.warning(f"Could not compute trial_key_hash")

    return computed_study_key_hash, computed_trial_key_hash


def _build_trial_output_dir(
    trial_params: Dict[str, Any],
    output_dir: Path,
    config_dir: Path,
    backbone: str,
    computed_study_key_hash: Optional[str],
    computed_trial_key_hash: Optional[str],
) -> Path:
    """
    Build trial output directory using v2 pattern.

    Returns:
        Path to trial base directory.
    """
    trial_number = trial_params.get("trial_number", "unknown")
    study_folder_name = output_dir.name
    is_v2_study_folder = study_folder_name.startswith("study-") and len(study_folder_name) > 7

    # CRITICAL: If we're in a v2 study folder, we MUST use v2 trial naming
    if is_v2_study_folder and not computed_trial_key_hash:
        logger.error(
            f"In v2 study folder {study_folder_name} but trial_key_hash is None. "
            f"study_key_hash={'YES' if computed_study_key_hash else 'NO'}. "
            f"Will attempt to compute hash."
        )

    trial_base_dir = None
    if computed_study_key_hash and computed_trial_key_hash:
        try:
            from infrastructure.naming import create_naming_context
            from infrastructure.paths import build_output_path
            from common.shared.platform_detection import detect_platform
            from infrastructure.paths.repo import detect_repo_root
            from infrastructure.paths.utils import resolve_project_paths_with_fallback

            # Resolve root_dir and config_dir
            if config_dir is not None:
                root_dir = detect_repo_root(config_dir=config_dir)
                resolved_config_dir = config_dir
            else:
                root_dir, resolved_config_dir = resolve_project_paths_with_fallback(
                    output_dir=output_dir,
                    config_dir=None,
                )

            # Create NamingContext for trial
            trial_context = create_naming_context(
                process_type="hpo",
                model=backbone.split("-")[0] if "-" in backbone else backbone,
                environment=detect_platform(),
                storage_env=detect_platform(),
                study_key_hash=computed_study_key_hash,
                trial_key_hash=computed_trial_key_hash,
                trial_number=trial_number,
            )

            # Build trial path using v2 pattern
            trial_base_dir = build_output_path(root_dir, trial_context, config_dir=resolved_config_dir)
            trial_base_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"build_output_path() failed: {e}. Will attempt fallback.")
            trial_base_dir = None

    # Fallback: Retry build_output_path() if it failed and we have hashes
    if trial_base_dir is None:
        if is_v2_study_folder:
            # We're in a v2 study folder - must use v2 trial naming
            if not computed_trial_key_hash and computed_study_key_hash:
                # Try to recompute trial_key_hash from trial_params
                logger.warning(
                    f"In v2 study folder {study_folder_name} but trial_key_hash is None. "
                    f"Attempting to recompute from trial_params..."
                )
                try:
                    from infrastructure.tracking.mlflow.hash_utils import get_or_compute_trial_key_hash
                    hyperparameters = {
                        k: v for k, v in trial_params.items()
                        if k not in ("backbone", "trial_number", "run_id")
                    }
                    computed_trial_key_hash = get_or_compute_trial_key_hash(
                        trial_key_hash=None,
                        trial_run_id=None,
                        study_key_hash=computed_study_key_hash,
                        hyperparameters=hyperparameters,
                        config_dir=config_dir,
                    )
                except Exception as e:
                    logger.error(f"Failed to recompute trial_key_hash: {e}", exc_info=True)

            # Retry build_output_path() if we now have both hashes
            if computed_study_key_hash and computed_trial_key_hash:
                try:
                    from infrastructure.naming import create_naming_context
                    from infrastructure.paths import build_output_path
                    from common.shared.platform_detection import detect_platform
                    from infrastructure.paths.utils import resolve_project_paths_with_fallback

                    root_dir, resolved_config_dir = resolve_project_paths_with_fallback(
                        output_dir=output_dir,
                        config_dir=config_dir,
                    )

                    trial_context = create_naming_context(
                        process_type="hpo",
                        model=backbone.split("-")[0] if "-" in backbone else backbone,
                        environment=detect_platform(),
                        storage_env=detect_platform(),
                        study_key_hash=computed_study_key_hash,
                        trial_key_hash=computed_trial_key_hash,
                        trial_number=trial_number,
                    )
                    trial_base_dir = build_output_path(root_dir, trial_context, config_dir=resolved_config_dir)
                    trial_base_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    logger.error(
                        f"CRITICAL: build_output_path() failed even with recomputed hashes: {e}",
                        exc_info=True
                    )
                    raise RuntimeError(
                        f"Cannot create trial in v2 study folder {study_folder_name} without trial_key_hash. "
                        f"Hash computation and path building failed. This is a critical error."
                    ) from e
            else:
                # Missing required hashes - cannot proceed
                raise RuntimeError(
                    f"Cannot create trial in v2 study folder {study_folder_name} without trial_key_hash. "
                    f"study_key_hash={'YES' if computed_study_key_hash else 'NO'}, "
                    f"trial_key_hash={'YES' if computed_trial_key_hash else 'NO'}. "
                    f"This is a critical error that must be fixed."
                )
        else:
            # Should not happen - we only support v2 paths
            raise RuntimeError(
                f"Cannot create trial in non-v2 study folder. Only v2 paths (study-{{hash}}) are supported. "
                f"Found study folder: {study_folder_name}"
            )

    # CRITICAL CHECK: If we're in a v2 study folder, verify we're using v2 naming
    if is_v2_study_folder:
        if trial_base_dir is None:
            raise RuntimeError(
                f"In v2 study folder {study_folder_name} but trial_base_dir is None. "
                f"This indicates a bug in the path construction logic."
            )
        if not trial_base_dir.name.startswith("trial-"):
            raise RuntimeError(
                f"In v2 study folder {study_folder_name} but trial_base_dir uses legacy naming: {trial_base_dir.name}. "
                f"This indicates a bug in the path construction logic. "
                f"trial_base_dir={trial_base_dir}"
            )

    return trial_base_dir


def _write_trial_metadata(
    trial_base_dir: Path,
    computed_study_key_hash: Optional[str],
    computed_trial_key_hash: Optional[str],
    trial_number: Any,
    study_name: str,
    run_id: Optional[str],
) -> Path:
    """
    Write trial metadata file for easy lookup during selection.

    Returns:
        Absolute path to trial base directory.
    """
    # Resolve to absolute path to ensure we're writing to the correct location
    trial_base_dir_abs = Path(trial_base_dir).resolve()

    trial_meta = {
        "study_key_hash": computed_study_key_hash,
        "trial_key_hash": computed_trial_key_hash,
        "trial_number": trial_number,
        "study_name": study_name,
        "run_id": run_id,
        "created_at": datetime.now().isoformat(),
    }
    trial_meta_path = trial_base_dir_abs / "trial_meta.json"

    # FINAL CHECK: Ensure we're not creating a legacy folder in a v2 study folder
    study_folder_name = trial_base_dir_abs.parent.name if trial_base_dir_abs.parent.name.startswith("study-") else None
    is_v2_study_folder = study_folder_name and len(study_folder_name) > 7
    if is_v2_study_folder and not trial_base_dir_abs.name.startswith("trial-"):
        raise RuntimeError(
            f"About to create legacy folder {trial_base_dir_abs.name} in v2 study folder {study_folder_name}. "
            f"This should never happen. Check path construction logic."
        )

    trial_base_dir_abs.mkdir(parents=True, exist_ok=True)
    with open(trial_meta_path, "w") as f:
        json.dump(trial_meta, f, indent=2)

    logger.info(f"[CV] Created trial folder: {trial_base_dir_abs} (trial {trial_number})")
    logger.debug(f"[CV] Trial metadata written to: {trial_meta_path}")

    return trial_base_dir_abs


def _execute_cv_folds(
    trial_params: Dict[str, Any],
    dataset_path: str,
    config_dir: Path,
    backbone: str,
    train_config: Dict[str, Any],
    mlflow_experiment_name: str,
    objective_metric: str,
    fold_splits: List[Tuple[List[int], List[int]]],
    fold_splits_file: Path,
    trial_base_dir: Path,
    trial_run_id: Optional[str],
    hpo_parent_run_id: Optional[str],
) -> List[float]:
    """
    Execute training for each CV fold.

    Returns:
        List of metrics for each fold.
    """
    fold_metrics = []

    for fold_idx, (train_indices, val_indices) in enumerate(fold_splits):
        # Construct fold-specific output directory
        fold_output_dir = trial_base_dir / "cv" / f"fold{fold_idx}"

        # Run training for this fold
        # Fold runs should be children of the trial run to maintain proper hierarchy:
        # HPO Parent -> Trial Run -> Fold Runs
        # Fallback to hpo_parent_run_id only if trial_run_id is not available
        fold_parent_id = trial_run_id if trial_run_id else hpo_parent_run_id
        fold_metric = run_training_trial(
            trial_params=trial_params,
            dataset_path=dataset_path,
            config_dir=config_dir,
            backbone=backbone,
            output_dir=fold_output_dir,
            train_config=train_config,
            mlflow_experiment_name=mlflow_experiment_name,
            objective_metric=objective_metric,
            fold_idx=fold_idx,
            fold_splits_file=fold_splits_file,
            parent_run_id=fold_parent_id,
        )
        fold_metrics.append(fold_metric)

    return fold_metrics

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
    study_key_hash: Optional[str] = None,
    study_family_hash: Optional[str] = None,
    data_config: Optional[Dict[str, Any]] = None,
    hpo_config: Optional[Dict[str, Any]] = None,
    benchmark_config: Optional[Dict[str, Any]] = None,
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
        study_key_hash: Optional study key hash from parent run (for grouping tags).
        study_family_hash: Optional study family hash from parent run (for grouping tags).

    Returns:
        Tuple of (average_metric, fold_metrics) where:
        - average_metric: Average metric across all folds
        - fold_metrics: List of metrics for each fold
    """
    # Create trial-level run (child of HPO parent) if parent is provided
    trial_run_id = _create_trial_run(
        trial_params=trial_params,
        config_dir=config_dir,
        backbone=backbone,
        output_dir=output_dir,
        hpo_parent_run_id=hpo_parent_run_id,
        study_key_hash=study_key_hash,
        study_family_hash=study_family_hash,
        data_config=data_config,
        hpo_config=hpo_config,
        train_config=train_config,
        benchmark_config=benchmark_config,
    )

    # Get trial metadata
    trial_number = trial_params.get("trial_number", "unknown")
    run_id = trial_params.get("run_id")

    # Compute study_key_hash and trial_key_hash
    computed_study_key_hash, computed_trial_key_hash = _compute_trial_hashes(
        trial_params,
        study_key_hash,
        hpo_parent_run_id,
        data_config,
        hpo_config,
        train_config,
        backbone,
        config_dir,
    )

    # Build trial output directory
    trial_base_dir = _build_trial_output_dir(
        trial_params,
        output_dir,
        config_dir,
        backbone,
        computed_study_key_hash,
        computed_trial_key_hash,
    )

    # Write trial metadata file
    study_name = output_dir.name
    trial_base_dir = _write_trial_metadata(
        trial_base_dir,
        computed_study_key_hash,
        computed_trial_key_hash,
        trial_number,
        study_name,
        run_id,
    )

    # Execute CV folds
    fold_metrics = _execute_cv_folds(
        trial_params,
        dataset_path,
        config_dir,
        backbone,
        train_config,
        mlflow_experiment_name,
        objective_metric,
        fold_splits,
        fold_splits_file,
        trial_base_dir,
        trial_run_id,
        hpo_parent_run_id,
    )

    # Calculate average metric
    average_metric = np.mean(fold_metrics)

    # Log aggregated metrics to trial run
    if trial_run_id:
        _log_cv_metrics_to_trial_run(
            trial_run_id=trial_run_id,
            trial_params=trial_params,
            objective_metric=objective_metric,
            average_metric=average_metric,
            fold_metrics=fold_metrics,
        )

    return average_metric, fold_metrics

def _create_trial_run(
    trial_params: Dict[str, Any],
    config_dir: Path,
    backbone: str,
    output_dir: Path,
    hpo_parent_run_id: Optional[str],
    study_key_hash: Optional[str] = None,
    study_family_hash: Optional[str] = None,
    data_config: Optional[Dict[str, Any]] = None,
    hpo_config: Optional[Dict[str, Any]] = None,
    train_config: Optional[Dict[str, Any]] = None,
    benchmark_config: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Create trial-level MLflow run for CV trials.

    Returns:
        Trial run ID, or None if creation failed.
    """
    if not hpo_parent_run_id:
        return None

    try:
        from infrastructure.tracking.mlflow.client import create_mlflow_client
        client = create_mlflow_client()
        
        # Get experiment_id from parent run instead of relying on mlflow.active_run()
        # This is more reliable, especially in Colab where active_run() may return None
        try:
            parent_run = client.get_run(hpo_parent_run_id)
            experiment_id = parent_run.info.experiment_id
        except Exception as e:
            logger.warning(f"Could not get experiment_id from parent run {hpo_parent_run_id[:12] if hpo_parent_run_id else 'None'}...: {e}")
            # Fallback to active_run() if parent lookup fails
            active_run = mlflow.active_run()
            if not active_run:
                logger.warning("Could not get experiment_id from parent run or active_run(), cannot create trial run")
                return None
            experiment_id = active_run.info.experiment_id
        
        trial_number = trial_params.get("trial_number", "unknown")

        # Build systematic run name using NamingContext
        run_name = None
        try:
            from infrastructure.naming import create_naming_context
            from infrastructure.naming.mlflow.run_names import build_mlflow_run_name
            from common.shared.platform_detection import detect_platform

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

            # Extract hyperparameters (excluding metadata fields)
            hyperparameters = {
                k: v for k, v in trial_params.items()
                if k not in ("backbone", "trial_number", "run_id")
            }

            # Use consolidated utility for study_key_hash computation
            from infrastructure.tracking.mlflow.hash_utils import (
                get_or_compute_study_key_hash,
                get_study_family_hash_from_run,
                get_or_compute_trial_key_hash,
            )
            
            computed_study_key_hash = get_or_compute_study_key_hash(
                study_key_hash=study_key_hash,
                hpo_parent_run_id=hpo_parent_run_id,
                data_config=data_config,
                hpo_config=hpo_config,
                train_config=train_config,
                backbone=backbone,
                config_dir=config_dir,
            )
            
            # Get study_family_hash (no consolidated utility yet, keep existing pattern)
            computed_study_family_hash = study_family_hash
            if not computed_study_family_hash and hpo_parent_run_id:
                computed_study_family_hash = get_study_family_hash_from_run(
                    hpo_parent_run_id, client, config_dir
                )
                    
            if not computed_study_family_hash:
                try:
                    from infrastructure.naming.mlflow.hpo_keys import (
                        build_hpo_study_family_key,
                        build_hpo_study_family_hash,
                    )
                    study_family_key = build_hpo_study_family_key(
                        data_config, hpo_config, benchmark_config
                    )
                    computed_study_family_hash = build_hpo_study_family_hash(study_family_key)
                except Exception as e:
                    logger.debug(f"Could not compute study_family_hash: {e}")

            # Create NamingContext for HPO trial WITH study_key_hash and trial_number
            # This must be done AFTER retrieving study_key_hash so run name includes it
            # Use explicit trial_number from Optuna (robust, no string parsing)
            trial_number_int = trial_params.get("trial_number")
            trial_context = create_naming_context(
                process_type="hpo",
                model=backbone_short,
                environment=detect_platform(),
                storage_env=detect_platform(),
                stage="hpo_trial",
                trial_id=trial_id,
                trial_number=trial_number_int,  # Explicit Optuna trial number
                study_key_hash=computed_study_key_hash,
                trial_key_hash=None,  # Will be computed below
            )

            # Build systematic run name (now with study_key_hash in context)
            run_name = build_mlflow_run_name(trial_context, config_dir)

            # Compute trial_key_hash using consolidated utility
            from infrastructure.tracking.mlflow.hash_utils import get_or_compute_trial_key_hash
            trial_key_hash = get_or_compute_trial_key_hash(
                trial_key_hash=None,  # Not available from trial run in this context
                trial_run_id=None,  # Not available in this context
                study_key_hash=computed_study_key_hash,
                hyperparameters=hyperparameters,
                config_dir=config_dir,
            )
            if trial_key_hash:
                # Update context with computed trial_key_hash
                trial_context = create_naming_context(
                    process_type="hpo",
                    model=backbone_short,
                    environment=detect_platform(),
                    storage_env=detect_platform(),
                    stage="hpo_trial",
                    trial_id=trial_id,
                    trial_number=trial_number_int,  # Keep explicit trial_number
                    study_key_hash=computed_study_key_hash,
                    trial_key_hash=trial_key_hash,
                )
            else:
                logger.warning(
                    f"Could not compute trial_key_hash from configs"
                )

            # Build tags including project identity tags and grouping tags
            from infrastructure.naming.mlflow.tags import build_mlflow_tags
            from infrastructure.naming.mlflow.run_keys import (
                build_mlflow_run_key,
                build_mlflow_run_key_hash,
            )
            trial_run_key = build_mlflow_run_key(
                trial_context) if trial_context else None
            trial_run_key_hash = build_mlflow_run_key_hash(
                trial_run_key) if trial_run_key else None
            trial_tags = build_mlflow_tags(
                context=trial_context,
                output_dir=output_dir,
                config_dir=config_dir,
                study_key_hash=computed_study_key_hash,
                study_family_hash=computed_study_family_hash,
                trial_key_hash=trial_key_hash,
                run_key_hash=trial_run_key_hash,
            )
            trial_tags.update({
                "mlflow.parentRunId": hpo_parent_run_id,
                "azureml.runType": "trial",
                "azureml.trial": "true",
                "trial_number": str(trial_number),
            })
        except Exception as e:
            logger.warning(
                f"Could not build systematic run name and tags: {e}, using fallback")
            run_name = f"trial_{trial_number}"
            try:
                from infrastructure.naming.mlflow.config import get_naming_config
                # config_dir is already available from function parameter, use it directly
                naming_config = get_naming_config(config_dir)
                project_name = naming_config.get("project_name", "resume-ner")
            except Exception:
                project_name = "resume-ner"
            trial_tags = {
                "mlflow.parentRunId": hpo_parent_run_id,
                "azureml.runType": "trial",
                "azureml.trial": "true",
                "trial_number": str(trial_number),
                "code.project": project_name,
            }

        # Ensure run_name is never None (MLflow will auto-generate random names if None)
        if not run_name:
            logger.warning(f"[TRIAL_RUN_CV] run_name is None, using fallback for trial {trial_number}")
            run_name = f"trial_{trial_number}"
        
        # Create trial run as child of HPO parent
        trial_run = client.create_run(
            experiment_id=experiment_id,
            tags=trial_tags,
            run_name=run_name
        )
        trial_run_id = trial_run.info.run_id

        return trial_run_id
    except Exception as e:
        logger.warning(f"Could not create trial run: {e}")
        return None

def _log_cv_metrics_to_trial_run(
    trial_run_id: str,
    trial_params: Dict[str, Any],
    objective_metric: str,
    average_metric: float,
    fold_metrics: List[float],
) -> None:
    """Log aggregated CV metrics to trial run."""
    try:
        from infrastructure.tracking.mlflow.client import create_mlflow_client
        client = create_mlflow_client()

        # Log aggregated metrics
        client.log_metric(trial_run_id, objective_metric, average_metric)
        client.log_metric(trial_run_id, "cv_std", float(np.std(fold_metrics)))
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
        trial_number = trial_params.get('trial_number', 'unknown')
        from infrastructure.tracking.mlflow import terminate_run_safe
        terminate_run_safe(trial_run_id, status="FINISHED", check_status=True)
    except Exception as e:
        logger.warning(f"Could not log metrics to trial run: {e}")


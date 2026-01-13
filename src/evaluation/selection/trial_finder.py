"""Find best trials from HPO studies or disk.

This module provides utilities to locate and extract best trial information
from Optuna studies or from saved outputs on disk.
"""

import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from common.shared.logging_utils import get_logger

from training.hpo.core.study import extract_best_config_from_study
from .disk_loader import load_best_trial_from_disk
from training.hpo.utils.paths import resolve_hpo_output_dir

logger = get_logger(__name__)


def find_best_trial_in_study_folder(
    study_folder: Path,
    objective_metric: str = "macro-f1",
) -> Optional[Dict[str, Any]]:
    """
    Find best trial in a specific study folder by reading metrics.json files.

    Supports v2 paths (trial-{hash}) only.

    Args:
        study_folder: Path to study folder containing trials
        objective_metric: Name of the objective metric to optimize

    Returns:
        Dictionary with best trial info, or None if no trials found
    """
    if not study_folder.exists():
        logger.warning(
            f"Study folder does not exist: {study_folder}")
        return None

    best_metric = None
    best_trial_dir = None
    best_trial_name = None

    # Collect all v2 trial directories (trial-{hash})
    trial_dirs = []
    for item in study_folder.iterdir():
        if item.is_dir() and item.name.startswith("trial-"):
            trial_dirs.append(item)

    if len(trial_dirs) == 0:
        logger.warning(
            f"No v2 trial directories found in {study_folder}. "
            f"Contents: {[item.name for item in study_folder.iterdir()]}"
        )

    # Find best trial by metrics
    trials_with_metrics = []
    for trial_dir in trial_dirs:
        # Try multiple locations for metrics.json
        # 1. Trial root: trial_dir/metrics.json
        # 2. CV folds: trial_dir/cv/fold0/metrics.json (for CV trials)
        metrics_file = None
        if (trial_dir / "metrics.json").exists():
            metrics_file = trial_dir / "metrics.json"
        elif (trial_dir / "cv").exists():
            # Check first fold for metrics (CV trials aggregate metrics at fold level)
            for fold_dir in (trial_dir / "cv").iterdir():
                if fold_dir.is_dir() and fold_dir.name.startswith("fold"):
                    fold_metrics = fold_dir / "metrics.json"
                    if fold_metrics.exists():
                        metrics_file = fold_metrics
                        break

        if not metrics_file or not metrics_file.exists():
            continue

        try:
            with open(metrics_file, "r") as f:
                metrics = json.load(f)

            if objective_metric in metrics:
                metric_value = metrics[objective_metric]

                # Skip fold-specific trials (we'll aggregate later if needed)
                if "_fold" in trial_dir.name:
                    continue

                trials_with_metrics.append((trial_dir, metric_value))

                if best_metric is None or metric_value > best_metric:
                    best_metric = metric_value
                    best_trial_dir = trial_dir
                    best_trial_name = trial_dir.name
        except Exception as e:
            logger.warning(
                f"Could not read {metrics_file}: {e}")
            continue

    if len(trials_with_metrics) == 0:
        logger.warning(
            f"No trials found with {objective_metric} metric. "
            f"Found {len(trial_dirs)} trial directories but none have valid metrics.json with {objective_metric}"
        )

    if best_trial_dir is None:
        logger.warning(
            f"No trials with {objective_metric} found in {study_folder}")
        return None

    # Load metrics - use same logic as above to find metrics.json
    # Try multiple locations for metrics.json
    # 1. Trial root: trial_dir/metrics.json
    # 2. CV folds: trial_dir/cv/fold0/metrics.json (for CV trials)
    metrics_file = None
    if (best_trial_dir / "metrics.json").exists():
        metrics_file = best_trial_dir / "metrics.json"
    elif (best_trial_dir / "cv").exists():
        # Check first fold for metrics (CV trials aggregate metrics at fold level)
        for fold_dir in (best_trial_dir / "cv").iterdir():
            if fold_dir.is_dir() and fold_dir.name.startswith("fold"):
                fold_metrics = fold_dir / "metrics.json"
                if fold_metrics.exists():
                    metrics_file = fold_metrics
                    break

    if not metrics_file or not metrics_file.exists():
        logger.warning(
            f"metrics.json not found in {best_trial_dir} (checked root and CV folds)")
        return None

    with open(metrics_file, "r") as f:
        metrics = json.load(f)

    # Try to read trial_meta.json for run_id and hashes
    trial_run_id = None
    study_key_hash = None
    trial_key_hash = None
    trial_meta_path = best_trial_dir / "trial_meta.json"
    if trial_meta_path.exists():
        try:
            import re
            with open(trial_meta_path, "r") as f:
                trial_meta = json.load(f)
            if "run_id" in trial_meta:
                run_id_from_meta = trial_meta["run_id"]
                uuid_pattern = re.compile(
                    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
                    re.IGNORECASE
                )
            # Extract hashes for benchmarking
            study_key_hash = trial_meta.get("study_key_hash")
            trial_key_hash = trial_meta.get("trial_key_hash")
            if uuid_pattern.match(run_id_from_meta):
                trial_run_id = run_id_from_meta
        except Exception:
            pass

    result = {
        "trial_name": best_trial_name,
        "trial_dir": str(best_trial_dir),
        "accuracy": best_metric,
        "metrics": metrics,
    }

    if trial_run_id:
        result["trial_run_id"] = trial_run_id
    
    # Include hashes for benchmarking
    if study_key_hash:
        result["study_key_hash"] = study_key_hash
    if trial_key_hash:
        result["trial_key_hash"] = trial_key_hash

    # Verify the trial_dir actually exists before returning
    if not best_trial_dir.exists():
        logger.error(
            f"Selected trial_dir does not exist: {best_trial_dir}. "
            f"Available trials: {[d.name for d in trial_dirs]}"
        )
        # Don't return None - return the result anyway so the caller can see what was attempted
        # The caller should handle the non-existent path

    return result


def format_trial_identifier(trial_dir: Path, trial_number: Optional[int] = None) -> str:
    """Format trial identifier using hash-based naming if available, else fallback to directory name.

    Args:
        trial_dir: Path to trial directory
        trial_number: Optional trial number to include in identifier

    Returns:
        Formatted identifier string (e.g., "study-350a79aa, trial-9d4153fb, t1" or "trial_1_20260106_173735")
    """
    trial_meta_path = trial_dir / "trial_meta.json"
    if trial_meta_path.exists():
        try:
            with open(trial_meta_path, "r") as f:
                meta = json.load(f)
            study_key_hash = meta.get("study_key_hash")
            trial_key_hash = meta.get("trial_key_hash")
            meta_trial_number = meta.get("trial_number")

            # Use trial_number from meta if available, else use provided trial_number
            display_trial_number = meta_trial_number if meta_trial_number is not None else trial_number

            if study_key_hash and trial_key_hash:
                if display_trial_number is not None:
                    return f"study-{study_key_hash[:8]}, trial-{trial_key_hash[:8]}, t{display_trial_number}"
                else:
                    return f"study-{study_key_hash[:8]}, trial-{trial_key_hash[:8]}"
            elif display_trial_number is not None:
                return f"t{display_trial_number}"
        except Exception:
            pass

    # Fallback to directory name or trial number
    if trial_number is not None:
        return f"t{trial_number}"
    return trial_dir.name


def find_study_folder_in_backbone_dir(backbone_dir: Path) -> Optional[Path]:
    """
    Find v2 study folder inside backbone directory.

    Supports v2 paths (study-{study8}/trial-{trial8}) only.

    Args:
        backbone_dir: Backbone directory containing study folders

    Returns:
        Path to study folder if found, else None
    """
    if not backbone_dir.exists():
        logger.warning(
            f"Backbone directory does not exist: {backbone_dir}")
        return None

    v2_folders = []

    for item in backbone_dir.iterdir():
        if not item.is_dir():
            continue

        # Check for v2 study folders (study-{hash})
        if item.name.startswith("study-") and len(item.name) > 7:
            # Check if it contains v2 trial folders (trial-{hash})
            has_trials = any(
                subitem.is_dir() and subitem.name.startswith("trial-")
                for subitem in item.iterdir()
            )
            if has_trials:
                v2_folders.append(item)

    if v2_folders:
        return v2_folders[0]

    logger.warning(
        f"No v2 study folders found in {backbone_dir}")
    return None


def find_best_trial_from_study(
    study: Any,
    backbone_name: str,
    dataset_version: str,
    objective_metric: str,
    hpo_backbone_dir: Path,
    hpo_config: Optional[Dict[str, Any]] = None,
    data_config: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Find best trial from an Optuna study object.

    Uses study.best_trial (source of truth) and locates the corresponding
    trial directory on disk by matching trial_key_hash.

    Args:
        study: Optuna study object
        backbone_name: Model backbone name
        dataset_version: Dataset version string
        objective_metric: Objective metric name
        hpo_backbone_dir: HPO backbone output directory
        hpo_config: HPO configuration (needed to compute trial_key_hash)
        data_config: Data configuration (needed to compute trial_key_hash)

    Returns:
        Dictionary with best trial info, or None if not found
    """
    if not study or study.best_trial is None:
        return None

    try:
        best_trial_config = extract_best_config_from_study(
            study, backbone_name, dataset_version, objective_metric
        )

        # Use resolve_storage_path to find the correct study folder (same logic as trial_meta_generator)
        from training.hpo.checkpoint.storage import resolve_storage_path

        checkpoint_config = hpo_config.get(
            "checkpoint", {}) if hpo_config else {}
        study_name_template = checkpoint_config.get("study_name") or (
            hpo_config.get("study_name") if hpo_config else None)
        study_name = None
        if study_name_template:
            study_name = study_name_template.replace(
                "{backbone}", backbone_name)

        # Find v2 study folder
        study_folder = find_study_folder_in_backbone_dir(hpo_backbone_dir)

        if not study_folder:
            logger.warning(f"V2 study folder not found in {hpo_backbone_dir}")
            return None

        best_trial = study.best_trial
        best_trial_number = best_trial.number

        # Compute trial_key_hash from Optuna trial hyperparameters
        computed_trial_key_hash = None
        if hpo_config and data_config:
            try:
                from infrastructure.tracking.mlflow.naming import (
                    build_hpo_study_key,
                    build_hpo_study_key_hash,
                    build_hpo_trial_key,
                    build_hpo_trial_key_hash,
                )

                # Compute study_key_hash
                study_key = build_hpo_study_key(
                    data_config=data_config,
                    hpo_config=hpo_config,
                    backbone=backbone_name,
                    benchmark_config=None,  # Not needed for trial lookup
                )
                study_key_hash = build_hpo_study_key_hash(study_key)

                # Extract hyperparameters (excluding metadata fields)
                hyperparameters = {
                    k: v
                    for k, v in best_trial.params.items()
                    if k not in ("backbone", "trial_number")
                }

                # Compute trial_key_hash
                trial_key = build_hpo_trial_key(
                    study_key_hash=study_key_hash,
                    hyperparameters=hyperparameters,
                )
                computed_trial_key_hash = build_hpo_trial_key_hash(trial_key)

            except Exception:
                pass

        best_trial_dir = None

        # Strategy 1: Match by trial_key_hash (most reliable)
        # Support v2 paths (trial-{hash}) only
        if computed_trial_key_hash:
            # Try v2 path lookup first if we have study_key_hash
            study_key_hash = None
            if hpo_config and data_config:
                try:
                    from infrastructure.tracking.mlflow.naming import (
                        build_hpo_study_key,
                        build_hpo_study_key_hash,
                    )
                    study_key = build_hpo_study_key(
                        data_config=data_config,
                        hpo_config=hpo_config,
                        backbone=backbone_name,
                        benchmark_config=None,
                    )
                    study_key_hash = build_hpo_study_key_hash(study_key)
                except Exception:
                    pass

            # Try v2 path lookup using find_trial_by_hash
            if study_key_hash:
                try:
                    from infrastructure.paths.parse import find_trial_by_hash
                    from common.shared.platform_detection import detect_platform
                    # Find project root and config_dir from hpo_backbone_dir
                    # hpo_backbone_dir is typically: outputs/hpo/{storage_env}/{model}
                    # So we need to go up to project root
                    # outputs/hpo/{storage_env}/{model} -> project_root
                    project_root = hpo_backbone_dir.parent.parent.parent
                    config_dir = project_root / "config"
                    storage_env = detect_platform()

                    v2_trial_dir = find_trial_by_hash(
                        root_dir=project_root,
                        config_dir=config_dir,
                        model=backbone_name,
                        storage_env=storage_env,
                        study_key_hash=study_key_hash,
                        trial_key_hash=computed_trial_key_hash,
                    )
                    if v2_trial_dir and v2_trial_dir.exists():
                        best_trial_dir = v2_trial_dir
                except Exception:
                    pass

            # Fallback: iterate through study_folder looking for v2 trials
            if best_trial_dir is None:
                for trial_dir in study_folder.iterdir():
                    # Support v2 (trial-{hash}) naming only
                    if not trial_dir.is_dir():
                        continue
                    if not (trial_dir.name.startswith("trial-") and len(trial_dir.name) > 7):
                        continue

                    trial_meta_path = trial_dir / "trial_meta.json"
                    if not trial_meta_path.exists():
                        continue

                    try:
                        with open(trial_meta_path, "r") as f:
                            meta = json.load(f)

                        # Match by trial_key_hash
                        if meta.get("trial_key_hash") == computed_trial_key_hash:
                            best_trial_dir = trial_dir
                            break
                    except Exception:
                        continue

        # Strategy 2: Fallback to trial number + verify checkpoint exists
        if best_trial_dir is None:
            for trial_dir in study_folder.iterdir():
                if not trial_dir.is_dir():
                    continue
                # Support v2 (trial-{hash}) naming only
                if not (trial_dir.name.startswith("trial-") and len(trial_dir.name) > 7):
                    continue

                # Check trial_meta.json for trial_number match (works for both v2 and legacy)
                trial_meta_path = trial_dir / "trial_meta.json"
                if trial_meta_path.exists():
                    try:
                        with open(trial_meta_path, "r") as f:
                            meta = json.load(f)
                        if meta.get("trial_number") == best_trial_number:
                            best_trial_dir = trial_dir
                            break
                    except Exception:
                        continue

        # Construct best_trial_from_disk from study.best_trial
        if best_trial_dir:
            # Extract hashes from trial_meta.json if available
            study_key_hash = None
            trial_key_hash = None
            trial_meta_path = best_trial_dir / "trial_meta.json"
            if trial_meta_path.exists():
                try:
                    with open(trial_meta_path, "r") as f:
                        meta = json.load(f)
                    study_key_hash = meta.get("study_key_hash")
                    trial_key_hash = meta.get("trial_key_hash")
                except Exception:
                    pass
            
            best_trial_from_disk = {
                "trial_name": best_trial_dir.name,
                "trial_dir": str(best_trial_dir),
                "checkpoint_dir": None,  # Will be determined later
                "checkpoint_type": "unknown",
                "accuracy": best_trial_config.get("selection_criteria", {}).get("best_value"),
                "metrics": best_trial_config.get("metrics", {}),
                "hyperparameters": best_trial_config.get("hyperparameters", {}),
                "study_key_hash": study_key_hash,  # Include hashes for benchmarking
                "trial_key_hash": trial_key_hash,
            }
        else:
            # Fallback: trial directory not found by hash or number
            # Use find_best_trial_in_study_folder to find best trial by metrics
            logger.warning(
                f"Trial directory for trial {best_trial_number} not found in {study_folder} "
                f"by hash or number. Falling back to find_best_trial_in_study_folder to find best trial by metrics."
            )
            study_folder_contents = [
                item.name for item in study_folder.iterdir() if item.is_dir()]

            # Use find_best_trial_in_study_folder as fallback
            best_trial_from_folder = find_best_trial_in_study_folder(
                study_folder,
                objective_metric,
            )

            if best_trial_from_folder:
                # Extract hashes from trial_meta.json if available
                study_key_hash = None
                trial_key_hash = None
                trial_dir_path = Path(best_trial_from_folder["trial_dir"])
                trial_meta_path = trial_dir_path / "trial_meta.json"
                if trial_meta_path.exists():
                    try:
                        with open(trial_meta_path, "r") as f:
                            meta = json.load(f)
                        study_key_hash = meta.get("study_key_hash")
                        trial_key_hash = meta.get("trial_key_hash")
                    except Exception:
                        pass
                
                best_trial_from_disk = {
                    "trial_name": best_trial_from_folder["trial_name"],
                    "trial_dir": best_trial_from_folder["trial_dir"],
                    "checkpoint_dir": None,
                    "checkpoint_type": "unknown",
                    "accuracy": best_trial_from_folder.get("accuracy"),
                    "metrics": best_trial_from_folder.get("metrics", {}),
                    # Use from study if available
                    "hyperparameters": best_trial_config.get("hyperparameters", {}),
                    "study_key_hash": study_key_hash,  # Include hashes for benchmarking
                    "trial_key_hash": trial_key_hash,
                }
            else:
                # Last resort: Try to find ANY v2 trial directory in the study folder
                any_trial_dir = None
                for item in study_folder.iterdir():
                    if item.is_dir() and item.name.startswith("trial-") and len(item.name) > 7:
                        any_trial_dir = item
                        break

                if any_trial_dir and any_trial_dir.exists():
                    logger.warning(
                        f"Using found v2 trial directory as fallback: {any_trial_dir.name} "
                        f"(NOTE: This may not be the best trial, but it exists)"
                    )
                    # Extract hashes from trial_meta.json if available
                    study_key_hash = None
                    trial_key_hash = None
                    trial_meta_path = any_trial_dir / "trial_meta.json"
                    if trial_meta_path.exists():
                        try:
                            with open(trial_meta_path, "r") as f:
                                meta = json.load(f)
                            study_key_hash = meta.get("study_key_hash")
                            trial_key_hash = meta.get("trial_key_hash")
                        except Exception:
                            pass
                    
                    best_trial_from_disk = {
                        "trial_name": any_trial_dir.name,
                        "trial_dir": str(any_trial_dir),
                        "checkpoint_dir": None,
                        "checkpoint_type": "unknown",
                        "accuracy": best_trial_config.get("selection_criteria", {}).get("best_value"),
                        "metrics": best_trial_config.get("metrics", {}),
                        "hyperparameters": best_trial_config.get("hyperparameters", {}),
                        "study_key_hash": study_key_hash,  # Include hashes for benchmarking
                        "trial_key_hash": trial_key_hash,
                    }
                else:
                    logger.error(
                        f"Could not find ANY v2 trial in {study_folder}. "
                        f"Study folder contents: {study_folder_contents}."
                    )
                    best_trial_from_disk = None

        return best_trial_from_disk

    except Exception as e:
        logger.warning(
            f"Could not extract best trial from study for {backbone_name}: {e}", exc_info=True
        )
        return None


def find_best_trials_for_backbones(
    backbone_values: list[str],
    hpo_studies: Optional[Dict[str, Any]],
    hpo_config: Dict[str, Any],
    data_config: Dict[str, Any],
    root_dir: Path,
    environment: str,
) -> Dict[str, Dict[str, Any]]:
    """
    Find best trials for multiple backbones.
    """
    best_trials = {}
    objective_metric = hpo_config["objective"]["metric"]
    dataset_version = data_config.get("version", "unknown")

    hpo_output_dir_new = root_dir / "outputs" / "hpo" / environment

    for backbone in backbone_values:
        backbone_name = backbone.split("-")[0] if "-" in backbone else backbone
        logger.info(
            f"Looking for best trial for {backbone} ({backbone_name})...")

        best_trial_info = None
        study = None

        if hpo_studies and backbone_name in hpo_studies:
            study = hpo_studies[backbone_name]

        # ---------- try loading study from disk ----------
        if not study:
            local_path = hpo_output_dir_new / backbone_name
            hpo_backbone_dir = resolve_hpo_output_dir(local_path)

            if hpo_backbone_dir.exists():
                from training.hpo.checkpoint.storage import resolve_storage_path

                checkpoint_config = hpo_config.get("checkpoint", {})
                study_name_template = (
                    checkpoint_config.get("study_name")
                    or hpo_config.get("study_name")
                )

                study_name = (
                    study_name_template.replace("{backbone}", backbone_name)
                    if study_name_template
                    else None
                )

                # Find v2 study folder
                study_folder = find_study_folder_in_backbone_dir(
                    hpo_backbone_dir)

                if study_folder:
                    study_db_path = study_folder / "study.db"
                    if study_db_path.exists():
                        try:
                            from training.hpo.core.optuna_integration import import_optuna
                            optuna, _, _, _ = import_optuna()
                        except ImportError:
                            import optuna

                        try:
                            study = optuna.load_study(
                                study_name=study_folder.name,
                                storage=f"sqlite:///{study_db_path.resolve()}",
                            )
                            logger.debug(
                                f"Loaded study for {backbone_name} from disk"
                            )
                        except Exception as e:
                            logger.debug(
                                f"Could not load study from disk for {backbone_name}: {e}"
                            )

        # ---------- use study ----------
        if study:
            local_path = hpo_output_dir_new / backbone_name
            hpo_backbone_dir = resolve_hpo_output_dir(local_path)

            if hpo_backbone_dir.exists():
                best_trial_from_disk = find_best_trial_from_study(
                    study,
                    backbone_name,
                    dataset_version,
                    objective_metric,
                    hpo_backbone_dir,
                    hpo_config=hpo_config,
                    data_config=data_config,
                )

                if best_trial_from_disk:
                    trial_dir_path = Path(best_trial_from_disk["trial_dir"])
                    study_name = trial_dir_path.parent.name if trial_dir_path.parent else None
                    trial_number = study.best_trial.number if study.best_trial else None

                    best_trial_info = {
                        "backbone": backbone_name,
                        "trial_name": best_trial_from_disk["trial_name"],
                        "trial_dir": best_trial_from_disk["trial_dir"],
                        "study_name": study_name,
                        "checkpoint_dir": best_trial_from_disk.get(
                            "checkpoint_dir",
                            str(trial_dir_path / "checkpoint"),
                        ),
                        "checkpoint_type": best_trial_from_disk.get(
                            "checkpoint_type", "unknown"
                        ),
                        "accuracy": best_trial_from_disk["accuracy"],
                        "metrics": best_trial_from_disk["metrics"],
                        "hyperparameters": best_trial_from_disk["hyperparameters"],
                        # Include hashes from trial_meta.json for benchmarking
                        "study_key_hash": best_trial_from_disk.get("study_key_hash"),
                        "trial_key_hash": best_trial_from_disk.get("trial_key_hash"),
                    }

                    identifier = format_trial_identifier(
                        trial_dir_path, trial_number)
                    logger.info(
                        f"{backbone}: Best trial is {identifier} "
                        f"({objective_metric}={best_trial_info['accuracy']:.4f})"
                    )

        # ---------- fallback disk search ----------
        if best_trial_info is None:
            local_path = hpo_output_dir_new / backbone_name
            hpo_backbone_dir = resolve_hpo_output_dir(local_path)

            if hpo_backbone_dir.exists():
                from training.hpo.checkpoint.storage import resolve_storage_path

                checkpoint_config = hpo_config.get("checkpoint", {})
                study_name_template = (
                    checkpoint_config.get("study_name")
                    or hpo_config.get("study_name")
                )

                study_name = (
                    study_name_template.replace("{backbone}", backbone_name)
                    if study_name_template
                    else None
                )

                # Find v2 study folder
                study_folder = find_study_folder_in_backbone_dir(
                    hpo_backbone_dir)

                if study_folder:
                    best_trial_info = find_best_trial_in_study_folder(
                        study_folder, objective_metric
                    )
                    if best_trial_info:
                        best_trial_info["study_name"] = study_folder.name
                        best_trial_info["backbone"] = backbone_name

            else:
                hpo_output_dir_old = root_dir / "outputs" / "hpo"
                old_backbone_dir = resolve_hpo_output_dir(
                    hpo_output_dir_old / backbone
                )

                if old_backbone_dir.exists():
                    study_folder = find_study_folder_in_backbone_dir(
                        old_backbone_dir)
                    if study_folder:
                        best_trial_info = find_best_trial_in_study_folder(
                            study_folder, objective_metric
                        )
                        if best_trial_info:
                            best_trial_info["study_name"] = study_folder.name
                            best_trial_info["backbone"] = backbone_name
                elif str(old_backbone_dir).startswith("/content/drive"):
                    best_trial_info = load_best_trial_from_disk(
                        old_backbone_dir.parent,
                        backbone,
                        objective_metric,
                    )
                else:
                    best_trial_info = load_best_trial_from_disk(
                        hpo_output_dir_old,
                        backbone,
                        objective_metric,
                    )

        if best_trial_info:
            best_trials[backbone] = best_trial_info
        else:
            logger.warning(f"No best trial found for {backbone}")

    logger.info(
        f"Summary: Found {len(best_trials)} / {len(backbone_values)} best trials"
    )
    return best_trials


def select_champion_per_backbone(
    backbone: str,
    hpo_experiment: Dict[str, str],
    selection_config: Dict[str, Any],
    mlflow_client: Any,
    root_dir: Optional[Path] = None,
    config_dir: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """
    Select champion (best configuration group winner) per backbone.
    
    Groups runs by study_key_hash v2 (comparable configuration groups),
    then selects best group and best trial within that group.
    
    All parameters come from selection_config (centralized config).
    
    Requirements enforced:
    1. Bound fingerprints in study_key_hash v2
    2. Never mix v1 and v2 runs in same selection (config-driven)
    3. Explicit objective direction (never assume max, with migration support)
    4. Handle missing/NaN metrics deterministically
    5. Minimum trial count guardrail (config-driven)
    6. Artifact availability constraint (config-driven source)
    7. Deterministic constraints (top_k <= min_trials)
    
    Args:
        backbone: Model backbone name
        hpo_experiment: Dict with 'name' and 'id' of HPO experiment
        selection_config: Selection configuration dictionary
        mlflow_client: MLflow client instance
    
    Returns:
        {
            "backbone": "distilbert",
            "champion": {
                "run_id": "...",  # PRIMARY: MLflow handle
                "trial_key_hash": "...",  # Optional: for display
                "metric": 0.87,
                "stable_score": 0.86,
                "study_key_hash": "abc123...",
                "schema_version": "2.0",
                "checkpoint_path": Path(...),
            },
            "all_groups": {...},
            "selection_metadata": {...},
        }
        or None if no valid champions found
    """
    from infrastructure.tracking.mlflow.queries import query_runs_by_tags
    from infrastructure.naming.mlflow.tags_registry import TagsRegistry
    from infrastructure.config.selection import (
        get_objective_direction,
        get_champion_selection_config,
    )
    
    # Extract config values with defaults and constraint validation
    champion_config = get_champion_selection_config(selection_config)
    min_trials_per_group = champion_config["min_trials_per_group"]
    top_k_for_stable_score = champion_config["top_k_for_stable_score"]
    require_artifact_available = champion_config["require_artifact_available"]
    artifact_check_source = champion_config["artifact_check_source"]
    allow_mixed_schema_groups = champion_config["allow_mixed_schema_groups"]
    prefer_schema_version = champion_config["prefer_schema_version"]
    
    # Get objective direction (with migration support)
    objective_metric = selection_config.get("objective", {}).get("metric", "macro-f1")
    objective_direction = get_objective_direction(selection_config)  # Uses migration helper
    maximize = objective_direction.lower() == "maximize"
    
    from infrastructure.naming.mlflow.tags_registry import load_tags_registry
    from pathlib import Path
    # Infer config_dir - try current directory first, then parent
    config_dir = Path.cwd() / "config"
    if not config_dir.exists():
        config_dir = Path.cwd().parent / "config"
    tags_registry = load_tags_registry(config_dir)
    backbone_tag = tags_registry.key("process", "backbone")
    stage_tag = tags_registry.key("process", "stage")
    study_key_tag = tags_registry.key("grouping", "study_key_hash")
    trial_key_tag = tags_registry.key("grouping", "trial_key_hash")
    schema_version_tag = tags_registry.key("study", "key_schema_version")
    artifact_tag = tags_registry.key("artifact", "available")
    
    backbone_name = backbone.split("-")[0] if "-" in backbone else backbone
    
    # Step 1: Filter runs
    # NOTE: Since experiments are already per-backbone (e.g., resume_ner_baseline-hpo-distilbert),
    # we don't strictly need the backbone tag filter. However, we'll try with it first,
    # and fallback to stage-only if backbone tag is missing (legacy runs).
    
    # Try "hpo_trial" first (new format), fallback to "hpo" (legacy format)
    # Try with backbone tag first
    required_tags_with_backbone = {
        backbone_tag: backbone_name,
        stage_tag: "hpo_trial",
    }
    
    logger.debug(
        f"Querying runs for {backbone} with tags: {backbone_tag}={backbone_name}, "
        f"{stage_tag}=hpo_trial"
    )
    
    runs = query_runs_by_tags(
        client=mlflow_client,
        experiment_ids=[hpo_experiment["id"]],
        required_tags=required_tags_with_backbone,
        max_results=1000,
    )
    
    # If no runs found, try without backbone tag (legacy runs may not have it)
    if not runs:
        logger.debug(
            f"No runs found with backbone tag, trying without backbone filter "
            f"(experiment is already backbone-specific)"
        )
        required_tags_stage_only = {stage_tag: "hpo_trial"}
        runs = query_runs_by_tags(
            client=mlflow_client,
            experiment_ids=[hpo_experiment["id"]],
            required_tags=required_tags_stage_only,
            max_results=1000,
        )
    
    # If still no runs, try legacy "hpo" stage tag (with backbone)
    if not runs:
        logger.info(
            f"No runs found with stage='hpo_trial' for {backbone}, "
            f"trying legacy stage='hpo'"
        )
        required_tags_with_backbone = {
            backbone_tag: backbone_name,
            stage_tag: "hpo",
        }
        runs = query_runs_by_tags(
            client=mlflow_client,
            experiment_ids=[hpo_experiment["id"]],
            required_tags=required_tags_with_backbone,
            max_results=1000,
        )
    
    # If still no runs, try legacy "hpo" stage tag (without backbone)
    if not runs:
        logger.debug(
            f"No runs found with backbone tag and stage='hpo', "
            f"trying stage-only filter"
        )
        required_tags_stage_only = {stage_tag: "hpo"}
        runs = query_runs_by_tags(
            client=mlflow_client,
            experiment_ids=[hpo_experiment["id"]],
            required_tags=required_tags_stage_only,
            max_results=1000,
        )
    
    logger.info(
        f"Found {len(runs)} runs with stage tag for {backbone} "
        f"(backbone={backbone_name})"
    )
    
    # Step 1.5: Filter out parent runs (they don't have trial metrics)
    # Parent runs have mlflow.parentRunId tag missing (they are the parent)
    # Child runs have mlflow.parentRunId tag set
    runs_before_parent_filter = len(runs)
    runs = [r for r in runs if r.data.tags.get("mlflow.parentRunId") is not None]
    parent_runs_filtered = runs_before_parent_filter - len(runs)
    if parent_runs_filtered > 0:
        logger.info(
            f"Filtered out {parent_runs_filtered} parent run(s) (only child/trial runs have metrics). "
            f"{len(runs)} child runs remaining."
        )
    
    # Step 2: Artifact availability filter (config-driven source)
    runs_before_artifact_filter = len(runs)
    if require_artifact_available:
        runs = _filter_by_artifact_availability(
            runs, artifact_check_source, artifact_tag, logger, mlflow_client, schema_version_tag
        )
        runs_after_artifact_filter = len(runs)
        if runs_after_artifact_filter < runs_before_artifact_filter:
            logger.warning(
                f"Artifact filter removed {runs_before_artifact_filter - runs_after_artifact_filter} "
                f"runs for {backbone} ({runs_after_artifact_filter} remaining). "
                f"Check that runs have '{artifact_tag}' tag set to 'true'."
            )
    
    # Step 3: Partition by study_key_hash AND schema version
    # CRITICAL: Never mix v1 and v2 runs if allow_mixed_schema_groups is False
    groups_v1 = {}  # v1 runs
    groups_v2 = {}  # v2 runs
    runs_without_study_key = 0
    
    for run in runs:
        study_key_hash = run.data.tags.get(study_key_tag)
        if not study_key_hash:
            runs_without_study_key += 1
            continue  # Skip runs without grouping tag
        
        # Check schema version (default to "1.0" if missing for backward compat)
        schema_version = run.data.tags.get(schema_version_tag, "1.0")
        
        # Partition by version (NEVER MIX if allow_mixed_schema_groups is False)
        if schema_version == "2.0":
            if study_key_hash not in groups_v2:
                groups_v2[study_key_hash] = []
            groups_v2[study_key_hash].append(run)
        else:
            # v1 or missing version
            if study_key_hash not in groups_v1:
                groups_v1[study_key_hash] = []
            groups_v1[study_key_hash].append(run)
    
    if runs_without_study_key > 0:
        logger.warning(
            f"Skipped {runs_without_study_key} runs without {study_key_tag} tag for {backbone}"
        )
    
    logger.info(
        f"Grouped runs for {backbone}: {len(groups_v1)} v1 group(s), "
        f"{len(groups_v2)} v2 group(s)"
    )
    
    # Step 4: Select groups based on prefer_schema_version and allow_mixed_schema_groups
    if allow_mixed_schema_groups:
        # WARNING: This is dangerous - only allow if explicitly enabled
        logger.warning(
            f"allow_mixed_schema_groups=True is enabled for {backbone}. "
            f"This may compare non-comparable runs. Use with caution."
        )
        # Merge groups (dangerous but allowed)
        groups_to_use = {**groups_v1, **groups_v2}
        schema_version_used = "mixed"
    else:
        # Safe: Prefer v2, fallback to v1 (never mix)
        if prefer_schema_version == "2.0" or (prefer_schema_version == "auto" and groups_v2):
            groups_to_use = groups_v2
            schema_version_used = "2.0"
        elif prefer_schema_version == "1.0" or (prefer_schema_version == "auto" and not groups_v2):
            groups_to_use = groups_v1
            schema_version_used = "1.0"
        else:
            groups_to_use = groups_v2 if groups_v2 else groups_v1
            schema_version_used = "2.0" if groups_v2 else "1.0"
    
    if not groups_to_use:
        logger.warning(
            f"No valid groups found for {backbone}. "
            f"Found {len(groups_v1)} v1 group(s) and {len(groups_v2)} v2 group(s), "
            f"but none matched selection criteria (schema_version preference: {prefer_schema_version})"
        )
        return None
    
    # Log version usage
    if groups_v1 and groups_v2 and not allow_mixed_schema_groups:
        logger.info(
            f"Found both v1 and v2 runs for {backbone}. "
            f"Using {schema_version_used} groups only (never mixing versions)."
        )
    
    # Step 5: Compute stable score per group (with all guards)
    group_scores = {}
    groups_skipped_min_trials = 0
    total_groups = len(groups_to_use)
    
    for study_key_hash, group_runs in groups_to_use.items():
        # Extract metrics (handle missing/NaN deterministically)
        run_metrics = []
        valid_count = 0
        invalid_count = 0
        missing_metric_runs = []
        invalid_metric_runs = []
        
        for run in group_runs:
            if objective_metric not in run.data.metrics:
                invalid_count += 1
                missing_metric_runs.append(run.info.run_id[:12])
                # Log available metrics for debugging
                available_metrics = list(run.data.metrics.keys())[:5]  # First 5 metrics
                logger.debug(
                    f"Run {run.info.run_id[:12]}... missing {objective_metric}. "
                    f"Available metrics: {available_metrics}"
                )
                continue
            
            metric_value = run.data.metrics[objective_metric]
            
            # Handle NaN/Inf deterministically
            if not isinstance(metric_value, (int, float)) or not math.isfinite(metric_value):
                invalid_count += 1
                invalid_metric_runs.append(run.info.run_id[:12])
                logger.debug(
                    f"Run {run.info.run_id[:12]}... has invalid {objective_metric}={metric_value}"
                )
                continue
            
            valid_count += 1
            run_metrics.append((run.info.run_id, metric_value))
        
        # Log metric validity with details
        if invalid_count > 0:
            logger.warning(
                f"Group {study_key_hash[:16]}...: "
                f"{valid_count} valid metrics, {invalid_count} missing/invalid. "
                f"Missing metric runs: {missing_metric_runs[:3]}{'...' if len(missing_metric_runs) > 3 else ''}"
            )
        
        # Winner's curse guardrail: require minimum trials
        if len(run_metrics) < min_trials_per_group:
            groups_skipped_min_trials += 1
            logger.warning(
                f"Skipping group {study_key_hash[:16]}... - "
                f"only {len(run_metrics)} valid trials (minimum: {min_trials_per_group})"
            )
            continue
        
        # Extract metrics for scoring
        metrics = [m for _, m in run_metrics]
        
        # Best metric (for champion selection within group)
        best_metric = max(metrics) if maximize else min(metrics)
        
        # Stable score: median of top-K (reduces flukes)
        # CONSTRAINT: top_k is already clamped to <= min_trials_per_group in config helper
        top_k = min(top_k_for_stable_score, len(metrics))
        sorted_metrics = sorted(metrics, reverse=maximize)
        stable_score = float(np.median(sorted_metrics[:top_k])) if top_k > 0 else 0.0
        
        group_scores[study_key_hash] = {
            "stable_score": stable_score,
            "best_metric": best_metric,
            "n_trials": len(run_metrics),
            "n_valid": valid_count,
            "n_invalid": invalid_count,
            "run_metrics": run_metrics,  # Lightweight: (run_id, metric) tuples
        }
    
    if not group_scores:
        logger.warning(
            f"No eligible groups for {backbone}. "
            f"Processed {total_groups} group(s), but {groups_skipped_min_trials} were skipped "
            f"due to insufficient trials (minimum: {min_trials_per_group}). "
            f"Remaining groups: {total_groups - groups_skipped_min_trials}"
        )
        return None
    
    logger.info(
        f"Found {len(group_scores)} eligible group(s) for {backbone} "
        f"({groups_skipped_min_trials} skipped due to min_trials requirement)"
    )
    
    # Step 6: Select winning group (by stable_score, respecting direction)
    if maximize:
        winning_key = max(group_scores.items(), key=lambda x: x[1]["stable_score"])[0]
    else:
        winning_key = min(group_scores.items(), key=lambda x: x[1]["stable_score"])[0]
    
    winning_group = group_scores[winning_key]
    
    # Step 7: Select champion within winning group (by best_metric, respecting direction)
    if maximize:
        champion_run_id, champion_metric = max(
            winning_group["run_metrics"],
            key=lambda x: x[1]
        )
    else:
        champion_run_id, champion_metric = min(
            winning_group["run_metrics"],
            key=lambda x: x[1]
        )
    
    # Fetch full run only when needed
    champion_run = mlflow_client.get_run(champion_run_id)
    champion_trial_key = champion_run.data.tags.get(trial_key_tag)
    
    # CRITICAL: Find refit run for this champion trial (checkpoints are usually in refit runs)
    # According to plan: "champion run_id" ≠ "checkpoint run_id" in a refit workflow
    refit_run_id = None
    try:
        refit_of_trial_tag = tags_registry.key("refit", "of_trial_run_id")
        stage_tag = tags_registry.key("process", "stage")
        
        # Strategy 1: Search for refit run using linking tag (most reliable)
        refit_runs = mlflow_client.search_runs(
            experiment_ids=[hpo_experiment["id"]],
            filter_string=f"tags.{refit_of_trial_tag} = '{champion_run_id}'",
            max_results=10,
        )
        
        # Strategy 2: Fallback - search by trial_key_hash if linking tag doesn't exist
        # (for existing refit runs created before linking tag was implemented)
        if not refit_runs and champion_trial_key:
            logger.debug(
                f"No refit run found with linking tag for trial {champion_run_id[:12]}... "
                f"- trying fallback search by trial_key_hash={champion_trial_key[:8]}..."
            )
            trial_key_tag = tags_registry.key("grouping", "trial_key_hash")
            refit_runs = mlflow_client.search_runs(
                experiment_ids=[hpo_experiment["id"]],
                filter_string=f"tags.{stage_tag} = 'hpo_refit' AND tags.{trial_key_tag} = '{champion_trial_key}'",
                max_results=10,
            )
        
        if refit_runs:
            # If multiple refit runs exist (reruns), pick the latest by start_time
            refit_runs_sorted = sorted(
                refit_runs,
                key=lambda r: r.info.start_time if r.info.start_time else 0,
                reverse=True
            )
            refit_run_id = refit_runs_sorted[0].info.run_id
            logger.info(
                f"Found refit run {refit_run_id[:12]}... for champion trial {champion_run_id[:12]}... "
                f"(selected latest from {len(refit_runs)} refit run(s))"
            )
        else:
            raise ValueError(
                f"No refit run found for champion trial {champion_run_id[:12]}... "
                f"(trial_key_hash={champion_trial_key[:8] if champion_trial_key else 'missing'}...). "
                f"Refit is required to acquire checkpoint deterministically."
            )
    except Exception as e:
        logger.error(
            f"Could not find refit run for champion trial {champion_run_id[:12]}...: {e}. "
            f"Failing fast to avoid using trial runs for checkpoint acquisition."
        )
        raise
    
    # Get checkpoint path (uses single source of truth for local disk lookup)
    # Refit is mandatory for checkpoint acquisition
    checkpoint_run = mlflow_client.get_run(refit_run_id)
    checkpoint_path = _get_checkpoint_path_from_run(
        checkpoint_run,
        study_key_hash=winning_key,
        trial_key_hash=champion_trial_key,
        root_dir=root_dir,
        config_dir=config_dir,
    )
    
    return {
        "backbone": backbone,
        "champion": {
            "trial_run_id": champion_run_id,  # Trial run ID (selected by CV metric)
            "refit_run_id": refit_run_id,  # Refit run ID (used for checkpoint + benchmark)
            "run_id": refit_run_id or champion_run_id,  # PRIMARY: refit if available, else trial (for backward compat)
            "trial_key_hash": champion_trial_key,  # Optional: for display
            "metric": champion_metric,  # CV metric from trial run
            "stable_score": winning_group["stable_score"],
            "study_key_hash": winning_key,
            "schema_version": schema_version_used,  # Track which version was used
            "checkpoint_path": checkpoint_path,
        },
        "all_groups": {
            k: {
                "best_metric": v["best_metric"],
                "stable_score": v["stable_score"],
                "n_trials": v["n_trials"],
                "n_valid": v["n_valid"],
                "n_invalid": v["n_invalid"],
            }
            for k, v in group_scores.items()
        },
        "selection_metadata": {
            "objective_direction": objective_direction,
            "min_trials_required": min_trials_per_group,
            "top_k_for_stable": top_k_for_stable_score,
            "artifact_required": require_artifact_available,
            "artifact_check_source": artifact_check_source,
            "allow_mixed_schema_groups": allow_mixed_schema_groups,
            "schema_version_used": schema_version_used,
        },
    }


def _filter_by_artifact_availability(
    runs: List[Any],
    check_source: str,
    artifact_tag: str,
    logger,
    mlflow_client: Any = None,
    schema_version_tag: str = "code.study.key_schema_version",
) -> List[Any]:
    """
    Filter runs by artifact availability using config-specified source.
    
    For child runs (trial runs), also checks parent run for artifact tag
    since artifact.available is typically set on parent runs.
    
    Args:
        runs: List of MLflow runs
        check_source: "tag" (uses MLflow tag) or "disk" (checks filesystem)
        artifact_tag: Tag key for artifact availability
        logger: Logger instance
        mlflow_client: Optional MLflow client for checking parent runs
    """
    if check_source == "tag":
        # Use MLflow tag as authoritative source
        # For legacy runs without the tag, be lenient: if tag is missing (not "false"),
        # allow the run through with a warning (assumes artifacts might exist)
        filtered_runs = []
        runs_without_tag = 0
        runs_explicitly_false = 0
        runs_missing_tag = 0
        
        for run in runs:
            # Check if this is a legacy run (no Phase 2 tags)
            # Legacy runs don't have schema_version tag, so we should be lenient with artifact filter
            is_legacy_run = run.data.tags.get(schema_version_tag) is None
            
            # Check run's own tag first
            run_tag_value = run.data.tags.get(artifact_tag)
            artifact_available = False
            tag_source = "run"
            
            if run_tag_value is not None:
                # Tag exists
                artifact_available = run_tag_value.lower() == "true"
                if not artifact_available:
                    # Tag is explicitly "false"
                    if is_legacy_run:
                        # Legacy run with false tag - be lenient (tag might not have been updated)
                        runs_missing_tag += 1
                        artifact_available = True
                        tag_source = "false (legacy, allowing)"
                        logger.debug(
                            f"Run {run.info.run_id[:12]}...: artifact.available=false on legacy run "
                            f"(allowing through - tag may not have been updated)"
                        )
                    else:
                        runs_explicitly_false += 1
            else:
                # Tag is missing - check parent run for legacy runs
                if mlflow_client:
                    parent_run_id = run.data.tags.get("mlflow.parentRunId")
                    if parent_run_id:
                        try:
                            parent_run = mlflow_client.get_run(parent_run_id)
                            parent_tag_value = parent_run.data.tags.get(artifact_tag)
                            if parent_tag_value is not None:
                                # Parent has tag - use it
                                artifact_available = parent_tag_value.lower() == "true"
                                tag_source = "parent"
                                if artifact_available:
                                    logger.debug(
                                        f"Run {run.info.run_id[:12]}...: artifact.available found on parent run"
                                    )
                                else:
                                    # Parent has false tag
                                    if is_legacy_run:
                                        # Legacy run - be lenient
                                        runs_missing_tag += 1
                                        artifact_available = True
                                        tag_source = "parent false (legacy, allowing)"
                                        logger.debug(
                                            f"Run {run.info.run_id[:12]}...: artifact.available=false on parent "
                                            f"of legacy run (allowing through)"
                                        )
                                    else:
                                        runs_explicitly_false += 1
                            else:
                                # Both run and parent missing tag - legacy run, be lenient
                                runs_missing_tag += 1
                                artifact_available = True  # Allow through for legacy runs
                                tag_source = "missing (legacy, allowing)"
                                logger.debug(
                                    f"Run {run.info.run_id[:12]}...: artifact tag missing on run and parent "
                                    f"(legacy run, allowing through)"
                                )
                        except Exception as e:
                            logger.debug(
                                f"Could not check parent run {parent_run_id[:12]}... for artifact tag: {e}"
                            )
                            # If we can't check parent, be lenient for legacy runs
                            runs_missing_tag += 1
                            artifact_available = True
                            tag_source = "missing (legacy, allowing)"
                    else:
                        # No parent run ID - be lenient
                        runs_missing_tag += 1
                        artifact_available = True
                        tag_source = "missing (legacy, allowing)"
                else:
                    # No MLflow client - be lenient
                    runs_missing_tag += 1
                    artifact_available = True
                    tag_source = "missing (legacy, allowing)"
            
            if not artifact_available:
                runs_without_tag += 1
            
            if artifact_available:
                filtered_runs.append(run)
        
        # Log detailed statistics
        if runs_explicitly_false > 0:
            logger.warning(
                f"Artifact filter: {runs_explicitly_false} run(s) have {artifact_tag}='false' "
                f"(explicitly marked as unavailable)"
            )
        if runs_missing_tag > 0:
            logger.info(
                f"Artifact filter: {runs_missing_tag} legacy run(s) missing {artifact_tag} tag "
                f"(allowing through - artifacts may exist on disk)"
            )
        if runs_without_tag > 0 and runs_explicitly_false > 0:
            logger.warning(
                f"Artifact filter: {runs_without_tag} run(s) excluded "
                f"({runs_explicitly_false} explicitly false, {runs_missing_tag} missing/legacy allowed)"
            )
        
        return filtered_runs
    elif check_source == "disk":
        # Fallback: check filesystem (requires run_id -> path mapping)
        # This is a fallback - tag should be primary
        logger.warning(
            "Using disk-based artifact check (fallback). "
            "Consider using 'tag' source for better performance."
        )
        # Implementation would check checkpoint files exist
        # For now, return all runs (disk check would need run_id -> path logic)
        return runs
    else:
        logger.error(f"Unknown artifact_check_source: {check_source}. Using tag-based check.")
        return [
            r for r in runs
            if r.data.tags.get(artifact_tag, "false").lower() == "true"
        ]


def _get_checkpoint_path_from_run(
    run: Any,
    study_key_hash: Optional[str] = None,
    trial_key_hash: Optional[str] = None,
    root_dir: Optional[Path] = None,
    config_dir: Optional[Path] = None,
) -> Optional[Path]:
    """
    Extract checkpoint path from MLflow run.
    
    Uses single source of truth: find_trial_checkpoint_by_hash() for local disk lookup.
    
    Args:
        run: MLflow run object
        study_key_hash: Study key hash for local disk lookup
        trial_key_hash: Trial key hash for local disk lookup
        root_dir: Project root directory (for local disk lookup)
        config_dir: Config directory (for local disk lookup)
    
    Returns:
        Path to checkpoint if available locally, else None
    """
    # Strategy 1: Try local disk lookup using single source of truth
    if study_key_hash and trial_key_hash and root_dir and config_dir:
        try:
            from evaluation.selection.local_selection_v2 import find_trial_checkpoint_by_hash
            from common.shared.platform_detection import detect_platform
            from infrastructure.paths import build_output_path
            from infrastructure.naming.mlflow.tags_registry import load_tags_registry
            
            # Get backbone from run
            tags_registry = load_tags_registry(config_dir)
            backbone_tag = tags_registry.key("process", "backbone")
            backbone = run.data.tags.get(backbone_tag) or run.data.tags.get("code.model", "unknown")
            backbone_name = backbone.split("-")[0] if "-" in backbone else backbone
            
            # Build HPO output directory path
            environment = detect_platform()
            hpo_output_dir = build_output_path(
                root_dir=root_dir,
                config_dir=config_dir,
                process_type="hpo",
                model=backbone_name,
                environment=environment,
            )
            
            # Use single source of truth for local disk lookup
            checkpoint_path = find_trial_checkpoint_by_hash(
                hpo_backbone_dir=hpo_output_dir,
                study_key_hash=study_key_hash,
                trial_key_hash=trial_key_hash,
            )
            
            if checkpoint_path and checkpoint_path.exists():
                return checkpoint_path
        except Exception:
            # Silently continue to next strategy
            pass
    
    # Strategy 2: Check checkpoint_path tag (if set)
    checkpoint_tag = run.data.tags.get("code.checkpoint_path")
    if checkpoint_tag:
        checkpoint_path = Path(checkpoint_tag)
        if checkpoint_path.exists():
            return checkpoint_path
    
    # Strategy 3: Return None (notebook will use acquire_best_model_checkpoint for MLflow)
    return None


def select_champions_for_backbones(
    backbone_values: List[str],
    hpo_experiments: Dict[str, Dict[str, str]],  # backbone -> {name, id}
    selection_config: Dict[str, Any],
    mlflow_client: Any,
    root_dir: Optional[Path] = None,
    config_dir: Optional[Path] = None,
    **kwargs,  # Pass through to select_champion_per_backbone
) -> Dict[str, Dict[str, Any]]:
    """
    Select champions for multiple backbones.
    
    Wrapper around select_champion_per_backbone() for multiple backbones.
    
    Args:
        backbone_values: List of backbone names
        hpo_experiments: Dict mapping backbone -> experiment info (name, id)
        selection_config: Selection configuration dictionary
        mlflow_client: MLflow client instance
        **kwargs: Additional arguments to pass to select_champion_per_backbone
    
    Returns:
        Dict mapping backbone -> champion selection result
    """
    champions = {}
    for backbone in backbone_values:
        if backbone not in hpo_experiments:
            logger.warning(f"No HPO experiment found for {backbone}, skipping")
            continue
        
        champion = select_champion_per_backbone(
            backbone=backbone,
            hpo_experiment=hpo_experiments[backbone],
            selection_config=selection_config,
            mlflow_client=mlflow_client,
            root_dir=root_dir,
            config_dir=config_dir,
            **kwargs,
        )
        if champion:
            champions[backbone] = champion
    
    return champions

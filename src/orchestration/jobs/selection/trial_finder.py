"""Find best trials from HPO studies or disk.

This module provides utilities to locate and extract best trial information
from Optuna studies or from saved outputs on disk.
"""

import re
from pathlib import Path
from typing import Any, Dict, Optional

from shared.logging_utils import get_logger

from ..hpo.study_extractor import extract_best_config_from_study
from .disk_loader import load_best_trial_from_disk
from orchestration.path_resolution import resolve_hpo_output_dir

logger = get_logger(__name__)


def find_study_folder_in_backbone_dir(backbone_dir: Path) -> Optional[Path]:
    """
    Find study folder inside backbone directory.

    In the new structure, trials are inside study folders like:
    backbone_dir/study_name/trial_0/...

    Args:
        backbone_dir: Backbone directory containing study folders

    Returns:
        Path to study folder if found, else None
    """
    if not backbone_dir.exists():
        return None

    for item in backbone_dir.iterdir():
        if item.is_dir() and not item.name.startswith("trial_"):
            has_trials = any(
                subitem.is_dir() and subitem.name.startswith("trial_")
                for subitem in item.iterdir()
            )
            if has_trials:
                return item

    return None


def find_best_trial_from_study(
    study: Any,
    backbone_name: str,
    dataset_version: str,
    objective_metric: str,
    hpo_backbone_dir: Path,
) -> Optional[Dict[str, Any]]:
    """
    Find best trial from an Optuna study object.

    Uses study.best_trial (source of truth) and locates the corresponding
    trial directory on disk.

    Args:
        study: Optuna study object
        backbone_name: Model backbone name
        dataset_version: Dataset version string
        objective_metric: Objective metric name
        hpo_backbone_dir: HPO backbone output directory

    Returns:
        Dictionary with best trial info, or None if not found
    """
    if not study or study.best_trial is None:
        return None

    try:
        best_trial_config = extract_best_config_from_study(
            study, backbone_name, dataset_version, objective_metric
        )

        study_folder = find_study_folder_in_backbone_dir(hpo_backbone_dir)
        if not study_folder:
            logger.debug(f"Study folder not found in {hpo_backbone_dir}")
            return None

        # Use study.best_trial directly (source of truth from Optuna)
        best_trial_number = study.best_trial.number
        best_trial_dir = None

        # Find trial directory matching best_trial.number
        for trial_dir in study_folder.iterdir():
            if not trial_dir.is_dir() or not trial_dir.name.startswith("trial_"):
                continue
            # Extract trial number from directory name (e.g., trial_1_20260104_201132 -> 1)
            match = re.match(r"trial_(\d+)_", trial_dir.name)
            if match and int(match.group(1)) == best_trial_number:
                best_trial_dir = trial_dir
                break

        # Construct best_trial_from_disk from study.best_trial
        if best_trial_dir:
            best_trial_from_disk = {
                "trial_name": best_trial_dir.name,
                "trial_dir": str(best_trial_dir),
                "checkpoint_dir": None,  # Will be determined later
                "checkpoint_type": "unknown",
                "accuracy": best_trial_config.get("selection_criteria", {}).get("best_value"),
                "metrics": best_trial_config.get("metrics", {}),
                "hyperparameters": best_trial_config.get("hyperparameters", {}),
            }
        else:
            # Fallback: trial directory not found, use best_trial_config
            logger.warning(
                f"Trial directory for trial {best_trial_number} not found in {study_folder}, "
                "using metadata from study"
            )
            best_trial_from_disk = {
                "trial_name": f"trial_{best_trial_number}",
                "trial_dir": str(study_folder / f"trial_{best_trial_number}"),
                "checkpoint_dir": None,
                "checkpoint_type": "unknown",
                "accuracy": best_trial_config.get("selection_criteria", {}).get("best_value"),
                "metrics": best_trial_config.get("metrics", {}),
                "hyperparameters": best_trial_config.get("hyperparameters", {}),
            }

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

    First tries to use in-memory study objects if available, otherwise
    searches disk for saved trial outputs.

    Args:
        backbone_values: List of backbone model names
        hpo_studies: Optional dictionary of backbone -> Optuna study
        hpo_config: HPO configuration dictionary
        data_config: Data configuration dictionary
        root_dir: Project root directory
        environment: Platform environment (e.g., "colab", "local")

    Returns:
        Dictionary mapping backbone -> best trial info
    """
    best_trials = {}
    objective_metric = hpo_config["objective"]["metric"]
    dataset_version = data_config.get("version", "unknown")

    hpo_output_dir_new = root_dir / "outputs" / "hpo" / environment

    for backbone in backbone_values:
        backbone_name = backbone.split("-")[0] if "-" in backbone else backbone

        logger.info(f"Looking for best trial for {backbone} ({backbone_name})...")

        best_trial_info = None

        # Try to use in-memory study if available
        if hpo_studies and backbone_name in hpo_studies:
            study = hpo_studies[backbone_name]
            local_path = hpo_output_dir_new / backbone_name
            hpo_backbone_dir = resolve_hpo_output_dir(local_path)

            if hpo_backbone_dir.exists():
                best_trial_from_disk = find_best_trial_from_study(
                    study, backbone_name, dataset_version, objective_metric, hpo_backbone_dir
                )

                if best_trial_from_disk:
                    best_trial_info = {
                        "backbone": backbone_name,
                        "trial_name": best_trial_from_disk["trial_name"],
                        "trial_dir": best_trial_from_disk["trial_dir"],
                        "checkpoint_dir": best_trial_from_disk.get(
                            "checkpoint_dir",
                            str(Path(best_trial_from_disk["trial_dir"]) / "checkpoint"),
                        ),
                        "checkpoint_type": best_trial_from_disk.get("checkpoint_type", "unknown"),
                        "accuracy": best_trial_from_disk["accuracy"],
                        "metrics": best_trial_from_disk["metrics"],
                        "hyperparameters": best_trial_from_disk["hyperparameters"],
                    }
                    logger.info(
                        f"{backbone}: Best trial from HPO run is {best_trial_info['trial_name']} "
                        f"({objective_metric}={best_trial_info['accuracy']:.4f})"
                    )

        # Fallback to disk search if study not available or didn't find trial
        if best_trial_info is None:
            logger.debug(f"Searching disk for best trial for {backbone_name}...")
            local_path = hpo_output_dir_new / backbone_name
            hpo_backbone_dir = resolve_hpo_output_dir(local_path)

            if hpo_backbone_dir.exists():
                study_folder = find_study_folder_in_backbone_dir(hpo_backbone_dir)
                if study_folder:
                    best_trial_info = load_best_trial_from_disk(
                        study_folder.parent.parent,
                        f"{backbone_name}/{study_folder.name}",
                        objective_metric,
                    )
                elif str(hpo_backbone_dir).startswith("/content/drive"):
                    drive_hpo_dir = hpo_backbone_dir.parent.parent
                    relative_backbone = f"{environment}/{backbone_name}"
                    best_trial_info = load_best_trial_from_disk(
                        drive_hpo_dir,
                        relative_backbone,
                        objective_metric,
                    )
                else:
                    best_trial_info = load_best_trial_from_disk(
                        hpo_output_dir_new.parent,
                        f"{environment}/{backbone_name}",
                        objective_metric,
                    )
            else:
                # Try old structure
                hpo_output_dir_old = root_dir / "outputs" / "hpo"
                old_backbone_dir = resolve_hpo_output_dir(hpo_output_dir_old / backbone)
                if old_backbone_dir.exists():
                    study_folder = find_study_folder_in_backbone_dir(old_backbone_dir)
                    if study_folder:
                        best_trial_info = load_best_trial_from_disk(
                            study_folder.parent.parent,
                            f"{backbone}/{study_folder.name}",
                            objective_metric,
                        )
                    elif str(old_backbone_dir).startswith("/content/drive"):
                        drive_hpo_dir = old_backbone_dir.parent
                        best_trial_info = load_best_trial_from_disk(
                            drive_hpo_dir,
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
                logger.info(
                    f"Found best trial for {backbone}: {best_trial_info.get('trial_name', 'unknown')} "
                    f"({objective_metric}={best_trial_info.get('accuracy', 0):.4f})"
                )

        if best_trial_info:
            best_trials[backbone] = best_trial_info
        else:
            logger.warning(f"No best trial found for {backbone}")

    logger.info(
        f"Summary: Found {len(best_trials)} best trial(s) out of {len(backbone_values)} backbone(s)"
    )
    return best_trials


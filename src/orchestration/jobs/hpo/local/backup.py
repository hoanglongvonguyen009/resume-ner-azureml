"""
@meta
name: hpo_backup
type: utility
domain: hpo
responsibility:
  - Backup HPO study.db and study folders to Google Drive
  - Verify trial_meta.json files
inputs:
  - HPO study directories
  - Checkpoint configuration
outputs:
  - Backup verification status
tags:
  - utility
  - hpo
  - backup
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""HPO backup utilities for Colab environments.

Handles backing up study.db and study folders to Google Drive,
with verification of trial_meta.json files.
"""

from pathlib import Path
from typing import Optional, Callable

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def backup_hpo_study_to_drive(
    backbone: str,
    backbone_output_dir: Path,
    checkpoint_config: dict,
    hpo_config: dict,
    backup_to_drive: Callable[[Path, bool], bool],
    backup_enabled: bool = True,
) -> None:
    """
    Backup HPO study.db and study folder to Google Drive.

    Args:
        backbone: Model backbone name
        backbone_output_dir: Base output directory for HPO
        checkpoint_config: Checkpoint configuration dict
        hpo_config: HPO configuration dict
        backup_to_drive: Function to backup files to Drive
        backup_enabled: Whether backup is enabled
    """
    if not backup_enabled:
        return

    # Get study name (for Optuna study name, not for path resolution)
    study_name_template = checkpoint_config.get(
        "study_name") or hpo_config.get("study_name")
    study_name = None
    if study_name_template:
        study_name = study_name_template.replace("{backbone}", backbone)

    # Find v2 study folder using v2 folder discovery (not study_name-based paths)
    from evaluation.selection.trial_finder import find_study_folder_in_backbone_dir

    # Use v2 folder discovery to find the actual study folder
    study_folder = find_study_folder_in_backbone_dir(backbone_output_dir)
    
    # Get the actual storage path from v2 folder
    if study_folder and study_folder.exists():
        actual_storage_path = study_folder / "study.db"
    else:
        # Fallback: try to resolve using legacy method (for backward compatibility)
        from training.hpo.checkpoint.storage import resolve_storage_path
        actual_storage_path = resolve_storage_path(
            output_dir=backbone_output_dir,
            checkpoint_config=checkpoint_config,
            backbone=backbone,
            study_name=study_name,
            create_dirs=False,  # Read-only path resolution
        )
        if actual_storage_path and actual_storage_path.exists():
            study_folder = actual_storage_path.parent
        else:
            study_folder = None

    # Backup study.db
    if actual_storage_path and str(actual_storage_path).startswith("/content/drive"):
        # File is already in Drive - no need to backup, just log
        logger.info(
            f"HPO checkpoint is already in Drive: {actual_storage_path}")
        if study_name:
            logger.info(f"  Study name: {study_name}")
    elif actual_storage_path and actual_storage_path.exists():
        # File exists locally - backup it
        backup_to_drive(actual_storage_path, is_directory=False)
        logger.info(
            f"Backed up HPO checkpoint database to Drive: {actual_storage_path}")
    else:
        logger.warning(f"HPO checkpoint not found")
        logger.warning(f"  Resolved path: {actual_storage_path}")
        if study_name:
            logger.warning(f"  Study name: {study_name}")

    # Backup entire study folder (v2 structure: outputs/hpo/{env}/{model}/study-{hash}/...)
    # Check if checkpoint is already in Drive - if so, study folder is also in Drive
    checkpoint_in_drive = actual_storage_path and str(
        actual_storage_path).startswith("/content/drive")

    # If we didn't find study_folder yet, search in Drive as well
    if not study_folder or not study_folder.exists():
        # Search for v2 study folder in Drive locations
        # Use unified path mapping instead of hardcoded string replacement
        from infrastructure.paths import get_drive_backup_path
        from infrastructure.paths.repo import detect_repo_root
        
        try:
            # Auto-detect root_dir and config_dir
            root_dir = detect_repo_root(output_dir=backbone_output_dir)
            config_dir = root_dir / "config"
            
            # Map local path to Drive path using unified function
            drive_dir = get_drive_backup_path(
                local_path=backbone_output_dir,
                root_dir=root_dir,
                config_dir=config_dir,
            )
            
            # Search in Drive directory if available
            if drive_dir and drive_dir.exists():
                study_folder = find_study_folder_in_backbone_dir(drive_dir)
                if study_folder:
                    logger.debug(f"Found v2 study folder in Drive: {study_folder}")
        except Exception as e:
            logger.debug(f"Could not search Drive for study folder: {e}")

    # Do NOT use old study_name format - only v2 paths are supported
    # If v2 folder not found, study_folder will be None and we'll skip backup

    if study_folder and study_folder.exists():
        if checkpoint_in_drive:
            # study.db and study folder are already in Drive
            # Verify trial_meta.json files exist in Drive
            logger.info(f"Study folder is in Drive: {study_folder}")
            # Look for both v2 format (trial-{hash}) and legacy format (trial_*)
            trial_dirs = [d for d in study_folder.iterdir() if d.is_dir() and (
                d.name.startswith("trial-") or d.name.startswith("trial_"))]
            trial_meta_count = 0
            for trial_dir in trial_dirs:
                trial_meta_path = trial_dir / "trial_meta.json"
                if trial_meta_path.exists():
                    trial_meta_count += 1
                else:
                    logger.warning(
                        f"Missing trial_meta.json in {trial_dir.name}")
            if trial_meta_count > 0:
                logger.info(
                    f"Found {trial_meta_count} trial_meta.json file(s) in Drive")
            else:
                logger.warning(
                    "No trial_meta.json files found in Drive study folder")
        else:
            # study.db is local, backup the entire study folder (includes study.db + all trials + trial_meta.json)
            result = backup_to_drive(study_folder, is_directory=True)
            if result:
                logger.info(
                    f"Backed up entire study folder to Drive: {study_folder.name}")

                # Verify trial_meta.json files were backed up
                # Look for both v2 format (trial-{hash}) and legacy format (trial_*)
                trial_dirs = [d for d in study_folder.iterdir() if d.is_dir() and (
                    d.name.startswith("trial-") or d.name.startswith("trial_"))]
                for trial_dir in trial_dirs:
                    trial_meta_path = trial_dir / "trial_meta.json"
                    if trial_meta_path.exists():
                        # Check if it was backed up (Drive path should exist)
                        # Use unified path mapping instead of hardcoded string replacement
                        try:
                            drive_trial_meta = get_drive_backup_path(
                                local_path=trial_meta_path,
                                root_dir=root_dir,
                                config_dir=config_dir,
                            )
                            if drive_trial_meta and drive_trial_meta.exists():
                                logger.debug(
                                    f"Verified trial_meta.json backed up: {trial_dir.name}/trial_meta.json")
                            else:
                                logger.warning(
                                    f"trial_meta.json not found in backup: {trial_dir.name}/trial_meta.json")
                        except Exception as e:
                            logger.debug(f"Could not verify Drive path for trial_meta.json: {e}")
            else:
                logger.warning(
                    f"Failed to backup study folder: {study_folder.name}")
    elif checkpoint_in_drive:
        # Checkpoint is in Drive, so study folder is also in Drive (not local)
        # This is expected behavior in Colab - no error needed
        logger.info(
            f"Study folder is in Drive (checkpoint already backed up): {actual_storage_path.parent if actual_storage_path else 'N/A'}")
    else:
        # Checkpoint is local but study folder doesn't exist - this is an error
        logger.warning(f"Study folder not found: {study_folder}")

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
from typing import Optional, Callable, Any

from common.shared.logging_utils import get_logger
from common.shared.platform_detection import is_drive_path
from training.hpo.core.optuna_integration import import_optuna as _import_optuna

logger = get_logger(__name__)


def create_incremental_backup_callback(
    target_path: Path,
    backup_to_drive: Callable[[Path, bool], bool],
    backup_enabled: bool = True,
    is_directory: bool = False,
) -> Callable[[Any, Any], None]:
    """
    Create reusable Optuna callback for incremental backup of files or directories.

    This callback backs up the target path after each trial completes, making it
    suitable for incremental backup of study.db or other files/folders during HPO.

    Args:
        target_path: Path to file or directory to backup (e.g., study.db)
        backup_to_drive: Function to backup files to Drive (takes Path and bool)
        backup_enabled: Whether backup is enabled (if False, callback does nothing)
        is_directory: Whether target_path is a directory (False for files)

    Returns:
        Optuna callback function that can be passed to study.optimize()
    """
    def trial_complete_callback(study: Any, trial: Any) -> None:
        """Callback to backup target path after trial completes."""
        if not backup_enabled:
            return

        # Import Optuna to check trial state
        optuna_module, _, _, _ = _import_optuna()

        # Only backup on trial completion (not on failure/pruning)
        if trial.state != optuna_module.trial.TrialState.COMPLETE:
            return

        # Skip backup if path is already in Drive
        if is_drive_path(target_path):
            logger.debug(
                f"Skipping backup - path is already in Drive: {target_path}"
            )
            return

        # Skip backup if target doesn't exist
        if not target_path.exists():
            logger.debug(
                f"Skipping backup - target path does not exist: {target_path}"
            )
            return

        # Perform backup
        try:
            result = backup_to_drive(target_path, is_directory=is_directory)
            if result:
                logger.debug(
                    f"Incremental backup successful: {target_path.name} "
                    f"(trial {trial.number})"
                )
            else:
                logger.warning(
                    f"Incremental backup failed: {target_path.name} "
                    f"(trial {trial.number})"
                )
        except Exception as e:
            # Log error but don't crash HPO
            logger.warning(
                f"Incremental backup error for {target_path.name} "
                f"(trial {trial.number}): {e}"
            )

    return trial_complete_callback


def create_study_db_backup_callback(
    target_path: Path,
    backup_to_drive: Callable[[Path, bool], bool],
    backup_enabled: bool = True,
) -> Callable[[Any, Any], None]:
    """
    Create Optuna callback for incremental backup of study.db.

    Convenience wrapper around create_incremental_backup_callback() specifically
    for study.db files (is_directory=False).

    Args:
        target_path: Path to study.db file
        backup_to_drive: Function to backup files to Drive (takes Path and bool)
        backup_enabled: Whether backup is enabled (if False, callback does nothing)

    Returns:
        Optuna callback function that can be passed to study.optimize()
    """
    return create_incremental_backup_callback(
        target_path=target_path,
        backup_to_drive=backup_to_drive,
        backup_enabled=backup_enabled,
        is_directory=False,
    )


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

    Simplified version that only backs up from canonical local root.
    No mixed-state handling - just checks if canonical folder is Drive or local.

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

    # Find canonical study folder in backbone_output_dir (v2 structure)
    from evaluation.selection.trial_finder import find_study_folder_in_backbone_dir

    study_folder = find_study_folder_in_backbone_dir(backbone_output_dir)

    # If study folder not found, skip backup
    if not study_folder or not study_folder.exists():
        logger.warning(f"Study folder not found in {backbone_output_dir}")
        return

    # Check if canonical folder is Drive or local
    study_folder_in_drive = is_drive_path(study_folder)

    if study_folder_in_drive:
        # Already in Drive - verify only (no backup needed)
        logger.info(f"Study folder is already in Drive: {study_folder}")
        
        # Verify trial_meta.json files exist in Drive
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
        # Local - backup study.db and study folder
        storage_path = study_folder / "study.db"
        
        # Backup study.db
        if storage_path.exists():
            result = backup_to_drive(storage_path, is_directory=False)
            if result:
                logger.info(
                    f"Backed up HPO checkpoint database to Drive: {storage_path.name}")
            else:
                logger.warning(
                    f"Failed to backup HPO checkpoint database: {storage_path.name}")
        else:
            logger.warning(f"study.db not found: {storage_path}")

        # Backup entire study folder (includes study.db + all trials + trial_meta.json)
        result = backup_to_drive(study_folder, is_directory=True)
        if result:
            logger.info(
                f"Backed up entire study folder to Drive: {study_folder.name}")

            # Verify trial_meta.json files were backed up
            trial_dirs = [d for d in study_folder.iterdir() if d.is_dir() and (
                d.name.startswith("trial-") or d.name.startswith("trial_"))]
            for trial_dir in trial_dirs:
                trial_meta_path = trial_dir / "trial_meta.json"
                if trial_meta_path.exists():
                    # Note: Verification would require Drive path mapping, but since
                    # backup_to_drive succeeded, we trust the backup worked
                    logger.debug(
                        f"trial_meta.json exists in local study folder: {trial_dir.name}/trial_meta.json")
        else:
            logger.warning(
                f"Failed to backup study folder: {study_folder.name}")
